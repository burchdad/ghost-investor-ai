"""Webhook management and event delivery service."""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
import httpx
import hmac
import hashlib
import json
import asyncio
from ..models import WebhookEvent, WebhookEndpoint
from ..config import settings


class WebhookService:
    """Manage webhook registration and async event delivery."""

    @staticmethod
    def register_webhook(
        user_id: int,
        endpoint_url: str,
        events: List[str],
        db: Session,
    ) -> Dict[str, Any]:
        """Register a webhook endpoint."""
        try:
            webhook = WebhookEndpoint(
                user_id=user_id,
                endpoint_url=endpoint_url,
                events=events,
                is_active=True,
                secret_key=WebhookService._generate_secret(),
            )
            db.add(webhook)
            db.commit()

            return {
                "success": True,
                "webhook_id": webhook.id,
                "endpoint_url": endpoint_url,
                "events": events,
                "secret_key": webhook.secret_key,
                "created_at": webhook.created_at.isoformat(),
            }
        except Exception as e:
            db.rollback()
            return {"success": False, "error": str(e)}

    @staticmethod
    def list_webhooks(user_id: int, db: Session) -> Dict[str, Any]:
        """List webhooks for user."""
        webhooks = (
            db.query(WebhookEndpoint)
            .filter(WebhookEndpoint.user_id == user_id)
            .order_by(WebhookEndpoint.created_at.desc())
            .all()
        )

        return {
            "webhooks": [
                {
                    "id": w.id,
                    "endpoint_url": w.endpoint_url,
                    "events": w.events,
                    "is_active": w.is_active,
                    "retry_count": w.retry_count,
                    "last_delivered_at": w.last_delivered_at.isoformat()
                    if w.last_delivered_at
                    else None,
                    "last_error": w.last_error,
                    "created_at": w.created_at.isoformat(),
                }
                for w in webhooks
            ]
        }

    @staticmethod
    def delete_webhook(webhook_id: int, user_id: int, db: Session) -> Dict[str, Any]:
        """Delete a webhook."""
        webhook = (
            db.query(WebhookEndpoint)
            .filter(
                WebhookEndpoint.id == webhook_id,
                WebhookEndpoint.user_id == user_id,
            )
            .first()
        )

        if not webhook:
            return {"success": False, "error": "Webhook not found"}

        db.delete(webhook)
        db.commit()

        return {"success": True, "message": "Webhook deleted"}

    @staticmethod
    def emit_event(
        event_type: str,
        data: Dict[str, Any],
        user_id: int,
        db: Session,
    ) -> Dict[str, Any]:
        """Emit a webhook event for delivery."""
        # Find matching webhooks
        webhooks = (
            db.query(WebhookEndpoint)
            .filter(
                WebhookEndpoint.user_id == user_id,
                WebhookEndpoint.is_active == True,
            )
            .all()
        )

        matching_webhooks = [
            w for w in webhooks if event_type in w.events or "*" in w.events
        ]

        if not matching_webhooks:
            return {"success": True, "delivered": 0}

        # Queue delivery for matching webhooks
        for webhook in matching_webhooks:
            event = WebhookEvent(
                webhook_endpoint_id=webhook.id,
                event_type=event_type,
                payload=data,
                status="pending",
            )
            db.add(event)

        db.commit()

        # Trigger async delivery
        return {
            "success": True,
            "delivered": len(matching_webhooks),
            "event_type": event_type,
        }

    @staticmethod
    async def deliver_event(event_id: int, db: Session) -> Dict[str, Any]:
        """Deliver a single webhook event."""
        event = db.query(WebhookEvent).filter(WebhookEvent.id == event_id).first()

        if not event or event.status != "pending":
            return {"success": False, "error": "Event not found or already delivered"}

        webhook = event.webhook_endpoint

        try:
            # Prepare payload
            payload = {
                "id": event.id,
                "event_type": event.event_type,
                "timestamp": event.created_at.isoformat(),
                "data": event.payload,
            }

            # Generate signature
            signature = WebhookService._generate_signature(
                json.dumps(payload), webhook.secret_key
            )

            # Attempt delivery
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    webhook.endpoint_url,
                    json=payload,
                    headers={
                        "X-Webhook-Signature": signature,
                        "X-Webhook-Event": event.event_type,
                        "User-Agent": "Ghost-Investor-AI/1.0",
                    },
                )

                if response.status_code in [200, 201]:
                    event.status = "delivered"
                    event.delivered_at = datetime.utcnow()
                    webhook.last_delivered_at = datetime.utcnow()
                    webhook.retry_count = 0
                    webhook.last_error = None
                    db.commit()

                    return {
                        "success": True,
                        "event_id": event_id,
                        "status": "delivered",
                    }
                else:
                    raise Exception(f"HTTP {response.status_code}: {response.text}")

        except Exception as e:
            event.status = "failed"
            event.error_message = str(e)
            webhook.retry_count = (webhook.retry_count or 0) + 1
            webhook.last_error = str(e)

            # Schedule retry if under retry limit
            if webhook.retry_count < 5:
                event.retry_at = datetime.utcnow() + timedelta(
                    minutes=5 * webhook.retry_count
                )
                event.status = "pending_retry"

            db.commit()

            return {
                "success": False,
                "event_id": event_id,
                "error": str(e),
                "retry_count": webhook.retry_count,
            }

    @staticmethod
    async def process_pending_events(db: Session) -> Dict[str, Any]:
        """Process all pending webhook events."""
        # Get pending events ready for delivery
        pending_events = (
            db.query(WebhookEvent)
            .filter(WebhookEvent.status.in_(["pending", "pending_retry"]))
            .filter(
                (WebhookEvent.retry_at.is_(None))
                | (WebhookEvent.retry_at <= datetime.utcnow())
            )
            .limit(100)
            .all()
        )

        results = {"successful": 0, "failed": 0, "errors": []}

        # Deliver events concurrently
        tasks = [WebhookService.deliver_event(event.id, db) for event in pending_events]

        if tasks:
            responses = await asyncio.gather(*tasks, return_exceptions=True)

            for response in responses:
                if isinstance(response, Exception):
                    results["failed"] += 1
                    results["errors"].append(str(response))
                elif response.get("success"):
                    results["successful"] += 1
                else:
                    results["failed"] += 1
                    results["errors"].append(response.get("error"))

        return results

    @staticmethod
    def get_event_history(
        webhook_id: int, user_id: int, db: Session, limit: int = 50
    ) -> Dict[str, Any]:
        """Get delivery history for a webhook."""
        webhook = (
            db.query(WebhookEndpoint)
            .filter(
                WebhookEndpoint.id == webhook_id,
                WebhookEndpoint.user_id == user_id,
            )
            .first()
        )

        if not webhook:
            return {"error": "Webhook not found"}

        events = (
            db.query(WebhookEvent)
            .filter(WebhookEvent.webhook_endpoint_id == webhook_id)
            .order_by(WebhookEvent.created_at.desc())
            .limit(limit)
            .all()
        )

        # Get stats
        total_events = (
            db.query(func.count(WebhookEvent.id))
            .filter(WebhookEvent.webhook_endpoint_id == webhook_id)
            .scalar()
        )

        successful_events = (
            db.query(func.count(WebhookEvent.id))
            .filter(
                WebhookEvent.webhook_endpoint_id == webhook_id,
                WebhookEvent.status == "delivered",
            )
            .scalar()
        )

        failed_events = (
            db.query(func.count(WebhookEvent.id))
            .filter(
                WebhookEvent.webhook_endpoint_id == webhook_id,
                WebhookEvent.status == "failed",
            )
            .scalar()
        )

        return {
            "webhook_id": webhook_id,
            "stats": {
                "total_events": total_events,
                "successful": successful_events,
                "failed": failed_events,
                "success_rate": (
                    round(successful_events / total_events * 100, 2)
                    if total_events > 0
                    else 0
                ),
            },
            "recent_events": [
                {
                    "id": e.id,
                    "event_type": e.event_type,
                    "status": e.status,
                    "created_at": e.created_at.isoformat(),
                    "delivered_at": e.delivered_at.isoformat() if e.delivered_at else None,
                    "error_message": e.error_message,
                    "retry_count": webhook.retry_count,
                }
                for e in events
            ],
        }

    @staticmethod
    def _generate_secret() -> str:
        """Generate a random secret key."""
        import secrets
        return secrets.token_urlsafe(32)

    @staticmethod
    def _generate_signature(payload: str, secret: str) -> str:
        """Generate HMAC signature for webhook payload."""
        return hmac.new(
            secret.encode(), payload.encode(), hashlib.sha256
        ).hexdigest()

    @staticmethod
    def verify_webhook_signature(
        payload: str, signature: str, secret: str
    ) -> bool:
        """Verify webhook signature."""
        expected_signature = WebhookService._generate_signature(payload, secret)
        return hmac.compare_digest(signature, expected_signature)
