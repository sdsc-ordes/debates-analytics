import logging
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import uuid
from dotenv import load_dotenv
from redis import Redis
from rq import Queue
from datetime import datetime
from lib.models import (
    S3MediaUrls,
    DebateDocument,
    SpeakersDocument,
    SegmentsDocument,
    SubtitlesDocument,
    Speaker,
    Subtitle,
    FacetFilter,
    EnumSubtitleType
)
from lib.s3 import s3Manager
from lib.solr import solr_search, solr_update_segment, solr_update_speakers
from lib.mongodb import (
    mongo_find_one_document,
    mongo_update_document,
    mongo_clean_document,
    mongo_insert_one_document,
    MONGO_MEDIA_COLLECTION,
    MONGO_SPEAKERS_COLLECTION,
    MONGO_SEGMENTS_COLLECTION,
    MONGO_SUBTITLE_COLLECTION,
)


load_dotenv()


SUBTITLE_TYPE_TRANSCRIPT = "transcript"
SUBTITLE_TYPE_TRANSLATION = "translation"
SUBTITLE_TYPE_TRANSCRIPT_EDITED = "transcript_edited"
SUBTITLE_TYPE_TRANSLATION_EDITED = "translation_edited"

api = FastAPI()


redis_conn = Redis(host='redis', port=6379)
q = Queue(connection=redis_conn)

# Configure basic logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - [%(levelname)s] - (%(filename)s:%(lineno)d) - %(funcName)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)


class S3MediaUrlRequest(BaseModel):
    media_id: str = Field(..., description="media_id", examples=["df2afc83-7e69-4868-ba4c-b7c4afed6218"])


class S3MediaUrlResponse(BaseModel):
    signedUrls: List[S3MediaUrls] = Field(..., description="List of presigned URLs")
    signedMediaUrl: str = Field(..., description="Presigned URL for the main media file")


@api.post("/get-signed-urls", response_model=S3MediaUrlResponse)
async def get_media_urls(request: S3MediaUrlRequest):
    """
    Get signed media urls for a debate: these urls allow to directly access objects on S3
    """
    logging.info(f"request: {request}")
    s3_client = s3Manager()

    transcript_keys = s3_client.list_objects_by_prefix(f"{request.media_id}/transcripts")
    logging.info(f"Retrieved transcript keys: {transcript_keys}")

    media_keys = s3_client.list_objects_by_prefix(f"{request.media_id}/media")
    logging.info(f"Retrieved media keys: {media_keys}")

    media_url: str = ""
    download_urls: List[Dict[str, str]] = []
    media_id = request.media_id

    for object_key in media_keys:
        if object_key.lower().endswith(".mp4"):

            media_url = s3_client.get_presigned_url(object_key)
            break

    if not media_url:
        logging.warning(f"No .mp4 media file found for media_id: {media_id}")

    for object_key in transcript_keys:
        filename = object_key.split('/')[-1]

        url = s3_client.get_presigned_url(object_key)

        download_urls.append({
            "url": url,
            "label": filename
        })

    response = {}
    response["signedUrls"] = download_urls
    response["signedMediaUrl"] = media_url

    logging.info(f"Response: {response}")

    return response


class MongoMetadataRequest(BaseModel):
    media_id: str = Field(..., description="media_id", examples=["df2afc83-7e69-4868-ba4c-b7c4afed6218"])


class MongoMetadataResponse(BaseModel):
    debate: Optional[DebateDocument] = None
    speakers: Optional[SpeakersDocument] = None
    segments: Optional[SegmentsDocument] = None
    subtitles: Optional[SubtitlesDocument] = None
    subtitles_en: Optional[SubtitlesDocument] = None

@api.post("/get-metadata", response_model=MongoMetadataResponse)
async def mongo_metadata(request: MongoMetadataRequest):
    logging.info(f"request: {request}")
    debate = mongo_find_one_document(
        {"media_id": request.media_id}, MONGO_MEDIA_COLLECTION
    )
    logging.info(f"debate found for {request.media_id}: {debate}")

    if not debate:
        logger.warning(f"No debate found for media_id: {request.media_id}")
        return MongoMetadataResponse(debate=None)

    debate_document = mongo_clean_document(debate)
    logging.info(f"debate_document after cleaning: {debate_document}")

    debate_obj = DebateDocument(**debate_document)
    logging.info(f"debate_obj: {debate_obj}")

    debate_id = debate["_id"]

    speakers = mongo_find_one_document(
        { "debate_id": debate_id }, MONGO_SPEAKERS_COLLECTION
    )
    speakers_document = mongo_clean_document(speakers)
    speakers_obj = SpeakersDocument(**speakers_document)
    segments = mongo_find_one_document(
        { "debate_id": debate_id }, MONGO_SEGMENTS_COLLECTION
    )
    segments_document = mongo_clean_document(segments)
    segments_obj = SegmentsDocument(**segments_document)

    subtitles = mongo_find_one_document(
        { "debate_id": debate_id, "type": SUBTITLE_TYPE_TRANSCRIPT }, MONGO_SUBTITLE_COLLECTION
    )
    subtitle_keys_to_clean = ["type", "language"]
    subtitles_document = mongo_clean_document(subtitles, keys=subtitle_keys_to_clean)
    subtitles_obj = SubtitlesDocument(**subtitles_document)
    subtitles_en = mongo_find_one_document(
        { "debate_id": debate_id, "type": SUBTITLE_TYPE_TRANSLATION }, MONGO_SUBTITLE_COLLECTION
    )
    subtitles_en_document = mongo_clean_document(subtitles_en, keys=subtitle_keys_to_clean)
    subtitles_en_obj = SubtitlesDocument(**subtitles_en_document)

    response = MongoMetadataResponse(
        debate=debate_obj,
        speakers=speakers_obj,
        segments=segments_obj,
        subtitles=subtitles_obj,
        subtitles_en=subtitles_en_obj,
    )
    return response


class SolrRequest(BaseModel):
    queryTerm: str = Field(..., description="Solr query term can be empty", examples=["honor"])
    sortBy: str = Field(..., description="Solr sort option", examples=["start asc"])
    facetFields: List[str] = Field(
        ..., description="Solr facet field to return",
        examples = [["debate_schedule", "statement_type"]]
    )
    facetFilters: List[FacetFilter]  = Field(
        ..., description="Solr facet filters with set values"
    )


@api.post("/search-solr")
async def search_solr(request: SolrRequest):
    """Fetch search results from Solr"""
    logging.info(f"request: {request}")
    try:
        solr_response = solr_search(solr_request=request)
        logger.info(f"Solr search request: {request}")
        logger.debug(f"Solr response: {solr_response}")
        return solr_response
    except Exception as e:
        logger.error(f"Error in Solr search: {e}")
        return {"error": "Solr search error"}


class UpdateSpeakersRequest(BaseModel):
    media_id: str
    speakers: List[Speaker]


@api.post("/update-speakers", include_in_schema=False)
async def update_speakers(request: UpdateSpeakersRequest):
    """
    Update speakers
    """
    logging.info(f"request: {request}")
    try:
        debate = mongo_find_one_document(
            { "media_id": request.media_id }, MONGO_MEDIA_COLLECTION
        )
        debate_id = debate["_id"]
        speakers_as_dicts = [speaker.dict() for speaker in request.speakers]
        mongo_update_document(
            query={ "debate_id": debate_id },
            values={ "$set": { "speakers": speakers_as_dicts } },
            collection=MONGO_SPEAKERS_COLLECTION
        )
        logger.info(f"Speakers for {request.media_id} updated successfully.")
        solr_update_speakers(media_id=request.media_id, speakers=speakers_as_dicts)
        logger.info(f"Speakers for {request.media_id} updated on Solr.")
    except Exception as e:
        logger.error(f"Error updating speakers for {request.media_id}: {e}")
        return {"error": "Error updating speakers"}


class UpdateSubtitlesRequest(BaseModel):
    media_id: str
    segmentNr: int
    subtitles: List[Subtitle]
    subtitleType: EnumSubtitleType


@api.post("/update-subtitles", include_in_schema=False)
async def update_subtitles(request: UpdateSubtitlesRequest):
    """
    Update subtitles
    """
    logging.info(f"request: {request}")
    try:
        print("in update subtitles")
        print(request)
        debate = mongo_find_one_document(
            { "media_id": request.media_id }, MONGO_MEDIA_COLLECTION
        )
        debate_id = debate["_id"]
        subtitles_as_dicts = [subtitle.dict() for subtitle in request.subtitles]
        if request.subtitleType == EnumSubtitleType.transcript:
            values = { "subtitles": subtitles_as_dicts }
        else:
            values = { "subtitles_en": subtitles_as_dicts }
        if request.subtitleType == EnumSubtitleType.transcript:
            subtitle_type = SUBTITLE_TYPE_TRANSCRIPT
        elif request.subtitleType == EnumSubtitleType.translation:
            subtitle_type = SUBTITLE_TYPE_TRANSLATION
        mongo_update_document(
            query={ "debate_id": debate_id, "type": subtitle_type },
            values={ "$set": values },
            collection=MONGO_SUBTITLE_COLLECTION,
        )
        logger.info(f"Subtitles for {request.media_id} updated successfully.")
        solr_update_segment(
            media_id=request.media_id,
            segment_nr=request.segmentNr,
            subtitles=subtitles_as_dicts,
            subtitle_type=subtitle_type,
        )
        logger.info(f"Subtitles for {request.media_id} updated on Solr.")
    except Exception as e:
        logger.error(f"Error updating subtitles for {request.media_id}: {e}")
        return {"error": "Error updating subtitles"}


class S3PostRequest(BaseModel):
    filename: str = Field(..., description="Original filename with extension (e.g., my_video.mp4)")


class S3PostResponse(BaseModel):
    postUrl: str = Field(..., description="The S3 endpoint URL to POST the file to")
    fields: Dict[str, str] = Field(..., description="Key-value fields required in the multipart form data")
    mediaId: str = Field(..., description="The unique media ID generated by the backend")
    s3Key: str = Field(..., description="The final S3 key where the file will be stored")

@api.post("/get-presigned-post", response_model=S3PostResponse)
async def get_presigned_post(request_data: S3PostRequest):
    """
    [POST] Returns a presigned URL and creates the initial Mongodb record.
    Status -> 'preparing'
    """
    # Generate unique media_id and s3_key
    media_id = str(uuid.uuid4())
    s3_key = f"{media_id}/source.mp4"

    logging.info(f"Generating presigned POST for media_id: {media_id}")

    # Get S3 Presigned URL
    s3_client = s3Manager()
    post_data = s3_client.get_presigned_post(s3_key)

    if not post_data:
        logger.error(f"Failed to generate presigned POST for key: {s3_key}")
        raise HTTPException(status_code=500, detail="Could not generate S3 POST data.")

    # 3. Create Initial Debate Record in MongoDB
    # Use: _id = media_id so it's easy to query later
    initial_doc = {
        "_id": media_id,
        "s3_key": s3_key,
        "original_filename": request_data.filename,
        "status": "preparing",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "error_message": None
    }

    # Insert into MongoDB
    try:
        mongo_insert_one_document(initial_doc, MONGO_MEDIA_COLLECTION)
    except Exception as e:
        logger.error(f"Database insertion failed: {e}")
        raise HTTPException(status_code=500, detail="Database error")

    return S3PostResponse(
        postUrl=post_data["url"],
        fields=post_data["fields"],
        mediaId=media_id,
        s3Key=s3_key
    )


class ProcessRequest(BaseModel):
    s3_key: str = Field(..., description="The final S3 key where the file will be stored")
    media_id: str = Field(..., description="The unique job ID generated by the backend")
    title: str = Field(None, description="filename of the media")


@api.post("/process")
async def start_processing(request: ProcessRequest):
    """
    [POST] Starts the worker job and updates DB status.
    Status -> 'queued'
    """
    logger.info(f"Enqueuing job for media_id: {request.media_id}")

    # Enqueue Job
    job = q.enqueue(
        'converter.process_video',
        request.s3_key,
        media_id=request.media_id,
    )

    # Update Status in MongoDB
    update_fields = {
        "status": "queued",
        "job_id": job.get_id(),
        "updated_at": datetime.utcnow()
    }

    result = mongo_update_document(
        {"_id": request.media_id},
        {"$set": update_fields},
        MONGO_MEDIA_COLLECTION,
    )
    logger.info(f"MongoDB update result: {result}")

    return {
        "status": "queued",
        "media_id": request.media_id,
        "job_id": job.get_id()
    }


def serve():
    """
    Start the FastAPI server.
    """
    uvicorn.run(
        api,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )


if __name__ == "__main__":
    serve()
