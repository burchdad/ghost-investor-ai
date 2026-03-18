"""API routes for activity logging."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models import Activity, Lead
from ..services.activity_logging import ActivityLoggingService
from . import schemas

router = APIRouter(prefix="/api/activities", tags=["activities"])


@router.post("/", response_model=schemas.ActivityResponse)
async def log_activity(
    activity: schemas.ActivityLogRequest,
    db: Session = Depends(get_db),
):
    """Log a new activity."""
    lead = db.query(Lead).filter(Lead.id == activity.lead_id).first()
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found",
        )

    logged_activity = ActivityLoggingService.log_manual_activity(
        lead_id=activity.lead_id,
        activity_type=activity.activity_type,
        description=activity.description,
        db=db,
    )
    return logged_activity


@router.get("/lead/{lead_id}")
async def get_lead_timeline(
    lead_id: int,
    db: Session = Depends(get_db),
):
    """Get activity timeline for a lead."""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found",
        )

    timeline = ActivityLoggingService.get_lead_timeline(lead_id, db)
    return {"lead_id": lead_id, "activities": timeline}


@router.post("/{activity_id}/sync-crm")
async def sync_activity_to_crm(
    activity_id: int,
    crm_id: str,
    db: Session = Depends(get_db),
):
    """Mark activity as synced to CRM."""
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity not found",
        )

    synced_activity = ActivityLoggingService.sync_to_crm(activity_id, crm_id, db)
    return {
        "activity_id": activity_id,
        "synced": True,
        "crm_id": crm_id,
    }
