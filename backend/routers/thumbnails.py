from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from datetime import datetime, timezone
from bson import ObjectId

from backend.database import get_database
from backend.dependencies import get_current_user
from backend.schemas.thumbnails import (
    ThumbnailCreate,
    ThumbnailUpdate,
    ThumbnailResponse,
    ThumbnailStatus,
)

router = APIRouter(prefix="/api/thumbnails", tags=["Thumbnail Lab"])

def serialize_thumbnail(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "user_email": doc["user_email"],
        "title": doc["title"],
        "concept_description": doc["concept_description"],
        "image_url": doc.get("image_url"),
        "target_platform": doc["target_platform"],
        "target_ctr": doc.get("target_ctr"),
        "impressions": doc.get("impressions", 0),
        "views": doc.get("views", 0),
        "ctr": doc.get("ctr"),
        "notes": doc.get("notes"),
        "status": doc["status"],
        "created_at": doc["created_at"],
        "updated_at": doc["updated_at"],
    }

@router.post("", response_model=ThumbnailResponse, status_code=status.HTTP_201_CREATED)
async def create_thumbnail(
    thumb_in: ThumbnailCreate,
    current_user: dict = Depends(get_current_user)
):
    db = get_database()
    now = datetime.now(timezone.utc)
    
    thumb_doc = thumb_in.model_dump()
    thumb_doc["user_email"] = current_user["email"]
    thumb_doc["impressions"] = 0
    thumb_doc["views"] = 0
    thumb_doc["ctr"] = None
    thumb_doc["notes"] = None
    thumb_doc["created_at"] = now
    thumb_doc["updated_at"] = now
    
    result = await db.thumbnails.insert_one(thumb_doc)
    thumb_doc["_id"] = result.inserted_id
    
    return serialize_thumbnail(thumb_doc)

@router.get("", response_model=List[ThumbnailResponse])
async def list_thumbnails(
    status_filter: Optional[ThumbnailStatus] = Query(default=None, alias="status"),
    platform_filter: Optional[str] = Query(default=None, alias="platform"),
    current_user: dict = Depends(get_current_user)
):
    db = get_database()
    query = {"user_email": current_user["email"]}
    if status_filter:
        query["status"] = status_filter
    if platform_filter:
        query["target_platform"] = platform_filter
        
    cursor = db.thumbnails.find(query).sort("created_at", -1)
    thumbnails = []
    async for doc in cursor:
        thumbnails.append(serialize_thumbnail(doc))
        
    return thumbnails

@router.get("/{id}", response_model=ThumbnailResponse)
async def get_thumbnail(
    id: str,
    current_user: dict = Depends(get_current_user)
):
    if not ObjectId.is_valid(id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid thumbnail ID format"
        )
        
    db = get_database()
    doc = await db.thumbnails.find_one({"_id": ObjectId(id)})
    
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thumbnail not found"
        )
        
    if doc.get("user_email") != current_user["email"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this thumbnail"
        )
        
    return serialize_thumbnail(doc)

@router.patch("/{id}", response_model=ThumbnailResponse)
async def update_thumbnail(
    id: str,
    thumb_update: ThumbnailUpdate,
    current_user: dict = Depends(get_current_user)
):
    if not ObjectId.is_valid(id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid thumbnail ID format"
        )
        
    db = get_database()
    existing = await db.thumbnails.find_one({"_id": ObjectId(id)})
    
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thumbnail not found"
        )
        
    if existing.get("user_email") != current_user["email"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this thumbnail"
        )
        
    update_data = thumb_update.model_dump(exclude_unset=True)
    
    if update_data:
        # Validate that views do not exceed impressions
        curr_impressions = update_data.get("impressions", existing.get("impressions", 0))
        curr_views = update_data.get("views", existing.get("views", 0))
        if curr_views > curr_impressions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="views cannot exceed impressions"
            )

        # CTR Handling Rule:
        # If manual CTR is explicitly passed in update, preserve it.
        # Otherwise, if impressions or views are updated, calculate CTR safely (capped at 100.0).
        if "ctr" not in update_data and ("impressions" in update_data or "views" in update_data):
            if curr_impressions > 0:
                calc_ctr = round((curr_views / curr_impressions) * 100, 2)
                update_data["ctr"] = min(calc_ctr, 100.0)
            else:
                update_data["ctr"] = 0.0
                
        update_data["updated_at"] = datetime.now(timezone.utc)
        await db.thumbnails.update_one(
            {"_id": ObjectId(id), "user_email": current_user["email"]},
            {"$set": update_data}
        )
        existing = await db.thumbnails.find_one({"_id": ObjectId(id), "user_email": current_user["email"]})
        
    return serialize_thumbnail(existing)

@router.delete("/{id}")
async def delete_thumbnail(
    id: str,
    current_user: dict = Depends(get_current_user)
):
    if not ObjectId.is_valid(id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid thumbnail ID format"
        )
        
    db = get_database()
    existing = await db.thumbnails.find_one({"_id": ObjectId(id)})
    
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thumbnail not found"
        )
        
    if existing.get("user_email") != current_user["email"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this thumbnail"
        )
        
    await db.thumbnails.delete_one({"_id": ObjectId(id), "user_email": current_user["email"]})
    return {"message": "Thumbnail deleted successfully", "id": id}
