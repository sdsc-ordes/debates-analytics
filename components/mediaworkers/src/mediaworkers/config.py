import os
import logging

# --- Configuration ---
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - [%(levelname)s] - (%(filename)s:%(lineno)d) - %(funcName)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

# Temporary Directory for file storage
TEMP_DIR = "/tmp"

# RabbitMQ Configuration
RABBITMQ_URL = os.getenv("RABBITMQ_URL")
# The queue this worker consumes from (Conversion Jobs)
CONVERSION_QUEUE = 'video_analysis_jobs'
# The queue this worker publishes to (Transcription Jobs)
TRANSCRIPTION_QUEUE = 'transcription_jobs'
MARKER_FILENAME = os.getenv("MARKER_FILENAME")

# S3 Configuration
S3_SERVER = os.getenv("S3_SERVER")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
WATCH_INTERVAL_SECONDS = 30
STATE_FILENAME = "status.json"
