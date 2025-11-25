import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL")

MONGO_DB_NAME = os.getenv("MONGO_DB_NAME")
MONGO_MEDIA_COLLECTION = os.getenv("MONGO_MEDIA_COLLECTION")
MONGO_SPEAKERS_COLLECTION = os.getenv("MONGO_SPEAKERS_COLLECTION")
MONGO_SEGMENTS_COLLECTION = os.getenv("MONGO_SEGMENTS_COLLECTION")
MONGO_SUBTITLE_COLLECTION = os.getenv("MONGO_SUBTITLE_COLLECTION")

def mongo_find_one_document(query, collection):
    """Find debates in MongoDB and return s3_prefix and version_id."""
    with MongoClient(MONGO_URL) as client:
        db = client[MONGO_DB_NAME]
        document = db[collection].find_one(query)
        return document


def mongo_insert_one_document(document, collection):
    """Insert a document into a MongoDB collection."""
    with MongoClient(MONGO_URL) as client:
        db = client[MONGO_DB_NAME]
        result = db[collection].insert_one(document)

        return result.inserted_id


def mongo_update_document(query, values, collection):
    with MongoClient(MONGO_URL) as client:
        db = client[MONGO_DB_NAME]
        result = db[collection].update_one(
            query,
            values,
        )
        print(result)


def mongo_clean_document(document, keys=None):
    cleaned_document = document.copy()
    cleaned_document.pop("_id", None)
    cleaned_document.pop("debate_id", None)
    if not keys:
        return cleaned_document
    for key in keys:
        cleaned_document.pop(key, None)
    return cleaned_document
