from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime

TaskStatus = Literal["planned", "in_progress", "ready", "published"]

class CalendarTaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="Title of the content or task")
    description: Optional[str] = Field(default=None, description="Detailed description or notes")
    platform: str = Field(..., min_length=1, max_length=50, description="Target platform (e.g., YouTube, TikTok, Instagram)")
    scheduled_date: datetime = Field(..., description="Scheduled release or deadline date/time")
    content_type: str = Field(..., min_length=1, max_length=50, description="Type of content (e.g., Video, Short, Reel, Post)")
    status: TaskStatus = Field(default="planned", description="Current workflow status")

class CalendarTaskUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = None
    platform: Optional[str] = Field(default=None, min_length=1, max_length=50)
    scheduled_date: Optional[datetime] = None
    content_type: Optional[str] = Field(default=None, min_length=1, max_length=50)
    status: Optional[TaskStatus] = None

class CalendarTaskResponse(BaseModel):
    id: str
    user_email: str
    title: str
    description: Optional[str] = None
    platform: str
    scheduled_date: datetime
    content_type: str
    status: TaskStatus
    created_at: datetime
    updated_at: datetime
