import logging
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from models.admin import (
    MediaListResponse, MediaListItem, ReindexMediaRequest,
    DeleteMediaRequest, DeleteMediaResponse, ReindexMediaResponse
)
from services.mongo import get_mongo_manager, MongoManager
from services.s3 import get_s3_manager, S3Manager
from services.solr import get_solr_manager, SolrManager
from tasks.reindex import reindex_solr

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/list", response_model=MediaListResponse)
async def list_media(
    mongo: MongoManager = Depends(get_mongo_manager)
):
    """
    Returns a list of all uploaded media for the dashboard.
    """
    docs = mongo.get_all_media()

    items = []
    for d in docs:
        items.append(MediaListItem(
            media_id=d.get("media_id", str(d.get("_id"))), # Fallback if media_id missing
            filename=d.get("original_filename", "Unknown"),
            status=d.get("status", "unknown"),
            created_at=d.get("created_at"),
            title=d.get("title")
        ))
    logger.info(f"media list {items}")

    return MediaListResponse(items=items, total=len(items))


@router.post("/delete", response_model=DeleteMediaResponse)
async def delete_media(
    request: DeleteMediaRequest,
    mongo: MongoManager = Depends(get_mongo_manager),
    s3: S3Manager = Depends(get_s3_manager),
    solr: SolrManager = Depends(get_solr_manager),
):
    """
    Nuclear Option: Deletes EVERYTHING.
    Uses 'Best Effort' strategy: if one service fails, it logs the error
    but continues trying to delete the others.
    """
    logger.info(f"request delete: {request}")
    media_id = request.mediaId
    cleanup_errors = []

    # 1. Try S3 (Soft Fail)
    try:
        s3.delete_media_folder(media_id)
    except Exception as e:
        logger.error(f"Failed to delete S3 files for {media_id}: {e}")
        cleanup_errors.append("S3 cleanup failed")

    # 2. Try Solr (Soft Fail)
    try:
        solr.delete_by_media_id(media_id)
    except Exception as e:
        logger.error(f"Failed to delete Solr index for {media_id}: {e}")
        cleanup_errors.append("Solr cleanup failed")

    # 3. Try MongoDB (The Source of Truth)
    # We attempt this even if S3/Solr failed, because we want to remove it from the UI.
    try:
        deleted = mongo.delete_everything(media_id)
        if not deleted:
            # If it wasn't in Mongo, we consider it a 404 (Not Found)
            raise HTTPException(status_code=404, detail="Media not found in DB")

    except HTTPException:
        raise # Re-raise 404
    except Exception as e:
        logger.error(f"Failed to delete MongoDB docs for {media_id}: {e}")
        raise HTTPException(status_code=500, detail="Database deletion failed")

    # 4. Return Status
    if cleanup_errors:
        # Return 200 but warn the frontend that some cleanup failed (Ghost files might remain)
        return {
            "status": "partial_deleted",
            "media_id": media_id,
            "warnings": cleanup_errors
        }

    return {"status": "deleted", "mediaId": media_id}


@router.post("/reindex", response_model=ReindexMediaResponse)
async def reindex_media(
    request: ReindexMediaRequest,
    background_tasks: BackgroundTasks,
    mongo: MongoManager = Depends(get_mongo_manager)
):
    """
    Triggers the Solr Indexing process manually.
    Useful if you changed the Solr schema or parser logic.
    """
    logger.info(f"request reindex: {request}")
    media_id = request.mediaId
    # 1. Validate ID exists
    doc = mongo.media_collection.find_one({"media_id": media_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Media not found")

    # 2. Run in background (don't block the HTTP request)
    background_tasks.add_task(reindex_solr, media_id)

    return {"status": "indexing_started", "media_id": media_id}
