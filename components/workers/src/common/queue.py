import os
from redis import Redis
from rq import Queue
from functools import lru_cache

class QueueManager:
    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
        self.conn = Redis.from_url(self.redis_url)
        self.q = Queue(connection=self.conn)

    def enqueue(self, function_name, **kwargs):
        """
        Wrapper to enqueue jobs.
        Accepts kwargs directly and passes them to the worker function.
        """
        return self.q.enqueue(function_name, **kwargs)

    def get_connection(self):
        return self.conn

@lru_cache()
def get_queue_manager() -> QueueManager:
    """
    Creates the manager once and caches it in memory.
    Acting like a Singleton, but that can be overridden in tests.
    """
    return QueueManager()
