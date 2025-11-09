import os
import sys
import time
import logging
import subprocess
import boto3
import uuid
import json
from botocore.exceptions import NoCredentialsError
from watchdog.observers.polling import PollingObserver as Observer
from watchdog.events import FileSystemEventHandler

# --- Configuration ---
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

INPUT_DIR = "/app/input"
TEMP_DIR = "/tmp"
VIDEO_EXTENSIONS = ('.mp4')

# S3 Configuration
S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "debates")

# S3 Prefixes
S3_BASE_PREFIX = "media"  # We'll store all media under here
S3_JOB_PREFIX = "jobs/new/"

# S3 client
s3_client = boto3.client(
    's3',
    endpoint_url=S3_ENDPOINT_URL,
    aws_access_key_id=S3_ACCESS_KEY,
    aws_secret_access_key=S3_SECRET_KEY
)

def process_file(video_path):
    """
    Generates a job ID, uploads original video, converts to WAV,
    uploads WAV, and uploads a job file to S3.
    """
    success = False
    temp_wav_path = ""
    temp_job_path = ""
    job_id = str(uuid.uuid4())
    s3_prefix = f"{S3_BASE_PREFIX}/{job_id}"

    try:
        filename = os.path.basename(video_path)
        base_filename = os.path.splitext(filename)[0]
        output_wav_file = f"{base_filename}.wav"
        temp_wav_path = os.path.join(TEMP_DIR, output_wav_file)

        logging.info(f"New video detected: {filename}. Assigning Job ID: {job_id}")

        # 1. Upload original video
        s3_video_key = f"{s3_prefix}/{filename}"
        logging.info(f"Uploading original video to {s3_video_key}...")
        s3_client.upload_file(video_path, S3_BUCKET_NAME, s3_video_key)
        logging.info("Original video upload successful.")

        # 2. Convert video to WAV
        logging.info(f"Converting {filename} to WAV...")
        subprocess.run(
            [
                "ffmpeg", "-i", video_path,
                "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
                "-y", temp_wav_path
            ],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )

        # 3. Upload the WAV file
        s3_wav_key = f"{s3_prefix}/audio.wav"
        logging.info(f"Uploading {output_wav_file} to {s3_wav_key}...")
        s3_client.upload_file(temp_wav_path, S3_BUCKET_NAME, s3_wav_key)
        logging.info("WAV upload successful.")

        # 4. Create and upload the JSON job file
        job_payload = {
            "job_id": job_id,
            "s3_prefix": s3_prefix,
            "audio_key": s3_wav_key,
            "original_video_key": s3_video_key
        }
        temp_job_path = os.path.join(TEMP_DIR, f"{job_id}.json")
        with open(temp_job_path, 'w') as f:
            json.dump(job_payload, f)

        s3_job_key = f"{S3_JOB_PREFIX}{job_id}.json"
        logging.info(f"Uploading job file to {s3_job_key}...")
        s3_client.upload_file(temp_job_path, S3_BUCKET_NAME, s3_job_key)
        logging.info("Job created successfully.")
        success = True

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        # If something fails, don't delete the video
    finally:
        # 5. Clean up all local temp files
        logging.info("Cleaning up local files...")
        if os.path.exists(temp_wav_path):
            os.remove(temp_wav_path)
        if os.path.exists(temp_job_path):
            os.remove(temp_job_path)

        if success and os.path.exists(video_path):
            os.remove(video_path)
            logging.info(f"Processed and deleted local file: {filename}")
        elif os.path.exists(video_path):
            logging.warning(f"Processing FAILED for {filename}. Local file was NOT deleted.")

class VideoHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return
        if event.src_path.lower().endswith(VIDEO_EXTENSIONS):
            time.sleep(2)
            process_file(event.src_path)

if __name__ == "__main__":
    os.makedirs(INPUT_DIR, exist_ok=True)
    logging.info(f"Starting converter service. Watching {INPUT_DIR}...")
    event_handler = VideoHandler()
    observer = Observer()
    observer.schedule(event_handler, INPUT_DIR, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
