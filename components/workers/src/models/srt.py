from pydantic import BaseModel, Field, computed_field
from typing import List, Optional
from datetime import datetime


class SubtitleItem(BaseModel):
    index: int
    start: float
    end: float
    content: str


class DebateSegment(BaseModel):
    """
    Represents a chunk of speech by one speaker.
    One segment = Multiple SRT subtitles merged together.
    """
    segment_nr: int
    speaker_id: str
    media_id: str
    language: str = "en" # Default, or extracted from filename
    subtitles: List[SubtitleItem]

    @computed_field
    def text_content(self) -> str:
        """Joins all subtitle lines into one text block for search"""
        return " ".join([s.content for s in self.subtitles]).strip()

    @computed_field
    def start_time(self) -> float:
        """Start time of the first subtitle in segment"""
        return self.subtitles[0].start if self.subtitles else 0.0

    @computed_field
    def end_time(self) -> float:
        """End time of the last subtitle in segment"""
        return self.subtitles[-1].end if self.subtitles else 0.0
