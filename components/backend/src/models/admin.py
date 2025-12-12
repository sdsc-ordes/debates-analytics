from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class MediaListItem(BaseModel):
    media_id: str
    filename: str
    status: str
    created_at: Optional[datetime] = None
    title: Optional[str] = None


class MediaListResponse(BaseModel):
    items: List[MediaListItem]
    total: int


class DeleteMediaRequest(BaseModel):
    mediaId: str


class DeleteMediaResponse(BaseModel):
    status: str
    mediaId: str
    warnings: Optional[List[str]] = None
    errors: Optional[List[str]] = None
