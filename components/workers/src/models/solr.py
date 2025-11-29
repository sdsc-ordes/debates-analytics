from pydantic import BaseModel, Field, computed_field
from typing import List, Optional
from datetime import datetime


class SolrSegmentDocument(BaseModel):
    """
    The exact shape Solr expects.
    We use the DebateSegment logic to populate this.
    """
    id: str
    media_id: str
    segment_nr: int
    speaker_id: str
    statement: str
    statement_type: str
    start: float
    end: float
    filename: str

    # Manual fields (can be populated later via update)
    debate_name: Optional[str] = None
    debate_date: Optional[datetime] = None
