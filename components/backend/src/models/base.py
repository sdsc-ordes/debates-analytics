from pydantic import BaseModel
from enum import Enum

class EnumSubtitleType(str, Enum):
    transcript = "Transcript"
    translation = "Translation"

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
