"""API routes for analytics and metrics."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..database import get_db
from ..auth import get_current_user
from ..models import User
from ..services.analytics import AnalyticsService

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/campaigns/{campaign_id}/metrics")
async def get_campaign_metrics(
    campaign_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get comprehensive metrics for a campaign."""
    metrics = AnalyticsService.get_campaign_metrics(campaign_id, db)
    
    if hasattr(metrics, "error"):
        raise HTTPException(status_code=404, detail=metrics["error"])
    
    return metrics


@router.get("/leads/{lead_id}/performance")
async def get_lead_performance(
    lead_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get engagement metrics for a lead."""
    performance = AnalyticsService.get_lead_performance(lead_id, db)
    
    if "error" in performance:
        raise HTTPException(status_code=404, detail=performance["error"])
    
    return performance


@router.get("/templates/performance")
async def get_email_template_performance(
    campaign_id: int = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Analyze performance of different email templates."""
    performance = AnalyticsService.get_email_template_performance(campaign_id, db)
    return performance


@router.get("/campaigns/{campaign_id}/investor-stages")
async def get_investor_stage_distribution(
    campaign_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get distribution of investor stages in campaign."""
    distribution = AnalyticsService.get_investor_stage_distribution(campaign_id, db)
    return distribution


@router.get("/campaigns/{campaign_id}/time-series")
async def get_time_series_metrics(
    campaign_id: int,
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get time-series data for campaign performance over time."""
    metrics = AnalyticsService.get_time_series_metrics(campaign_id, db, days)
    return metrics
