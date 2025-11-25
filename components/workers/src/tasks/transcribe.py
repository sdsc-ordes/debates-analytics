import logging
import os
from gradio_client import Client, handle_file

logger = logging.getLogger(__name__)

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
