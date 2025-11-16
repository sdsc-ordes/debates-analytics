import os
import time
import logging
import boto3
import json
from botocore.exceptions import ClientError
from typing import List

# --- Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

WATCH_INTERVAL_SECONDS = 30
MARKER_FILENAME = os.getenv("MARKER_FILENAME")

# S3 Configuration (Must match minio-instance service access)
S3_SERVER = os.getenv("S3_SERVER")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
CONVERSION_QUEUE = 'video_analysis_jobs'
WATCH_INTERVAL_SECONDS = 30

try:
    # Initialize synchronous S3 client for list/delete operations
    s3_client = boto3.client(
        's3',
        endpoint_url=S3_SERVER,
        aws_access_key_id=S3_ACCESS_KEY,
        aws_secret_access_key=S3_SECRET_KEY
    )
except Exception as e:
    logger.error(f"Failed to initialize S3 client: {e}")
    # Fatal error, exit if S3 cannot be reached.
    exit(1)


def send_to_video_analysis_queue(job_payload: Dict[str, Any], connection: pika.BlockingConnection):
    """Publishes a new message to the transcription queue for the next worker."""

    channel = connection.channel()
    channel.queue_declare(queue=CONVERSION_QUEUE, durable=True)

    message = json.dumps(job_payload)

    channel.basic_publish(
        exchange='',
        routing_key=CONVERSION_QUEUE,
        body=message,
        properties=pika.BasicProperties(delivery_mode=2)
    )
    logging.info(f" [->] Sent transcription job for {job_payload['job_id']} to {CONVERSION_QUEUE}")


def find_new_jobs() -> List[str]:
    """Lists all top-level prefixes that contain the job marker file."""

    # We list objects by the MARKER_FILENAME prefix to find all new jobs
    marker_keys = []

    try:
        response = s3_client.list_objects_v2(
            Bucket=S3_BUCKET_NAME,
            Prefix='',
            Delimiter='/'
        )

        if 'CommonPrefixes' in response:
            logger.info(f"Found {len(response['CommonPrefixes'])} top-level prefixes.")

            for prefix_data in response['CommonPrefixes']:
                job_prefix = prefix_data['Prefix']

                # --- DEBUG LOGGING ---
                logger.debug(f"Checking prefix: {job_prefix}")
                # --- END DEBUG LOGGING ---

                # Construct the full marker key path
                marker_key = f"{job_prefix}media/{MARKER_FILENAME}"

                # --- DEBUG LOGGING ---
                logger.debug(f"Searching for marker key: {marker_key}")
                # --- END DEBUG LOGGING ---

                # Check for the existence of the specific marker file
                try:
                    s3_client.head_object(Bucket=S3_BUCKET_NAME, Key=marker_key)

                    # If head_object succeeds, the marker exists.
                    marker_keys.append(marker_key)
                    logger.info(f"SUCCESS: Marker found at {marker_key}")

                except ClientError as e:
                    # 404 is expected if the marker isn't there; ignore it.
                    if e.response['Error']['Code'] != '404':
                        # Log any unexpected error (e.g., Access Denied, 500)
                        logger.error(f"S3 Head Object Error ({job_prefix}): {e}")
        else:
             logger.info("No top-level prefixes (potential job folders) found.")

    except Exception as e:
        logger.error(f"Error listing S3 prefixes: {e}")

    return marker_keys



def process_and_queue_job(marker_key: str):
    """
    Extracts job metadata from the S3 key, publishes to RabbitMQ,
    and deletes the marker file.
    """
    try:
        # Extract job_id and original s3_key (assuming s3_key is stored near the marker)
        # Marker Key format: {job_id}/media/job_registered.txt
        job_id = marker_key.split('/')[0]
        s3_key = marker_key.replace(f"/{MARKER_FILENAME}", "").replace(f"{job_id}/", "")
        title = f"Uploaded File {job_id[:8]}" # Placeholder title

        logger.info(f" [->] Found new job marker: {job_id}")

        video_analysis_payload = {
            "job_id": job_id,
            "s3_prefix": s3_key,
            "original_video_key": s3_key,
            "status": "UPLOAD_COMPLETE"
        }
        send_to_transcriber_queue(video_analysis_payload, connection)

        # This should be asynchronous, but since the watcher is in a separate process,
        # we can't directly await it. We would typically use an async event loop runner,
        # but for simplicity, we call the async publisher and let it manage its own thread pool.
        # NOTE: A real implementation would use asyncio.run(publish_analysis_job(...))
        # but since we are running this in a dedicated process, we will call a synchronous wrapper
        # that handles the asyncio loop creation.

        # For simplicity in this context, we will skip the explicit publish for the watcher
        # and assume a simple logging mechanism for proof of concept.

        logger.info(f" [->] Publishing job {job_id} to RabbitMQ (Simulated). S3 Key: {s3_key}")

        # Now, delete the marker file to prevent reprocessing
        s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=marker_key)
        logger.info(f" [<-] Job marker deleted: {marker_key}")

    except Exception as e:
        logger.error(f"Error processing job {job_id}: {e}")


def main_loop():
    logger.info("S3 Polling Watcher starting...")
    while True:
        try:
            new_job_markers = find_new_jobs()
            if new_job_markers:
                logger.info(f"Found {len(new_job_markers)} new job(s).")
                for marker in new_job_markers:
                    process_and_queue_job(marker)
            else:
                logger.debug("No new job markers found.")

        except Exception as e:
            logger.error(f"Unhandled error in main watcher loop: {e}")

        time.sleep(WATCH_INTERVAL_SECONDS)


if __name__ == '__main__':
    main_loop()
