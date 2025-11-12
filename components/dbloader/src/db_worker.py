import typer
import traceback
import os
from pprint import pprint
import logging
import dbloader.srt_parser as parse
import dbloader.mongodb as mongo
import dbloader.utils as utils
import dbloader.solr as solr
from typing_extensions import Annotated
import dbloader.s3 as s3
import dbloader.merge as merge
from typing import List, Dict, Union
from dotenv import load_dotenv
from datetime import datetime, timezone
import pytz
import pika
import time
import json
import logging
from typing import Dict, Any

# --- Configuration and Setup ---

# Configure basic logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - [%(levelname)s] - (%(filename)s:%(lineno)d) - %(funcName)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

logger = logging.getLogger(__name__)

# RabbitMQ Configuration
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
QUEUE_NAME = 'dbloader_jobs' # Queue this worker listens to
load_dotenv()


# --- Worker Actions ---

def delete_job(job_id: str) -> None:
    """
    Deletes all related data for a given job_id.
    """
    logger.info(f"🗑️ DELETE ACTION: Deleting all data for job_id: {job_id}")
    try:
        solr.delete_all_documents_in_solr()
    except Exception as e:
        logger.exception(f"Solr data could not be deleted: {e}")
    logger.info(f"✅ Delete process completed for job_id: {job_id}")

def load_job(job_id: str) -> None:
    """
    Simulates the existing data loading process for a given job_id.
    """
    logger.info(f"📦 LOAD ACTION: Starting load process for job_id: {job_id}")
    try:
        s3_prefix = f"{job_id}/transcripts"
        s3_client = s3.s3Manager()
        keys = s3_client.list_objects_by_prefix(s3_prefix)
        transcripts = dict()
        for key in keys:
            media, role, format = utils.get_media_role_format(key)
            transcripts[(role, format)] = s3_client.get_s3_data(key)
        logging.info(f"Got files from S3: {transcripts.keys()}")

        raw_srt_en = transcripts[("eng", "srt")]
        raw_srt_orig = transcripts[("orig", "srt")]

        subtitles_orig = parse.parse_subtitles(raw_srt_orig)
        subtitles_en = parse.parse_subtitles(raw_srt_en)

        segments = merge.merge_and_segment(subtitles_en, subtitles_orig)
        speakers = merge.get_speakers_from_segments(segments)
        subtitles_orig = merge.assign_segments_to_subtitles(subtitles_orig, segments)
        subtitles_en = merge.assign_segments_to_subtitles(subtitles_en, segments)
        pprint(segments)
        pprint(speakers)
        pprint(subtitles_orig)
        pprint(subtitles_en)

        debate_metadata = {
            "job_id": job_id,
            "media": media,
        }
        solr.update_solr(
            job_id=job_id,
            subtitles_orig=subtitles_orig,
            subtitles_en=subtitles_en,
            segments=segments,
            speakers=speakers,
            metadata=debate_metadata,
        )

        mongo.mongodb_insert_debate(
            job_id=job_id,
            subtitles_orig=subtitles_orig,
            subtitles_en=subtitles_en,
            segments=segments,
            speakers=speakers,
            metadata=debate_metadata,
        )
    except Exception as e:
        print(f"S3 data could not be loaded into secondary databases. An exception occurred: {e}")
    # Placeholder for actual loading logic (e.g., calling an ETL pipeline)
    # Your existing loading implementation would go here...
    logger.info(f"✅ Load process finished for job_id: {job_id}")

# --- RabbitMQ Callback and Dispatcher ---

def callback(ch, method, properties, body):
    """
    Callback function that is executed every time a message is received.
    It handles message parsing, action dispatch, and acknowledgment.
    """
    try:
        # Decode the message body (which should be JSON)
        message: Dict[str, Any] = json.loads(body)

        # Ensure 'action' and 'job_id' are present
        action = message.get('action')
        job_id = message.get('job_id')

        if not action or not job_id:
            logger.error(f"❌ Invalid message format: Missing 'action' or 'job_id'. Body: {body.decode()}")
            # Rejects the message and discards it (or sends it to dead-letter queue if configured)
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            return

        # Dispatch based on the action type
        if action == 'delete':
            delete_job(str(job_id))

        elif action == 'load':
            load_job(str(job_id))

        else:
            logger.warning(f"⚠️ Unknown action '{action}' received for job_id: {job_id}. Skipping.")

        # Acknowledge the message only if processing was successful
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except json.JSONDecodeError:
        logger.error(f"❌ Failed to decode JSON message: {body.decode()}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False) # NACK corrupted message

    except Exception as e:
        logger.error(f"❌ An unexpected error occurred during message processing: {e}")
        # Optionally, you might requeue the message or send it to a DLQ here
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True) # Requeue if processing failed

# --- Main Consumer Loop ---

def start_worker():
    """
    Connects to RabbitMQ, declares the queue, and starts consuming messages.
    """
    logger.info(f"Connecting to RabbitMQ host: {RABBITMQ_HOST}")
    try:
        # Establish connection
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=RABBITMQ_HOST)
        )
        channel = connection.channel()

        # Declare the queue (idempotent operation)
        # durable=True ensures the queue persists even if RabbitMQ restarts
        channel.queue_declare(queue=QUEUE_NAME, durable=True)

        # Set quality of service: only send one unacknowledged message at a time to the worker
        channel.basic_qos(prefetch_count=1)

        logger.info('Worker started. Waiting for messages. To exit press CTRL+C')

        # Start consuming messages
        channel.basic_consume(
            queue=QUEUE_NAME,
            on_message_callback=callback
        )

        channel.start_consuming()

    except pika.exceptions.AMQPConnectionError as e:
        logger.error(f"Failed to connect to RabbitMQ. Ensure the server is running on {RABBITMQ_HOST}. Error: {e}")
    except KeyboardInterrupt:
        logger.info("Worker stopped by user.")
        if 'connection' in locals():
            connection.close()

if __name__ == '__main__':
    start_worker()
