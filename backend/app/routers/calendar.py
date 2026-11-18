from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from datetime import datetime, timezone
from bson import ObjectId

from backend.database import get_database
from backend.dependencies import get_current_user
from backend.schemas.calendar import (
    CalendarTaskCreate,
    CalendarTaskUpdate,
    CalendarTaskResponse,
    TaskStatus,
)

router = APIRouter(prefix="/api/calendar", tags=["Calendar & Kanban"])

def serialize_task(task: dict) -> dict:
    return {
        "id": str(task["_id"]),
        "user_email": task["user_email"],
        "title": task["title"],
        "description": task.get("description"),
        "platform": task["platform"],
        "scheduled_date": task["scheduled_date"],
        "content_type": task["content_type"],
        "status": task["status"],
        "created_at": task["created_at"],
        "updated_at": task["updated_at"],
    }

@router.post("", response_model=CalendarTaskResponse, status_code=status.HTTP_201_CREATED)
async def create_calendar_task(
    task_in: CalendarTaskCreate,
    current_user: dict = Depends(get_current_user)
):
    db = get_database()
    now = datetime.now(timezone.utc)
    
    task_doc = task_in.model_dump()
    task_doc["user_email"] = current_user["email"]
    task_doc["created_at"] = now
    task_doc["updated_at"] = now
    
    result = await db.calendar_tasks.insert_one(task_doc)
    task_doc["_id"] = result.inserted_id
    
    return serialize_task(task_doc)

@router.get("", response_model=List[CalendarTaskResponse])
async def get_calendar_tasks(
    status_filter: Optional[TaskStatus] = Query(default=None, alias="status"),
    current_user: dict = Depends(get_current_user)
):
    db = get_database()
    query = {"user_email": current_user["email"]}
    if status_filter:
        query["status"] = status_filter
        
    cursor = db.calendar_tasks.find(query).sort("scheduled_date", 1)
    tasks = []
    async for doc in cursor:
        tasks.append(serialize_task(doc))
        
    return tasks

@router.patch("/{id}", response_model=CalendarTaskResponse)
async def update_calendar_task(
    id: str,
    task_update: CalendarTaskUpdate,
    current_user: dict = Depends(get_current_user)
):
    if not ObjectId.is_valid(id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid task ID format"
        )
        
    db = get_database()
    existing_task = await db.calendar_tasks.find_one({"_id": ObjectId(id)})
    
    if not existing_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
        
    # Security: Ensure creator only modifies their own tasks
    if existing_task.get("user_email") != current_user["email"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this task"
        )
        
    update_data = {
        k: v for k, v in task_update.model_dump(exclude_unset=True).items()
        if v is not None
    }
    
    if update_data:
        update_data["updated_at"] = datetime.now(timezone.utc)
        await db.calendar_tasks.update_one(
            {"_id": ObjectId(id)},
            {"$set": update_data}
        )
        existing_task = await db.calendar_tasks.find_one({"_id": ObjectId(id)})
        
    return serialize_task(existing_task)
