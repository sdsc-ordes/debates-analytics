from pydantic import BaseModel, Field, computed_field
from typing import List, Optional
from datetime import datetime


class FacetFilter(BaseModel):
    facetField: str = Field(..., description="Solr facet field name", examples=["statement_type"])
    facetValue: str = Field(..., description="Solr facet field value", examples=["translation"])


class SolrRequest(BaseModel):
    queryTerm: str = Field(..., description="Solr query term can be empty", examples=["honor"])
    sortBy: str = Field(..., description="Solr sort option", examples=["start asc"])
    facetFields: List[str] = Field(
        ..., description="Solr facet field to return",
        examples = [["debate_schedule", "statement_type"]]
    )
    facetFilters: List[FacetFilter]  = Field(
        ..., description="Solr facet filters with set values"
    )


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
