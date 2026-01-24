import logging
import os
from gradio_client import Client, handle_file
from rq import get_current_job
from services.s3 import get_s3_manager
from services.queue import get_queue_manager
from services.filesystem import temp_workspace
from services.mongo import get_mongo_manager
from services.reporter import JobReporter
from config.settings import get_settings

logger = logging.getLogger(__name__)

def process_transcription(s3_key, media_id):
    """
    1.Downloads audio
    2.Runs Whisper (Transcribe + Translate)
    3.Uploads artifacts
    4.Queues for indexing
    """
    try:
        logger.info(f"media_id={media_id} - Task 'process_transcription' started.")
        s3 = get_s3_manager()
        mongo = get_mongo_manager()
        job = get_current_job()
        rq = get_queue_manager()
        reporter = JobReporter(media_id, mongo, logger, job)
        settings = get_settings()

        logger.info(f"media_id={media_id} - Status change on mongodb: transcribing_started.")
        reporter.report_status_change("transcribing_started")

        hf_model = settings.hf_model
        hf_token = settings.hf_token
        hf_space_url = settings.hf_space_url
        whisper_service = WhisperService(hf_space_url=hf_space_url, hf_token=hf_token, hf_model=hf_model)
        logger.info(f"WhisperService initialized with model={hf_model} at {hf_space_url}")

        with temp_workspace() as work_dir:

            # 1.Downloads audio
            local_input_path = os.path.join(work_dir, "input.wav")
            logger.info(f"media_id={media_id} - Downloading from S3: {s3_key}")
            s3.download_file(s3_key, local_input_path)
            logger.info(f"media_id={media_id} - Download completed.")

            # 2. Runs Whisper (Transcribe + Translate)
            transcription_files = whisper_service.run_inference(
                local_input_path, task="transcribe"
            )
            logger.info(f"media_id={media_id} - Transcribing completed: {s3_key}")
            reporter.report_status_change("transcribing_original_completed")

            translation_files = whisper_service.run_inference(
                local_input_path, task="translate"
            )
            logger.info(f"media_id={media_id} - Translating completed: {s3_key}")
            reporter.report_status_change("transcribing_translation_completed")

            # 3. Uploads artifacts
            s3_base_path = f"{media_id}/transcripts"
            uploaded_keys = {}
            def process_uploads(file_set, type_suffix):
                """
                Iterates over the Whisper output dict and uploads files.
                type_suffix: 'original' or 'translation'
                """
                # Map internal keys (from whisper service) to S3 filenames
                file_map = {
                    'srt': f"subtitles-{type_suffix}.srt",
                    'json': f"subtitles-{type_suffix}.json",
                    'segments_json': f"segments-{type_suffix}.json",
                    'segments_pdf': f"segments-{type_suffix}.pdf",
                    'segments_md': f"segments-{type_suffix}.md"
                }

                for key_name, s3_filename in file_map.items():
                    local_path = file_set.get(key_name)
                    if local_path and os.path.exists(local_path):
                        s3_dest = f"{s3_base_path}/{s3_filename}"
                        s3.upload_file(local_path, s3_dest)
                        uploaded_keys[s3_filename] = s3_dest

            process_uploads(transcription_files, "original")
            process_uploads(translation_files, "translation")
            logger.info(f"media_id={media_id} - Uploaded {len(uploaded_keys)} transcript files.")

            # 4. Queues for indexing
            rq.enqueue_reindex(media_id=media_id,)
            logger.info(f"media_id={media_id} - queued for reindexing.")
            reporter.report_status_change("queued_for_reindexing")

            return {"status": "success", "uploaded_keys": uploaded_keys}

    except Exception as e:
        reporter.mark_failed(e)
        raise e


class WhisperService:
    def __init__(self, hf_space_url, hf_token, hf_model):
        self.hf_space_url = hf_space_url
        self.hf_token = hf_token
        self.hf_model = hf_model

        try:
            self.client = Client(self.hf_space_url)
            logger.info(f"Connected to HF Space at {self.hf_space_url}")
        except Exception as e:
            logger.error(f"Error connecting to HF Space: {e}")
            raise ConnectionError(f"Failed to connect to HF Space ({self.hf_space_url}). Error: {e}") from e

    def run_inference(self, file_path, task="transcribe", media_id="SYSTEM"):
        """
        Runs inference on HF Space.
        Added 'media_id' for traceable logging.
        """
        lang = "en" if task == "translate" else "auto"

        logger.info(f"media_id={media_id} - Running Whisper Inference. Task={task}, Language={lang} Model={self.hf_model}")

        try:
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

            logger.info(f"media_id={media_id} - Whisper {task} completed successfully.")

            return {
                "srt": result_tuple[3],
                "json": result_tuple[4],
                "segments_json": result_tuple[5],
                "segments_md": result_tuple[6],
                "segments_pdf": result_tuple[7]
            }
        except Exception as e:
            logger.error(f"media_id={media_id} - Whisper Inference Failed for task '{task}': {e}")
            raise RuntimeError(f"Whisper Service Failed: {e}")
