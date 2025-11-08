import os
import sys
import time
import logging
import boto3
import requests
import json
from botocore.exceptions import ClientError

# --- Configuration ---
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

# Paths *inside this container*
AUDIO_DIR = "/app/audio"
TRANSCRIPTS_DIR = "/app/transcripts"
TEMP_DIR = "/tmp"

# S3 Configuration
S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "debates")

S3_JOB_PREFIX = "jobs/new/"
S3_JOB_PROCESSED_PREFIX = "jobs/processed/"

# Whisper API Configuration
WHISPER_API_URL = "http://whisper-diarize:7860/run/process_audio"
WHISPER_HEALTH_URL = "http://whisper-diarize:7860/"
WHISPER_INPUT_DIR = "/app/audio" # Path *inside the whisper container*

# Global definitions to match the Whisper container's internal paths
WHISPER_INPUT_SUBDIR = "odtp-input"
WHISPER_OUTPUT_SUBDIR = "odtp-output"
WHISPER_TEMP_DIR = "/tmp/odtp_transcriber"

# S3 client
s3_client = boto3.client(
    's3',
    endpoint_url=S3_ENDPOINT_URL,
    aws_access_key_id=S3_ACCESS_KEY,
    aws_secret_access_key=S3_SECRET_KEY
)

def wait_for_api():
    """Pings the Whisper API until it's ready."""
    logging.info("Waiting for Whisper API at http://whisper-diarize:7860/ ...")
    while True:
        try:
            requests.get(WHISPER_HEALTH_URL, timeout=5)
            logging.info("Whisper API is ready.")
            break
        except requests.ConnectionError:
            logging.info("API not ready, retrying in 5 seconds...")
            time.sleep(5)

def process_job(job_key):
    """
    Downloads audio, transcribes it, uploads results, and cleans up S3.
    """
    local_wav_path = ""
    local_json_path = ""
    job_data = {}

    try:
        # 1. Download and read the job file
        logging.info(f"New job detected: {job_key}. Downloading...")
        local_job_path = os.path.join(TEMP_DIR, os.path.basename(job_key))
        s3_client.download_file(S3_BUCKET_NAME, job_key, local_job_path)

        with open(local_job_path) as f:
            job_data = json.load(f)

        audio_key = job_data['audio_key']
        s3_prefix = job_data['s3_prefix']

        # The Whisper container is expecting a file named input.wav in its input folder.
        # We will name the downloaded file "input.wav" to match the container's expectations.
        audio_filename_standardized = "input.wav"
        local_wav_path = os.path.join(AUDIO_DIR, audio_filename_standardized)

        # 2. Download audio file to the shared volume
        logging.info(f"Downloading audio file: {audio_key} to {local_wav_path}")
        s3_client.download_file(S3_BUCKET_NAME, audio_key, local_wav_path)

        # 3. Call Whisper API with the explicit parameters.
        # We need to send the path AS IT EXISTS INSIDE THE WHISPER CONTAINER.
        # The whisper image seems to internally use a temporary directory structure like
        # /tmp/odtp_<random>/odtp-input/input.wav
        # However, the Gradio API expects the path relative to its mounted input folder.
        # Let's try sending the path *relative* to the root of the shared volume.

        whisper_api_input_path = os.path.join(WHISPER_INPUT_DIR, audio_filename_standardized) # /app/audio/input.wav

        # The API payload must now match the arguments the Gradio function expects.
        # Based on the shell command you provided, the function likely expects:
        # [MODEL, HF_TOKEN, TASK, INPUT_FILE, OUTPUT_FILE_BASE_NAME, VERBOSE]
        # NOTE: The path inside the Gradio container seems to be /odtp/odtp-input/input.wav.
        # Since we mapped /app/audio in transcriber to /app/audio in whisper, 
        # let's try mapping the path as /app/audio/input.wav and hoping the API resolves it.
        # The simplest way to fix the whisper crash is to just send the path that *it* can read.

        # We must align with the whisper container's internal view of the shared volume!
        # Your docker-compose.yml maps:
        # transcriber: ./audio-to-process:/app/audio
        # whisper-diarize: ./audio-to-process:/app/audio

        # Let's assume the Gradio function takes the *actual* path to the audio file on the shared volume.

        # Re-reading the crash log:
        # Command '['python3', '/odtp/odtp-app/app.py', ..., '--input-file', '/tmp/odtp_86661bo_/odtp-input/input.wav', ...]'
        # This confirms the Whisper app *internally* copies the file to a temp folder.
        # But the Gradio API call should just take the input path, which is shared.

        # Let's try to send the parameters that the *shell command* requires, NOT just the audio path.
        # This is a common pattern for Gradio interfaces that wrap shell scripts.
        # The arguments are sent as a list of data fields.

        api_payload = {
            "data": [
                model_name, # 1. MODEL
                whisper_hf_token, # 2. HF_TOKEN
                "transcribe", # 3. TASK
                whisper_api_input_path, # 4. INPUT_FILE
                job_data['job_id'], # 5. OUTPUT_FILE_BASE_NAME (we use job_id)
                "TRUE" # 6. VERBOSE
            ]
        }

        logging.info(f"Calling Whisper API with payload: {api_payload['data']}")

        response = requests.post(WHISPER_API_URL, json=api_payload, timeout=900)
        response.raise_for_status()

        result_data = response.json().get("data")
        # ... (rest of the script is for steps 4-7 and cleanup) ...

        # 4. Save transcription JSON locally (temporarily)
        # The result from the API call will be the JSON file content.
        # The Gradio app returns the output-json-file content, which is typically transcription_json

        # The Gradio result is usually a list of outputs corresponding to the blocks.
        # Based on the logs, the result_data[0] is the JSON *content*.
        transcription_json = json.loads(result_data[0])

        # ... (rest of the script for steps 4-7 and cleanup remains the same) ...
        # This part of the cleanup might be tricky:
        # if os.path.exists(local_wav_path): os.remove(local_wav_path)
        # The file is named 'input.wav' now.

    except Exception as e:
        logging.error(f"Failed to process job {job_key}: {e}")
        # We don't delete the job file, so it will be retried
    finally:
        # 7. Clean up all local files from this job
        if os.path.exists(local_wav_path):
            os.remove(local_wav_path)
        if os.path.exists(local_json_path):
            os.remove(local_json_path)
        if os.path.exists(local_job_path):
            os.remove(local_job_path)

def poll_s3_for_jobs():
    """
    Main loop that checks for new files in the S3 "jobs/new" folder.
    """
    logging.info(f"Polling S3 bucket '{S3_BUCKET_NAME}' at prefix '{S3_JOB_PREFIX}' for jobs...")
    while True:
        try:
            response = s3_client.list_objects_v2(
                Bucket=S3_BUCKET_NAME,
                Prefix=S3_JOB_PREFIX,
                MaxKeys=1
            )

            if 'Contents' in response:
                job_key = response['Contents'][0]['Key']
                if job_key.endswith('/'): # Skip the folder itself
                    time.sleep(10)
                    continue
                process_job(job_key)
            else:
                time.sleep(10)

        except ClientError as e:
            logging.error(f"S3 Client Error: {e}. Retrying in 15 seconds.")
            time.sleep(15)
        except Exception as e:
            logging.error(f"An unexpected error in polling loop: {e}")
            time.sleep(15)

if __name__ == "__main__":
    os.makedirs(AUDIO_DIR, exist_ok=True)
    os.makedirs(TRANSCRIPTS_DIR, exist_ok=True)
    os.makedirs(TEMP_DIR, exist_ok=True)

    wait_for_api()
    poll_s3_for_jobs()
