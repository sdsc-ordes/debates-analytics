import os
import json
import logging
from datetime import datetime
from gradio_client import Client
from rq import get_current_job

# --- Import Shared Libraries ---
from lib.s3 import get_s3_manager
from lib.filesystem import temp_workspace
from lib.mongo import get_mongo_manager
from lib.hf import WhisperService

logger = logging.getLogger(__name__)

def process_transcription(s3_key, media_id):
    job = get_current_job()
    job_id = job.get_id()

    if job:
        job.meta['progress'] = 'transcribing'
        job.save_meta()

    logger.info(f"Job {media_id}: Starting processing for {s3_key}")

    db = get_mongo_manager()
    s3 = get_s3_manager()
    whisper_service = WhisperService()

    try:
        db.update_status(media_id, "processing")

        with temp_workspace() as job_temp_dir:
            local_input_path = os.path.join(job_temp_dir, "input.wav")

            logger.info(f"Downloading {s3_key}...")
            s3.download_file(s3_key, local_input_path)

            # --- PASS 1: TRANSCRIPTION ---
            transcription_files = whisper_service.run_inference(
                local_input_path, task="transcribe"
            )

            # --- PASS 2: TRANSLATION ---
            translation_files = whisper_service.run_inference(
                local_input_path, task="translate"
            )

            # --- Map Artifacts for Upload ---
            logger.info("Uploading artifacts to S3...")
            s3_base_path = f"{media_id}/transcripts"
            uploaded_files = {}

            # Helper to upload and record
            def upload_artifact(file_path, s3_suffix):
                if file_path and os.path.exists(file_path):
                    key = f"{s3_base_path}/{s3_suffix}"
                    s3.upload_file(file_path, key)
                    uploaded_files[s3_suffix] = key

            # Upload Transcription Set
            upload_artifact(transcription_files['srt'], "subtitles-original.srt")
            upload_artifact(transcription_files['json'], "subtitles-original.json")
            upload_artifact(transcription_files['segments_json'], "segments-original.json")

            # Upload Translation Set
            upload_artifact(translation_files['srt'], "subtitles-translation.srt")
            upload_artifact(translation_files['json'], "subtitles-translation.json")
            upload_artifact(translation_files['segments_json'], "segments-translation.json")

            db.update_status(
                media_id,
                status="transcribing_completed",
                metadata={"transcript_s3_keys": uploaded_files}
            )

            logger.info(f"Job {job_id}: Complete.")
            return {"status": "completed"}

    except Exception as e:
        logger.error(f"Job {job_id} Failed: {e}")
        try:
            db.update_status(
                media_id,
                status="error in transcribing",
                metadata={"errorMessage": str(e)}
            )
        except Exception:
            pass
        raise e
