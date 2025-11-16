import sys
import time
import logging
import pika
from typing import NoReturn
# Use relative imports for package settings
from mediaworkers.config import RABBITMQ_URL, CONVERSION_QUEUE, TRANSCRIPTION_QUEUE

logger = logging.getLogger(__name__)

def connect_to_rabbitmq(max_retries: int = 10, retry_delay: int = 5) -> pika.BlockingConnection:
    """
    Attempts to establish a pika BlockingConnection to RabbitMQ with retries.
    Also ensures all required queues are declared before returning the connection.

    :returns: A successful pika.BlockingConnection instance.
    :raises: SystemExit if connection fails after all retries.
    """
    if not RABBITMQ_URL:
        logger.error("FATAL: RABBITMQ_URL environment variable is not set.")
        sys.exit(1)

    url_params = pika.URLParameters(RABBITMQ_URL)

    for attempt in range(max_retries):
        try:
            logger.info(f"Attempting to connect to RabbitMQ (Attempt {attempt + 1}/{max_retries})...")

            connection = pika.BlockingConnection(url_params)
            channel = connection.channel()

            # Declare all relevant queues for robustness
            channel.queue_declare(queue=CONVERSION_QUEUE, durable=True)
            channel.queue_declare(queue=TRANSCRIPTION_QUEUE, durable=True)

            logger.info(' [*] SUCCESSFULLY CONNECTED and Queues Declared.')
            return connection

        except pika.exceptions.AMQPConnectionError as e:
            if attempt < max_retries - 1:
                logger.warning(f" [!] Connection failed. Retrying in {retry_delay} seconds. Error: {e}")
                time.sleep(retry_delay)
            else:
                logger.error(f" [!] Fatal Error: Could not connect to RabbitMQ after {max_retries} attempts. Error: {e}")
                sys.exit(1)
        except Exception as e:
            logger.error(f"An unexpected error occurred during connection: {e}")
            sys.exit(1)

    # Should be unreachable if sys.exit(1) is called on fatal error, but included for typing clarity.
    raise SystemExit(1)
