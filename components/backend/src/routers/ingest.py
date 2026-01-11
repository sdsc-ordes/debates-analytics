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
    """
    filename = request_data.filename
    logger.info(f"Upload initiated for filename='{filename}'")

    # 2. Assign Identity
    media_id = str(uuid.uuid4())
    logger.info(f"Media_id={media_id} - Assigned new Media ID.")

    media_type = ""
    s3_key = ""

    if _is_video_file(filename):
        s3_key = f"{media_id}/source.mp4"
        media_type = "video"
    elif _is_audio_file(filename):
        s3_key = f"{media_id}/source.wav"
        media_type = "audio"
    else:
        logger.warning(f"Media_id={media_id} - Upload rejected: Unsupported file type '{filename}'")
        raise HTTPException(status_code=400, detail="Unsupported file type. Only MP4 and WAV are allowed.")

    logger.info(f"Media_id={media_id} - Logic resolved: Type={media_type}, TargetKey={s3_key}")

    # 4. External Service: S3
    try:
        post_data = s3_client.get_presigned_post(s3_key)
        logger.info(f"Media_id={media_id} - S3 Presigned URL generated successfully.")
    except Exception:
        logger.exception(f"Media_id={media_id} - CRITICAL: S3 Presigned URL generation failed.")
        raise HTTPException(status_code=500, detail="Storage service unavailable.")

    try:
        mongo_client.insert_initial_media_document(
            media_id=media_id,
            s3_key=s3_key,
            filename=filename,
            media_type=media_type,
        )
        logger.info(f"Media_id={media_id} - MongoDB document initialized.")
    except Exception:
        logger.exception(f"Media_id={media_id} - CRITICAL: MongoDB initialization failed.")
        raise HTTPException(status_code=500, detail="Database error")

    logger.info(f"Media_id={media_id} - Upload handshake complete. Returning to client.")

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
    [POST] Starts processing: starts redis queue with first task.
    """
    media_id = request.media_id
    file_type = request.file_type
    s3_key = request.s3_key
    job = None

    # Log Intent immediately with Media_id ID
    logger.info(f"media_id={media_id} - PROCESSING request received. Type={file_type}")

    try:
        # Enqueue Job (Specific logs replace generic ones)
        if file_type == FileType.video:
            job = rq.enqueue_video_processing(media_id=media_id, s3_key=s3_key)
            logger.info(f"media_id={media_id} - Video job enqueued. JobID={job.get_id()}")

        elif file_type == FileType.audio:
            job = rq.enqueue_audio_processing(media_id=media_id, s3_key=s3_key)
            logger.info(f"media_id={media_id} - Audio job enqueued. JobID={job.get_id()}")

        else:
            # Log as Warning (User Error)
            logger.warning(f"media_id={media_id} - Processing rejected: Unsupported file type '{file_type}'")
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {file_type}")

        job_id = job.get_id()

        # Update DB Status to 'queued'
        result = mongo.update_processing_status(
            media_id=media_id,
            status="queued",
            job_id=job_id,
        )

        # 4. Validation: Check for Data Inconsistency
        if not result:
            # Log as Error because this SHOULD have existed from the upload step
            logger.error(f"media_id={media_id} - Data Inconsistency: Media ID not found in MongoDB during process start.")
            raise ValueError(f"media ID {media_id} not found in MongoDB")

        logger.info(f"media_id={media_id} - MongoDB status updated to 'queued'.")

        return {
            "status": "queued",
            "media_id": media_id,
            "job_id": job_id,
        }

    except Exception as e:
        # Rollback Logic (Crucial for debugging stuck jobs)
        if job:
            logger.warning(f"media_id={media_id} - Error detected. Rolling back JobID={job.get_id()}...")
            try:
                job.delete()
                logger.info(f"media_id={media_id} - Rollback successful: Job deleted.")
            except Exception as cleanup_error:
                # Log this separately so you know why you have 'ghost' jobs
                logger.exception(f"media_id={media_id} - Rollback FAILED: {cleanup_error}")

        # 6. Exception Handling / Categorization
        if isinstance(e, ValueError):
            raise HTTPException(status_code=404, detail=str(e))

        if isinstance(e, HTTPException):
            raise e

        # Catch-all for unexpected crashes
        logger.exception(f"media_id={media_id} - CRITICAL: Processing failed unexpectedly.")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process video: {str(e)}"
        )
