import os
import logging
from datetime import datetime
from pymongo import MongoClient, ReturnDocument
from functools import lru_cache

# Setup Logger
logger = logging.getLogger(__name__)

class MongoManager:
    def __init__(self):
        self.mongo_uri = os.getenv("MONGO_URI")
        self.db_name = os.getenv("MONGO_DB_NAME")
        self.collection_name = os.getenv("MONGO_MEDIA_COLLECTION")

        try:
            self.client = MongoClient(self.mongo_uri)
            self.db = self.client[self.db_name]
            self.collection = self.db[self.collection_name]
            logger.info(f"Connected to MongoDB: {self.db_name}.{self.collection_name}")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise e

    def get_media(self, media_id: str):
        """Retrieves the full media document."""
        return self.collection.find_one({"media_id": media_id})

    def update_status(self, media_id: str, status: str, job_id: str = None, metadata: dict = None):
        """
        Updates the status of a media entry.

        Args:
            media_id: The UUID of the media.
            status: The new status string (e.g., 'converting', 'transcribing').
            job_id: (Optional) The Redis Job ID associated with this step.
            metadata: (Optional) Dictionary of extra data to merge (e.g., {'wav_key': '...'})
        """
        update_fields = {
            "status": status,
            "updated_at": datetime.utcnow()
        }

        if job_id:
            update_fields["current_job_id"] = job_id

        if metadata:
            for key, value in metadata.items():
                update_fields[key] = value

        logger.info(f"Updating Media {media_id} -> Status: {status}")

        return self.collection.find_one_and_update(
            {"media_id": media_id},
            {"$set": update_fields},
            return_document=ReturnDocument.AFTER
        )

    def mark_failed(self, media_id: str, error_message: str):
        """Special helper to mark a job as failed with an error reason."""
        logger.error(f"Marking Media {media_id} as FAILED: {error_message}")

        self.collection.update_one(
            {"media_id": media_id},
            {"$set": {
                "status": "error",
                "error_message": str(error_message),
                "updated_at": datetime.utcnow()
            }}
        )


@lru_cache()
def get_mongo_manager() -> MongoManager:
    """
    Creates the manager once and caches it in memory.
    Acting like a Singleton, but that can be overridden in tests.
    """
    return MongoManager()
