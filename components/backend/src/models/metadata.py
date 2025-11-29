from pydantic import BaseModel, Field
from typing import List, Optional
from .base import Speaker, Subtitle, EnumSubtitleType
from .documents import DebateDocument, SpeakersDocument, SegmentsDocument, SubtitlesDocument


class MongoMetadataRequest(BaseModel):
    media_id: str = Field(..., description="media_id", examples=["df2afc83-7e69-4868-ba4c-b7c4afed6218"])


class UpdateSpeakersRequest(BaseModel):
    media_id: str
    speakers: List[Speaker]


class UpdateSubtitlesRequest(BaseModel):
    media_id: str
    segmentNr: int
    subtitles: List[Subtitle]
    subtitleType: EnumSubtitleType


class MongoMetadataResponse(BaseModel):
    debate: Optional[DebateDocument] = None
    speakers: Optional[SpeakersDocument] = None
    segments: Optional[SegmentsDocument] = None
    subtitles: Optional[SubtitlesDocument] = None
    subtitles_en: Optional[SubtitlesDocument] = None
