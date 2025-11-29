from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # App Config
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "info"

    # S3 Config (No default value = Required)
    s3_access_key: str
    s3_secret_key: str
    s3_server: str
    s3_bucket_name: str
    s3_frontend_base_url: str

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
    task_convert: str = "converter.process_video"

    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings():
    return Settings()
