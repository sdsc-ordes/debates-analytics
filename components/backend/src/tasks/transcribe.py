import logging
import os
from gradio_client import Client, handle_file
import os
import logging
from rq import get_current_job
from services.s3 import get_s3_manager
from services.filesystem import temp_workspace
from services.mongo import get_mongo_manager

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


class WhisperService:
    def __init__(self):
        self.space_url = os.getenv("HF_SPACE_URL")
        self.hf_token = os.getenv("HF_TOKEN")
        self.hf_model = os.getenv("HF_MODEL")
        self.client = Client(self.space_url)

    def run_inference(self, file_path, task="transcribe"):
        lang = "en" if task == "translate" else "auto"
        logger.info(f"Running Whisper: Task={task}, Language={lang}")

        # Usage is exactly the same
        result_tuple = self.client.predict(
            audio_file=handle_file(file_path),
            youtube_link="",
            model=self.hf_model,
            task=task,
            language=lang,
            quantize=False,
            api_name="/process_audio",
            hf_token=self.hf_token,
        )

        return {
            "srt": result_tuple[3],
            "json": result_tuple[4],
            "segments_json": result_tuple[5],
            "segments_md": result_tuple[6],
            "segments_pdf": result_tuple[7]
        }
