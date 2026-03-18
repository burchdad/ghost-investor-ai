"""API routes for webhook management."""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
import json

from ..database import get_db
from ..auth import get_current_user
from ..models import User
from ..services.webhooks import WebhookService

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


class WebhookRequest:
    """Webhook registration request."""
    endpoint_url: str
    events: List[str]  # ["email.sent", "reply.received", "*"]


@router.post("/register")
async def register_webhook(
    endpoint_url: str,
    events: List[str],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Register a webhook endpoint."""
    result = WebhookService.register_webhook(
        current_user.id, endpoint_url, events, db
    )

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))

    return result


@router.get("/")
async def list_webhooks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all webhooks for current user."""
    return WebhookService.list_webhooks(current_user.id, db)


@router.delete("/{webhook_id}")
async def delete_webhook(
    webhook_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a webhook."""
    result = WebhookService.delete_webhook(webhook_id, current_user.id, db)

    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error"))

    return result


@router.post("/{webhook_id}/test")
async def test_webhook(
    webhook_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Send a test event to a webhook."""
    test_payload = {
        "test": True,
        "message": "This is a test webhook event"
    }
    
    result = WebhookService.emit_event(
        event_type="test.event",
        data=test_payload,
        user_id=current_user.id,
        db=db
    )

    return result


@router.get("/{webhook_id}/history")
async def get_webhook_history(
    webhook_id: int,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get delivery history for a webhook."""
    result = WebhookService.get_event_history(webhook_id, current_user.id, db, limit)

    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    return result


@router.post("/events/emit")
async def emit_webhook_event(
    event_type: str,
    data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    """Emit a webhook event (internal use)."""
    result = WebhookService.emit_event(event_type, data, current_user.id, db)

    # Queue async delivery in background
    # In production, this would be a Celery task

    return result
