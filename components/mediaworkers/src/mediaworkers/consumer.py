import sys
import time
import logging
from typing import Callable, NoReturn
# Updated to use relative imports
from .config import CONVERSION_QUEUE, TRANSCRIPTION_QUEUE
from .connection import connect_to_rabbitmq # NEW IMPORT

logger = logging.getLogger(__name__)

def start_consuming(consumer_queue: str, callback_function: Callable) -> NoReturn:
    """
    Establishes connection to RabbitMQ and starts consuming messages.

    :param consumer_queue: The name of the queue to consume messages from.
    :param callback_function: The function to execute when a message is received.
    """

    connection = None

    try:
        # Use centralized connection logic
        connection = connect_to_rabbitmq()
        channel = connection.channel()

        # The queues are already declared by connect_to_rabbitmq, so we just log and consume
        logger.info(f' [*] Waiting for jobs on {consumer_queue}.')

        # Ensure we only process one message at a time
        channel.basic_qos(prefetch_count=1)

        # Define the callback function that includes the active connection object.
        callback_with_connection = lambda ch, method, properties, body: callback_function(
            ch, method, properties, body, connection
        )

        channel.basic_consume(
            queue=consumer_queue,
            on_message_callback=callback_with_connection,
            auto_ack=False
        )

        channel.start_consuming()

    except KeyboardInterrupt:
        logger.info('Consumer shutting down...')
    except Exception as e:
        logger.error(f"An unexpected error occurred in consumer loop: {e}")
    finally:
        if connection and connection.is_open:
            connection.close()
