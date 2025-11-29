from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime
from .base import Speaker, Subtitle, EnumSubtitleType
from .documents import DebateDocument, SpeakersDocument, SegmentsDocument, SubtitlesDocument

# Requests
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

# 1. The Dashboard List Item (Lightweight)
class MediaListItem(BaseModel):
    media_id: str
    filename: str
    status: str
    created_at: datetime
    title: Optional[str] = None

class MediaListResponse(BaseModel):
    items: List[MediaListItem]
    total: int

# 2. The Detailed Progress Response
class ProcessingStatusResponse(BaseModel):
    media_id: str
    status: str             # From MongoDB (e.g., 'transcribing')
    job_id: Optional[str]   # The Redis Job ID

    # Real-time info from Redis
    job_state: Optional[str] # queued, started, failed, finished
    progress: Optional[str]  # 'downloading', 'transcribing', 'uploading'
    error: Optional[str]     # If failed, why?

    # Timestamps
    created_at: datetime
    updated_at: datetime
