import logging
import uuid
from fastapi import APIRouter, HTTPException, Depends
from services.s3 import get_s3_manager, S3Manager
from services.queue import get_queue_manager, QueueManager
from services.mongo import get_mongo_manager, MongoManager
from models.ingest import S3PostRequest, S3PostResponse, ProcessRequest, FileType

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
    filename = request_data.filename
    media_type = ""
    if _is_video_file(filename):
        s3_key = f"{media_id}/source.mp4"
    elif _is_audio_file(filename):
        s3_key = f"{media_id}/source.wav"
        media_type = "audio"
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type. Only MP4 and WAV are allowed.")

    logger.info(f"Generating presigned POST for media_id: {media_id}, s3 key: {s3_key}")

    try:
        post_data = s3_client.get_presigned_post(s3_key)
        logger.info(f"Presigned url generated for: {s3_key}")
    except Exception:
        logger.exception(f"Failed to generate presigned URL for {media_id}")
        raise HTTPException(status_code=500, detail="Storage service unavailable.")

    try:
        mongo_client.insert_initial_media_document(
            media_id=media_id,
            s3_key=s3_key,
            filename=filename,
            media_type=media_type,
        )
        logger.info(f"Debate document created for: {media_id}")
    except Exception as e:
        logger.exception(f"Database insertion failed: {e}")
        raise HTTPException(status_code=500, detail="Database error")

    return S3PostResponse(
        postUrl=post_data["url"],
        fields=post_data["fields"],
        mediaId=media_id,
        s3Key=s3_key
    )


def _is_video_file(filename: str) -> bool:
    return filename.lower().endswith(('.mp4'))


def _is_audio_file(filename: str) -> bool:
    return filename.lower().endswith(('.wav'))


@router.post("/process")
async def start_processing(
    request: ProcessRequest,
    rq: QueueManager = Depends(get_queue_manager),
    mongo: MongoManager = Depends(get_mongo_manager),
):
    """
    [POST] Starts processing: starts redis queue with first task: converting
    the video to audio. Updates status on Mongo DB.
    Status -> 'preparing'
    """
    media_id = request.media_id
    file_type = request.file_type
    s3_key = request.s3_key
    job = None
    logger.info(f"Starting processing for media_id: {media_id}")

    try:
        logger.info(f"Creating job for media_id: {media_id}")
        status = ""
        if file_type == FileType.video:
            job = rq.enqueue_video_processing(
                media_id=media_id,
                s3_key=s3_key,
            )
        elif file_type == FileType.audio:
            job = rq.enqueue_audio_processing(
                media_id=media_id,
                s3_key=s3_key,
            )
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {file_type}")
        job_id = job.get_id()
        logger.info(f"Enqueuing job {job_id} for media_id: {media_id}")

        logger.info(f"Updating status on mongodb for: {media_id}")
        result = mongo.update_processing_status(
            media_id=media_id,
            status="queued",
            job_id=job_id,
        )

        # Validation: If MongoDB didn't find the document:
        # manually trigger the error flow,
        # so that no job runs without monitoring
        if not result:
            raise ValueError(f"Media ID {media_id} not found in MongoDB")

        logger.info(f"MongoDB update result: {result}")

        return {
            "status": "queued",
            "media_id": media_id,
            "job_id": job_id,
        }

    except Exception as e:
        # roll job back in case of an exception.
        if job:
            logger.warning(f"Error occurred. Rolling back job {job.get_id()}")
            try:
                job.delete()
            except Exception as cleanup_error:
                logger.error(f"Failed to cancel job during rollback: {cleanup_error}")

        logger.exception(f"Critical error processing media_id {media_id}")

        if isinstance(e, ValueError):
            raise HTTPException(status_code=404, detail=str(e))

        raise HTTPException(
            status_code=500,
            detail=f"Failed to process video: {str(e)}"
        )
