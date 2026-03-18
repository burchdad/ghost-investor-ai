"""API schemas for request/response validation."""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class LeadCreate(BaseModel):
    """Schema for creating a new lead."""
    email: EmailStr
    first_name: str
    last_name: str
    company_name: str
    job_title: str
    linkedin_url: Optional[str] = None
    phone: Optional[str] = None


class LeadEnrich(BaseModel):
    """Schema for enrichment request."""
    lead_id: int
    force_refresh: Optional[bool] = False


class LeadResponse(BaseModel):
    """Schema for lead response."""
    id: int
    email: str
    first_name: str
    last_name: str
    company_name: str
    job_title: str
    contact_score: float
    company_score: float
    is_enriched: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ContactScoreResponse(BaseModel):
    """Schema for contact score details."""
    lead_id: int
    title_score: float
    company_score: float
    activity_score: float
    engagement_score: float
    total_score: float
    score_reason: str


class EmailDraftRequest(BaseModel):
    """Schema for email drafting request."""
    lead_id: int
    tone: Optional[str] = "professional"  # professional, casual, friendly


class EmailDraftResponse(BaseModel):
    """Schema for email draft response."""
    subject: str
    body: str
    personalization_factors: Dict[str, Any]


class OutreachEmailCreate(BaseModel):
    """Schema for creating outreach email."""
    lead_id: int
    subject: str
    body: str
    personalization_factors: Optional[Dict[str, Any]] = None


class OutreachCampaignCreate(BaseModel):
    """Schema for creating outreach campaign."""
    name: str
    description: str
    follow_up_delays: Optional[List[int]] = None  # in hours


class OutreachCampaignResponse(BaseModel):
    """Schema for campaign response."""
    id: int
    name: str
    status: str
    email_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class ActivityLogRequest(BaseModel):
    """Schema for logging activity."""
    lead_id: int
    activity_type: str
    description: str


class ActivityResponse(BaseModel):
    """Schema for activity response."""
    id: int
    lead_id: int
    activity_type: str
    description: str
    event_timestamp: Optional[datetime]
    synced_to_crm: bool

    class Config:
        from_attributes = True


class CSVImportRequest(BaseModel):
    """Schema for CSV import."""
    csv_content: str


class CSVImportResponse(BaseModel):
    """Schema for CSV import response."""
    imported: int
    skipped: int
    errors: List[str]
    total_processed: int


class InvestorProfileResponse(BaseModel):
    """Schema for investor profile."""
    id: int
    lead_id: int
    investment_stage: str
    investment_sectors: List[str]
    key_interests: List[str]
    communication_preference: str

    class Config:
        from_attributes = True
