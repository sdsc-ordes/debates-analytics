import logging
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from backend.s3 import s3Manager
from backend import mongodb
from backend import solr
from backend import s3
from backend import helpers
from backend import models
import uuid
from uuid import uuid4
from backend.rabbitmq import publish_analysis_job


SUBTITLE_TYPE_TRANSCRIPT = "transcript"
SUBTITLE_TYPE_TRANSLATION = "translation"
SUBTITLE_TYPE_TRANSCRIPT_EDITED = "transcript_edited"
SUBTITLE_TYPE_TRANSLATION_EDITED = "translation_edited"

api = FastAPI()

# Configure basic logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - [%(levelname)s] - (%(filename)s:%(lineno)d) - %(funcName)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)


class S3MediaUrlRequest(BaseModel):
    job_id: str = Field(..., description="job_id", examples=["df2afc83-7e69-4868-ba4c-b7c4afed6218"])

class S3MediaUrlResponse(BaseModel):
    signedUrls: List[models.S3MediaUrls] = Field(..., description="List of presigned URLs")
    signedMediaUrl: str = Field(..., description="Presigned URL for the main media file")


@api.post("/get-signed-urls", response_model=S3MediaUrlResponse)
async def get_media_urls(request: S3MediaUrlRequest):
    """
    Get signed media urls for a debate: these urls allow to directly access objects on S3
    """
    logging.info(f"request: {request}")
    s3_client = s3.s3Manager()

    # Get transcript keys for job_id
    transcript_keys = s3_client.list_objects_by_prefix(f"{request.job_id}/transcripts")
    logging.info(f"Retrieved transcript keys: {transcript_keys}")

    # Get media keys for job_id
    media_keys = s3_client.list_objects_by_prefix(f"{request.job_id}/media")
    logging.info(f"Retrieved media keys: {media_keys}")

    # Initialize variables
    media_url: str = ""
    download_urls: List[Dict[str, str]] = []
    job_id = request.job_id

    # Process Media Keys to find the .mp4 file
    for object_key in media_keys:
        if object_key.lower().endswith(".mp4"):
            # Get the presigned URL for the primary media file
            media_url = s3_client.get_presigned_url(object_key)
            # Assuming only one main media file is needed, break the loop
            break

    if not media_url:
        logging.warning(f"No .mp4 media file found for job_id: {job_id}")

    # Process Transcript Keys for download links
    for object_key in transcript_keys:
        # The label is the filename (the part after the last '/')
        filename = object_key.split('/')[-1]

        # Generate the presigned URL
        url = s3_client.get_presigned_url(object_key)

        # Append the structured dictionary to the list
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
    job_id: str = Field(..., description="job_id", examples=["df2afc83-7e69-4868-ba4c-b7c4afed6218"])


class MongoMetadataResponse(BaseModel):
    debate: Optional[models.DebateDocument] = None
    speakers: Optional[models.SpeakersDocument] = None
    segments: Optional[models.SegmentsDocument] = None
    subtitles: Optional[models.SubtitlesDocument] = None
    subtitles_en: Optional[models.SubtitlesDocument] = None


@api.post("/get-metadata", response_model=MongoMetadataResponse)
async def mongo_metadata(request: MongoMetadataRequest):
    logging.info(f"request: {request}")
    debate = mongodb.mongodb_find_one_document(
        {"job_id": request.job_id}, mongodb.MONGO_DEBATES_COLLECTION
    )
    logging.info(f"debate found for {request.job_id}: {debate}")

    if not debate:
        logger.warning(f"No debate found for job_id: {request.job_id}")
        return MongoMetadataResponse(debate=None)

    debate_document = helpers.clean_document(debate)
    logging.info(f"debate_document after cleaning: {debate_document}")

    debate_obj = models.DebateDocument(**debate_document)
    logging.info(f"debate_obj: {debate_obj}")

    debate_id = debate["_id"]

    speakers = mongodb.mongodb_find_one_document(
        { "debate_id": debate_id }, mongodb.MONGO_SPEAKERS_COLLECTION
    )
    speakers_document = helpers.clean_document(speakers)
    speakers_obj = models.SpeakersDocument(**speakers_document)

    segments = mongodb.mongodb_find_one_document(
        { "debate_id": debate_id }, mongodb.MONGO_SEGMENTS_COLLECTION
    )
    segments_document = helpers.clean_document(segments)
    segments_obj = models.SegmentsDocument(**segments_document)

    subtitles = mongodb.mongodb_find_one_document(
        { "debate_id": debate_id, "type": SUBTITLE_TYPE_TRANSCRIPT }, mongodb.MONGO_SUBTITLE_COLLECTION
    )
    subtitle_keys_to_clean = ["type", "language"]
    subtitles_document = helpers.clean_document(subtitles, keys=subtitle_keys_to_clean)
    subtitles_obj = models.SubtitlesDocument(**subtitles_document)

    subtitles_en = mongodb.mongodb_find_one_document(
        { "debate_id": debate_id, "type": SUBTITLE_TYPE_TRANSLATION }, mongodb.MONGO_SUBTITLE_COLLECTION
    )
    subtitles_en_document = helpers.clean_document(subtitles_en, keys=subtitle_keys_to_clean)
    subtitles_en_obj = models.SubtitlesDocument(**subtitles_en_document)

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
    facetFilters: List[models.FacetFilter]  = Field(
        ..., description="Solr facet filters with set values"
    )


@api.post("/search-solr")
async def search_solr(request: SolrRequest):
    """Fetch search results from Solr"""
    logging.info(f"request: {request}")
    try:
        solr_response = solr.search_solr(solr_request=request)
        logger.info(f"Solr search request: {request}")
        logger.debug(f"Solr response: {solr_response}")
        return solr_response
    except Exception as e:
        logger.error(f"Error in Solr search: {e}")
        return {"error": "Solr search error"}


class UpdateSpeakersRequest(BaseModel):
    job_id: str
    speakers: List[models.Speaker]


@api.post("/update-speakers", include_in_schema=False)
async def update_speakers(request: UpdateSpeakersRequest):
    """
    Update speakers
    """
    logging.info(f"request: {request}")
    try:
        debate = mongodb.mongodb_find_one_document(
            { "job_id": request.job_id }, mongodb.MONGO_DEBATES_COLLECTION
        )
        debate_id = debate["_id"]
        speakers_as_dicts = [speaker.dict() for speaker in request.speakers]
        mongodb.update_document(
            query={ "debate_id": debate_id },
            values={ "$set": { "speakers": speakers_as_dicts } },
            collection=mongodb.MONGO_SPEAKERS_COLLECTION
        )
        logger.info(f"Speakers for {request.job_id} updated successfully.")
        solr.update_speakers(job_id=request.job_id, speakers=speakers_as_dicts)
        logger.info(f"Speakers for {request.job_id} updated on Solr.")
    except Exception as e:
        logger.error(f"Error updating speakers for {request.job_id}: {e}")
        return {"error": "Error updating speakers"}


class UpdateSubtitlesRequest(BaseModel):
    job_id: str
    segmentNr: int
    subtitles: List[models.Subtitle]
    subtitleType: models.EnumSubtitleType


@api.post("/update-subtitles", include_in_schema=False)
async def update_subtitles(request: UpdateSubtitlesRequest):
    """
    Update subtitles
    """
    logging.info(f"request: {request}")
    try:
        print("in update subtitles")
        print(request)
        debate = mongodb.mongodb_find_one_document(
            { "job_id": request.job_id }, mongodb.MONGO_DEBATES_COLLECTION
        )
        debate_id = debate["_id"]
        subtitles_as_dicts = [subtitle.dict() for subtitle in request.subtitles]
        if request.subtitleType == models.EnumSubtitleType.transcript:
            values = { "subtitles": subtitles_as_dicts }
        else:
            values = { "subtitles_en": subtitles_as_dicts }
        if request.subtitleType == models.EnumSubtitleType.transcript:
            subtitle_type = SUBTITLE_TYPE_TRANSCRIPT
        elif request.subtitleType == models.EnumSubtitleType.translation:
            subtitle_type = SUBTITLE_TYPE_TRANSLATION
        mongodb.update_document(
            query={ "debate_id": debate_id, "type": subtitle_type },
            values={ "$set": values },
            collection=mongodb.MONGO_SUBTITLE_COLLECTION,
        )
        logger.info(f"Subtitles for {request.job_id} updated successfully.")
        solr.update_segment(
            job_id=request.job_id,
            segment_nr=request.segmentNr,
            subtitles=subtitles_as_dicts,
            subtitle_type=subtitle_type,
        )
        logger.info(f"Subtitles for {request.job_id} updated on Solr.")
    except Exception as e:
        logger.error(f"Error updating subtitles for {request.job_id}: {e}")
        return {"error": "Error updating subtitles"}


class UploadedMedia(BaseModel):
    label: str
    value: str


class S3UploadedResponse(BaseModel):
    uploadedMedia: List[UploadedMedia] = Field(..., description="List of job ids")

@api.get("/get-uploaded", response_model=S3UploadedResponse)
async def get_uploaded(request: Request):

    logging.info(f"request: {request}")
    s3_client = s3.s3Manager()

    s3_top_prefixes = s3_client.list_top_level_prefixes()
    logging.info(f"Retrieved uploaded keys: {s3_top_prefixes}")

    if s3_top_prefixes:
        media_list = [_get_job_list_item_from_prefix(prefix) for prefix in s3_top_prefixes]
    else:
        media_list = []

    logging.info(f"Derived media list: {media_list}")

    response = {}
    response["uploadedMedia"] = media_list

    logging.info(f"Response: {response}")

    return response


def _get_job_list_item_from_prefix(prefix):
    job_id = prefix.replace("/", "")
    list_item = {"label": f"uploaded {job_id}", "value": job_id}
    return list_item

# --- NEW MODEL: Request for upload POST data ---
class S3PostRequest(BaseModel):
    filename: str = Field(..., description="Original filename with extension (e.g., my_video.mp4)")


# --- NEW MODEL: Response containing the presigned POST data ---
class S3PostResponse(BaseModel):
    postUrl: str = Field(..., description="The S3 endpoint URL to POST the file to")
    fields: Dict[str, str] = Field(..., description="Key-value fields required in the multipart form data")
    jobId: str = Field(..., description="The unique job ID generated by the backend")
    s3Key: str = Field(..., description="The final S3 key where the file will be stored")

# --- NEW ENDPOINT: Get presigned POST data ---
@api.post("/get-presigned-post", response_model=S3PostResponse)
async def get_presigned_post(request_data: S3PostRequest):
    """
    [POST] Returns a presigned URL and fields for the client to upload a file directly to S3 via HTTP POST.
    The file will be stored under {job_id}/media/{filename}.
    """
    # 1. GENERATE THE UNIQUE JOB ID IN THE BACKEND
    job_id = str(uuid.uuid4())

    logging.info(f"Generating presigned POST for job_id: {job_id} / Filename: {request_data.filename}")
    s3_client = s3.s3Manager()

    # Define the full S3 key path for the video
    s3_key = f"{job_id}/media/{request_data.filename}"

    post_data = s3_client.get_presigned_post(s3_key)

    if not post_data:
        logger.error(f"Failed to generate presigned POST data for key: {s3_key}")
        raise HTTPException(status_code=500, detail="Could not generate S3 POST data.")

    # 2. RETURN the S3 URL, the required fields, and the generated IDs
    return S3PostResponse(
        postUrl=post_data["url"],
        fields=post_data["fields"],
        jobId=job_id,
        s3Key=s3_key
    )

class StartAnalysisRequest(BaseModel):
    job_id: str
    s3_key: str
    title: str


@api.post("/start-analysis", response_model=dict[str, str])
async def start_analysis(request_data: StartAnalysisRequest):
    """
    [POST] Registers a job by sending a message to RabbitMQ after a file is successfully uploaded to S3.
    """
    logger.info(f"Received analysis request for job_id: {request_data.job_id}")

    try:
        # FIX: Directly call and AWAIT the asynchronous function.
        # This uses the AIO-PIKA logic which handles the connection/channel pool.
        await publish_analysis_job(
            request_data.job_id, 
            request_data.s3_key, 
            request_data.title
        )
        logger.info(f"Job successfully published to RabbitMQ queue for {request_data.job_id}")
        return {"status": "Job processing triggered."}
    except Exception as e:
        logger.error(f"Failed to publish job {request_data.job_id} to RabbitMQ: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to queue job for processing. RabbitMQ error: {e}"
        )

