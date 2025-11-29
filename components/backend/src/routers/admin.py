from fastapi import APIRouter, Depends, HTTPException
from typing import List

from models.metadata import MediaListResponse, MediaListItem, ProcessingStatusResponse
from services.mongo import get_mongo_manager, MongoManager
from services.queue import get_queue_manager, QueueManager
from services.s3 import get_s3_manager, S3Manager
from services.solr import get_solr_manager, SolrManager

router = APIRouter()

# --- 1. LIST ALL MEDIA (Dashboard) ---
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
        # Map DB document to Pydantic model
        items.append(MediaListItem(
            media_id=d.get("media_id", str(d.get("_id"))), # Fallback if media_id missing
            filename=d.get("original_filename", "Unknown"),
            status=d.get("status", "unknown"),
            created_at=d.get("created_at"),
            title=d.get("title")
        ))

    return MediaListResponse(items=items, total=len(items))


# --- 2. CHECK STATUS (Polling Endpoint) ---
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
    # 1. Get DB State
    doc = mongo.media_collection.find_one({"media_id": media_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Media not found")

    job_id = doc.get("job_id")
    job_info = None

    # 2. Get Redis State (if job exists)
    if job_id:
        job_info = rq.get_job_status(job_id)

    # 3. Construct Response
    return ProcessingStatusResponse(
        media_id=media_id,
        status=doc.get("status", "unknown"),
        job_id=job_id,
        created_at=doc.get("created_at"),
        updated_at=doc.get("updated_at"),

        # Redis details (or defaults if job is gone/expired)
        job_state=job_info.get("state") if job_info else "expired",
        progress=job_info.get("progress") if job_info else None,
        error=job_info.get("error") if job_info else doc.get("error_message")
    )


# --- 3. DELETE (Cleanup) ---
@router.delete("/{media_id}")
async def delete_media(
    media_id: str,
    mongo: MongoManager = Depends(get_mongo_manager),
    s3: S3Manager = Depends(get_s3_manager),
    solr: SolrManager = Depends(get_solr_manager)
):
    """
    Nuclear Option: Deletes EVERYTHING associated with this media_id.
    """
    # 1. S3 (Files)
    s3.delete_media_folder(media_id)

    # 2. Solr (Search Index)
    solr.delete_by_media_id(media_id)

    # 3. MongoDB (Metadata & Relations)
    # We do this last so if S3 fails, we still have the record to try again
    deleted = mongo.delete_everything(media_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Media not found in DB")

    return {"status": "deleted", "media_id": media_id}
