import subprocess
import logging
import os
from rq import get_current_job
from services.s3 import get_s3_manager
from services.queue import get_queue_manager
from services.filesystem import temp_workspace
from services.mongo import get_mongo_manager
from services.reporter import JobReporter

logger = logging.getLogger(__name__)

def process_video(s3_key: str, media_id: str):
    """
    Orchestrates video conversion pipeline (S3 -> FFmpeg -> S3).
    """
    # Setup Services inside the task (Thread-safe)
    s3 = get_s3_manager()
    rq = get_queue_manager()
    mongo = get_mongo_manager()
    job = get_current_job()
    reporter = JobReporter(media_id, mongo, logger, job)

    logger.info(f"media_id={media_id} - Task 'process_video' started.")

    try:
        # Context manager handles folder cleanup automatically
        with temp_workspace() as work_dir:
            local_video = os.path.join(work_dir, "source.mp4")
            local_wav = os.path.join(work_dir, "audio.wav")
            s3_wav_key = f"{media_id}/audio.wav"

            logger.info(f"media_id={media_id} - Downloading from S3: {s3_key}")
            s3.download_file(s3_key, local_video)

            convert_to_wav(local_video, local_wav, media_id)

            logger.info(f"media_id={media_id} - Uploading WAV to S3: {s3_wav_key}")
            s3.upload_file(local_wav, s3_wav_key)
            reporter.report_status_change("conversion completed", {"s3_wav_key": s3_wav_key})

            rq.enqueue_audio_processing(
                media_id=media_id,
                s3_key=s3_wav_key,
            )
            logger.info(f"media_id={media_id} - queued for transcribing: {s3_wav_key}")
            reporter.report_status_change("queued_for_transcribing")

            return {"status": "success", "wav_key": s3_wav_key}

    except Exception as e:
        reporter.mark_failed(e)
        raise e


def convert_to_wav(input_path: str, output_path: str, media_id: str):
    """
    Wraps FFmpeg logic.
    Converts input to 16kHz Mono WAV (ideal for Whisper).
    """
    # Safety Check
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"FFmpeg input file missing: {input_path}")

    cmd = [
        "ffmpeg",
        "-i", input_path,       # Input
        "-vn",                  # No Video
        "-acodec", "pcm_s16le", # Codec: PCM 16-bit
        "-ar", "16000",         # Rate: 16kHz
        "-ac", "1",             # Channels: Mono
        "-y",                   # Overwrite output
        "-nostdin",             # Disable interaction (Important for background jobs)
        "-hide_banner",         # Reduce log noise
        "-loglevel", "error",   # Only log errors
        output_path
    ]

    logger.info(f"media_id={media_id} - Running FFmpeg conversion...")

    try:
        subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
    except subprocess.CalledProcessError as e:
        error_msg = f"FFmpeg failed with exit code {e.returncode}. Stderr: {e.stderr}"
        logger.error(f"media_id={media_id} - {error_msg}")
        raise RuntimeError(error_msg)
