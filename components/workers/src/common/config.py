from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # S3 Config (No default value = Required)
    s3_access_key: str
    s3_secret_key: str
    s3_server: str
    s3_bucket_name: str

    # HF output
    hf_srt_original
    hf_srt_translation
    hf_subtitles_original_json
    hf_subtitles_translation_json
    hf_segments_original_json
    hf_segments_translation_json
    hf_segments_original_pdf
    hf_segments_translation_pdf
    hf_segments_original_md
    hf_segments_translation_md

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
    task_transcribe: str = "transcriber.process_transcription"
    task_load: str = "loader.load_transcripts"

    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings():
    return Settings()
