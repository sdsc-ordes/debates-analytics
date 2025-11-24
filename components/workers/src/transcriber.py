import os
import boto3
import logging
import shutil # For safer file cleanup
from pymongo import MongoClient # You need to update the DB!
from bson.objectid import ObjectId
from gradio_client import Client, handle_file
from rq import get_current_job

# --- Configuration ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment Variables
TEMP_DIR = "/tmp/processing"
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "debates")
BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
HF_TOKEN = os.getenv("HF_TOKEN")
HF_SPACE_URL = os.getenv("HF_SPACE_URL")

# Clients
s3_client = boto3.client(
    's3',
    endpoint_url=os.getenv("S3_SERVER"),
    aws_access_key_id=os.getenv("S3_ACCESS_KEY"),
    aws_secret_access_key=os.getenv("S3_SECRET_KEY")
)
BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
HF_TOKEN = os.getenv("HF_TOKEN")
HF_SPACE_URL = os.getenv("HF_SPACE_URL")
HF_MODEL = os.getenv("HF_MODEL")

mongo_client = MongoClient(MONGO_URI)
db = mongo_client[DB_NAME]

os.makedirs(TEMP_DIR, exist_ok=True)

def process_transcription(s3_key, media_id):
    """
    Downloads audio, runs Transcription AND Translation, updates DB.
    """
    job = get_current_job()
    job_id = job.get_id()
    job.meta['progress'] = 'transcribing'
    job.save_meta()

    # Create a unique temp folder for this specific job to avoid collisions
    job_temp_dir = os.path.join(TEMP_DIR, str(media_id))
    os.makedirs(job_temp_dir, exist_ok=True)

    local_input_path = os.path.join(job_temp_dir, "input.wav")

    logger.info(f"Job {media_id}: Starting processing for {s3_key}")

    try:
        # Download WAV from S3
        logger.info(f"Job {job_id}: Downloading {s3_key}...")
        s3_client.download_file(BUCKET_NAME, s3_key, local_input_path)

        # Initialize Client
        client = Client(HF_SPACE_URL)

        # ---------------------------------------------------------
        # PASS 1: TRANSCRIPTION (Original Language)
        # ---------------------------------------------------------
        logger.info(f"Job {job_id}: Running Transcription...")
        res_transcribe = client.predict(
            audio_file=handle_file(local_input_path),
            youtube_link="",
            model="large-v3",
            task="transcribe",
            language="auto",
            quantize=False,
            api_name="/process_audio",
            hf_token=HF_TOKEN,
        )

        # ---------------------------------------------------------
        # PASS 2: TRANSLATION (English)
        # ---------------------------------------------------------
        logger.info(f"Job {job_id}: Running Translation...")
        res_translate = client.predict(
            audio_file=handle_file(local_input_path),
            youtube_link="",
            model="large-v3",
            task="translate",
            language="en",
            quantize=False,
            api_name="/process_audio",
            hf_token=HF_TOKEN,
        )

        # ---------------------------------------------------------
        # MAP & UPLOAD
        # ---------------------------------------------------------

        # Combine results into one dictionary so we don't overwrite!
        artifacts_map = {
            # Transcription Files
            "subtitles-original.srt": res_transcribe[3],
            "subtitles-original.json": res_transcribe[4],
            "segments-original.json": res_transcribe[5],
            "segments-original.md": res_transcribe[6],
            "segments-original.pdf": res_transcribe[7],

            # Translation Files
            "subtitles-translation.srt": res_translate[3],
            "subtitles-translation.json": res_translate[4],
            "segments-translation.json": res_translate[5],
            "segments-translation.md": res_translate[6],
            "segments-translation.pdf": res_translate[7],
        }

        logger.info(f"Job {job_id}: Uploading artifacts to S3...")

        s3_base_path = f"{media_id}/transcripts"
        uploaded_files = {}

        for filename, local_path in artifacts_map.items():
            if local_path and os.path.exists(local_path):
                s3_dest_key = f"{s3_base_path}/{filename}"
                s3_client.upload_file(local_path, BUCKET_NAME, s3_dest_key)
                uploaded_files[filename] = s3_dest_key

        logger.info(f"Job {job_id}: Complete.")
        return {"status": "completed"}

    except Exception as e:
        logger.error(f"Job {job_id} Failed: {e}")

        raise e

    finally:
        # ALWAYS cleanup, even if successful or if it crashed
        if os.path.exists(job_temp_dir):
            shutil.rmtree(job_temp_dir)
            logger.info(f"Cleaned up temp dir: {job_temp_dir}")
