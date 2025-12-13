import logging
from typing import Optional, Dict, Any, List, Set
from pymongo import MongoClient, ReturnDocument
from datetime import datetime
from config.settings import get_settings
from functools import lru_cache

logger = logging.getLogger(__name__)


class DocumentNotFoundError(Exception):
    pass

class MongoManager:
    def __init__(self):
        settings = get_settings()
        self.mongo_url = settings.mongo_url
        self.db_name = settings.mongo_db_name
        self.type_original = settings.type_original
        self.type_translation = settings.type_translation

        try:
            self.client = MongoClient(self.mongo_url)
            self.db = self.client[self.db_name]

            # Collections
            self.media_collection = self.db[settings.mongo_media_collection]
            self.speakers_collection = self.db[settings.mongo_speaker_collection]
            # We use one collection for subtitles/segments, differentiated by 'type'
            self.subtitles_collection = self.db[settings.mongo_subtitle_collection]
            self.segments_collection = self.db[settings.mongo_segment_collection]

            logger.info(f"MongoManager initialized for DB: {self.db_name}")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise e

    def update_processing_status(self, media_id: str, status: str, job_id: str = None, metadata: Dict = None):
        update_fields = {"status": status, "updated_at": datetime.utcnow()}
        if job_id:
            update_fields["job_id"] = job_id
        if metadata:
            update_fields.update(metadata)

        return self.media_collection.find_one_and_update(
            {"_id": media_id},
            {"$set": update_fields},
            return_document=ReturnDocument.AFTER
        )

    def save_speakers(self, media_id: str, speaker_ids: Set[str]):
        speakers = [{"speaker_id": sid, "name": "", "role_tag": ""} for sid in speaker_ids]
        doc = {
            "media_id": media_id,
            "speakers": speakers,
            "updated_at": datetime.utcnow()
        }

        self.speakers_collection.update_one(
            {"media_id": media_id},
            {"$set": doc},
            upsert=True
        )

    def save_segments(
        self,
        media_id: str,
        segment_nr: int,
        subtitle_type: str,
        subtitles: List[Dict],
        start: float = None,
        end: float = None,
        speaker_id: str = None,
    ):
        """
        Saves subtitles to a specific segment document.
        Optionally updates the segment's root metadata (Start/End/Speaker).
        """
        if subtitle_type == self.type_original:
            target_field = "subtitles_original"
        elif subtitle_type == self.type_translation:
            target_field = "subtitles_translation"
        else:
            raise ValueError(f"Unknown subtitle_type: {subtitle_type}")

        update_fields = {
            target_field: subtitles,
            "updated_at": datetime.utcnow()
        }

        if start is not None:
            update_fields["start"] = start
        if end is not None:
            update_fields["end"] = end
        if speaker_id is not None:
            update_fields["speaker_id"] = speaker_id

        self.segments_collection.update_one(
            {
                "media_id": media_id,
                "segment_nr": segment_nr
            },
            {
                "$set": update_fields
            },
            upsert=True
        )

    def get_full_metadata(self, media_id: str) -> Dict[str, Any]:
        # 1. Get Debate Document
        debate = self.media_collection.find_one({"_id": media_id})
        if not debate:
            raise DocumentNotFoundError(f"Debate {media_id} not found")

        # Clean _id to media_id
        debate["media_id"] = str(debate.pop("_id"))
        logger.info(debate)

        # 2. Get Speakers
        # (Assuming your save_speakers stores a document with a "speakers" list field)
        logger.info(f"media_id = {media_id}")
        speakers_doc = self.speakers_collection.find_one({"media_id": media_id})
        logger.info(f"found: {speakers_doc}")
        speakers_list = speakers_doc.get("speakers", []) if speakers_doc else []

        # 3. Get All Segments (Sorted)
        # This returns the docs that ALREADY contain 'subtitles_original'
        # and 'subtitles_translation' arrays inside them.
        cursor = self.segments_collection.find({"media_id": media_id}).sort("segment_nr", 1)
        segments_list = list(cursor)
        logger.info(segments_list)

        # 4. Return the clean structure
        return {
            "debate": debate,
            "speakers": speakers_list,
            "segments": segments_list
        }

    def update_speakers(self, media_id: str, speakers: List[Dict[str, Any]]):
        """
        Updates the speaker list with new names and roles.
        Expects 'speakers' to be a list of dicts:
        [{'speaker_id': '...', 'name': '...', 'role_tag': '...'}, ...]
        """
        doc = {
            "speakers": speakers,
            "updated_at": datetime.utcnow()
        }

        self.speakers_collection.update_one(
            {"media_id": media_id},
            {"$set": doc}
        )

    def update_subtitles(self, media_id: str, subtitle_type: str, subtitles: list[dict]):
        """
        Updates subtitles based on type (transcript vs translation).
        Handles the logic of which field to update (subtitles vs subtitles_en).
        """
        if subtitle_type == "transcript":
            db_type = "original"
            update_field = "subtitles"
        else:
            db_type = "translation"
            update_field = "subtitles_en"

        self.subtitles_collection.update_one(
            {"media_id": media_id, "type": db_type},
            {"$set": {update_field: subtitles}}
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
        self.speakers_collection.delete_one({"media_id": media_id})
        self.subtitles_collection.delete_many({"media_id": media_id})
        self.segments_collection.delete_one({"media_id": media_id})
        self.media_collection.delete_one({"_id": media_id})
        return True


@lru_cache()
def get_mongo_manager() -> MongoManager:
    return MongoManager()
