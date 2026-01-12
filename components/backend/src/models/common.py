

class SpeakerAttributes(BaseModel):
    speaker_name: Optional[str] = None
    speaker_role_tag: Optional[str] = None
    speaker_country: Optional[str] = None
    debate_agenda_item: Optional[str] = None


class DebateAttributes(BaseModel):
    debate_type: Optional[str] = None
    debate_date: Optional[str] = None
    debate_link_agenda: Optional[str] = None
    debate_link_mediasource: Optional[str] = None
    debate_session_timeslot: Optional[Timeslot] = None
