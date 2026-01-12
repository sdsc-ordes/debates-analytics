import logging
from services.s3 import get_s3_manager
from services.solr import get_solr_manager
from services.mongo import get_mongo_manager
from services.parser import JsonTranscriptParser
from config.settings import get_settings
from services.reporter import JobReporter
from services.queue import get_queue_manager
from rq import get_current_job

logger = logging.getLogger(__name__)


def reindex_solr(media_id: str):
    """
    1.Reset Solr
    2.Parse transcript files from S3
    3.Index to Solr
    4.Update MongoDB
    """
    try:
        s3 = get_s3_manager()
        solr = get_solr_manager()
        mongo = get_mongo_manager()
        parser = JsonTranscriptParser()
        rq = get_queue_manager()
        settings = get_settings()

        job = get_current_job()
        if job:
            task_type = "indexing"
        else:
            task_type = "reindexing"

        # Start reporter without job as this step can be called outside of RQ
        reporter = JobReporter(media_id, mongo, logger, job)
        logger.info(f"Starting {task_type} task for {media_id}")

        subtitles_original_key = f"{media_id}/transcripts/subtitles-original.json"
        subtitles_translation_key = f"{media_id}/transcripts/subtitles-translation.json"

        # 1.Reset Solr
        solr.delete_by_media_id(media_id)

        # Helper to Process Each File Type
        def process_transcript_type(key, subtitle_type, is_original):
            logger.info(f"Processing {key}...")

            content = s3.get_file_content(key)
            if not content:
                logger.warning(f"Skipping {key} (not found)")
                return

            # Parse Raw -> Enriched Subtitles
            raw_subtitles = parser.enrich_subtitles(content)

            # Group into Segments (The new robust structure)
            segments = parser.extract_segments(raw_subtitles)
            logger.info(segments)
            logger.info(f"Extracted {len(segments)} segments for {subtitle_type}")

            # Save to MongoDB (Segment by Segment)
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

            # Extract Speakers
            if is_original:
                 unique_speakers = parser.extract_speakers(segments)
                 mongo.save_speakers(media_id, unique_speakers)

            # Index to Solr
            solr_docs = parser.parse(segments, media_id, subtitle_type)
            payload = [doc.model_dump() for doc in solr_docs]

            if payload:
                solr.client.add(payload, commit=True)
                logger.info(f"Indexed {len(payload)} docs to Solr for {subtitle_type}")

        # 2.Parse transcript files and update mongo/solr
        process_transcript_type(subtitles_original_key, settings.type_original, is_original=True)
        process_transcript_type(subtitles_translation_key, settings.type_translation, is_original=False)

        # 3.Finish reporting status
        reporter.report_status_change(f"{task_type}_completed")
        logger.info(f"{task_type} task finished for {media_id}")

    except Exception as e:
        logger.exception(f"CRITICAL: {task_type} failed for {media_id}")
        reporter.report_failed(e)
        raise e
