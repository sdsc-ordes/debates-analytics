from pydantic_settings import BaseSettings
from typing import List
from functools import lru_cache

class Settings(BaseSettings):
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "info"

    # S3 Config
    s3_access_key: str
    s3_secret_key: str
    s3_server: str
    s3_bucket_name: str
    s3_public_url: str
    s3_signing_url: str

    # Mongo Config
    mongo_url: str
    mongo_db_name: str
    mongo_media_collection: str
    mongo_subtitle_collection: str
    mongo_speaker_collection: str
    mongo_segment_collection: str

    # Solr Config
    solr_url: str

    # Redis
    redis_url: str
    redis_queue_name: str = "default"
    task_convert: str = "tasks.convert.process_video"
    task_transcribe: str = "tasks.transcribe.process_transcription"
    task_reindex: str = "tasks.reindex.reindex_solr"
    hf_model: str = "large-v3"
    hf_token: str
    hf_space_url: str = "https://katospiegel-odtp-pyannote-whisper.hf.space/"

    type_translation: str
    type_original: str

    # CORS
    cors_origins: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings():
    return Settings()
