import logging
from typing import Optional, Dict, Any
from pymongo import MongoClient, ReturnDocument
from functools import lru_cache
from datetime import datetime

# 1. Import settings instead of os.getenv
from common.config import get_settings

logger = logging.getLogger(__name__)

# 2. Define Constants
SUBTITLE_TYPE_TRANSCRIPT = "transcript"
SUBTITLE_TYPE_TRANSLATION = "translation"

class MongoManager:
    def __init__(self):
        # Load settings
        settings = get_settings()

        self.mongo_url = settings.mongo_url
        self.db_name = settings.mongo_db_name

        try:
            self.client = MongoClient(self.mongo_url)
            self.db = self.client[self.db_name]

            # 3. Initialize ALL collections here
            # If you don't do this, 'self.speakers_collection' will fail later
            self.media_collection = self.db[settings.mongo_media_collection]
            self.speakers_collection = self.db[settings.mongo_speaker_collection]
            self.segments_collection = self.db[settings.mongo_segment_collection]
            self.subtitles_collection = self.db[settings.mongo_subtitle_collection]

            logger.info(f"MongoManager initialized for DB: {self.db_name}")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise e

    # 4. Fixed Indentation: This method is now inside the class
    def get_full_metadata(self, media_id: str) -> Optional[Dict[str, Any]]:
        """
        Aggregates data from Media, Speakers, Segments, and Subtitles collections.
        Returns a dictionary ready for the Pydantic model, or None if media not found.
        """
        debate = self.media_collection.find_one({"media_id": media_id})
        if not debate:
            return None

        # Clean the debate doc
        debate_clean = self._clean_document(debate)

        internal_id = debate["_id"]

        # Fetch Related Data
        speakers = self.speakers_collection.find_one({"debate_id": internal_id})
        segments = self.segments_collection.find_one({"debate_id": internal_id})

        sub_transcript = self.subtitles_collection.find_one({
            "debate_id": internal_id,
            "type": SUBTITLE_TYPE_TRANSCRIPT
        })

        sub_translation = self.subtitles_collection.find_one({
            "debate_id": internal_id,
            "type": SUBTITLE_TYPE_TRANSLATION
        })

        # Construct the result dictionary
        return {
            "debate": debate_clean,
            "speakers": self._clean_document(speakers),
            "segments": self._clean_document(segments),
            "subtitles": self._clean_document(sub_transcript, keys_to_remove=["type", "language"]),
            "subtitles_en": self._clean_document(sub_translation, keys_to_remove=["type", "language"])
        }

    # 4. Fixed Indentation: This method is now inside the class
    def _clean_document(self, doc: dict, keys_to_remove: list = None) -> Optional[dict]:
        """
        Internal helper to clean MongoDB documents.
        """
        if not doc:
            return None

        cleaned = doc.copy()

        # Convert ObjectId to string
        if "_id" in cleaned:
            cleaned["_id"] = str(cleaned["_id"])

        if keys_to_remove:
            for key in keys_to_remove:
                cleaned.pop(key, None)

        return cleaned

    def _get_debate_id_by_media_id(self, media_id: str):
        """Helper to resolve public media_id to internal MongoDB _id"""
        doc = self.media_collection.find_one({"media_id": media_id}, {"_id": 1})
        return doc["_id"] if doc else None

    def update_debate_speakers(self, media_id: str, speakers: list[dict]):
        """
        Updates the speakers list for a specific debate.
        """
        debate_id = self._get_debate_id_by_media_id(media_id)
        if not debate_id:
            return False

        result = self.speakers_collection.update_one(
            {"debate_id": debate_id},
            {"$set": {"speakers": speakers}}
        )
        return result.modified_count > 0 or result.matched_count > 0

    def update_debate_subtitles(self, media_id: str, subtitle_type_enum: str, subtitles: list[dict]):
        """
        Updates subtitles based on type (transcript vs translation).
        Handles the logic of which field to update (subtitles vs subtitles_en).
        """
        debate_id = self._get_debate_id_by_media_id(media_id)
        if not debate_id:
            return False

        # Map Enum to DB Configuration
        # (Moving this logic here keeps the Router clean)
        if subtitle_type_enum == "transcript":
            db_type = "transcript" # The 'type' field in Mongo
            update_field = "subtitles" # The field holding the array
        else:
            # Assuming 'translation'
            db_type = "translation"
            update_field = "subtitles_en"

        result = self.subtitles_collection.update_one(
            {"debate_id": debate_id, "type": db_type},
            {"$set": {update_field: subtitles}}
        )
        return result.modified_count > 0 or result.matched_count > 0

    def update_media_processing_status(self, media_id: str, job_id: str, status: str):
        """Update the status of the media processing."""
        update_fields = {
            "status": status,
            "job_id": job_id,
            "updated_at": datetime.utcnow()
        }

        return self.media_collection.find_one_and_update(
            {"_id": media_id},
            {"$set": update_fields},
            return_document=ReturnDocument.AFTER
        )

    def insert_initial_media_document(self, media_id: str, s3_key: str, filename: str):
        """First entry of the media in the db: assumes that upload to S3 already happened."""
        document = {
            "_id": media_id,
            "s3_key": s3_key,
            "original_filename": filename,
            "status": "preparing",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "error_message": None
        }

        return self.media_collection.insert_one(document)

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
    return MongoManager()
