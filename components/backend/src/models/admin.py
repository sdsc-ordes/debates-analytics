from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class ProcessingStep(BaseModel):
    step: str
    timestamp: datetime


class MediaListItem(BaseModel):
    media_id: str
    filename: str
    status: str
    error_message: Optional[str] = None
    processing_history: Optional[List[ProcessingStep]] = None
    created_at: Optional[datetime] = None
    title: Optional[str] = None


# ---------------------------------
# routes/admin.py
# ---------------------------------

# list media response model

class MediaListResponse(BaseModel):
    items: List[MediaListItem]
    total: int

# list media request/response model

class DeleteMediaRequest(BaseModel):
    mediaId: str


class DeleteMediaResponse(BaseModel):
    status: str
    mediaId: str
    warnings: Optional[List[str]] = None
    errors: Optional[List[str]] = None


# delete media request/response model

class ReindexMediaRequest(BaseModel):
    mediaId: str


class ReindexMediaResponse(BaseModel):
    status: str
    mediaId: str
    warnings: Optional[List[str]] = None
    errors: Optional[List[str]] = None
