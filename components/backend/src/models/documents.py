from pydantic import BaseModel
from typing import List
from datetime import datetime
from .base import Speaker, Segment, Subtitle


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


class SpeakersDocument(BaseModel):
    speakers: List[Speaker]


class SegmentsDocument(BaseModel):
    segments: List[Segment]


class SubtitlesDocument(BaseModel):
    subtitles: List[Subtitle]
