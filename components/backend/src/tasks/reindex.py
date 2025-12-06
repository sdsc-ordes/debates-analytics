import logging
from services.s3 import get_s3_manager
from services.solr import get_solr_manager
from services.mongo import get_mongo_manager
from services.parser import JsonTranscriptParser

logger = logging.getLogger(__name__)

def reindex_solr(media_id: str):
    """
    Idempotent task: Reads existing SRTs from S3 and re-indexes them to Solr.
    """
    logger.info(f"Starting Loader Task for {media_id}")

    s3 = get_s3_manager()
    solr = get_solr_manager()
    mongo = get_mongo_manager()
    parser = JsonTranscriptParser()

    # 1. Define S3 Keys (Logic shared with your transcriber)
    # You might want to get these from Mongo, but predicting them is faster for dev
    transcript_key = f"{media_id}/transcripts/segments-original.json"
    translation_key = f"{media_id}/transcripts/segments-translation.json"

    # 2. Clear existing Solr data for this ID (Clean Slate)
    solr.delete_by_media_id(media_id)

    # 3. Helper to process one file
    def process_file(key, subtitle_type):
        logger.info(f"Downloading {key}...")
        # Use the get_file_content helper we wrote earlier
        content = s3.get_file_content(key)

        if not content:
            logger.warning(f"No content found for {key}, skipping.")
            return

        logger.info(f"Parsing {subtitle_type}...")
        solr_docs = parser.parse(
            json_content=content,
            media_id=media_id,
            subtitle_type=subtitle_type,
        )
        logger.info(f"solr_docs: {solr_docs}")

        payload = [doc.model_dump() for doc in solr_docs]

        if payload:
            logger.info(f"Indexing {len(payload)} documents to Solr...")
            solr.client.add(payload, commit=True)

    # 4. Run for both types
    process_file(transcript_key, "original")
    process_file(translation_key, "translation")

    # 5. Update Mongo
    mongo.update_status(media_id, "indexing_completed")
    logger.info(f"Loader task finished for {media_id}")
