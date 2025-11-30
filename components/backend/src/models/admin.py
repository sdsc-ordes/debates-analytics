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


class ProcessingStatusResponse(BaseModel):
    media_id: str
    status: str
    job_id: Optional[str]

    # Real-time info from Redis
    job_state: Optional[str]
    progress: Optional[str]
    error: Optional[str]

    # Timestamps
    created_at: datetime
    updated_at: datetime
