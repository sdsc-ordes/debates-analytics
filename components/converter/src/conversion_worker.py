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
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
CONVERSION_QUEUE = 'video_conversion_jobs'  # Queue this worker consumes from
TRANSCRIPTION_QUEUE = 'transcription_jobs'  # Queue this worker produces to

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
                "-vn",             # No video
                "-acodec", "pcm_s16le", # PCM 16-bit Little-Endian (standard for speech)
                "-ar", "16000",     # Sample rate 16kHz
                "-ac", "1",         # Mono channel
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

    # Use the same connection (if possible) or establish a new channel for publishing
    channel = connection.channel()
    channel.queue_declare(queue=TRANSCRIPTION_QUEUE, durable=True)

    message = json.dumps(job_payload)

    channel.basic_publish(
        exchange='',
        routing_key=TRANSCRIPTION_QUEUE,
        body=message,
        properties=pika.BasicProperties(delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE)
    )
    logging.info(f" [->] Sent transcription job for {job_payload['job_id']} to {TRANSCRIPTION_QUEUE}")

    # NOTE: We keep the channel open if we reuse the connection, but for simplicity
    # in a worker setup, we might close it if the connection wasn't passed in.

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
        s3_video_key = job_data['s3_path']
        file_name = job_data['file_name']
        file_ext = job_data['file_ext']
        s3_prefix = os.path.dirname(s3_video_key) # e.g., job-uuid

        logging.info(f" [x] Received job {job_id}. S3 Path: {s3_video_key}")

        # 2. Define local paths
        local_video_path = os.path.join(TEMP_DIR, file_name)
        local_wav_path = os.path.join(TEMP_DIR, f"{file_name}.wav")
        s3_wav_key = f"{s3_prefix}/{file_name}.wav"

        # 3. Execute Workflow Steps

        # 3a. Download Video
        download_video(s3_video_key, local_video_path)

        # 3b. Convert to WAV
        convert_to_wav(local_video_path, local_wav_path)

        # 3c. Upload WAV
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
        # Acknowledge to remove bad message from queue
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        # For critical errors (S3, FFmpeg), reject and requeue so another worker can try
        logging.error(f" [!] Fatal error processing job {job_data.get('job_id', 'Unknown')}: {e}")
        # Reject and requeue for retry
        ch.basic_reject(delivery_tag=method.delivery_tag, requeue=True)
    finally:
        # 6. Clean up local files
        if os.path.exists(local_video_path):
            os.remove(local_video_path)
        if os.path.exists(local_wav_path):
            os.remove(local_wav_path)


def start_worker():
    """Establishes connection to RabbitMQ and starts consuming messages."""

    # Ensure temp directory exists
    os.makedirs(TEMP_DIR, exist_ok=True)

    connection = None
    max_retries = 10
    retry_delay = 5

    # Retry loop to wait for RabbitMQ to become available
    for attempt in range(max_retries):
        try:
            logging.info(f"Attempting to connect to RabbitMQ at {RABBITMQ_HOST} (Attempt {attempt + 1}/{max_retries})...")
            # 1. Establish connection
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=RABBITMQ_HOST))
            channel = connection.channel()

            # 2. Declare all necessary queues (idempotent)
            channel.queue_declare(queue=CONVERSION_QUEUE, durable=True)
            channel.queue_declare(queue=TRANSCRIPTION_QUEUE, durable=True)

            logging.info(f' [*] Waiting for jobs on {CONVERSION_QUEUE}. To exit press CTRL+C')

            # 3. Set Quality of Service (QoS): Process one message at a time
            # This ensures if the worker dies, only one message needs to be retried.
            channel.basic_qos(prefetch_count=1)

            # 4. Start consuming (listening)
            # Use a lambda to pass the connection object into the callback function
            callback_with_connection = lambda ch, method, properties, body: process_conversion_job(
                ch, method, properties, body, connection
            )

            channel.basic_consume(
                queue=CONVERSION_QUEUE,
                on_message_callback=callback_with_connection,
                # auto_ack=False is CRITICAL for job queues, as we manually acknowledge in the callback
                auto_ack=False
            )

            channel.start_consuming()
            return

        except pika.exceptions.AMQPConnectionError as e:
            if attempt < max_retries - 1:
                logging.warning(f" [!] Connection failed. Retrying in {retry_delay} seconds. Error: {e}")
                time.sleep(retry_delay)
            else:
                logging.error(f" [!] Fatal Error: Could not connect to RabbitMQ after {max_retries} attempts.")
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
