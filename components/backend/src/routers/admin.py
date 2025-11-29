from fastapi import APIRouter, Depends, HTTPException

from models.metadata import MediaListResponse, MediaListItem, ProcessingStatusResponse
from services.mongo import get_mongo_manager, MongoManager
from services.queue import get_queue_manager, QueueManager
from services.s3 import get_s3_manager, S3Manager
from services.solr import get_solr_manager, SolrManager

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
    s3.delete_media_folder(media_id)

    solr.delete_by_media_id(media_id)

    deleted = mongo.delete_everything(media_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Media not found in DB")

    return {"status": "deleted", "media_id": media_id}
