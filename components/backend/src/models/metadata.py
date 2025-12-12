from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime
from enum import Enum


class EnumSubtitleType(str, Enum):
    transcript = "Transcript"
    translation = "Translation"


class Speaker(BaseModel):
    speaker_id: str
    name: str
    role_tag: str


class Subtitle(BaseModel):
    start: float
    end: float
    text: str
    speaker_id: str
    language: str
    segment_nr: int


class Segment(BaseModel):
    start: float
    end: float
    subtitles: List[str]
    speaker_id: str
    language: str
    segment_nr: int


class DebateDocument(BaseModel):
    media_id: str
    s3_key: str
    original_filename: str
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    error_message: Optional[str] = None
    job_id: Optional[str] = None
    s3_audio_key: Optional[str] = None
    transcript_s3_keys: Dict[str, str] = {}


class MetadataResponse(BaseModel):
    debate: DebateDocument
    speakers: Optional[List[Speaker]] = []
    segments: Optional[List[Segment]] = []
    segments_en: Optional[List[Segment]] = []
    subtitles: Optional[List[Subtitle]] = []
    subtitles_en: Optional[List[Subtitle]] = []


class UpdateSpeakersRequest(BaseModel):
    media_id: str
    speakers: List[Speaker]


class UpdateSubtitlesRequest(BaseModel):
    media_id: str
    segment_nr: int
    subtitles: List[Subtitle]
    subtitle_type: EnumSubtitleType


class UpdateMetadataResponse(BaseModel):
    status: str
    media_id: str
