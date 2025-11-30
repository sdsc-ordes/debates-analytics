import logging
from typing import Optional, Dict, Any
from pymongo import MongoClient, ReturnDocument
from functools import lru_cache
from datetime import datetime
from config.settings import get_settings

logger = logging.getLogger(__name__)

SUBTITLE_TYPE_TRANSCRIPT = "transcript"
SUBTITLE_TYPE_TRANSLATION = "translation"

class MongoManager:
    def __init__(self):
        settings = get_settings()

        self.mongo_url = settings.mongo_url
        self.db_name = settings.mongo_db_name

        try:
            self.client = MongoClient(self.mongo_url)
            self.db = self.client[self.db_name]

            self.media_collection = self.db[settings.mongo_media_collection]
            self.speakers_collection = self.db[settings.mongo_speaker_collection]
            self.segments_collection = self.db[settings.mongo_segment_collection]
            self.subtitles_collection = self.db[settings.mongo_subtitle_collection]

            logger.info(f"MongoManager initialized for DB: {self.db_name}")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise e

    def get_full_metadata(self, media_id: str) -> Optional[Dict[str, Any]]:
        """
        Aggregates data from Media, Speakers, Segments, and Subtitles collections.
        Returns a dictionary ready for the Pydantic model, or None if media not found.
        """
        debate = self.media_collection.find_one({"media_id": media_id})
        if not debate:
            return None

        debate_clean = self._clean_document(debate)

        internal_id = debate["_id"]

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

        return {
            "debate": debate_clean,
            "speakers": self._clean_document(speakers),
            "segments": self._clean_document(segments),
            "subtitles": self._clean_document(sub_transcript, keys_to_remove=["type", "language"]),
            "subtitles_en": self._clean_document(sub_translation, keys_to_remove=["type", "language"])
        }

    def _clean_document(self, doc: dict, keys_to_remove: list = None) -> Optional[dict]:
        """
        Internal helper to clean MongoDB documents.
        """
        if not doc:
            return None

        cleaned = doc.copy()

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

        if subtitle_type_enum == "transcript":
            db_type = "transcript"
            update_field = "subtitles"
        else:
            db_type = "translation"
            update_field = "subtitles_en"

        result = self.subtitles_collection.update_one(
            {"debate_id": debate_id, "type": db_type},
            {"$set": {update_field: subtitles}}
        )
        return result.modified_count > 0 or result.matched_count > 0

    def update_processing_status(
        self,
        media_id: str,
        status: str,
        job_id: str = None,
        metadata: Dict = None,
    ):
        """Update the status of the media processing."""
        update_fields = {
            "status": status,
            "updated_at": datetime.utcnow()
        }

        if job_id:
            update_fields["job_id"] = job_id

        if metadata:
            for key, value in metadata.items():
                update_fields[key] = value

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

    def get_all_media(self):
        """Returns all media documents sorted by date"""
        cursor = self.media_collection.find().sort("created_at", -1)
        return list(cursor)

    def delete_everything(self, media_id: str):
        """
        Deletes media doc AND all related speakers/subtitles/segments.
        """
        logger.info(f"delete mongo for {media_id}")
        # 1. Get the internal ObjectId to find relations
        doc = self.media_collection.find_one({"_id": media_id})
        logger.info(f"found doc {doc}")
        if not doc:
            return False

        #internal_id = doc["_id"]

        # 2. Delete Related Data first
        ##self.speakers_collection.delete_many({"debate_id": internal_id})
        #self.subtitles_collection.delete_many({"debate_id": internal_id})
        #self.segments_collection.delete_many({"debate_id": internal_id})

        # 3. Delete the Media Doc
        self.media_collection.delete_one({"_id": media_id})
        return True


@lru_cache()
def get_mongo_manager() -> MongoManager:
    return MongoManager()
