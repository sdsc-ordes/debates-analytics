import logging
from fastapi import APIRouter, Depends, HTTPException
from models.admin import (
    MediaListResponse, MediaListItem, ProcessingStatusResponse,
    DeleteMediaRequest, DeleteMediaResponse,
)
from services.mongo import get_mongo_manager, MongoManager
from services.queue import get_queue_manager, QueueManager
from services.s3 import get_s3_manager, S3Manager
from services.solr import get_solr_manager, SolrManager

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

    return MediaListResponse(items=items, total=len(items))


@router.get("/status/{media_id}", response_model=ProcessingStatusResponse)
async def check_processing_status(
    media_id: str,
    mongo: MongoManager = Depends(get_mongo_manager),
    rq: QueueManager = Depends(get_queue_manager)
):
    """
    Combines MongoDB Status (Persistent) with Redis Status (Real-time).
    Frontend should poll this every 3-5 seconds.
    """
    doc = mongo.media_collection.find_one({"media_id": media_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Media not found")

    job_id = doc.get("job_id")
    job_info = None

    if job_id:
        job_info = rq.get_job_status(job_id)

    return ProcessingStatusResponse(
        media_id=media_id,
        status=doc.get("status", "unknown"),
        job_id=job_id,
        created_at=doc.get("created_at"),
        updated_at=doc.get("updated_at"),

        job_state=job_info.get("state") if job_info else "expired",
        progress=job_info.get("progress") if job_info else None,
        error=job_info.get("error") if job_info else doc.get("error_message")
    )


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