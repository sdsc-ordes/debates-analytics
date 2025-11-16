# This script is the single entry point for the S3 Watcher Service.
# It relies on the 'worker_lib' package being discoverable (e.g., in a Docker container).
import sys
import os
import logging
import time
from typing import List, Dict, Any, NoReturn
from mediaworkers.s3_handler import s3Manager
from mediaworkers.connection import connect_to_rabbitmq
from mediaworkers.watcher import process_and_queue_job
from mediaworkers.config import WATCH_INTERVAL_SECONDS

# Add the parent directory of worker_lib to the path to enable package discovery
# This assumes the script is run from the project root.
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

logger = logging.getLogger(__name__)

s3_client = s3Manager()

def start_worker() -> NoReturn:
    """Initializes S3, connects to RabbitMQ, and starts the polling loop."""

    connection = None

    try:
        # Use centralized connection logic
        connection = connect_to_rabbitmq()

        # Start Polling Loop
        logger.info("S3 Polling Watcher connected and starting main loop...")
        while True:
            try:
                new_job_markers = s3_client.find_new_jobs()
                if new_job_markers:
                    logger.info(f"Found {len(new_job_markers)} new job(s).")
                    for marker in new_job_markers:
                        # Pass the connection to the processor
                        process_and_queue_job(marker, connection, s3_client)
                else:
                    logger.debug("No new job markers found.")

            except Exception as e:
                logger.error(f"Unhandled error in main watcher loop: {e}")

            time.sleep(WATCH_INTERVAL_SECONDS)

    except KeyboardInterrupt:
        logger.info('Watcher shutting down...')
    finally:
        if connection and connection.is_open:
            connection.close()

if __name__ == '__main__':
    start_worker()
