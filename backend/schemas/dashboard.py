"""backend/schemas/dashboard.py

Response model for the Dashboard Summary endpoint.
"""

from datetime import datetime
from typing import List

from pydantic import BaseModel, Field


class RecentActivityItem(BaseModel):
    """One recent record from any module."""
    module: str = Field(..., description="Module name: calendar, thumbnails, audience, or brand.")
    id: str = Field(..., description="MongoDB ObjectId as a string.")
    created_at: datetime = Field(..., description="When the record was created.")


class DashboardSummary(BaseModel):
    """Aggregated dashboard data for a single user."""
    total_scheduled_content: int = Field(
        0,
        description="Number of calendar tasks that are NOT published (pending count).",
    )
    published_content: int = Field(
        0,
        description="Calendar tasks whose status is 'published'.",
    )
    pending_content: int = Field(
        0,
        description="All non‑published calendar tasks (same as total_scheduled_content).",
    )
    # `draft_content` is an alias for `pending_content`, kept for backward compatibility.
    draft_content: int = Field(
        0,
        description="Alias for pending_content (same value).",
    )
    total_thumbnail_briefs: int = Field(0, description="Number of thumbnail briefs.")
    total_audience_analyses: int = Field(0, description="Number of audience analyses.")
    total_brand_campaigns: int = Field(0, description="Number of brand campaigns.")
    recent_activity: List[RecentActivityItem] = Field(
        default_factory=list,
        description="Latest five records across all modules, sorted by created_at descending.",
    )
