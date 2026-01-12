from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime
from enum import Enum
from models.domain import DebateAttributes, SpeakerAttributes


class S3MediaUrls(BaseModel):
    url: str = Field(..., description="Url")
    label: str = Field(..., description="Label for Url")


class MediaType(str, Enum):
    video = "video"
    audio = "audio"


class SubtitleType(str, Enum):
    transcript = "original"
    translation = "translation"


class Subtitle(BaseModel):
    start: float
    end: float
    text: str


class Segment(BaseModel):
    segment_nr: int
    start: float
    end: float
    speaker_id: Optional[str] = "UNKNOWN"
    subtitles_original: List[Subtitle] = []
    subtitles_translation: List[Subtitle] = []


class DebateDocument(BaseModel):
    media_id: str
    s3_key: str
    original_filename: str
    media_type: MediaType
    status: str
    created_at: datetime
    job_id: Optional[str] = None
    s3_audio_key: Optional[str] = None
    transcript_s3_keys: Dict[str, str] = {}
    updated_at: Optional[datetime] = None
    error_message: Optional[str] = None
    file_name: Optional[str] = None
    debate_attributes: DebateAttributes = Field(default_factory=DebateAttributes)

    def to_mongo(self):
        return self.model_dump()


class Speaker(BaseModel):
    speaker_id: str
    speaker_attributes: SpeakerAttributes = Field(default_factory=SpeakerAttributes)

# ---------------------------------
# routes/metadata.py
# ---------------------------------

# S3 media URL request/response models

class S3MediaUrlRequest(BaseModel):
    media_id: str = Field(..., description="media_id", examples=["df2afc83-7e69-4868-ba4c-b7c4afed6218"])


class S3MediaUrlResponse(BaseModel):
    signedUrls: List[S3MediaUrls] = Field(..., description="List of presigned URLs")
    signedMediaUrl: str = Field(None, description="Presigned URL for video or audio file")


# metadata response model

class MetadataResponse(BaseModel):
    debate: DebateDocument
    speakers: List[Speaker] = []
    segments: List[Segment] = []


# speakers and subtitles and debate update request models

class UpdateSpeakersRequest(BaseModel):
    media_id: str
    speakers: List[Speaker]


class UpdateSubtitlesRequest(BaseModel):
    media_id: str
    segment_nr: int
    subtitles: List[Subtitle]
    subtitle_type: SubtitleType


class UpdateDebateRequest(BaseModel):
    media_id: str
    session: Optional[str] = None
    debate_type: Optional[str] = None
    schedule: Optional[str] = None


# general metadata update response models

class UpdateMetadataResponse(BaseModel):
    status: str
    media_id: str
