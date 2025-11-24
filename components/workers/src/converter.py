import os
import subprocess
import boto3
import logging
from rq import get_current_job, Queue
from redis import Redis

# --- Configuration ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TEMP_DIR = "/tmp/processing"
os.makedirs(TEMP_DIR, exist_ok=True)
redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
redis_conn = Redis.from_url(redis_url)
q = Queue(connection=redis_conn)

# S3 Client
s3_client = boto3.client(
    's3',
    endpoint_url=os.getenv("S3_SERVER"),
    aws_access_key_id=os.getenv("S3_ACCESS_KEY"),
    aws_secret_access_key=os.getenv("S3_SECRET_KEY")
)
BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

def process_video(s3_key, media_id):
    """
    1. Downloads MP4 from S3 (based on media_id)
    2. Converts to WAV
    3. Uploads WAV to S3
    4. Enqueues the Transcriber job
    """
    job = get_current_job()

    # 1. Update Status
    logger.info(f"Job {media_id}: Starting processing for {s3_key}")
    job.meta['progress'] = 'downloading'
    job.save_meta()

    # Paths
    filename = os.path.basename(media_id)
    local_video_path = os.path.join(TEMP_DIR, filename)
    local_wav_path = os.path.join(TEMP_DIR, f"{filename}.wav")
    s3_wav_key = f"{media_id}/audio.wav"

    try:
        # 2. Download
        logger.info(f"Job {media_id}: Downloading...")
        s3_client.download_file(BUCKET_NAME, s3_key, local_video_path)

        # 3. Convert (FFmpeg)
        logger.info(f"Job {media_id}: Converting to WAV...")
        job.meta['progress'] = 'converting'
        job.save_meta()
        # -ar 16000 (16kHz) and -ac 1 (Mono) are standard for Whisper/Speech-to-text
        subprocess.run(
            [
                "ffmpeg", "-i", local_video_path,
                "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
                "-y", local_wav_path
            ],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )

        # 4. Upload
        logger.info(f"Job {media_id}: Uploading WAV...")
        job.meta['progress'] = 'uploading'
        job.save_meta()

        s3_client.upload_file(local_wav_path, BUCKET_NAME, s3_wav_key)

        # 5. Enqueue Transcriber (The Next Step)
        logger.info(f"Job {media_id}: Enqueuing transcription job...")

        # We pass media_id AND the specific wav_key we just created
        q.enqueue(
            'transcriber.process_transcription',
            media_id=media_id,
            s3_key=s3_wav_key,
            job_timeout=-1
        )

        # 6. Cleanup
        if os.path.exists(local_video_path):
            os.remove(local_video_path)
        if os.path.exists(local_wav_path):
            os.remove(local_wav_path)

        return {"status": "completed", "wav_key": s3_wav_key}

    except Exception as e:
        logger.error(f"Job {media_id} Failed: {e}")
        # Attempt cleanup even on fail
        if os.path.exists(local_video_path):
            os.remove(local_video_path)
        if os.path.exists(local_wav_path):
            os.remove(local_wav_path)
        raise e
