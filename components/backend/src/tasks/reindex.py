import logging
from services.s3 import get_s3_manager
from services.solr import get_solr_manager
from services.mongo import get_mongo_manager
from services.parser import JsonTranscriptParser
from config.settings import get_settings

logger = logging.getLogger(__name__)


def reindex_solr(media_id: str):
    logger.info(f"Starting Reindex Task for {media_id}")

    try:
        s3 = get_s3_manager()
        solr = get_solr_manager()
        mongo = get_mongo_manager()
        parser = JsonTranscriptParser()
        settings = get_settings()

        subtitles_original_key = f"{media_id}/transcripts/subtitles-original.json"
        subtitles_translation_key = f"{media_id}/transcripts/subtitles-translation.json"

        # 1. Reset Solr
        solr.delete_by_media_id(media_id)

        # 2. Helper to Process Each File Type
        def process_transcript_type(key, subtitle_type, is_original):
            logger.info(f"Processing {key}...")

            content = s3.get_file_content(key)
            if not content:
                logger.warning(f"Skipping {key} (not found)")
                return

            # A. Parse Raw -> Enriched Subtitles
            raw_subtitles = parser.enrich_subtitles(content)

            # B. Group into Segments (The new robust structure)
            segments = parser.extract_segments(raw_subtitles)
            logger.info(segments)
            logger.info(f"Extracted {len(segments)} segments for {subtitle_type}")

            # C. Save to MongoDB (Segment by Segment)
            # This loop replaces the old "save_subtitles" monolithic call
            for seg in segments:
                mongo.save_segments(
                    media_id=media_id,
                    segment_nr=seg["segment_nr"],
                    speaker_id=seg["speaker_id"],
                    start=seg["start"],
                    end=seg["end"],
                    subtitle_type=subtitle_type,
                    subtitles=seg["subtitles"],
                )

                # Special Case: If this is the ORIGINAL transcript, ensure
                # the segment metadata (Start/End/Speaker) is also set correctly.
                # (You might add a specific 'save_segment_metadata' method
                # or just let 'save_subtitles' handle the upsert logic as we discussed)

            # D. Extract Speakers (Only needed once, usually from original)
            if is_original:
                 unique_speakers = parser.extract_speakers(segments)
                 # Note: use update_speakers, not save_speakers (to avoid overwriting names)
                 # But for a reindex (fresh start), save_speakers might be okay
                 # if you want to reset everything.
                 mongo.save_speakers(media_id, unique_speakers)

            # E. Index to Solr
            solr_docs = parser.parse(segments, media_id, subtitle_type)
            payload = [doc.model_dump() for doc in solr_docs]

            if payload:
                solr.client.add(payload, commit=True)
                logger.info(f"Indexed {len(payload)} docs to Solr for {subtitle_type}")

        # 3. Run Process
        process_transcript_type(subtitles_original_key, settings.type_original, is_original=True)
        process_transcript_type(subtitles_translation_key, settings.type_translation, is_original=False)

        # 4. Finish
        mongo.update_processing_status(media_id, "indexing_completed")
        logger.info(f"Reindex task finished for {media_id}")

    except Exception as e:
        logger.exception(f"Reindex Task failed for {media_id}")
        try:
            mongo = get_mongo_manager()
            mongo.update_processing_status(media_id, "indexing_failed", error=str(e))
        except Exception:
            pass
        raise e