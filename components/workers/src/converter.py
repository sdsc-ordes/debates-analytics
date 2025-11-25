import os
import logging
from rq import get_current_job

# Import shared libraries
from lib.s3 import get_s3_manager
from lib.queue import get_queue_manager
from lib.filesystem import temp_workspace
from lib.media import convert_to_wav
from lib.mongo import get_mongo_manager

logger = logging.getLogger(__name__)

def process_video(s3_key, media_id):
    """
    1. Downloads video from S3
    2. Converts to WAV
    3. Uploads WAV to S3
    4. Updates MongoDB
    5. Enqueues Transcription Job
    """
    # Setup Dependencies
    s3 = get_s3_manager()
    queue = get_queue_manager()
    db = get_mongo_manager()
    job = get_current_job()

    logger.info(f"Job {media_id}: Starting processing")

    # Update Job Status (Redis)
    job.meta['progress'] = 'downloading'
    job.save_meta()

    # Update DB Status
    db.update_status(media_id, "converting_started")

    try:
        # Context Manager handles filesystem cleanup automatically
        with temp_workspace() as work_dir:

            # Define Paths
            local_video = os.path.join(work_dir, "source.mp4")
            local_wav = os.path.join(work_dir, "audio.wav")
            s3_wav_key = f"{media_id}/audio.wav"

            # Download
            s3.download_file(s3_key, local_video)

            # Convert
            job.meta['progress'] = 'converting'
            job.save_meta()
            db.update_status(media_id, "converting_processing")

            convert_to_wav(local_video, local_wav)

            # 4. Upload to S3
            job.meta['progress'] = 'uploading'
            job.save_meta()

            s3.upload_file(local_wav, s3_wav_key)

            db.update_status(
                media_id,
                status="converting_completed",
                metadata={"audio_s3_key": s3_wav_key}
            )

            logger.info(f"Job {media_id}: Enqueuing transcription...")
            queue.enqueue(
                'transcriber.process_transcription',
                media_id=media_id,
                s3_key=s3_wav_key,
                job_timeout=-1
            )

            return {"status": "completed", "wav_key": s3_wav_key}

    except Exception as e:
        logger.error(f"Job {media_id} Failed: {e}")

        db.mark_failed(media_id, str(e))

        # re-raise the exception so RQ marks the job as 'Failed' in Redis
        raise e
