from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from datetime import datetime, timezone
from bson import ObjectId

from backend.database import get_database
from backend.dependencies import get_current_user
from backend.schemas.dashboard import DashboardSummary, RecentActivityItem

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard Summary"])

# Helper to normalize datetime values (ensure naive UTC for comparison)
def _normalize_dt(value: any) -> datetime:
    if isinstance(value, datetime):
        # Convert aware datetime to UTC naive
        if value.tzinfo is not None:
            return value.astimezone(timezone.utc).replace(tzinfo=None)
        return value
    # Fallback for missing or malformed timestamps
    return datetime.min

@router.get("/summary", response_model=DashboardSummary)
async def get_dashboard_summary(current_user: dict = Depends(get_current_user)):
    db = get_database()
    email = current_user["email"]

    # Calendar metrics
    total_tasks = await db.calendar_tasks.count_documents({"user_email": email})
    published = await db.calendar_tasks.count_documents({"user_email": email, "status": "published"})
    pending = total_tasks - published

    # Other collection counts
    total_thumbnails = await db.thumbnails.count_documents({"user_email": email})
    total_audience = await db.audience_analyses.count_documents({"user_email": email})
    total_brand = await db.brand_campaigns.count_documents({"user_email": email})

    recent_items: List[RecentActivityItem] = []

    async def _add_recent(collection, module_name: str):
        cursor = collection.find({"user_email": email}).sort("created_at", -1).limit(5)
        async for doc in cursor:
            created_raw = doc.get("created_at")
            created_norm = _normalize_dt(created_raw)
            recent_items.append(
                RecentActivityItem(
                    module=module_name,
                    id=str(doc["_id"]),
                    created_at=created_norm,
                )
            )

    # Gather recent activity from each module
    await _add_recent(db.calendar_tasks, "calendar")
    await _add_recent(db.thumbnails, "thumbnails")
    await _add_recent(db.audience_analyses, "audience")
    await _add_recent(db.brand_campaigns, "brand")

    # Sort combined recent items by created_at descending and keep top 5
    recent_items.sort(key=lambda x: x.created_at, reverse=True)
    recent_items = recent_items[:5]

    summary = DashboardSummary(
        total_scheduled_content=pending,
        published_content=published,
        pending_content=pending,
        draft_content=pending,  # alias for backward compatibility
        total_thumbnail_briefs=total_thumbnails,
        total_audience_analyses=total_audience,
        total_brand_campaigns=total_brand,
        recent_activity=recent_items,
    )
    return summary
