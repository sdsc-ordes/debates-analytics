import os
import sys
import time
import logging
import subprocess
import boto3
import json
import pika
from botocore.exceptions import ClientError
from typing import Dict, Any

# --- Configuration ---
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

TEMP_DIR = "/tmp"

# RabbitMQ Configuration
# FIX 1: Use the standard RABBITMQ_URL environment variable
RABBITMQ_URL = os.getenv("RABBITMQ_URL")
CONVERSION_QUEUE = 'video_conversion_jobs'
TRANSCRIPTION_QUEUE = 'transcription_jobs'

# S3 Configuration
S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

# S3 client initialization
try:
    s3_client = boto3.client(
        's3',
        endpoint_url=S3_ENDPOINT_URL,
        aws_access_key_id=S3_ACCESS_KEY,
        aws_secret_access_key=S3_SECRET_KEY
    )
except Exception as e:
    logging.error(f"Failed to initialize S3 client: {e}")
    sys.exit(1)


# --- Utility Functions ---

def download_video(s3_video_key: str, local_path: str):
    """Downloads a video file from S3 to a local path."""
    logging.info(f"Downloading video from S3: {s3_video_key}...")
    try:
        s3_client.download_file(S3_BUCKET_NAME, s3_video_key, local_path)
        logging.info("Download successful.")
    except ClientError as e:
        if e.response['Error']['Code'] == '404':
            logging.error(f"S3 Object not found: {s3_video_key}")
            raise FileNotFoundError(f"Video not found at {s3_video_key}")
        raise

def convert_to_wav(local_video_path: str, local_wav_path: str):
    """Converts the local video file to 16kHz mono WAV using ffmpeg."""
    logging.info(f"Starting conversion of {os.path.basename(local_video_path)} to WAV...")
    try:
        subprocess.run(
            [
                "ffmpeg", "-i", local_video_path,
                "-vn",
                "-acodec", "pcm_s16le",
                "-ar", "16000",
                "-ac", "1",
                "-y", local_wav_path
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        logging.info("Conversion successful.")
    except subprocess.CalledProcessError as e:
        logging.error(f"FFmpeg conversion failed: {e}")
        raise

def upload_wav(local_wav_path: str, s3_wav_key: str):
    """Uploads the converted WAV file to S3."""
    logging.info(f"Uploading WAV file to S3: {s3_wav_key}...")
    s3_client.upload_file(local_wav_path, S3_BUCKET_NAME, s3_wav_key)
    logging.info("WAV upload successful.")


def send_to_transcriber_queue(job_payload: Dict[str, Any], connection: pika.BlockingConnection):
    """Publishes a new message to the transcription queue for the next worker."""

    channel = connection.channel()
    channel.queue_declare(queue=TRANSCRIPTION_QUEUE, durable=True)

    message = json.dumps(job_payload)

    channel.basic_publish(
        exchange='',
        routing_key=TRANSCRIPTION_QUEUE,
        body=message,
        properties=pika.BasicProperties(delivery_mode=pika.spec.DELIVERY_MODE_PERSISTENT)
    )
    logging.info(f" [->] Sent transcription job for {job_payload['job_id']} to {TRANSCRIPTION_QUEUE}")


# --- Core Worker Logic ---

def process_conversion_job(ch, method, properties, body, connection: pika.BlockingConnection):
    """
    Main callback when a job message is received from RabbitMQ.
    """
    job_data = {}
    local_video_path = ""
    local_wav_path = ""

    try:
        # 1. Deserialize the message
        job_data = json.loads(body)
        job_id = job_data['job_id']
        # FIX: The message payload from FastAPI should match the key structure (s3_key)
        # Assuming the job payload from FastAPI uses 's3_key'
        s3_video_key = job_data['s3_key']

        # Derive file name/ext from the s3_key instead of relying on separate fields
        file_name_with_ext = os.path.basename(s3_video_key)
        file_name, file_ext = os.path.splitext(file_name_with_ext)

        s3_prefix = os.path.dirname(s3_video_key)

        logging.info(f" [x] Received job {job_id}. S3 Path: {s3_video_key}")

        # 2. Define local paths
        local_video_path = os.path.join(TEMP_DIR, file_name_with_ext)
        local_wav_path = os.path.join(TEMP_DIR, f"{file_name}.wav")
        s3_wav_key = f"{s3_prefix}/{file_name}.wav"

        # 3. Execute Workflow Steps
        download_video(s3_video_key, local_video_path)
        convert_to_wav(local_video_path, local_wav_path)
        upload_wav(local_wav_path, s3_wav_key)

        # 4. Prepare and Send Next Job (Producer action)
        transcription_payload = {
            "job_id": job_id,
            "s3_prefix": s3_prefix,
            "audio_key": s3_wav_key,
            "original_video_key": s3_video_key,
            "status": "CONVERSION_COMPLETE"
        }
        send_to_transcriber_queue(transcription_payload, connection)

        # 5. Acknowledge success
        ch.basic_ack(delivery_tag=method.delivery_tag)
        logging.info(f" [x] Job {job_id} fully processed and acknowledged.")

    except (json.JSONDecodeError, KeyError) as e:
        logging.error(f" [!] Malformed job message received: {body.decode()}. Error: {e}")
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        logging.error(f" [!] Fatal error processing job {job_data.get('job_id', 'Unknown')}: {e}")
        ch.basic_reject(delivery_tag=method.delivery_tag, requeue=True)
    finally:
        # 6. Clean up local files
        if os.path.exists(local_video_path):
            os.remove(local_video_path)
        if os.path.exists(local_wav_path):
            os.remove(local_wav_path)


def start_worker():
    """Establishes connection to RabbitMQ and starts consuming messages."""

    os.makedirs(TEMP_DIR, exist_ok=True)

    if not RABBITMQ_URL:
        logging.error("FATAL: RABBITMQ_URL environment variable is not set. Cannot start worker.")
        sys.exit(1)

    url_params = pika.URLParameters(RABBITMQ_URL)
    connection = None
    max_retries = 10
    retry_delay = 5

    # Retry loop to wait for RabbitMQ to become available
    for attempt in range(max_retries):
        try:
            logging.info(f"Attempting to connect to RabbitMQ (Attempt {attempt + 1}/{max_retries})...")

            # FIX 2: Use URLParameters for robust connection
            connection = pika.BlockingConnection(url_params)
            channel = connection.channel()

            channel.queue_declare(queue=CONVERSION_QUEUE, durable=True)
            channel.queue_declare(queue=TRANSCRIPTION_QUEUE, durable=True)

            logging.info(f' [*] Waiting for jobs on {CONVERSION_QUEUE}. To exit press CTRL+C')

            channel.basic_qos(prefetch_count=1)

            callback_with_connection = lambda ch, method, properties, body: process_conversion_job(
                ch, method, properties, body, connection
            )

            channel.basic_consume(
                queue=CONVERSION_QUEUE,
                on_message_callback=callback_with_connection,
                auto_ack=False
            )

            channel.start_consuming()
            return

        except pika.exceptions.AMQPConnectionError as e:
            if attempt < max_retries - 1:
                logging.warning(f" [!] Connection failed. Retrying in {retry_delay} seconds. Error: {e}")
                time.sleep(retry_delay)
            else:
                logging.error(f" [!] Fatal Error: Could not connect to RabbitMQ after {max_retries} attempts. Error: {e}")
                sys.exit(1)
        except KeyboardInterrupt:
            logging.info('Worker shutting down...')
            break
        except Exception as e:
            logging.error(f"An unexpected error occurred in worker setup: {e}")
            break
        finally:
            if connection and connection.is_open:
                connection.close()

if __name__ == '__main__':
    start_worker()
