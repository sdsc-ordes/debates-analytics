import logging
from redis import Redis
from rq import Queue
from functools import lru_cache
from common.config import get_settings

logger = logging.getLogger(__name__)

class QueueManager:
    def __init__(self):
        settings = get_settings()

        self.redis_conn = Redis.from_url(settings.redis_url)
        self.q = Queue(connection=self.redis_conn)
        self.task_convert = settings.task_convert

    def enqueue_video_processing(self, media_id: str, s3_key: str):
        """
        Specific method for processing videos.
        Abstraction: The caller doesn't need to know the task function path.
        """
        # We delegate to RQ here
        job = self.q.enqueue(
            self.task_convert,
            media_id=media_id,
            s3_key=s3_key,
        )
        return job

    def get_connection(self):
        return self.conn

@lru_cache()
def get_queue_manager() -> QueueManager:
    """
    Creates the manager once and caches it in memory.
    Acting like a Singleton, but that can be overridden in tests.
    """
    return QueueManager()
