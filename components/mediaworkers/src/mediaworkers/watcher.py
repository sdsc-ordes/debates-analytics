import os
import time
import logging
import json
import pika
import sys
from botocore.exceptions import ClientError
from typing import List, Dict, Any, NoReturn

# Use relative imports for all package dependencies
from .config import (
    S3_BUCKET_NAME, WATCH_INTERVAL_SECONDS, MARKER_FILENAME, CONVERSION_QUEUE
)
from mediaworkers.connection import connect_to_rabbitmq

logger = logging.getLogger(__name__)


def process_and_queue_job(marker_key: str, connection: pika.BlockingConnection, s3_client):
    """
    Extracts job metadata, publishes to RabbitMQ, and deletes the marker file.
    """
    job_id = "unknown"
    try:
        # Extract job_id from the key (first path segment)
        # Marker Key format: {job_id}/media/{MARKER_FILENAME}
        job_id = marker_key.split('/')[0]

        # Derive the expected video key.
        # Assuming the video file is stored next to the marker in a known path structure.
        s3_key_base = marker_key.replace(f"/media/{MARKER_FILENAME}", "")
        s3_video_key = f"{s3_key_base}/media/video.mp4" # Placeholder key

        logger.info(f" [->] Found new job marker: {job_id}")

        video_analysis_payload = {
            "job_id": job_id,
            "s3_key": s3_video_key, # Key to the actual video file for the next worker
            "status": "UPLOAD_COMPLETE"
        }

        # --- Publish to RabbitMQ ---
        channel = connection.channel()
        # Queue is already declared by connect_to_rabbitmq

        message = json.dumps(video_analysis_payload)

        channel.basic_publish(
            exchange='',
            routing_key=CONVERSION_QUEUE,
            body=message,
            properties=pika.BasicProperties(delivery_mode=2)
        )
        logger.info(f" [->] Published job {job_id} to {CONVERSION_QUEUE}. Video Key: {s3_video_key}")
        # --- End Publish ---

        # Now, delete the marker file to prevent reprocessing
        s3_client.delete_object(marker_key)
        logger.info(f" [<-] Job marker deleted: {marker_key}")

    except Exception as e:
        logger.error(f"Error processing job {job_id}: {e}")
