"""API routes for outreach campaigns."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models import OutreachCampaign, OutreachEmail, Lead
from ..services.outreach_sequence import OutreachSequenceService, FollowUpSequence
from ..services.email_drafting import EmailDraftingService
from . import schemas

router = APIRouter(prefix="/api/campaigns", tags=["campaigns"])


@router.post("/", response_model=schemas.OutreachCampaignResponse)
async def create_campaign(
    campaign: schemas.OutreachCampaignCreate,
    db: Session = Depends(get_db),
):
    """Create a new outreach campaign."""
    sequence = FollowUpSequence(
        campaign.follow_up_delays or FollowUpSequence.default_sequence().delays
    )
    db_campaign = OutreachSequenceService.create_campaign(
        name=campaign.name,
        description=campaign.description,
        follow_up_sequence=sequence,
        db=db,
    )
    return {
        "id": db_campaign.id,
        "name": db_campaign.name,
        "status": db_campaign.status,
        "email_count": 0,
        "created_at": db_campaign.created_at,
    }


@router.get("/{campaign_id}", response_model=schemas.OutreachCampaignResponse)
async def get_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
):
    """Get campaign by ID."""
    campaign = db.query(OutreachCampaign).filter(
        OutreachCampaign.id == campaign_id
    ).first()
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found",
        )
    return {
        "id": campaign.id,
        "name": campaign.name,
        "status": campaign.status,
        "email_count": len(campaign.emails),
        "created_at": campaign.created_at,
    }


@router.post("/{campaign_id}/add-lead/{lead_id}")
async def add_lead_to_campaign(
    campaign_id: int,
    lead_id: int,
    db: Session = Depends(get_db),
):
    """Add a lead to a campaign with generated email."""
    campaign = db.query(OutreachCampaign).filter(
        OutreachCampaign.id == campaign_id
    ).first()
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found",
        )

    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found",
        )

    # Draft email
    email_data = EmailDraftingService.draft_email(lead)

    # Add to campaign
    outreach_email = OutreachSequenceService.add_lead_to_campaign(
        campaign_id,
        lead_id,
        email_data,
        db,
    )

    return {
        "email_id": outreach_email.id,
        "lead_id": lead_id,
        "subject": outreach_email.subject,
        "added_at": outreach_email.generated_at,
    }


@router.post("/{campaign_id}/schedule")
async def schedule_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
):
    """Schedule campaign for sending."""
    result = OutreachSequenceService.schedule_sends(campaign_id, db)
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result["error"],
        )
    return result


@router.post("/{campaign_id}/pause")
async def pause_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
):
    """Pause a campaign."""
    campaign = OutreachSequenceService.pause_campaign(campaign_id, db)
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found",
        )
    return {
        "id": campaign.id,
        "status": campaign.status,
    }


@router.post("/{campaign_id}/resume")
async def resume_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
):
    """Resume a paused campaign."""
    campaign = OutreachSequenceService.resume_campaign(campaign_id, db)
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found",
        )
    return {
        "id": campaign.id,
        "status": campaign.status,
    }
