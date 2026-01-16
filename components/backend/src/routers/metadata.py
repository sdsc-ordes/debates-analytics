import logging
from fastapi import APIRouter, HTTPException, Depends, Query
from services.mongo import get_mongo_manager, MongoManager, DocumentNotFoundError
from services.s3 import get_s3_manager, S3Manager
from services.solr import get_solr_manager, SolrManager
from models.metadata import (
    MetadataResponse, UpdateMetadataResponse, UpdateDebateRequest,
    UpdateSpeakersRequest, UpdateSubtitlesRequest, MediaType, S3MediaUrlResponse
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/get-signed-urls", response_model=S3MediaUrlResponse)
async def get_media_urls(
    media_id: str = Query(..., description="The UUID of the media"),
    s3_client: S3Manager = Depends(get_s3_manager),
    mongo_client: MongoManager = Depends(get_mongo_manager),
):
    """
    Get signed media urls for a debate.
    """
    # Entry Log
    logger.info(f"media_id={media_id} - GET signed URLs request received.")

    # Fetch Metadata
    try:
        debate = mongo_client.get_debate_metadata(media_id)
        if not debate:
            logger.warning(f"media_id={media_id} - Metadata not found in MongoDB.")
            raise HTTPException(status_code=404, detail="Media not found")
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        logger.exception(f"media_id={media_id} - Failed to fetch metadata from MongoDB.")
        raise HTTPException(status_code=500, detail="Database error")

    # List Files from S3
    try:
        file_keys = s3_client.list_objects_by_prefix(f"{media_id}")
        logger.info(f"media_id={media_id} - Found {len(file_keys)} files in S3.")
    except Exception:
        logger.exception(f"media_id={media_id} - Failed to list objects from S3.")
        raise HTTPException(status_code=500, detail="Storage service unavailable.")

    # Generate URLs
    download_urls = []

    # Default to video if missing
    media_type = debate.get("media_type", MediaType.video.value)
    media_url = ""

    for object_key in file_keys:
        try:
            filename = _get_file_name_from_s3_key(object_key)
            url = s3_client.get_presigned_url(object_key, as_attachment=True)

            download_urls.append({
                "url": url,
                "label": filename
            })

            if _is_audio_file(filename) and media_type == MediaType.audio.value:
                media_url = s3_client.get_presigned_url(object_key, as_attachment=False)
            elif _is_video_file(filename) and media_type == MediaType.video.value:
                media_url = s3_client.get_presigned_url(object_key, as_attachment=False)
        except Exception as e:
            # Log specific signing failure, but don't crash the whole request
            logger.error(f"media_id={media_id} - Failed to sign URL for key '{object_key}': {e}")

    if not media_url:
        logger.warning(f"media_id={media_id} - No playable media found matching type '{media_type}'")

    logger.info(f"media_id={media_id} - Returning {len(download_urls)} signed URLs.")

    logger.info(f"response: urls {download_urls}, media_url: {media_url}")
    return {
        "signedUrls": download_urls,
        "signedMediaUrl": media_url,
    }


def _get_file_name_from_s3_key(s3_key: str) -> str:
    return s3_key.split('/')[-1]


def _is_audio_file(file_key) -> bool:
    return file_key.lower().endswith('.wav')


def _is_video_file(file_key) -> bool:
    return file_key.lower().endswith('.mp4')


@router.get("/get-metadata", response_model=MetadataResponse)
async def mongo_metadata(
    media_id: str = Query(..., description="The UUID of the media"),
    mongo_client: MongoManager = Depends(get_mongo_manager),
):
    logger.info(f"media_id={media_id} - GET metadata request received.")

    try:
        # Fetch full metadata from MongoDB
        metadata = mongo_client.get_full_metadata(media_id)

        seg_count = len(metadata.get("segments", []) or [])
        spk_count = len(metadata.get("speakers", []) or [])
        logger.info(f"media_id={media_id} - Metadata retrieved successfully. "
                    f"Contains {seg_count} segments and {spk_count} speakers.")

        return metadata

    except DocumentNotFoundError:
        logger.warning(f"media_id={media_id} - Metadata not found in MongoDB.")
        raise HTTPException(status_code=404, detail="Media not found")

    except Exception:
        logger.exception(f"media_id={media_id} - CRITICAL: Failed to fetch metadata.")
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
    media_id = request.media_id
    count = len(request.speakers)

    logger.info(f"media_id={media_id} - UPDATE speakers request received. Updating {count} speakers.")

    speakers_data = [s.dict() for s in request.speakers]

    try:
        mongo_client.update_speakers(media_id, speakers_data)

        logger.info(f"media_id={media_id} - MongoDB speakers updated successfully.")

        solr_client.update_speakers(
            media_id=media_id,
            speakers=speakers_data
        )
        logger.info(f"media_id={media_id} - Solr index synced successfully.")

        return {"status": "success", "media_id": media_id}

    except HTTPException:
        raise

    except Exception:
        logger.exception(f"media_id={media_id} - CRITICAL: Failed to update speakers.")
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
    # Setup Context Variables
    media_id = request.media_id
    segment_nr = request.segment_nr
    subtitle_count = len(request.subtitles)

    # Extract Enum value safely
    subtitle_type_str = request.subtitle_type.value if hasattr(request.subtitle_type, 'value') else request.subtitle_type
    logger.info(f"media_id={media_id} - UPDATE subtitles request. "
                f"Segment={segment_nr}, Type={subtitle_type_str}, Items={subtitle_count}")

    subtitles_data = [s.dict() for s in request.subtitles]

    try:
        # 3. Update MongoDB (Source of Truth)
        mongo_client.update_subtitles(
            media_id=media_id,
            segment_nr=segment_nr,
            subtitle_type=subtitle_type_str,
            subtitles=subtitles_data
        )
        logger.info(f"media_id={media_id} - MongoDB segment {segment_nr} updated successfully.")

        # 4. Update Solr (Search Index)
        solr_client.update_segment(
            media_id=media_id,
            segment_nr=segment_nr,
            subtitles=subtitles_data,
            subtitle_type=subtitle_type_str,
        )
        logger.info(f"media_id={media_id} - Solr index for segment {segment_nr} synced successfully.")

        return {"status": "success", "media_id": media_id}

    except ValueError as ve:
        # Handle Validation Errors (Client-side issue)
        logger.warning(f"media_id={media_id} - Validation failed for Segment {segment_nr}: {ve}")
        raise HTTPException(status_code=404, detail=str(ve))

    except Exception:
        # Handle System Crashes (Server-side issue)
        logger.exception(f"media_id={media_id} - CRITICAL: Failed to update subtitles for Segment {segment_nr}.")
        raise HTTPException(status_code=500, detail="Error updating subtitles")


@router.post("/update-debate", response_model=UpdateMetadataResponse)
def update_debate(
    request: UpdateDebateRequest,
    mongo_client: MongoManager = Depends(get_mongo_manager),
    solr_client: SolrManager = Depends(get_solr_manager),
):
    media_id = request.media_id

    # Prepare Data
    update_data = request.dict(exclude={"media_id"})
    keys_changed = list(update_data.keys())
    logger.info(f"media_id={media_id} - UPDATE debate details request. Fields={keys_changed}")

    if not update_data:
        logger.warning(f"media_id={media_id} - Update received with no fields changed. Skipping.")
        return {"status": "no_change", "media_id": media_id}

    try:
        # Update MongoDB
        mongo_client.update_debate_details(media_id, update_data)
        logger.info(f"media_id={media_id} - MongoDB debate details updated.")

        # Sync Solr (Search Index)
        try:
            solr_client.update_debate_details(media_id, update_data)
            logger.info(f"media_id={media_id} - Solr index synced successfully.")
        except Exception as e:
            logger.error(f"media_id={media_id} - PARTIAL FAIL: MongoDB updated, but Solr sync failed: {e}", exc_info=True)

        return {"status": "success", "media_id": media_id}

    except HTTPException:
        raise
    except Exception:
        # Catch-all for MongoDB or logic crashes
        logger.exception(f"media_id={media_id} - CRITICAL: Failed to update debate details.")
        raise HTTPException(status_code=500, detail="Error updating debate details")
