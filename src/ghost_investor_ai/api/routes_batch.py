"""API routes for batch operations."""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..auth import get_current_user
from ..models import User, OutreachEmail, OutreachCampaign
from ..services.batch_jobs import (
    batch_enrich_leads,
    batch_generate_emails,
    batch_send_emails,
)

router = APIRouter(prefix="/api/batch", tags=["batch"])


@router.post("/enrich-leads")
async def submit_batch_enrich(
    lead_ids: List[int],
    enrichment_source: str = "apollo",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Submit batch enrichment job."""
    if not lead_ids:
        raise HTTPException(status_code=400, detail="lead_ids cannot be empty")
    
    # Submit Celery task
    task = batch_enrich_leads.delay(lead_ids, enrichment_source)
    
    return {
        "job_id": task.id,
        "status": "submitted",
        "lead_count": len(lead_ids),
        "enrichment_source": enrichment_source,
    }


@router.post("/generate-emails")
async def submit_batch_generate_emails(
    outreach_email_ids: List[int],
    email_type: str = "first_touch",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Submit batch email generation job."""
    if not outreach_email_ids:
        raise HTTPException(status_code=400, detail="outreach_email_ids cannot be empty")
    
    if email_type not in ["first_touch", "follow_up", "reengagement"]:
        raise HTTPException(status_code=400, detail="Invalid email_type")
    
    # Submit Celery task
    task = batch_generate_emails.delay(outreach_email_ids, email_type)
    
    return {
        "job_id": task.id,
        "status": "submitted",
        "email_count": len(outreach_email_ids),
        "email_type": email_type,
    }


@router.post("/send-emails")
async def submit_batch_send_emails(
    sent_email_ids: List[int],
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Submit batch email sending job."""
    if not sent_email_ids:
        raise HTTPException(status_code=400, detail="sent_email_ids cannot be empty")
    
    # Verify account belongs to user
    # (This would check EmailAccount.user_id)
    
    # Submit Celery task
    task = batch_send_emails.delay(sent_email_ids, account_id)
    
    return {
        "job_id": task.id,
        "status": "submitted",
        "email_count": len(sent_email_ids),
        "account_id": account_id,
    }


@router.post("/launch-campaign")
async def launch_campaign(
    campaign_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Launch an outreach campaign (batch send all prepared emails)."""
    campaign = (
        db.query(OutreachCampaign)
        .filter(
            OutreachCampaign.id == campaign_id,
            OutreachCampaign.user_id == current_user.id,
        )
        .first()
    )
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    if campaign.status != "draft":
        raise HTTPException(status_code=400, detail="Campaign must be in draft status")
    
    # Get all unsent emails for this campaign
    emails_to_send = (
        db.query(OutreachEmail)
        .filter(
            OutreachEmail.campaign_id == campaign_id,
            OutreachEmail.sent_at.is_(None),
        )
        .all()
    )
    
    if not emails_to_send:
        raise HTTPException(status_code=400, detail="No emails to send")
    
    # Submit batch send job
    sent_email_ids = [email.id for email in emails_to_send]
    task = batch_send_emails.delay(sent_email_ids, campaign.email_account_id)
    
    # Update campaign status
    campaign.status = "launching"
    campaign.batch_job_id = task.id
    db.commit()
    
    return {
        "campaign_id": campaign_id,
        "job_id": task.id,
        "status": "launching",
        "email_count": len(emails_to_send),
    }


@router.get("/job-status/{job_id}")
async def get_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user),
):
    """Get status of a background job."""
    from ..services.batch_jobs import app as celery_app
    
    task_result = celery_app.AsyncResult(job_id)
    
    return {
        "job_id": job_id,
        "status": task_result.status,
        "result": task_result.result if task_result.status == "SUCCESS" else None,
    }
