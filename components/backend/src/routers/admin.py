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
from rq.job import Job
from services.queue import get_queue_manager, QueueManager
from pymongo.errors import PyMongoError, ServerSelectionTimeoutError, ConnectionFailure

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/list", response_model=MediaListResponse)
async def list_media(
    mongo: MongoManager = Depends(get_mongo_manager)
):
    """
    Returns a list of all uploaded media for the dashboard.
    """
    logger.info("Listing all media items from MongoDB")

    try:
        docs = mongo.get_all_media()

        items = []
        for d in docs:
            items.append(MediaListItem(
                media_id=d.get("media_id", str(d.get("_id"))),
                filename=d.get("original_filename", "Unknown"),
                status=d.get("status", "unknown"),
                processing_history=d.get("processing_history", []),
                created_at=d.get("created_at"),
                title=d.get("title")
            ))

        logger.info(f"Dashboard list requested. Returning {len(items)} items.")
        return MediaListResponse(items=items, total=len(items))

    # Catch Connection Issues (DB Down / Timeout)
    except (ServerSelectionTimeoutError, ConnectionFailure) as e:
        logger.error(f"MongoDB Connection Failed: {e}")
        raise HTTPException(
            status_code=503,  # Service Unavailable
            detail="Database connection timeout. The service is temporarily unavailable."
        )

    # Catch Query/Data Issues (Permissions, Index missing, etc)
    except PyMongoError as e:
        logger.error(f"MongoDB Query Error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Database query error."
        )

    # Catch Logic Issues
    except Exception as e:
        logger.exception(f"Unexpected logic error in list_media: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal Server Error"
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
    media_id = request.mediaId
    logger.info(f"media_id={media_id} - DELETE request received.")
    cleanup_errors = []

    # Try S3 (Soft Fail)
    try:
        s3.delete_media_folder(media_id)
        logger.info(f"media_id={media_id} - S3 files deleted.")
    except Exception as e:
        logger.error(f"media_id={media_id} - S3 deletion failed: {e}", exc_info=True)
        cleanup_errors.append(f"S3 cleanup failed: {str(e)}")

    # Try Solr (Soft Fail)
    try:
        solr.delete_by_media_id(media_id)
        logger.info(f"media_id={media_id} - Solr index deleted.")
    except Exception as e:
        logger.error(f"media_id={media_id} - Solr deletion failed: {e}", exc_info=True)
        cleanup_errors.append(f"Solr cleanup failed: {str(e)}")

    # Try MongoDB (Hard Fail)
    try:
        deleted = mongo.delete_everything(media_id)
        if not deleted:
            logger.warning(f"media_id={media_id} - Not found in MongoDB during delete.")
            raise HTTPException(status_code=404, detail="Media not found in DB")

        logger.info(f"media_id={media_id} - MongoDB document deleted.")

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"media_id={media_id} - CRITICAL: MongoDB deletion failed: {e}")
        raise HTTPException(status_code=500, detail="Database deletion failed")

    # Return Status
    if cleanup_errors:
        logger.warning(f"media_id={media_id} - Completed with warnings: {cleanup_errors}")

        return {
            "status": "partial_deleted",
            "media_id": media_id,
            "warnings": cleanup_errors
        }

    logger.info(f"media_id={media_id} - Successfully deleted from all systems.")
    return {"status": "deleted", "mediaId": media_id}


@router.post("/reindex", response_model=ReindexMediaResponse)
async def reindex_media(
    request: ReindexMediaRequest,
    background_tasks: BackgroundTasks,
    mongo_client: MongoManager = Depends(get_mongo_manager)
):
    """
    Triggers the Solr Indexing process manually.
    Useful if you changed the Solr schema or parser logic.
    """
    media_id = request.mediaId
    logger.info(f"media_id={media_id} - REINDEX request received.")

    # 1. Validate ID exists
    debate = mongo_client.get_debate_metadata(media_id)
    if not debate:
        logger.warning(f"media_id={media_id} - Reindex rejected. Media ID not found.")
        raise HTTPException(status_code=404, detail="Media not found")

    background_tasks.add_task(reindex_solr, media_id)
    logger.info(f"media_id={media_id} - Reindex task queued in background.")
    return {"status": "indexing_started", "mediaId": media_id}
