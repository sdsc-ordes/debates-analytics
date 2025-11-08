import os
import sys
import time
import logging
import subprocess
import boto3
from botocore.exceptions import NoCredentialsError
from watchdog.observers.polling import PollingObserver as Observer
from watchdog.events import FileSystemEventHandler

# --- Configuration ---
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

INPUT_DIR = "/app/input"
OUTPUT_DIR = "/app/output"
VIDEO_EXTENSIONS = ('.mp4', '.mov', '.mkv', '.avi')

# Get S3 config from environment variables
S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "debates") # Default to "debates"

# Check for essential config
if not all([S3_ENDPOINT_URL, S3_ACCESS_KEY, S3_SECRET_KEY]):
    logging.error("S3 credentials are not fully set. Exiting.")
    sys.exit(1)

# Set up the S3 client for Minio
s3_client = boto3.client(
    's3',
    endpoint_url=S3_ENDPOINT_URL,
    aws_access_key_id=S3_ACCESS_KEY,
    aws_secret_access_key=S3_SECRET_KEY
)

# --- Main Logic ---

def process_file(video_path):
    """
    Converts a video to WAV, uploads to S3, and cleans up.
    """
    try:
        filename = os.path.basename(video_path)
        base_filename = os.path.splitext(filename)[0]
        output_wav_file = f"{base_filename}.wav"
        output_path = os.path.join(OUTPUT_DIR, output_wav_file)

        logging.info(f"New video detected: {filename}")

        # 1. Convert video to WAV using FFmpeg
        logging.info(f"Converting {filename} to WAV...")
        subprocess.run(
            [
                "ffmpeg",
                "-i", video_path,    # Input file
                "-vn",               # No video
                "-acodec", "pcm_s16le", # Standard WAV format
                "-ar", "16000",      # 16kHz sample rate
                "-ac", "1",          # Mono audio
                "-y",                # Overwrite output file
                output_path
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        logging.info(f"File converted and saved to {output_path}")

        # 2. Upload the WAV file to S3 (Minio)
        s3_key = f"audio/{output_wav_file}"
        logging.info(f"Uploading {output_wav_file} to S3 bucket '{S3_BUCKET_NAME}' as {s3_key}...")
        s3_client.upload_file(output_path, S3_BUCKET_NAME, s3_key)
        logging.info("Upload successful.")

    except subprocess.CalledProcessError:
        logging.error(f"FFmpeg failed to convert {filename}")
    except NoCredentialsError:
        logging.error("S3 credentials not found by boto3.")
    except Exception as e:
        logging.error(f"An error occurred: {e}")
    finally:
        # 3. Clean up the original video file
        logging.info(f"Cleaning up {video_path}")
        os.remove(video_path)


class VideoHandler(FileSystemEventHandler):
    """
    Watches for new files and processes them.
    """
    def on_created(self, event):
        if event.is_directory:
            return

        # Check if the file is a video
        if event.src_path.lower().endswith(VIDEO_EXTENSIONS):
            # Wait a moment to ensure file is fully copied
            time.sleep(2)
            process_file(event.src_path)

# --- Start the Watcher ---
if __name__ == "__main__":
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
