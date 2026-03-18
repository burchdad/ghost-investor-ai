"""Celery task definitions for background job processing."""
from celery import Celery, group
from celery.utils.log import get_task_logger
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Dict, Any
from ..config import settings
from ..database import SessionLocal
from ..models import Lead, OutreachEmail, EmailAccount, SentEmail
from .ai_email_generation import AIEmailGenerationService
from .reply_parsing import ReplyParsingService
from ..integrations.email_service import EmailServiceCoordinator
from ..integrations.crm_sync import GhostCRMSync

logger = get_task_logger(__name__)

# Configure Celery
app = Celery(
    "ghost_investor_ai",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend_url,
)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_soft_time_limit=3600,  # 1 hour soft limit
    task_time_limit=3600,  # 1 hour hard limit
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
)


@app.task(bind=True, max_retries=3)
def batch_enrich_leads(self, lead_ids: List[int], enrichment_source: str):
    """Enrich multiple leads in batch."""
    db = SessionLocal()
    try:
        from .enrichment_adapters import EnrichmentService

        enrichment_svc = EnrichmentService()
        results = {"successful": 0, "failed": 0, "errors": []}

        for lead_id in lead_ids:
            try:
                lead = db.query(Lead).filter(Lead.id == lead_id).first()
                if not lead:
                    results["failed"] += 1
                    continue

                # Enrich lead
                enriched = enrichment_svc.enrich_lead(
                    lead.email, lead.company_name, enrichment_source
                )

                if enriched:
                    lead.is_enriched = True
                    lead.enrichment_source = enrichment_source
                    # Update fields from enriched data
                    lead.company_industry = enriched.get("industry")
                    lead.company_size = enriched.get("company_size")
                    db.add(lead)
                    results["successful"] += 1
                else:
                    results["failed"] += 1

            except Exception as e:
                results["failed"] += 1
                results["errors"].append(f"Lead {lead_id}: {str(e)}")

        db.commit()
        logger.info(
            f"Batch enrich completed: {results['successful']} successful, "
            f"{results['failed']} failed"
        )
        return results

    except Exception as exc:
        db.rollback()
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
    finally:
        db.close()


@app.task(bind=True, max_retries=3)
def batch_generate_emails(
    self, outreach_email_ids: List[int], email_type: str
):
    """Generate emails for multiple leads."""
    db = SessionLocal()
    try:
        ai_service = AIEmailGenerationService()
        results = {
            "successful": 0,
            "failed": 0,
            "total_cost": 0.0,
            "errors": [],
        }

        for email_id in outreach_email_ids:
            try:
                email_obj = db.query(OutreachEmail).filter(
                    OutreachEmail.id == email_id
                ).first()
                if not email_obj or not email_obj.lead:
                    results["failed"] += 1
                    continue

                # Generate email
                if email_type == "first_touch":
                    result = ai_service.generate_first_touch_email(
                        email_obj.lead, email_obj.deal_brief
                    )
                elif email_type == "follow_up":
                    result = ai_service.generate_followup_email(
                        email_obj.lead, email_obj.previous_email_body or ""
                    )
                elif email_type == "reengagement":
                    result = ai_service.generate_reengagement_email(email_obj.lead)
                else:
                    results["failed"] += 1
                    continue

                if result.get("success"):
                    email_obj.subject = result["subject"]
                    email_obj.body = result["body"]
                    email_obj.is_generated = True
                    email_obj.generated_at = datetime.utcnow()
                    results["total_cost"] += result.get("cost_estimate", 0.0)
                    db.add(email_obj)
                    results["successful"] += 1
                else:
                    results["failed"] += 1
                    results["errors"].append(
                        f"Email {email_id}: {result.get('error', 'Unknown error')}"
                    )

            except Exception as e:
                results["failed"] += 1
                results["errors"].append(f"Email {email_id}: {str(e)}")

        db.commit()
        logger.info(
            f"Batch email generation: {results['successful']} successful, "
            f"${results['total_cost']:.2f} cost estimated"
        )
        return results

    except Exception as exc:
        db.rollback()
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
    finally:
        db.close()


@app.task(bind=True, max_retries=3)
def batch_send_emails(
    self, sent_email_ids: List[int], account_id: int
):
    """Send batch of prepared emails."""
    db = SessionLocal()
    try:
        results = {
            "successful": 0,
            "failed": 0,
            "errors": [],
        }

        coordinator = EmailServiceCoordinator()

        for sent_email_id in sent_email_ids:
            try:
                sent_email = db.query(SentEmail).filter(
                    SentEmail.id == sent_email_id
                ).first()
                if not sent_email or not sent_email.outreach_email:
                    results["failed"] += 1
                    continue

                email_obj = sent_email.outreach_email
                lead = email_obj.lead

                # Send email
                result = coordinator.send_email(
                    account_id=account_id,
                    to_email=lead.email,
                    subject=email_obj.subject,
                    body=email_obj.body,
                    lead_id=lead.id,
                    outreach_email_id=email_obj.id,
                    db=db,
                )

                if result.get("success"):
                    results["successful"] += 1
                    # Push activity to CRM
                    crm_sync = GhostCRMSync()
                    crm_sync.push_activity(
                        lead.id,
                        {
                            "activity_type": "email_sent",
                            "description": f"Email sent: {email_obj.subject}",
                        },
                    )
                else:
                    results["failed"] += 1
                    results["errors"].append(
                        f"Email {sent_email_id}: {result.get('error', 'Unknown error')}"
                    )

            except Exception as e:
                results["failed"] += 1
                results["errors"].append(f"Email {sent_email_id}: {str(e)}")

        logger.info(
            f"Batch send: {results['successful']} successful, "
            f"{results['failed']} failed"
        )
        return results

    except Exception as exc:
        db.rollback()
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
    finally:
        db.close()


@app.task(bind=True, max_retries=2)
def fetch_and_classify_replies(self, account_id: int):
    """Fetch replies and classify them."""
    db = SessionLocal()
    try:
        coordinator = EmailServiceCoordinator()
        reply_service = ReplyParsingService()
        results = {"processed": 0, "classified": 0, "errors": []}

        # Get replies
        reply_result = coordinator.get_replies(account_id, db)
        if not reply_result.get("success"):
            return {"error": reply_result.get("error")}

        messages = reply_result.get("messages", [])

        for message in messages:
            try:
                # Check if already classified
                existing = (
                    db.query(ReplyClassification)
                    .filter(ReplyClassification.message_id == message.get("id"))
                    .first()
                )
                if existing:
                    continue

                # Classify
                classification = reply_service.classify_reply(
                    message.get("body", ""), message.get("subject", "")
                )

                if classification.get("success"):
                    class_data = classification["classification"]

                    reply_obj = ReplyClassification(
                        message_id=message.get("id"),
                        sender_email=message.get("from"),
                        subject=message.get("subject"),
                        body=message.get("body"),
                        classification=class_data.get("classification"),
                        confidence=class_data.get("confidence"),
                        sentiment=class_data.get("sentiment"),
                        key_points=class_data.get("key_points"),
                        suggested_action=class_data.get("suggested_action"),
                        requires_human_review=class_data.get(
                            "requires_human_review", False
                        ),
                        received_at=datetime.utcnow(),
                    )
                    db.add(reply_obj)
                    results["classified"] += 1

                results["processed"] += 1

            except Exception as e:
                results["errors"].append(f"Message {message.get('id')}: {str(e)}")

        db.commit()
        logger.info(f"Processed {results['processed']} replies, classified {results['classified']}")
        return results

    except Exception as exc:
        db.rollback()
        raise self.retry(exc=exc, countdown=300 * (2 ** self.request.retries))
    finally:
        db.close()


@app.task
def schedule_batch_followups():
    """Scheduled task to find leads needing follow-ups."""
    db = SessionLocal()
    try:
        # Find emails sent 3+ days ago with no reply
        three_days_ago = datetime.utcnow() - timedelta(days=3)
        pending_followups = (
            db.query(OutreachEmail)
            .filter(
                OutreachEmail.sent_at < three_days_ago,
                OutreachEmail.email_type == "first_touch",
            )
            .all()
        )

        logger.info(f"Found {len(pending_followups)} emails needing follow-ups")
        # These would be queued for manual review or automatic follow-up

    finally:
        db.close()


@app.task
def sync_crm_periodic():
    """Periodic sync with GhostCRM."""
    db = SessionLocal()
    try:
        crm_sync = GhostCRMSync()
        synced = 0

        # Get recently updated leads
        recent_leads = db.query(Lead).filter(
            Lead.updated_at > datetime.utcnow() - timedelta(hours=1)
        ).all()

        for lead in recent_leads:
            result = crm_sync.push_lead(lead)
            if result.get("success"):
                synced += 1

        logger.info(f"CRM sync: {synced}/{len(recent_leads)} leads synced")

    finally:
        db.close()
