from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum

# --- Enums (Shared) ---
class MediaType(str, Enum):
    video = "video"
    audio = "audio"

class Timeslot(str, Enum):
    morning = "am"
    afternoon = "pm"


class MediaType(str, Enum):
    video = "video"
    audio = "audio"


class SubtitleType(str, Enum):
    transcript = "original"
    translation = "translation"


# --- Central Attribute Definitions ---

class SpeakerAttributes(BaseModel):
    name: Optional[str]     = Field(None, alias="speaker_name")
    role_tag: Optional[str] = Field(None, alias="speaker_role_tag")
    country: Optional[str]  = Field(None, alias="speaker_country")

    class Config:
        populate_by_name = True
        extra = "ignore" # Important: ignores 'speaker_id' when parsing

class DebateAttributes(BaseModel):
    debate_type: Optional[str]      = Field(None, alias="debate_type")
    date: Optional[str]      = Field(None, alias="debate_date")
    agenda: Optional[str]    = Field(None, alias="debate_link_agenda")
    source: Optional[str]    = Field(None, alias="debate_link_mediasource")
    session_timeslot: Optional[str]  = Field(None, alias="debate_session_timeslot")

    class Config:
        populate_by_name = True
