from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum


class FacetFilter(BaseModel):
    facetField: str = Field(..., description="Solr facet field name", examples=["statement_type"])
    facetValue: str = Field(..., description="Solr facet field value", examples=["translation"])


class SearchQuery(BaseModel):
    queryTerm: str = Field(..., description="Solr query term can be empty", examples=["honor"])
    sortBy: str = Field(..., description="Solr sort option", examples=["start asc"])
    facetFields: List[str] = Field(
        ..., description="Solr facet field to return",
        examples = [["debate_date", "statement_type"]]
    )
    facetFilters: List[FacetFilter]  = Field(
        ..., description="Solr facet filters with set values"
    )
    start: int = Field(0, description="Pagination start index", examples=[0])
    rows: int = Field(10, description="Number of rows to return", examples=[10])


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
    start: float
    end: float
    debate_date: Optional[datetime]= None
    debate_type: Optional[str]= None
    debate_session: Optional[str]= None
    statement_language: Optional[str]= None


# ---------------------------------
# routes/search.py
# ---------------------------------

# search response model

class SearchResponse(BaseModel):
    docs: List[SearchDocument]
    total: int
    facets: List[FacetField] = []
    highlighting: Dict[str, HighlightedDoc] = {}
