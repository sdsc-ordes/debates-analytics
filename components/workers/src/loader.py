import logging
from app.config import get_settings
from common.s3 import get_s3_manager
from common.solr import get_solr_manager
from common.queue import get_queue_manager
from .parser import SrtParser

logger = logging.getLogger(__name__)

def load_transcripts(media_id: str, s3_key: str):
    """
    RQ Task: Downloads SRT, Parses it, Pushes to Solr.
    """
    s3 = get_s3_manager()
    queue = get_queue_manager()
    db = get_mongo_manager()
    job = get_current_job()
    parser = SrtParser()

    try:
        logger.info(f"Starting processing for {media_id}")

        srt_key = f"{media_id}/transcripts/transcript.srt"

        logger.info(f"Downloading SRT: {srt_key}")
        srt_content = s3.download_as_string(srt_key)

        if not srt_content:
            raise ValueError("SRT file empty or not found")

        # 2. Parse and Map
        logger.info("Parsing SRT...")
        solr_documents = parser.parse(srt_content, media_id, subtitle_type="transcript")

        # 3. Convert Pydantic to Dicts for Solr
        solr_payload = [doc.model_dump() for doc in solr_documents]

        # 4. Upload to Solr
        logger.info(f"Indexing {len(solr_payload)} segments to Solr")
        solr.client.add(solr_payload, commit=True) # Assuming SolrManager exposes client or has add method

        logger.info(f"Successfully processed {media_id}")
        return True

    except Exception as e:
        logger.exception(f"Failed to process transcript for {media_id}")
        # RQ will catch this and mark job as failed
        raise e
