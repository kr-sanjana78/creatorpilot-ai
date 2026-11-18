from pydantic import BaseModel, Field, validator
from typing import Optional, List, Literal, Dict
from datetime import datetime

# ---------- Campaign schemas ----------

class BrandInfo(BaseModel):
    name: str = Field(..., description="Brand name")
    values: Optional[str] = Field(None, description="Core brand values or tagline")

class CampaignBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="Campaign name")
    description: Optional[str] = Field(None, description="Long description of the campaign")
    brand_info: BrandInfo = Field(..., description="Information about the brand")
    product: str = Field(..., description="Product or service being promoted")
    target_audience: str = Field(..., description="Target audience description")
    objective: str = Field(..., description="Primary campaign objective")
    budget: float = Field(..., gt=0, description="Budget in USD")
    platforms: List[str] = Field(..., description="Platforms to run the campaign on")

class CampaignCreate(CampaignBase):
    pass

class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    brand_info: Optional[BrandInfo] = None
    product: Optional[str] = None
    target_audience: Optional[str] = None
    objective: Optional[str] = None
    budget: Optional[float] = None
    platforms: Optional[List[str]] = None

class CampaignSummary(BaseModel):
    id: str
    name: str
    budget: float
    platforms: List[str]
    created_at: datetime
    has_proposal: bool

# ---------- Brand proposal schema ----------

class BrandProposal(BaseModel):
    generated_at: datetime = Field(..., description="When Gemini generated the proposal")
    overview: str
    target_audience: str
    campaign_objectives: str
    content_strategy: str
    suggested_content_ideas: List[str]
    platform_recommendations: List[str]
    suggested_posting_schedule: str
    budget_allocation: str
    expected_outcomes: str

class CampaignResponse(CampaignBase):
    id: str
    user_email: str
    created_at: datetime
    updated_at: datetime
    proposal: Optional[BrandProposal] = None

# ---------- Request model for proposal generation ----------

class ProposalGenerationRequest(BaseModel):
    additional_guidance: Optional[str] = Field(None, description="Extra instructions for Gemini")
