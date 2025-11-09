import json
import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL")

MONGO_DB = "debates"
MONGO_DEBATES_COLLECTION = "debates"
MONGO_SPEAKERS_COLLECTION = "speakers"
MONGO_SEGMENTS_COLLECTION = "segments"
MONGO_SUBTITLE_COLLECTION = "subtitles"


def mongodb_find_one_document(query, collection):
    """Find debates in MongoDB and return s3_prefix and version_id."""
    with MongoClient(MONGO_URL) as client:
        db = client[MONGO_DB]
        document = db[collection].find_one(query)
        return document


def update_document(query, values, collection):
    with MongoClient(MONGO_URL) as client:
        db = client[MONGO_DB]
        result = db[collection].update_one(
            query,
            values,
        )
        print(result)
