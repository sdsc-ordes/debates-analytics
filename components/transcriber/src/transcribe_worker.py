import os
import sys
import json
import time
import logging
import pika
import boto3

# --- Configuration ---
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

# Environment Variables from Docker Compose
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
TRANSCRIPTION_QUEUE = 'transcription_jobs' # Queue this consumer listens to

S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "debates")

# Local directory where placeholder transcription files are expected
LOCAL_TRANSCRIPT_DIR = "/app/input"

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


# --- Core Logic: The Consumer Action ---

def upload_transcript_files(job_id: str):
    """
    Looks for matching .json and .srt files locally and uploads them to S3.
    """
    logging.info(f"--- Processing Transcription Job ID: {job_id} ---")

    # Define the S3 destination path based on the job ID
    s3_prefix = f"transcripts/{job_id}/"

    files_to_find = os.listdir(LOCAL_TRANSCRIPT_DIR)
    uploaded_count = 0

    for filename in files_to_find:
        local_path = os.path.join(LOCAL_TRANSCRIPT_DIR, filename)
        s3_key = s3_prefix + filename

        if os.path.exists(local_path):
            try:
                logging.info(f"Found {filename}. Uploading to S3 key: {s3_key}")

                # Upload the file
                s3_client.upload_file(local_path, S3_BUCKET_NAME, s3_key)

                logging.info(f"Successfully uploaded {filename}.")
                os.remove(local_path) # Clean up the local file after upload
                logging.info(f"Cleaned up local file {local_path}.")
                uploaded_count += 1
            except Exception as e:
                logging.error(f"Failed to upload {filename} to S3: {e}")
                # Do not delete the local file if upload fails, allowing manual retry
        else:
            logging.warning(f"File not found in {LOCAL_TRANSCRIPT_DIR}: {filename}")
            # In a real system, you might mark this job for review if files are missing

    if uploaded_count == len(files_to_find):
        logging.info(f"--- Transcription files for {job_id} successfully processed and uploaded. ---")
        return True
    else:
        logging.warning(f"--- Transcription job {job_id} completed with missing files ({uploaded_count}/{len(files_to_find)} uploaded). ---")
        return False


def process_job(ch, method, properties, body):
    """
    Callback function executed when a message is received.
    """
    try:
        job_data = json.loads(body)
        job_id = job_data.get('job_id')

        if not job_id:
            logging.error("Received job message missing 'job_id'. Rejecting.")
            ch.basic_reject(delivery_tag=method.delivery_tag, requeue=False)
            return

        success = upload_transcript_files(job_id)

        if success:
            ch.basic_ack(delivery_tag=method.delivery_tag)
        else:
            # If files were missing or failed to upload, reject/requeue for potential manual fix
            # For simplicity, we acknowledge here to prevent endless retries on missing files
            ch.basic_ack(delivery_tag=method.delivery_tag)

    except json.JSONDecodeError:
        logging.error(f" [!] Failed to decode JSON body: {body.decode()}")
        ch.basic_reject(delivery_tag=method.delivery_tag, requeue=False) # Dead letter
    except Exception as e:
        logging.error(f" [!] An error occurred during transcription processing: {e}")
        # Reject and requeue on unexpected errors (e.g., network failure)
        ch.basic_reject(delivery_tag=method.delivery_tag, requeue=True)


def start_worker():
    """Starts the consumer process to listen for transcription jobs."""
    os.makedirs(LOCAL_TRANSCRIPT_DIR, exist_ok=True)
    connection = None
    max_retries = 10
    retry_delay = 5

    # Connect to RabbitMQ with retry logic
    for attempt in range(max_retries):
        try:
            logging.info(f"Attempting to connect to RabbitMQ at {RABBITMQ_HOST} (Attempt {attempt + 1}/{max_retries})...")
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=RABBITMQ_HOST))
            channel = connection.channel()

            channel.queue_declare(queue=TRANSCRIPTION_QUEUE, durable=True)

            logging.info("RabbitMQ connection successful. Listening for jobs...")
            print(' [*] Waiting for transcription jobs. To exit press CTRL+C')

            channel.basic_qos(prefetch_count=1) # One job at a time
            channel.basic_consume(
                queue=TRANSCRIPTION_QUEUE,
                on_message_callback=process_job
            )

            channel.start_consuming()
            break

        except pika.exceptions.AMQPConnectionError as e:
            if attempt < max_retries - 1:
                logging.warning(f" [!] RabbitMQ connection failed. Retrying in {retry_delay} seconds.")
                time.sleep(retry_delay)
            else:
                logging.error(f" [!] Fatal Error: Could not connect to RabbitMQ after {max_retries} attempts. Exiting.")
                sys.exit(1)
        except Exception as e:
            logging.error(f" [!] An unexpected error occurred during worker setup: {e}")
            sys.exit(1)
        finally:
            if 'connection' in locals() and connection and connection.is_open:
                # This should only close if connection was established and then interrupted
                pass

if __name__ == '__main__':
    start_worker()