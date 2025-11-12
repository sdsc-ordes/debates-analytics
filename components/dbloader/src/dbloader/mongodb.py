import json
import os
from bson import ObjectId
from importlib import resources
from datetime import datetime, timezone
import pytz
from pymongo import MongoClient
from dotenv import load_dotenv
from dbloader import merge
from dbloader import utils
import logging

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


def mongodb_insert_debate(
    job_id,
    subtitles_orig,
    subtitles_en,
    metadata,
    segments,
    speakers
):
    """Insert one debate into the mongodb"""
    debate_id = _mongodb_insert_one_document(metadata, MONGO_DEBATES_COLLECTION)
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
    logging.info(f"Successfully inserted debate into mongodb with id: {job_id}")


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
