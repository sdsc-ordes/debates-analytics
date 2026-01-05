from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime
from enum import Enum


class MediaType(str, Enum):
    video = "video"
    audio = "audio"


class SubtitleType(str, Enum):
    transcript = "original"
    translation = "translation"


class Speaker(BaseModel):
    speaker_id: str
    name: Optional[str] = ""
    role_tag: Optional[str] = ""


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
    session: Optional[str] = None
    debate_type: Optional[str] = None
    schedule: Optional[str] = None
    name: Optional[str] = None


class MetadataResponse(BaseModel):
    debate: DebateDocument
    speakers: List[Speaker] = []
    segments: List[Segment] = []


class UpdateSpeakersRequest(BaseModel):
    media_id: str
    speakers: List[Speaker]


class UpdateSubtitlesRequest(BaseModel):
    media_id: str
    segment_nr: int
    subtitles: List[Subtitle]
    subtitle_type: SubtitleType


class UpdateMetadataResponse(BaseModel):
    status: str
    media_id: str


class UpdateDebateRequest(BaseModel):
    media_id: str
    session: Optional[str] = None
    debate_type: Optional[str] = None
    schedule: Optional[str] = None
