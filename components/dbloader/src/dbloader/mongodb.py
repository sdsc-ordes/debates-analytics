import json
import os
from bson import ObjectId
from importlib import resources
from datetime import datetime, timezone
import pytz
from pymongo import MongoClient
from dotenv import load_dotenv
from dbloader import merge

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL")

MONGO_DB = "debates"
MONGO_DEBATES_COLLECTION = "debates"
MONGO_SPEAKERS_COLLECTION = "speakers"
MONGO_SEGMENTS_COLLECTION = "segments"
MONGO_SUBTITLE_COLLECTION = "subtitles"
ZURICH_TZ = pytz.timezone('Europe/Zurich')
LANGUAGE_ENGLISH = "en"


class DataloaderMongoException(Exception):
    pass


def mongodb_insert_debate(subtitles_orig, subtitles_en, metadata, segments, speakers):
    """Insert one debate into the mongodb"""
    debate = _prepare_debate_data(metadata)
    debate_id = _mongodb_insert_one_document(debate, MONGO_DEBATES_COLLECTION)
    document_speakers = {
        "debate_id": ObjectId(debate_id),
        "speakers": _prepare_speakers(speakers)
    }
    _mongodb_insert_one_document(document_speakers, MONGO_SPEAKERS_COLLECTION)
    document_segments = {
        "debate_id": ObjectId(debate_id),
        "segments": segments
    }
    _mongodb_insert_one_document(document_segments, MONGO_SEGMENTS_COLLECTION)
    document_subtitles_orig = {
        "debate_id": ObjectId(debate_id),
        "subtitles": subtitles_orig,
        "type": merge.SUBTITLE_TYPE_TRANSCRIPT,
        "language": None,
    }
    _mongodb_insert_one_document(document_subtitles_orig, MONGO_SUBTITLE_COLLECTION)
    document_subtitles_en = {
        "debate_id": ObjectId(debate_id),
        "subtitles": subtitles_en,
        "type": merge.SUBTITLE_TYPE_TRANSLATION,
        "language": "en",
    }
    _mongodb_insert_one_document(document_subtitles_en, MONGO_SUBTITLE_COLLECTION)
    print(f"Successfully inserted debate into mongodb with id: {debate_id}")
    return {
        "debate": debate,
        "segments": segments,
        "subtitles": subtitles_orig,
        "subtitles_en": subtitles_en,
    }


def _mongodb_insert_one_document(document, collection):
    with MongoClient(MONGO_URL) as client:
        db = client[MONGO_DB]
        document_id = db[collection].insert_one(
            document
        ).inserted_id
        return document_id


def _prepare_speakers(speakers):
    for speaker in speakers:
        speaker["name"] = ""
        speaker["role_tag"] = ""
    return speakers


def _prepare_debate_data(metadata):
    debate = {
        "s3_prefix": metadata["s3_prefix"],
        "created_at": _format_current_datetime(),
        "s3_keys": metadata["s3_keys"],
        "media": metadata["media"],
        "schedule": _format_debate_schedule(metadata["schedule"]),
        "public": metadata["context"]["public"],
        "type": metadata["context"]["type"],
        "session": metadata["context"]["session"],
    }
    return debate


def _format_debate_schedule(schedule):
    datetime_str = f"{schedule['date']} {schedule['time']}"
    naive_datetime = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")
    timezone_obj = pytz.timezone(schedule["timezone"])
    localized_datetime = timezone_obj.localize(naive_datetime)
    utc_datetime = localized_datetime.astimezone(pytz.UTC)
    return _format_date(utc_datetime)


def _format_current_datetime():
    current_datetime = datetime.now(
        timezone.utc
    )
    return _format_date(current_datetime)


def _format_date(dt):
    return dt.isoformat(timespec='milliseconds').replace('+00:00', 'Z')
