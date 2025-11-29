from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional, Dict
from enum import Enum


class S3MediaItem(BaseModel):
    name: str
    type: str
    description: str


class S3MediaPlayer(BaseModel):
    key: str
    type: str
    format: str


class Speaker(BaseModel):
    speaker_id: str
    name: str
    role_tag: str


class Subtitle(BaseModel):
    index: int
    start: float
    end: float
    content: str
    speaker_id: str
    segment_nr: int


class Segment(BaseModel):
    segment_nr: int
    speaker_id: str
    start: float
    end: float


class SpeakersDocument(BaseModel):
    speakers: List[Speaker]


class SegmentsDocument(BaseModel):
    segments: List[Segment]


class SubtitlesDocument(BaseModel):
    subtitles: List[Subtitle]


class EnumSubtitleType(str, Enum):
    transcript = "Transcript"
    translation = "Translation"


class S3Key(BaseModel):
    name: str
    type: str
    description: str


class Media(BaseModel):
    key: str
    type: str
    format: str


class DebateDocument(BaseModel):
    s3_prefix: str
    created_at: datetime
    s3_keys: List[S3Key]
    media: Media
    schedule: datetime
    public: bool
    type: str
    session: str


class MongoMetadataRequest(BaseModel):
    media_id: str = Field(..., description="media_id", examples=["df2afc83-7e69-4868-ba4c-b7c4afed6218"])


class MongoMetadataResponse(BaseModel):
    debate: Optional[DebateDocument] = None
    speakers: Optional[SpeakersDocument] = None
    segments: Optional[SegmentsDocument] = None
    subtitles: Optional[SubtitlesDocument] = None
    subtitles_en: Optional[SubtitlesDocument] = None


class UpdateSpeakersRequest(BaseModel):
    media_id: str
    speakers: List[Speaker]


class UpdateSubtitlesRequest(BaseModel):
    media_id: str
    segmentNr: int
    subtitles: List[Subtitle]
    subtitleType: EnumSubtitleType
