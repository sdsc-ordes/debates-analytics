from pydantic import BaseModel, Field
from datetime import datetime
from typing import List
from enum import Enum


class S3MediaUrls(BaseModel):
    url: str = Field(..., description="Url")
    label: str = Field(..., description="Label for Url")


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


class FacetFilter(BaseModel):
    facetField: str = Field(..., description="Solr facet field name", examples=["statement_type"])
    facetValue: str = Field(..., description="Solr facet field value", examples=["translation"])


class S3Key(BaseModel):
    name: str
    type: str
    description: str

class Media(BaseModel):
    key: str
    type: str
    format: str

class DebateDocument(BaseModel):
    job_id: str
    media: str
