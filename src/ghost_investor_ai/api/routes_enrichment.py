"""API routes for enrichment."""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Lead, ContactScore
from ..services.enrichment import EnrichmentService
from ..services.scoring import ContactScoringService
from . import schemas as schemas_module

router = APIRouter(prefix="/api/enrichment", tags=["enrichment"])


@router.post("/enrich/{lead_id}")
async def enrich_lead(
    lead_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Trigger enrichment for a lead."""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found",
        )

    # Run enrichment in background
    background_tasks.add_task(run_enrichment, lead_id)

    return {
        "status": "enrichment_started",
        "lead_id": lead_id,
    }


@router.get("/score/{lead_id}")
async def get_contact_score(
    lead_id: int,
    db: Session = Depends(get_db),
):
    """Get contact score for a lead."""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found",
        )

    # Calculate or get existing score
    score = db.query(ContactScore).filter(ContactScore.lead_id == lead_id).first()
    if not score:
        score = ContactScoringService.calculate_score(lead, db)

    return {
        "lead_id": score.lead_id,
        "title_score": score.title_score,
        "company_score": score.company_score,
        "activity_score": score.activity_score,
        "engagement_score": score.engagement_score,
        "total_score": score.total_score,
        "score_reason": score.score_reason,
    }


@router.post("/score/{lead_id}/recalculate")
async def recalculate_contact_score(
    lead_id: int,
    db: Session = Depends(get_db),
):
    """Recalculate contact score for a lead."""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found",
        )

    score = ContactScoringService.calculate_score(lead, db)
    return {
        "lead_id": score.lead_id,
        "title_score": score.title_score,
        "company_score": score.company_score,
        "activity_score": score.activity_score,
        "engagement_score": score.engagement_score,
        "total_score": score.total_score,
        "score_reason": score.score_reason,
    }


# Background task
async def run_enrichment(lead_id: int):
    """Run enrichment in background."""
    from ..database import SessionLocal
    
    db = SessionLocal()
    try:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if lead:
            service = EnrichmentService()
            await service.enrich_lead(lead)
            
            # Recalculate score after enrichment
            ContactScoringService.calculate_score(lead, db)
            db.commit()
    finally:
        db.close()
