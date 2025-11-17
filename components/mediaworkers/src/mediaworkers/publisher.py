import json
import logging
import pika
from typing import Dict, Any
# Updated to use relative import
from mediaworkers.config import TRANSCRIPTION_QUEUE

def send_to_queue(job_payload: Dict[str, Any], connection: pika.BlockingConnection):
    """
    Publishes a message to the transcription queue using an existing connection.
    """
    try:
        # Use a new channel for thread-safety if needed, but safe here for synchronous worker
        channel = connection.channel()
        channel.queue_declare(queue=TRANSCRIPTION_QUEUE, durable=True)

        message = json.dumps(job_payload)

        channel.basic_publish(
            exchange='',
            routing_key=TRANSCRIPTION_QUEUE,
            body=message,
            properties=pika.BasicProperties(delivery_mode=1)
        )
        logging.info(f" [->] Sent job {job_payload['job_id']} to {TRANSCRIPTION_QUEUE}")

    except pika.exceptions.AMQPError as e:
        logging.error(f"Failed to publish message to RabbitMQ: {e}")
        raise # Re-raise to allow the main worker to handle rejection/requeue
