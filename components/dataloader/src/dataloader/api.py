import logging
from datetime import datetime
from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import List, Optional
from dataloader.s3 import s3Manager
from dataloader import mongodb
from dataloader import solr
from dataloader import helpers
from dataloader import merge
from dataloader import models

api = FastAPI()

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class S3MediaUrlRequest(BaseModel):
    prefix: str = Field(..., description="S3 prefix", examples=["HRC_20220328T10000"])
    objectKeys: list[str] = Field(..., description="List of S3 object keys", examples=[["HRC_20220328T10000-files.json"]])
    mediaKey: str = Field(..., description="Object key for main media file", examples=["HRC_20220328T10000.mp4"])

class S3MediaUrlResponse(BaseModel):
    signedUrls: List[models.S3MediaUrls] = Field(..., description="List of presigned URLs")
    signedMediaUrl: str = Field(..., description="Presigned URL for the main media file")


@api.post("/get-media-urls", response_model=S3MediaUrlResponse)
async def get_media_urls(request: S3MediaUrlRequest):
    """
    Get signed media urls for a debate: these urls allow to directly access objects on S3
    """
    try:
        s3_client = s3Manager()
        presigned_urls = []
        for object_key in request.objectKeys:
            url = s3_client.get_presigned_url(request.prefix, object_key)
            presigned_urls.append({
                "url": url,
                "label": object_key,
            })

        response = {}
        response["signedUrls"] = presigned_urls

        filter_media_url = [item["url"]
                            for item in presigned_urls
                            if item["label"] == request.mediaKey]
        if filter_media_url:
            media_url = filter_media_url[0]
        else:
            media_url = s3_client.get_presigned_url(request.prefix, object_key)
        response["signedMediaUrl"] = media_url

        logger.info(f"Generated media URLs for prefix: {request.prefix}, keys: {request.objectKeys}, media key: {request.mediaKey}")
        logger.debug(f"Response: {response}")

        return response
    except Exception as e:
        logger.error(f"Error retrieving signed urls for prefix {request.prefix}: {e}")
        return {"error": f"Error retrieving signed urls for {request.prefix}"}


class MongoMetadataRequest(BaseModel):
    prefix: str = Field(..., description="S3 prefix", examples=["HRC_20220328T0000"])


class MongoMetadataResponse(BaseModel):
    debate: Optional[models.DebateDocument] = None
    speakers: Optional[models.SpeakersDocument] = None
    segments: Optional[models.SegmentsDocument] = None
    subtitles: Optional[models.SubtitlesDocument] = None
    subtitles_en: Optional[models.SubtitlesDocument] = None


@api.post("/mongo-metadata", response_model=MongoMetadataResponse)
async def mongo_metadata(request: MongoMetadataRequest):
    try:
        debate = mongodb.mongodb_find_one_document(
            {"s3_prefix": request.prefix}, mongodb.MONGO_DEBATES_COLLECTION
        )

        if not debate:
            logger.warning(f"No debate found for prefix: {request.prefix}")
            return MongoMetadataResponse(debate=None)

        debate_document = helpers.clean_document(debate)

        debate_document['created_at'] = datetime.fromisoformat(
            debate_document['created_at'].replace('Z', '+00:00'))
        debate_document['schedule'] = datetime.fromisoformat(
            debate_document['schedule'].replace('Z', '+00:00'))

        debate_obj = models.DebateDocument(**debate_document)

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
            { "debate_id": debate_id, "type": merge.SUBTITLE_TYPE_TRANSCRIPT }, mongodb.MONGO_SUBTITLE_COLLECTION
        )
        subtitle_keys_to_clean = ["type", "language"]
        subtitles_document = helpers.clean_document(subtitles, keys=subtitle_keys_to_clean)
        subtitles_obj = models.SubtitlesDocument(**subtitles_document)

        subtitles_en = mongodb.mongodb_find_one_document(
            { "debate_id": debate_id, "type": merge.SUBTITLE_TYPE_TRANSLATION }, mongodb.MONGO_SUBTITLE_COLLECTION
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

    except Exception as e:
        logger.error(f"Error retrieving metadata for prefix {request.prefix}: {e}")
        return {"error": "Error retrieving metadata"}  # For errors, return a dict


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
    try:
        solr_response = solr.search_solr(solr_request=request)
        logger.info(f"Solr search request: {request}")
        logger.debug(f"Solr response: {solr_response}")
        return solr_response
    except Exception as e:
        logger.error(f"Error in Solr search: {e}")
        return {"error": "Solr search error"}


class UpdateSpeakersRequest(BaseModel):
    prefix: str
    speakers: List[models.Speaker]


@api.post("/update-speakers", include_in_schema=False)
async def update_speakers(request: UpdateSpeakersRequest):
    """
    Update speakers
    """
    try:
        debate = mongodb.mongodb_find_one_document(
            { "s3_prefix": request.prefix }, mongodb.MONGO_DEBATES_COLLECTION
        )
        debate_id = debate["_id"]
        speakers_as_dicts = [speaker.dict() for speaker in request.speakers]
        mongodb.update_document(
            query={ "debate_id": debate_id },
            values={ "$set": { "speakers": speakers_as_dicts } },
            collection=mongodb.MONGO_SPEAKERS_COLLECTION
        )
        logger.info(f"Speakers for {request.prefix} updated successfully.")
        solr.update_speakers(s3_prefix=request.prefix, speakers=speakers_as_dicts)
        logger.info(f"Speakers for {request.prefix} updated on Solr.")
    except Exception as e:
        logger.error(f"Error updating speakers for {request.prefix}: {e}")
        return {"error": "Error updating speakers"}


class UpdateSubtitlesRequest(BaseModel):
    prefix: str
    segmentNr: int
    subtitles: List[models.Subtitle]
    subtitleType: models.EnumSubtitleType


@api.post("/update-subtitles", include_in_schema=False)
async def update_subtitles(request: UpdateSubtitlesRequest):
    """
    Update subtitles
    """
    try:
        print("in update subtitles")
        print(request)
        debate = mongodb.mongodb_find_one_document(
            { "s3_prefix": request.prefix }, mongodb.MONGO_DEBATES_COLLECTION
        )
        debate_id = debate["_id"]
        subtitles_as_dicts = [subtitle.dict() for subtitle in request.subtitles]
        if request.subtitleType == models.EnumSubtitleType.transcript:
            values = { "subtitles": subtitles_as_dicts }
        else:
            values = { "subtitles_en": subtitles_as_dicts }
        if request.subtitleType == models.EnumSubtitleType.transcript:
            subtitle_type = merge.SUBTITLE_TYPE_TRANSCRIPT
        elif request.subtitleType == models.EnumSubtitleType.translation:
            subtitle_type = merge.SUBTITLE_TYPE_TRANSLATION
        mongodb.update_document(
            query={ "debate_id": debate_id, "type": subtitle_type },
            values={ "$set": values },
            collection=mongodb.MONGO_SUBTITLE_COLLECTION,
        )
        logger.info(f"Subtitles for {request.prefix} updated successfully.")
        solr.update_segment(
            s3_prefix=request.prefix,
            segment_nr=request.segmentNr,
            subtitles=subtitles_as_dicts,
            subtitle_type=subtitle_type,
        )
        logger.info(f"Subtitles for {request.prefix} updated on Solr.")
    except Exception as e:
        logger.error(f"Error updating subtitles for {request.prefix}: {e}")
        return {"error": "Error updating subtitles"}
