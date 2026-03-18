"""API routes for leads."""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models import Lead, EnrichmentSourceEnum
from ..services import LeadImportService
from . import schemas

router = APIRouter(prefix="/api/leads", tags=["leads"])


@router.post("/import/csv", response_model=schemas.CSVImportResponse)
async def import_leads_csv(
    request: schemas.CSVImportRequest,
    db: Session = Depends(get_db),
):
    """Import leads from CSV content."""
    result = LeadImportService.import_from_csv(request.csv_content, db)
    return result


@router.post("/", response_model=schemas.LeadResponse)
async def create_lead(
    lead: schemas.LeadCreate,
    db: Session = Depends(get_db),
):
    """Create a new lead."""
    # Check if lead already exists
    existing = db.query(Lead).filter(Lead.email == lead.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Lead with this email already exists",
        )

    db_lead = Lead(
        email=lead.email,
        first_name=lead.first_name,
        last_name=lead.last_name,
        company_name=lead.company_name,
        job_title=lead.job_title,
        linkedin_url=lead.linkedin_url or "",
        phone=lead.phone or "",
        enrichment_source=EnrichmentSourceEnum.MANUAL,
    )
    db.add(db_lead)
    db.commit()
    db.refresh(db_lead)
    return db_lead


@router.get("/{lead_id}", response_model=schemas.LeadResponse)
async def get_lead(
    lead_id: int,
    db: Session = Depends(get_db),
):
    """Get lead by ID."""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found",
        )
    return lead


@router.get("/", response_model=List[schemas.LeadResponse])
async def list_leads(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """List all leads."""
    leads = db.query(Lead).offset(skip).limit(limit).all()
    return leads


@router.put("/{lead_id}", response_model=schemas.LeadResponse)
async def update_lead(
    lead_id: int,
    lead_update: schemas.LeadCreate,
    db: Session = Depends(get_db),
):
    """Update a lead."""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found",
        )

    for field, value in lead_update.dict(exclude_unset=True).items():
        setattr(lead, field, value)

    db.commit()
    db.refresh(lead)
    return lead


@router.delete("/{lead_id}")
async def delete_lead(
    lead_id: int,
    db: Session = Depends(get_db),
):
    """Delete a lead."""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found",
        )

    db.delete(lead)
    db.commit()

    return {"message": "Lead deleted successfully"}
