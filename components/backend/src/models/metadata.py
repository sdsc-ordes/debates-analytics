from pydantic import BaseModel
from typing import List, Optional, Dict
from .base import Speaker, Subtitle, EnumSubtitleType
from datetime import datetime
from .documents import SpeakersDocument, SegmentsDocument, SubtitlesDocument


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


class UpdateSpeakersRequest(BaseModel):
    media_id: str
    speakers: List[Speaker]


class UpdateSubtitlesRequest(BaseModel):
    media_id: str
    segmentNr: int
    subtitles: List[Subtitle]
    subtitleType: EnumSubtitleType


class MetadataResponse(BaseModel):
    debate: DebateDocument
    speakers: Optional[SpeakersDocument] = None
    segments: Optional[SegmentsDocument] = None
    subtitles: Optional[SubtitlesDocument] = None
    subtitles_en: Optional[SubtitlesDocument] = None
