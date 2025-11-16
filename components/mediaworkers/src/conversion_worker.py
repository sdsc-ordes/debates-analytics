import os
import sys
import json
import logging
import pika
import logging
from typing import Dict, Any, Callable
from mediaworkers.state import load_job_state, update_job_log

# Import modular components
from mediaworkers.config import (
    CONVERSION_QUEUE, TEMP_DIR
)
from mediaworkers.s3_handler import s3Manager
from mediaworkers.publisher import send_to_queue
from mediaworkers.convert import convert_to_wav
from mediaworkers.consumer import start_consuming # NEW IMPORT

logger = logging.getLogger(__name__)

s3_client = s3Manager()

def process_conversion_job(ch, method, properties, body, connection: pika.BlockingConnection):
    """
    Main callback when a job message is received from RabbitMQ.
    Downloads video, converts to WAV, uploads WAV, and sends the next job.

    NOTE: This signature must accept the connection object to allow for publishing.
    """
    job_data: Dict[str, Any] = {}
    local_video_path = ""
    local_wav_path = ""

    try:
        # 1. Deserialize the message
        job_data = json.loads(body)
        job_id = job_data['job_id']
        s3_video_key = job_data['s3_key']

        existing_state = s3_client.load_job_state(job_id)
        status = existing_state.get('status') if existing_state else "MISSING"

        if status in ["CONVERSION_COMPLETE", "PROCESSING", "TRANSCRIPTION_COMPLETE", "CONVERSION_FAILED"]:
            logger.warning(f" [STATE] Job {job_id} already processed or locked. Status: {status}. Acknowledging.")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        s3_client.update_job_log(job_id, "PROCESSING", "Conversion worker started processing video file.")

        # Derive paths
        file_name_with_ext = os.path.basename(s3_video_key)
        file_name = os.path.splitext(file_name_with_ext)[0]
        s3_prefix = os.path.dirname(s3_video_key)

        logging.info(f" [x] RECEIVED JOB {job_id}. Starting conversion workflow for {s3_video_key}.")

        # 2. Define local paths
        local_video_path = os.path.join(TEMP_DIR, file_name_with_ext)
        local_wav_path = os.path.join(TEMP_DIR, f"{file_name}.wav")
        s3_wav_key = f"{s3_prefix}/{file_name}.wav"

        # 3. Execute Workflow Steps (using imported modules)
        s3_client.download_file(s3_video_key, local_video_path)
        convert_to_wav(local_video_path, local_wav_path)
        s3_client.upload_file(local_wav_path, s3_wav_key)

        s3_client.update_job_log(
            job_id=job_id,
            status="CONVERSION_COMPLETE",
            log_message=f"Successfully converted video to WAV at {s3_wav_key}.",
            new_fields={"s3_audio_key": s3_wav_key}
        )

        # 4. Prepare and Send Next Job (Producer action)
        transcription_payload = {
            "job_id": job_id,
            "s3_prefix": s3_prefix,
            "audio_key": s3_wav_key,
            "original_video_key": s3_video_key,
            "status": "CONVERSION_COMPLETE"
        }
        send_to_queue(transcription_payload, connection)

        # 5. Acknowledge success
        ch.basic_ack(delivery_tag=method.delivery_tag)
        logging.info(f" [x] Job {job_id} fully processed and acknowledged.")

    except (json.JSONDecodeError, KeyError) as e:
        # Malformed message, acknowledge and skip
        logging.error(f" [!] Malformed job message received: {body.decode()}. Error: {e}")
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        # Other fatal errors (S3, FFmpeg), reject and requeue for retry
        logging.error(f" [!] Fatal error processing job {job_data.get('job_id', 'Unknown')}: {e}")
        self.update_job_log(job_id, "CONVERSION_FAILED", f"Critical error during conversion: {e}")
        ch.basic_reject(delivery_tag=method.delivery_tag, requeue=True)
    finally:
        # 6. Clean up local files
        if os.path.exists(local_video_path):
            os.remove(local_video_path)
        if os.path.exists(local_wav_path):
            os.remove(local_wav_path)


def start_worker():
    """Initializes environment and delegates consumption to the consumer module."""

    # Ensure local directory exists
    os.makedirs(TEMP_DIR, exist_ok=True)

    # Start consuming messages on the CONVERSION_QUEUE, passing the job processor
    # The consumer module handles connection, retries, and queue declaration.
    start_consuming(CONVERSION_QUEUE, process_conversion_job)

if __name__ == '__main__':
    start_worker()
