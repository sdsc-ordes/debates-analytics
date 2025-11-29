import subprocess
import logging
import os
from rq import get_current_job

# Imports
from services.s3 import get_s3_manager
from services.queue import get_queue_manager
from services.filesystem import temp_workspace
from services.mongo import get_mongo_manager
from config.settings import get_settings
from services.reporter import JobReporter

logger = logging.getLogger(__name__)

def process_video(s3_key, media_id):
    """
    Orchestrates video conversion pipeline.
    """
    s3 = get_s3_manager()
    rq = get_queue_manager()
    mongo = get_mongo_manager()
    settings = get_settings()
    job = get_current_job()

    reporter = JobReporter(media_id, mongo, job, logger)

    reporter.update("converting_started", progress="starting")

    try:
        # Context manager handles folder cleanup automatically
        with temp_workspace() as work_dir:

            local_video = os.path.join(work_dir, "source.mp4")
            local_wav = os.path.join(work_dir, "audio.wav")
            s3_wav_key = f"{media_id}/audio.wav"

            reporter.update("converting_downloading", progress="downloading")
            s3.download_file(s3_key, local_video)

            reporter.update("converting_processing", progress="converting")
            convert_to_wav(local_video, local_wav)

            reporter.update("converting_uploading", progress="uploading")
            s3.upload_file(local_wav, s3_wav_key)

            reporter.update("converting_completed", progress="completed")
            reporter.update(
                "converting_completed",
                progress="completed",
                metadata={"s3_audio_key": s3_wav_key}
            )

            logger.info(f"Job {media_id}: Enqueuing transcription...")

            rq.enqueue(
                settings.task_transcribe, # Use settings!
                media_id=media_id,
                s3_key=s3_wav_key,
                job_timeout=-1
            )

            return {"status": "completed", "wav_key": s3_wav_key}

    except Exception as e:
        reporter.mark_failed(e)
        raise e


def convert_to_wav(input_path: str, output_path: str):
    """
    Wraps FFmpeg logic.
    Converts input to 16kHz Mono WAV (ideal for Whisper).
    """
    cmd = [
        "ffmpeg", "-i", input_path,
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "16000",
        "-ac", "1",
        "-y",
        output_path
    ]

    logger.info(f"Running FFmpeg: {' '.join(cmd)}")

    # Run silently unless it fails
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg failed: {result.stderr}")
