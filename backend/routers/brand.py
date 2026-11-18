'''backend/routers/brand.py

FastAPI router for the Brand Assistant module. Implements CRUD endpoints for brand
campaigns and endpoints for generating/retrieving Gemini‑powered brand proposals.
''' 

from fastapi import APIRouter, Depends, HTTPException, status, Path
from typing import List
from datetime import datetime, timezone
from bson import ObjectId

# Standard imports
from backend.database import get_database
from backend.dependencies import get_current_user
from backend.schemas.brand import (
    CampaignCreate,
    CampaignUpdate,
    CampaignResponse,
    CampaignSummary,
    ProposalGenerationRequest,
    BrandProposal,
)
from backend.services.brand import generate_brand_proposal

router = APIRouter(prefix="/api/brand", tags=["Brand Assistant"])

# Helper to convert a raw MongoDB document into the public response model
def _serialize_campaign(doc: dict) -> dict:
    """Convert a campaign document to the shape expected by ``CampaignResponse``.

    The document stored in MongoDB contains ``_id`` and timestamps as ``datetime``
    objects; FastAPI will serialise them to ISO strings automatically.
    """
    return {
        "id": str(doc["_id"]),
        "user_email": doc["user_email"],
        "name": doc["name"],
        "description": doc.get("description"),
        "brand_info": doc["brand_info"],
        "product": doc["product"],
        "target_audience": doc["target_audience"],
        "objective": doc["objective"],
        "budget": doc["budget"],
        "platforms": doc["platforms"],
        "created_at": doc["created_at"],
        "updated_at": doc["updated_at"],
        "proposal": doc.get("proposal"),
    }

# ---------------------------------------------------------------------------
# POST /api/brand/ – create a campaign
# ---------------------------------------------------------------------------
@router.post("/", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    payload: CampaignCreate,
    current_user: dict = Depends(get_current_user),
):
    db = get_database()
    now = datetime.now(timezone.utc)
    doc: dict = payload.model_dump()
    doc.update({
        "user_email": current_user["email"],
        "created_at": now,
        "updated_at": now,
        # No proposal yet
    })
    result = await db.brand_campaigns.insert_one(doc)
    doc["_id"] = result.inserted_id
    return _serialize_campaign(doc)

# ---------------------------------------------------------------------------
# GET /api/brand/ – list user's campaigns (summary view)
# ---------------------------------------------------------------------------
@router.get("/", response_model=List[CampaignSummary])
async def list_campaigns(
    limit: int = 20,
    current_user: dict = Depends(get_current_user),
):
    db = get_database()
    cursor = (
        db.brand_campaigns.find({"user_email": current_user["email"]})
        .sort("created_at", -1)
        .limit(limit)
    )
    campaigns: List[dict] = []
    async for doc in cursor:
        campaigns.append(
            {
                "id": str(doc["_id"]),
                "name": doc["name"],
                "budget": doc["budget"],
                "platforms": doc["platforms"],
                "created_at": doc["created_at"],
                "has_proposal": "proposal" in doc and doc["proposal"] is not None,
            }
        )
    return campaigns

# ---------------------------------------------------------------------------
# GET /api/brand/{id} – retrieve full campaign
# ---------------------------------------------------------------------------
@router.get("/{id}", response_model=CampaignResponse)
async def get_campaign(
    id: str = Path(..., description="MongoDB ObjectId of the campaign"),
    current_user: dict = Depends(get_current_user),
):
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid campaign ID format")
    db = get_database()
    doc = await db.brand_campaigns.find_one({"_id": ObjectId(id), "user_email": current_user["email"]})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    return _serialize_campaign(doc)

# ---------------------------------------------------------------------------
# PATCH /api/brand/{id} – partial update
# ---------------------------------------------------------------------------
@router.patch("/{id}", response_model=CampaignResponse)
async def update_campaign(
    payload: CampaignUpdate,
    id: str = Path(..., description="MongoDB ObjectId of the campaign"),
    current_user: dict = Depends(get_current_user),
):
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid campaign ID format")
    update_data = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields provided for update")
    update_data["updated_at"] = datetime.now(timezone.utc)
    db = get_database()
    result = await db.brand_campaigns.update_one(
        {"_id": ObjectId(id), "user_email": current_user["email"]},
        {"$set": update_data},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    doc = await db.brand_campaigns.find_one({"_id": ObjectId(id)})
    return _serialize_campaign(doc)

# ---------------------------------------------------------------------------
# DELETE /api/brand/{id}
# ---------------------------------------------------------------------------
@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_campaign(
    id: str = Path(..., description="MongoDB ObjectId of the campaign"),
    current_user: dict = Depends(get_current_user),
):
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid campaign ID format")
    db = get_database()
    result = await db.brand_campaigns.delete_one({"_id": ObjectId(id), "user_email": current_user["email"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    return None

# ---------------------------------------------------------------------------
# POST /api/brand/{id}/generate-proposal – Gemini generation
# ---------------------------------------------------------------------------
@router.post("/{id}/generate-proposal", response_model=BrandProposal)
async def generate_proposal(
    request: ProposalGenerationRequest,
    id: str = Path(..., description="MongoDB ObjectId of the campaign"),
    current_user: dict = Depends(get_current_user),
):
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid campaign ID format")
    db = get_database()
    campaign = await db.brand_campaigns.find_one({"_id": ObjectId(id), "user_email": current_user["email"]})
    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    # Prepare data for the service – we only need the fields defined in CampaignBase.
    campaign_data = {
        "name": campaign["name"],
        "description": campaign.get("description"),
        "brand_info": campaign["brand_info"],
        "product": campaign["product"],
        "target_audience": campaign["target_audience"],
        "objective": campaign["objective"],
        "budget": campaign["budget"],
        "platforms": campaign["platforms"],
    }
    proposal_dict = await generate_brand_proposal(campaign_data, request.additional_guidance)
    # Persist the proposal.
    await db.brand_campaigns.update_one(
        {"_id": ObjectId(id)},
        {"$set": {"proposal": proposal_dict, "updated_at": datetime.now(timezone.utc)}},
    )
    return proposal_dict

# ---------------------------------------------------------------------------
# GET /api/brand/{id}/proposal – retrieve stored proposal
# ---------------------------------------------------------------------------
@router.get("/{id}/proposal", response_model=BrandProposal)
async def get_proposal(
    id: str = Path(..., description="MongoDB ObjectId of the campaign"),
    current_user: dict = Depends(get_current_user),
):
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid campaign ID format")
    db = get_database()
    doc = await db.brand_campaigns.find_one({"_id": ObjectId(id), "user_email": current_user["email"]})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    proposal = doc.get("proposal")
    if not proposal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proposal not generated yet")
    # Validate before returning – ensures stored data still conforms.
    validated = BrandProposal.model_validate(proposal)
    return validated.model_dump()
