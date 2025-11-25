import subprocess
import logging

logger = logging.getLogger(__name__)

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
