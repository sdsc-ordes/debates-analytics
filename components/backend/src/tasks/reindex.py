import logging
from services.s3 import get_s3_manager
from services.solr import get_solr_manager
from services.mongo import get_mongo_manager
from services.parser import JsonTranscriptParser

logger = logging.getLogger(__name__)

# Constants
TYPE_ORIGINAL = "original"
TYPE_TRANSLATION = "translation"

def reindex_solr(media_id: str):
    logger.info(f"Starting Reindex Task for {media_id}")

    try:
        s3 = get_s3_manager()
        solr = get_solr_manager()
        mongo = get_mongo_manager()
        parser = JsonTranscriptParser()

        # Detailed Subtitles (Small chunks for player)
        subtitles_original_key = f"{media_id}/transcripts/subtitles-original.json"
        subtitles_translation_key = f"{media_id}/transcripts/subtitles-translation.json"

        # 1. Reset Solr
        solr.delete_by_media_id(media_id)

        # 2. Helper Function
        def process_file(key, file_type):
            logger.info(f"Processing {key} -> ...")

            content = s3.get_file_content(key)
            if not content:
                logger.warning(f"Skipping {key} (not found)")
                return

            # A. Parse and Enrich
            subtitles = parser.enrich_subtitles(content)
            logger.info("Subtitles received for %s", file_type)

            # B. Save Raw Subtitles to Mongo
            mongo.save_subtitles(media_id, file_type, subtitles)
            segments = []

            # C. Extract Semantic Segments
            # MOVED UP: We need 'segments' for Solr indexing regardless of file_type

            if file_type == TYPE_ORIGINAL:
                # Save segments specifically for the Original (Source of Truth)
                segments = parser.extract_segments(subtitles)
                mongo.save_segments(media_id, file_type, segments)

                # Extract Speakers (usually only needed from original)
                unique_speakers = parser.extract_speakers(segments)
                mongo.save_speakers(media_id, unique_speakers)

            solr_docs = parser.parse(segments, media_id, file_type)

            payload = [doc.model_dump() for doc in solr_docs]
            if payload:
                solr.client.add(payload, commit=True)
                logger.info(f"Indexed {len(payload)} docs to Solr for {file_type}")

        # 3. Process Files
        process_file(subtitles_original_key, TYPE_ORIGINAL)
        process_file(subtitles_translation_key, TYPE_TRANSLATION)

        # 4. Finish Success
        mongo.update_processing_status(media_id, "indexing_completed")
        logger.info(f"Reindex task finished for {media_id}")

    except Exception as e:
        # 5. Handle Failure
        logger.exception(f"Reindex Task failed for {media_id}")

        # Ideally, get the mongo manager here again or rely on the outer scope if initialized
        try:
            mongo = get_mongo_manager()
            mongo.update_processing_status(media_id, "indexing_failed", error=str(e))
        except Exception:
            # If even MongoDB fails, just log it so we don't mask the original error
            logger.error("Could not update MongoDB status to failed.")
            
        # Re-raise the exception so the Task Queue (e.g. Celery/RQ) knows the job failed
        raise e
