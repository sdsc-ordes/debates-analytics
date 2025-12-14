import logging
from fastapi import APIRouter, HTTPException, Depends, Query
from services.mongo import get_mongo_manager, MongoManager, DocumentNotFoundError
from services.s3 import get_s3_manager, S3Manager
from services.solr import get_solr_manager, SolrManager
from models.media import S3MediaUrlResponse
from models.metadata import (
    MetadataResponse, UpdateMetadataResponse, UpdateDebateRequest,
    UpdateSpeakersRequest, UpdateSubtitlesRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/get-signed-urls", response_model=S3MediaUrlResponse)
async def get_media_urls(
    media_id: str = Query(..., description="The UUID of the media"),
    s3_client: S3Manager = Depends(get_s3_manager),
):
    """
    Get signed media urls for a debate.
    """
    logger.info(f"Fetching signed URLs for media_id: {media_id}")

    try:
        transcript_keys = s3_client.list_objects_by_prefix(f"{media_id}/transcripts")
        media_keys = s3_client.list_objects_by_prefix(f"{media_id}")
        logger.info(f"media_keys: {media_keys}")
        logger.info(f"transcript_keys: {transcript_keys}")

        logger.info(f"Found {len(transcript_keys)} transcripts and {len(media_keys)} media files.")

    except Exception:
        logger.exception(f"Failed to list objects from S3 for {media_id}")
        raise HTTPException(status_code=500, detail="Storage service unavailable.")

    media_url = ""

    mp4_key = next((key for key in media_keys if key.lower().endswith(".mp4")), None)

    if mp4_key:
        try:
            media_url = s3_client.get_presigned_url(mp4_key)
        except Exception as e:
            logger.error(f"Failed to sign media url for {mp4_key}: {e}")
    else:
        logger.warning(f"No .mp4 media file found for media_id: {media_id}")

    download_urls = []
    for object_key in transcript_keys:
        try:
            filename = object_key.split('/')[-1]
            url = s3_client.get_presigned_url(object_key)

            download_urls.append({
                "url": url,
                "label": filename
            })
        except Exception as e:
            logger.error(f"Failed to sign transcript url for {object_key}: {e}")

    response = {
        "signedUrls": download_urls,
        "signedMediaUrl": media_url
    }

    logger.debug(f"Returning response for {media_id}")
    return response


@router.get("/get-metadata", response_model=MetadataResponse)
async def mongo_metadata(
    media_id: str = Query(..., description="The UUID of the media"),
    mongo_client: MongoManager = Depends(get_mongo_manager),
):
    logger.info(f"Fetching metadata for media_id: {media_id}")

    try:
        # This now returns { debate: ..., speakers: ..., segments: ... }
        metadata = mongo_client.get_full_metadata(media_id)
        logger.info(metadata)
        return metadata

    except DocumentNotFoundError:
        logger.warning(f"Metadata for {media_id} not found")
        raise HTTPException(status_code=404, detail="Media not found")
    except Exception:
        logger.exception(f"Error fetching metadata for {media_id}")
        raise HTTPException(status_code=500, detail="Database error")

@router.post("/update-speakers", response_model=UpdateMetadataResponse)
async def update_speakers(
    request: UpdateSpeakersRequest,
    mongo_client: MongoManager = Depends(get_mongo_manager),
    solr_client: SolrManager = Depends(get_solr_manager),
):
    """
    Update speakers in Mongo and Solr
    """
    logger.info(f"Updating speakers for media_id: {request.media_id}")

    speakers_data = [s.dict() for s in request.speakers]

    try:
        mongo_client.update_speakers(request.media_id, speakers_data)

        solr_client.update_speakers(
            media_id=request.media_id,
            speakers=speakers_data
        )

        return {"status": "success", "media_id": request.media_id}

    except HTTPException:
        raise
    except Exception:
        logger.exception(f"Error updating speakers for {request.media_id}")
        raise HTTPException(status_code=500, detail="Error updating speakers")


@router.post("/update-subtitles", response_model=UpdateMetadataResponse)
async def update_subtitles(
    request: UpdateSubtitlesRequest,
    mongo_client: MongoManager = Depends(get_mongo_manager),
    solr_client: SolrManager = Depends(get_solr_manager),
):
    """
    Update subtitles in Mongo (Segment-based) and Solr
    """
    # Extract values safely from the Pydantic model
    # (If using Enum, .value gives the string, e.g. "Transcript")
    subtitle_type_str = request.subtitle_type.value if hasattr(request.subtitle_type, 'value') else request.subtitle_type

    segment_nr = request.segment_nr
    media_id = request.media_id
    subtitles_data = [s.dict() for s in request.subtitles]

    logger.info(f"Updating segment {segment_nr} ({subtitle_type_str}) for {media_id}")

    try:
        # 1. Update MongoDB (The Source of Truth)
        mongo_client.update_subtitles(
            media_id=media_id,
            segment_nr=segment_nr,  # <--- Now passing this!
            subtitle_type=subtitle_type_str,
            subtitles=subtitles_data
        )

        # 2. Update Solr (Search Index)
        solr_client.update_segment(
            media_id=media_id,
            segment_nr=segment_nr,
            subtitles=subtitles_data,
            subtitle_type=subtitle_type_str,
        )

        return {"status": "success", "media_id": request.media_id}

    except ValueError as ve:
        # Handle the case where segment wasn't found in Mongo
        logger.warning(f"Validation error: {ve}")
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception:
        logger.exception(f"Error updating subtitles for {request.media_id}")
        raise HTTPException(status_code=500, detail="Error updating subtitles")


@router.post("/update-debate", response_model=UpdateMetadataResponse)
def update_debate(
    request: UpdateDebateRequest,
    mongo_client: MongoManager = Depends(get_mongo_manager),
    solr_client: SolrManager = Depends(get_solr_manager),
):
    media_id = request.media_id
    logger.info(f"Updating debate details for {request.media_id}")

    update_data = request.dict(exclude={"media_id"}, exclude_unset=True)
    mongo_client.update_debate_details(media_id, update_data)

    try:
        solr_client.update_debate_details(media_id, update_data)
    except Exception as e:
        logger.error(f"Failed to update Solr metadata: {e}")

    return {"status": "success", "media_id": request.media_id}
