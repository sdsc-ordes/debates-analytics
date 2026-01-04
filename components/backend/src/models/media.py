from pydantic import BaseModel, Field
from typing import List


class S3MediaUrls(BaseModel):
    url: str = Field(..., description="Url")
    label: str = Field(..., description="Label for Url")


class S3MediaUrlRequest(BaseModel):
    media_id: str = Field(..., description="media_id", examples=["df2afc83-7e69-4868-ba4c-b7c4afed6218"])


class S3MediaUrlResponse(BaseModel):
    signedUrls: List[S3MediaUrls] = Field(..., description="List of presigned URLs")
    signedVideoUrl: str = Field(..., description="Presigned URL for the video file")
    signedAudioUrl: str = Field(..., description="Presigned URL for the audio file")
