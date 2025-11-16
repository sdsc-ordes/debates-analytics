import subprocess
import logging
from typing import NoReturn

def convert_to_wav(local_video_path: str, local_wav_path: str) -> NoReturn:
    """
    Converts the local video file to 16kHz mono WAV using ffmpeg.
    Raises subprocess.CalledProcessError if conversion fails.
    """
    logging.info(f"Starting FFmpeg conversion of {local_video_path} to WAV...")

    # FFmpeg command to extract 16kHz mono audio (PCM S16LE)
    command = [
        "ffmpeg", "-i", local_video_path,
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "16000",
        "-ac", "1",
        "-y", local_wav_path
    ]

    try:
        subprocess.run(
            command,
            check=True, # Will raise CalledProcessError on non-zero exit code
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        logging.info("FFmpeg conversion successful.")
    except subprocess.CalledProcessError as e:
        logging.error(f"FFmpeg conversion failed: {e}")
        raise
