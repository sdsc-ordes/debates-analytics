import os
import boto3
import logging
from gradio_client import Client, handle_file
from rq import get_current_job

# --- Configuration ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TEMP_DIR = "/tmp/processing"
os.makedirs(TEMP_DIR, exist_ok=True)

# S3 Client
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

# Hugging Face Client
HF_SPACE_URL = "https://katospiegel-odtp-pyannote-whisper.hf.space/"

def process_transcription(s3_key, media_id):
    """
    Downloads audio, sends to HF API, uploads results to S3.
    """
    job = get_current_job()
    job_id = job.get_id()
    
    logger.info(f"Job {media_id}: Starting processing for {s3_key}")
    job.meta['progress'] = 'transcribing'
    job.save_meta()

    # Paths
    filename = os.path.basename(s3_key)
    local_video_path = os.path.join(TEMP_DIR, filename)
    local_input_path = os.path.join(TEMP_DIR, f"{filename}.wav")
    s3_wav_key = s3_key.replace(".mp4", ".wav")

    local_input_path = os.path.join(TEMP_DIR, f"{media_id}_input.wav")

    try:
        # 2. Download WAV from S3
        logger.info(f"Job {job_id}: Downloading {s3_key}...")
        s3_client.download_file(BUCKET_NAME, s3_key, local_input_path)

        # 3. Call Hugging Face API
        logger.info(f"Job {job_id}: Sending to Hugging Face API...")
        client = Client(HF_SPACE_URL)
        
        # The API returns a tuple of 8 elements
        result = client.predict(
            audio_file=handle_file(local_input_path),
            youtube_link="",  # Required param, but unused if audio_file is present
            model="large-v3", # Recommend 'large-v3' for best quality, or 'base' for speed
            task="transcribe",
            language="auto",
            hf_token=HF_TOKEN,    # Add your token here if the space becomes private
            quantize=False,
            api_name="/process_audio"
        )

        # 4. Map results to filenames
        # Based on API docs: 
        # [3]=SRT, [4]=JSON, [5]=JSON Segments, [6]=MD, [7]=PDF
        artifacts = {
            "transcript.srt": result[3],
            "transcript.json": result[4],
            "segments.json": result[5],
            "transcript.md": result[6],
            "transcript.pdf": result[7]
        }

        # 5. Upload all results to S3
        logger.info(f"Job {job_id}: Uploading results to S3...")
        
        uploaded_keys = []
        for filename, local_path in artifacts.items():
            if local_path and os.path.exists(local_path):
                s3_key = f"{media_id}/transcripts/{filename}"
                s3_client.upload_file(local_path, BUCKET_NAME, s3_key)
                uploaded_keys.append(s3_key)
                logger.info(f"Uploaded: {s3_key}")

        # 6. Cleanup local input
        if os.path.exists(local_input_path):
            os.remove(local_input_path)

        logger.info(f"Job {job_id}: Transcription complete.")
        return {"status": "completed", "uploaded": uploaded_keys}

    except Exception as e:
        logger.error(f"Job {job_id} Failed: {e}")
        # Clean up on failure
        if os.path.exists(local_input_path):
            os.remove(local_input_path)
        raise e