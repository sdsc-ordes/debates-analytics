import logging
import os
from gradio_client import Client, handle_file
from rq import get_current_job
from services.s3 import get_s3_manager
from services.queue import get_queue_manager
from services.filesystem import temp_workspace
from services.mongo import get_mongo_manager
from services.reporter import JobReporter

logger = logging.getLogger(__name__)

def process_transcription(s3_key, media_id):
    """
    1. Downloads audio
    2. Runs Whisper (Transcribe + Translate)
    3. Uploads artifacts
    4. Updates DB
    """
    s3 = get_s3_manager()
    mongo = get_mongo_manager()
    whisper_service = WhisperService()
    job = get_current_job()
    rq = get_queue_manager()

    reporter = JobReporter(media_id, mongo, job, logger)

    reporter.update("transcribing_started", progress="starting")

    try:
        with temp_workspace() as work_dir:
            local_input_path = os.path.join(work_dir, "input.wav")

            reporter.update("transcribing_downloading", progress="downloading")
            s3.download_file(s3_key, local_input_path)

            reporter.update("transcribing_processing", progress="transcribing")

            transcription_files = whisper_service.run_inference(
                local_input_path, task="transcribe"
            )
            reporter.update("transcribing_translating", progress="translating")

            translation_files = whisper_service.run_inference(
                local_input_path, task="translate"
            )

            reporter.update("transcribing_uploading", progress="uploading")

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

            reporter.update(
                "transcribing_completed",
                progress="completed",
                metadata={"transcript_s3_keys": uploaded_keys}
            )

            rq.enqueue(
                settings.task_reindex,
                media_id=media_id,
            )

            return {"status": "completed"}

    except Exception as e:
        reporter.mark_failed(e)
        # Re-raise for RQ
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
