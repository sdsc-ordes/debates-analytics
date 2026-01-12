from pydantic import BaseModel, Field

from typing import List, Optional
from pydantic import BaseModel
from models.domain import DebateAttributes, SpeakerAttributes
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum

# ---------------------------------
# models for the search query
# ---------------------------------

class FacetFilter(BaseModel):
    facetField: str = Field(..., description="Solr facet field name", examples=["statement_type"])
    facetValue: str = Field(..., description="Solr facet field value", examples=["translation"])


class SearchQuery(BaseModel):
    queryTerm: str = Field(..., description="Solr query term can be empty", examples=["honor"])
    sortBy: str = Field(..., description="Solr sort option", examples=["start asc"])
    facetFields: List[str] = Field(
        ..., description="Solr facet field to return",
        examples = [["debate_schedule", "statement_type"]]
    )
    facetFilters: List[FacetFilter]  = Field(
        ..., description="Solr facet filters with set values"
    )
    start: int = Field(0, description="Pagination start index", examples=[0])
    rows: int = Field(10, description="Number of rows to return", examples=[10])

# ---------------------------------
# models for the search response
# ---------------------------------

class StatementType(str, Enum):
    original = "original"
    translation = "translation"


class FacetValue(BaseModel):
    label: str
    count: int


class FacetField(BaseModel):
    field_name: str
    values: List[FacetValue]


class HighlightedDoc(BaseModel):
    statement: Optional[List[str]] = None


class SearchDocument(BaseModel):
    id: str
    media_id: str
    segment_nr: int
    speaker_id: str
    statement: List[str]
    statement_type: StatementType
    statement_language: Optional[str]= None
    start: float
    end: float
    debate_schedule: Optional[datetime]= None
    debate_type: Optional[str]= None
    debate_session: Optional[str]= None
    speaker_attributes: Optional[SpeakerAttributes]= None
    debate_attributes: Optional[DebateAttributes]= None



class SearchDocument(BaseModel):
    # --- Core Solr Fields ---
    id: str
    media_id: str
    statement: List[str]
    start: float
    end: float
    
    # --- Embedded Domain Models ---
    # We keep them nested in Python for cleanliness
    speaker: Optional[SpeakerAttributes] = None
    debate: Optional[DebateAttributes] = None

    def to_solr(self) -> dict:
        """
        Flattens the object.
        1. Dumps core fields normally.
        2. Dumps speaker/debate fields using their ALIASES (speaker_name, etc).
        """
        # 1. Dump core fields (excluding the nested objects)
        payload = self.model_dump(exclude={'speaker', 'debate'}, exclude_none=True)

        # 2. Flatten Speaker: Use by_alias=True to get 'speaker_name' instead of 'name'
        if self.speaker:
            payload.update(self.speaker.model_dump(by_alias=True, exclude_none=True))

        # 3. Flatten Debate: Use by_alias=True to get 'debate_date' instead of 'date'
        if self.debate:
            payload.update(self.debate.model_dump(by_alias=True, exclude_none=True))

        return payload

# ---------------------------------
# routes/search.py
# ---------------------------------

# search response model

class SearchResponse(BaseModel):
    docs: List[SearchDocument]
    total: int
    facets: List[FacetField] = []
    highlighting: Dict[str, HighlightedDoc] = {}
