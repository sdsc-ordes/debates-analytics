import logging
import uuid
from fastapi import APIRouter, HTTPException, Depends
from services.s3 import get_s3_manager, S3Manager
from services.queue import get_queue_manager, QueueManager
from services.mongo import get_mongo_manager, MongoManager
from models import S3PostRequest, S3PostResponse, ProcessRequest

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/get-presigned-post", response_model=S3PostResponse)
async def get_presigned_post(
    request_data: S3PostRequest,
    s3_client: S3Manager = Depends(get_s3_manager),
    mongo_client: MongoManager = Depends(get_mongo_manager),
):
    """
    [POST] Returns a presigned URL and creates the initial Mongodb record.
    Status -> 'preparing'
    """
    media_id = str(uuid.uuid4())
    s3_key = f"{media_id}/source.mp4"

    logging.info(f"Generating presigned POST for media_id: {media_id}")

    try:
        post_data = s3_client.get_presigned_post(s3_key)
    except Exception:
        logger.exception(f"Failed to generate presigned URL for {media_id}")
        raise HTTPException(status_code=500, detail="Storage service unavailable.")

    try:
        mongo_client.insert_initial_media_document(
            media_id=media_id,
            s3_key=s3_key,
            filename=request_data.filename,
        )
    except Exception as e:
        logger.exception(f"Database insertion failed: {e}")
        raise HTTPException(status_code=500, detail="Database error")

    return S3PostResponse(
        postUrl=post_data["url"],
        fields=post_data["fields"],
        mediaId=media_id,
        s3Key=s3_key
    )


@router.post("/process")
async def start_processing(
    request: ProcessRequest,
    rq: QueueManager = Depends(get_queue_manager),
    mongo: MongoManager = Depends(get_mongo_manager),
):
    media_id = request.media_id
    s3_key = request.s3_key
    job = None
    logger.info(f"Starting processing for media_id: {media_id}")

    try:
        logger.info(f"Creating job for media_id: {media_id}")
        job = rq.enqueue_video_processing(
            media_id=media_id,
            s3_key=s3_key,
        )
        job_id = job.get_id()
        logger.info(f"Enqueuing job {job_id} for media_id: {media_id}")

        logger.info(f"Updating status on mongodb for: {media_id}")
        result = mongo.update_processing_status(
            media_id=media_id,
            status="queued",
            job_id=job_id,
        )

        # Validation: If MongoDB didn't find the document, manually trigger the error flow
        if not result:
            raise ValueError(f"Media ID {media_id} not found in MongoDB")

        logger.info(f"MongoDB update result: {result}")

        return {
            "status": "queued",
            "media_id": media_id,
            "job_id": job_id,
        }

    except Exception as e:
        # --- Unified Rollback Logic ---

        # 3. Check if 'job' was created before the error happened
        if job:
            logger.warning(f"Error occurred. Rolling back job {job.get_id()}")
            try:
                job.delete()
            except Exception as cleanup_error:
                # Just log this, don't let it hide the real error 'e'
                logger.error(f"Failed to cancel job during rollback: {cleanup_error}")

        # 4. Handle the actual error
        logger.exception(f"Critical error processing media_id {media_id}")

        # Distinguish between 404 (ValueError) and 500 (Everything else)
        if isinstance(e, ValueError):
            raise HTTPException(status_code=404, detail=str(e))

        raise HTTPException(
            status_code=500,
            detail=f"Failed to process video: {str(e)}"
        )
