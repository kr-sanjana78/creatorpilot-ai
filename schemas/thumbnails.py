import re
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, Literal
from datetime import datetime

ThumbnailStatus = Literal["draft", "in_progress", "ready", "published", "archived"]

IMAGE_URL_REGEX = re.compile(
    r"^(https?://[^\s]+|data:image/(?:png|jpeg|jpg|webp|gif|svg\+xml);base64,[A-Za-z0-9+/=]+)$",
    re.IGNORECASE
)

def _validate_image_url(v: Optional[str]) -> Optional[str]:
    if v is None:
        return None
    v_clean = v.strip()
    if not v_clean:
        return None
    if not IMAGE_URL_REGEX.match(v_clean):
        raise ValueError(
            "image_url must be a valid HTTP/HTTPS URL or supported image data URI (png, jpeg, webp, gif, svg)"
        )
    return v_clean

class ThumbnailCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="Title of the thumbnail or associated content")
    concept_description: str = Field(..., min_length=1, description="Description of the thumbnail visual concept and idea")
    image_url: Optional[str] = Field(default=None, description="Optional URL of the preview, draft, or hosted thumbnail image")
    target_platform: str = Field(..., min_length=1, max_length=50, description="Target platform (e.g., YouTube, TikTok, Instagram)")
    target_ctr: Optional[float] = Field(default=None, ge=0.0, le=100.0, description="Target CTR percentage goal (e.g. 8.5 for 8.5%)")
    status: ThumbnailStatus = Field(default="draft", description="Current status of the thumbnail brief")

    @field_validator("image_url")
    @classmethod
    def check_image_url(cls, v: Optional[str]) -> Optional[str]:
        return _validate_image_url(v)

class ThumbnailUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    concept_description: Optional[str] = Field(default=None, min_length=1)
    image_url: Optional[str] = Field(default=None, description="URL of the preview or final thumbnail image")
    target_platform: Optional[str] = Field(default=None, min_length=1, max_length=50)
    target_ctr: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    impressions: Optional[int] = Field(default=None, ge=0, description="Manual impressions count")
    views: Optional[int] = Field(default=None, ge=0, description="Manual views / clicks count")
    ctr: Optional[float] = Field(default=None, ge=0.0, le=100.0, description="Manual CTR percentage")
    notes: Optional[str] = Field(default=None, description="Feedback, design notes, or performance observations")
    status: Optional[ThumbnailStatus] = None

    @field_validator("image_url")
    @classmethod
    def check_image_url(cls, v: Optional[str]) -> Optional[str]:
        return _validate_image_url(v)

    @model_validator(mode="after")
    def validate_views_and_impressions(self):
        if self.impressions is not None and self.views is not None:
            if self.views > self.impressions:
                raise ValueError("views cannot exceed impressions")
        return self

class ThumbnailResponse(BaseModel):
    id: str
    user_email: str
    title: str
    concept_description: str
    image_url: Optional[str] = None
    target_platform: str
    target_ctr: Optional[float] = None
    impressions: int = 0
    views: int = 0
    ctr: Optional[float] = None
    notes: Optional[str] = None
    status: ThumbnailStatus
    created_at: datetime
    updated_at: datetime
