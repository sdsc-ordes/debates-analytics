import os
import sys
import time
import logging
import subprocess
import boto3
import requests
import json
from botocore.exceptions import NoCredentialsError
from watchdog.observers.polling import PollingObserver as Observer
from watchdog.events import FileSystemEventHandler

# --- Configuration ---
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

INPUT_DIR = "/app/input"
OUTPUT_DIR = "/app/output"
TRANSCRIPTS_DIR = "/app/transcripts"
VIDEO_EXTENSIONS = ('.mp4', '.mov', '.mkv', '.avi')

# S3 Configuration
S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "debates")

# Whisper API Configuration
WHISPER_API_URL = "http://whisper-diarize:7860/predict"
# This is the path *inside the whisper container*
WHISPER_INPUT_DIR = "/app/audio"

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
    Full pipeline: Convert, upload WAV, transcribe, upload result, cleanup.
    """
    output_wav_file = ""
    output_path = ""
    output_json_path = ""

    try:
        filename = os.path.basename(video_path)
        base_filename = os.path.splitext(filename)[0]
        output_wav_file = f"{base_filename}.wav"
        output_path = os.path.join(OUTPUT_DIR, output_wav_file)

        logging.info(f"New video detected: {filename}")

        # 1. Convert video to WAV
        logging.info(f"Converting {filename} to WAV...")
        subprocess.run(
            [
                "ffmpeg", "-i", video_path,
                "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
                "-y", output_path
            ],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        logging.info(f"File converted and saved to {output_path}")

        # 2. Upload the WAV file to S3
        s3_wav_key = f"{base_filename}/{output_wav_file}"
        logging.info(f"Uploading {output_wav_file} to S3 as {s3_wav_key}...")
        s3_client.upload_file(output_path, S3_BUCKET_NAME, s3_wav_key)
        logging.info("WAV upload successful.")

        # 3. Call Whisper API to start transcription
        # We pass the file path *as the whisper container sees it*
        whisper_file_path = os.path.join(WHISPER_INPUT_DIR, output_wav_file)

        logging.info(f"Calling Whisper API for file: {whisper_file_path}")
        # This payload structure is typical for Gradio APIs
        api_payload = {"data": [whisper_file_path]}

        response = requests.post(WHISPER_API_URL, json=api_payload, timeout=900) # 15 min timeout
        response.raise_for_status() # Raise an error if API call fails

        result_data = response.json().get("data")
        if not result_data:
            raise Exception("No 'data' in API response.")

        # 4. Save transcription result to JSON
        # The result is often a JSON string inside the first list item
        transcription_json = json.loads(result_data[0])

        output_json_file = f"{base_filename}.json"
        output_json_path = os.path.join(TRANSCRIPTS_DIR, output_json_file)

        with open(output_json_path, 'w') as f:
            json.dump(transcription_json, f, indent=2)
        logging.info(f"Transcription result saved to {output_json_path}")

        # 5. Upload the JSON result to S3
        s3_json_key = f"transcripts/{output_json_file}"
        logging.info(f"Uploading {output_json_file} to S3 as {s3_json_key}...")
        s3_client.upload_file(output_json_path, S3_BUCKET_NAME, s3_json_key)
        logging.info("JSON upload successful.")

    except subprocess.CalledProcessError:
        logging.error(f"FFmpeg failed to convert {filename}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to call Whisper API: {e}")
    except Exception as e:
        logging.error(f"An error occurred: {e}")
    finally:
        # 6. Clean up all local files
        logging.info("Cleaning up local files...")
        if os.path.exists(video_path):
            os.remove(video_path)
        if os.path.exists(output_path):
            os.remove(output_path)
        # We leave the final JSON in ./transcripts for inspection
        # if os.path.exists(output_json_path):
        #     os.remove(output_json_path)


class VideoHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return
        if event.src_path.lower().endswith(VIDEO_EXTENSIONS):
            time.sleep(2)
            process_file(event.src_path)

# --- Start the Watcher ---
if __name__ == "__main__":
    # Create dirs just in case
    os.makedirs(INPUT_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(TRANSCRIPTS_DIR, exist_ok=True)

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
