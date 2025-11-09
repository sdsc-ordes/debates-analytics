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


def connect_rabbitmq(host: str) -> pika.BlockingConnection:
    """Creates and returns a new RabbitMQ connection."""
    return pika.BlockingConnection(pika.ConnectionParameters(host=host))


def produce_conversion_job(video_path: str, connection: pika.BlockingConnection):
    """
    Uploads the video to S3 and publishes a job message to the RabbitMQ queue.
    NOTE: We now check the connection status and handle channel lifecycle robustly.
    """
    job_id = str(uuid.uuid4())
    filename = os.path.basename(video_path)
    s3_prefix = f"{S3_BASE_PREFIX}/{job_id}"
    s3_video_key = f"{s3_prefix}/{filename}"

    logging.info(f"Processing new file: {filename}. Assigned Job ID: {job_id}")

    # --- MinIO Upload ---
    try:
        upload_to_s3(video_path, s3_video_key)
    except Exception as e:
        logging.error(f"MinIO Upload Failed for job {job_id}: {e}")
        # Stop processing if MinIO fails, leave file for retry.
        return

    # --- RabbitMQ Publish ---
    channel = None
    try:
        # Check if the existing connection is still open (highly recommended)
        if not connection or connection.is_closed:
            logging.warning("RabbitMQ connection was closed. Attempting to re-establish...")
            # Re-establishing is handled in the file watcher's event handler's setup phase,
            # but for simplicity here, we assume the connection object passed is ready OR
            # that the caller (handler) ensures readiness.

        # 2. Get a channel and prepare the job message
        channel = connection.channel()
        channel.queue_declare(queue=CONVERSION_QUEUE, durable=True)

        job_payload = {
            "job_id": job_id,
            "s3_path": s3_video_key, # CRITICAL data for Converter
            "original_filename": filename
        }
        message = json.dumps(job_payload)

        # 3. Publish the message to RabbitMQ
        channel.basic_publish(
            exchange='',
            routing_key=CONVERSION_QUEUE,
            body=message,
            properties=pika.BasicProperties(delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE)
        )
        logging.info(f" [->] Sent conversion job for {job_id} to {CONVERSION_QUEUE}")

        # 4. Clean up the local file ONLY after successful S3 upload AND RabbitMQ publish
        os.remove(video_path)
        logging.info(f"Local file cleaned up: {filename}")

    except pika.exceptions.AMQPConnectionError as e:
        logging.error(f" [!!!] Fatal RabbitMQ Error: Connection lost during publish. Job {job_id} failed to queue. File kept locally. Details: {e}")
        # The main loop needs to handle connection recovery.
    except Exception as e:
        logging.error(f"An unexpected error occurred during job production {job_id}: {e}")
    finally:
        # Close the channel immediately after use
        if channel and channel.is_open:
            channel.close()


# --- File Watcher and Startup ---

class VideoProducerHandler(FileSystemEventHandler):
    """Watches for new files and triggers the producer job."""

    def __init__(self):
        super().__init__()
        self.connection = None
        self.max_retries = 10
        self.retry_delay = 5
        self._ensure_connection()

    def _ensure_connection(self):
        """Ensures the RabbitMQ connection is open, attempting reconnection if necessary."""
        for attempt in range(self.max_retries):
            if self.connection and self.connection.is_open:
                return # Connection is already good

            try:
                logging.info(f"Attempting to connect to RabbitMQ at {RABBITMQ_HOST} (Attempt {attempt + 1}/{self.max_retries})...")
                self.connection = connect_rabbitmq(RABBITMQ_HOST)
                logging.info("RabbitMQ connection successful.")
                return # Connection established successfully
            except pika.exceptions.AMQPConnectionError as e:
                if attempt < self.max_retries - 1:
                    logging.warning(f" [!] RabbitMQ connection failed. Retrying in {self.retry_delay} seconds.")
                    time.sleep(self.retry_delay)
                else:
                    logging.error(f" [!] Fatal Error: Could not connect to RabbitMQ after {self.max_retries} attempts. Exiting.")
                    sys.exit(1)

    def on_created(self, event):
        if event.is_directory:
            return
        # Wait a moment for the file to finish copying to the watched directory
        time.sleep(2)
        if event.src_path.lower().endswith(VIDEO_EXTENSIONS):
            # Before producing the job, ensure the connection is ready
            self._ensure_connection()
            if self.connection and self.connection.is_open:
                produce_conversion_job(event.src_path, self.connection)
            else:
                logging.error(f"Cannot process {event.src_path}: RabbitMQ connection is not open.")


def start_producer():
    """Starts the file watcher."""
    os.makedirs(INPUT_DIR, exist_ok=True)

    # Initialize the handler, which handles its own connection
    event_handler = VideoProducerHandler()

    observer = Observer()
    observer.schedule(event_handler, INPUT_DIR, recursive=False)
    observer.start()

    logging.info(f"Starting Dataloader Producer service. Watching {INPUT_DIR} for new videos...")

    try:
        while True:
            # We check the connection health periodically in case it closed due to network or timeout
            event_handler._ensure_connection()
            time.sleep(5)
    except KeyboardInterrupt:
        logging.info("Producer shutting down...")
    finally:
        observer.stop()
        observer.join()
        if event_handler.connection and event_handler.connection.is_open:
            event_handler.connection.close()
            logging.info("RabbitMQ connection closed.")

if __name__ == "__main__":
    start_producer()
