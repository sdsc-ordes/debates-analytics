import os
import sys
import time
import logging
import uuid
import json
import pika
import boto3
from watchdog.observers.polling import PollingObserver as Observer
from watchdog.events import FileSystemEventHandler

# --- Configuration ---
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

INPUT_DIR = "/app/input"
VIDEO_EXTENSIONS = ('.mp4', '.mov', '.avi')

# RabbitMQ Configuration
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
CONVERSION_QUEUE = 'video_conversion_jobs'  # Queue this producer sends to

# S3 Configuration
S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "debates")
S3_BASE_PREFIX = "media"

# Initialize S3 Client
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


# --- Core Logic: The Producer Action ---

def upload_to_s3(local_path: str, s3_key: str):
    """Uploads a local file to S3."""
    logging.info(f"Uploading file to {s3_key}...")
    s3_client.upload_file(local_path, S3_BUCKET_NAME, s3_key)
    logging.info("S3 upload successful.")


def produce_conversion_job(video_path: str, rabbitmq_connection: pika.BlockingConnection):
    """
    Uploads the video to S3 and publishes a job message to the RabbitMQ queue.
    """
    job_id = str(uuid.uuid4())
    filename = os.path.basename(video_path)
    s3_prefix = f"{S3_BASE_PREFIX}/{job_id}"
    s3_video_key = f"{s3_prefix}/{filename}"

    logging.info(f"Processing new file: {filename}. Assigned Job ID: {job_id}")

    try:
        # 1. Upload the file to MinIO (S3)
        upload_to_s3(video_path, s3_video_key)

        # 2. Prepare the job message (Producer)
        job_payload = {
            "job_id": job_id,
            "s3_path": s3_video_key, # This is the CRITICAL piece of data for the Converter
            "original_filename": filename
        }
        message = json.dumps(job_payload)

        # 3. Publish the message to RabbitMQ
        channel = rabbitmq_connection.channel()
        channel.queue_declare(queue=CONVERSION_QUEUE, durable=True)
        channel.basic_publish(
            exchange='',
            routing_key=CONVERSION_QUEUE,
            body=message,
            properties=pika.BasicProperties(delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE)
        )
        logging.info(f" [->] Sent conversion job for {job_id} to {CONVERSION_QUEUE}")

        # 4. Clean up the local file
        os.remove(video_path)
        logging.info(f"Local file cleaned up: {filename}")

    except Exception as e:
        logging.error(f"An error occurred during production of job {job_id}: {e}")
        # Note: If upload fails, the local file is intentionally left for manual inspection/retry.
        # If publish fails, the local file is still available for manual retry.

# --- File Watcher and Startup ---

class VideoProducerHandler(FileSystemEventHandler):
    """Watches for new files and triggers the producer job."""

    def __init__(self, connection: pika.BlockingConnection):
        super().__init__()
        self.connection = connection

    def on_created(self, event):
        if event.is_directory:
            return
        # Wait a moment for the file to finish copying to the watched directory
        time.sleep(2)
        if event.src_path.lower().endswith(VIDEO_EXTENSIONS):
            produce_conversion_job(event.src_path, self.connection)


def start_producer():
    """Starts the file watcher and RabbitMQ connection."""

    os.makedirs(INPUT_DIR, exist_ok=True)
    connection = None
    max_retries = 10
    retry_delay = 5

    # Connect to RabbitMQ with retry logic
    for attempt in range(max_retries):
        try:
            logging.info(f"Attempting to connect to RabbitMQ at {RABBITMQ_HOST} (Attempt {attempt + 1}/{max_retries})...")
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=RABBITMQ_HOST))
            logging.info("RabbitMQ connection successful.")
            break
        except pika.exceptions.AMQPConnectionError as e:
            if attempt < max_retries - 1:
                logging.warning(f" [!] RabbitMQ connection failed. Retrying in {retry_delay} seconds.")
                time.sleep(retry_delay)
            else:
                logging.error(f" [!] Fatal Error: Could not connect to RabbitMQ after {max_retries} attempts. Exiting.")
                sys.exit(1)

    # Start the file watcher if connection succeeded
    event_handler = VideoProducerHandler(connection)
    observer = Observer()
    observer.schedule(event_handler, INPUT_DIR, recursive=False)
    observer.start()

    logging.info(f"Starting Dataloader Producer service. Watching {INPUT_DIR} for new videos...")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("Producer shutting down...")
    finally:
        observer.stop()
        observer.join()
        if connection and connection.is_open:
            connection.close()
            logging.info("RabbitMQ connection closed.")

if __name__ == "__main__":
    start_producer()
