import os
import json
from datetime import datetime
import logging
import aio_pika # New asynchronous library
from aio_pika import connect_robust
from typing import Dict, Any 

logger = logging.getLogger(__name__)

# Constants for the queue and connection
RABBITMQ_QUEUE = "video_analysis_jobs"
RABBITMQ_URL = os.getenv("RABBITMQ_URL") 
# Use a connection pool to manage connections asynchronously
RABBITMQ_POOL = None 

async def get_connection_pool():
    """Returns the global connection pool, initializing it if necessary."""
    global RABBITMQ_POOL
    if RABBITMQ_URL and RABBITMQ_POOL is None:
        try:
            # We initialize a connection/channel pool for efficient reuse
            RABBITMQ_POOL = aio_pika.Pool(
                lambda: connect_robust(RABBITMQ_URL),
                max_size=10 # Max connections in pool
            )
            logger.info("RabbitMQ Connection Pool initialized.")
        except Exception as e:
            logger.error(f"Failed to initialize RabbitMQ connection pool: {e}")
            raise ConnectionError(f"RabbitMQ Pool failed to initialize: {e}")
    
    if RABBITMQ_POOL is None:
        raise ConnectionError("RabbitMQ Pool is not configured or failed to start.")
        
    return RABBITMQ_POOL

async def publish_analysis_job(job_id: str, s3_key: str, title: str):
    """
    Constructs the job message and publishes it using an asynchronous connection pool.
    """
    pool = await get_connection_pool()
    
    # Use 'with' statement for acquiring and releasing connection/channel from the pool
    async with pool.acquire() as connection:
        async with connection.channel() as channel:
            
            # Declare the queue (idempotent operation)
            await channel.declare_queue(RABBITMQ_QUEUE, durable=True)

            message = {
                "job_id": job_id,
                "s3_key": s3_key,
                "title": title,
                "timestamp": datetime.now().isoformat(),
                "origin": os.environ.get("HOSTNAME", "unknown-backend")
            }
            
            message_body = json.dumps(message)
            
            # Publish the message (AIO-PIKA automatically handles persistence)
            await channel.default_exchange.publish(
                aio_pika.Message(
                    body=message_body.encode(),
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                ),
                routing_key=RABBITMQ_QUEUE,
            )
            logger.info(f"Published message successfully to {RABBITMQ_QUEUE}.")

# Remove synchronous publish_analysis_job wrapper
# The client object is no longer needed since we use a pool
# The old RabbitMQClient class is removed
# Note: The api.py file will now call publish_analysis_job directly.