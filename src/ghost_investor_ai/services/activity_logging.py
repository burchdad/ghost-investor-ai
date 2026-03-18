"""Activity logging and tracking service."""
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from .models import Activity, Lead


class ActivityLoggingService:
    """Log and track all interactions with leads."""

    @staticmethod
    def log_email_sent(
        lead_id: int,
        email_id: int,
        subject: str,
        db: Session,
    ) -> Activity:
        """Log when an email is sent."""
        activity = Activity(
            lead_id=lead_id,
            activity_type="email_sent",
            description=f"Email sent with subject: {subject}",
            email_id=email_id,
            event_timestamp=datetime.utcnow(),
        )
        db.add(activity)
        db.commit()
        return activity

    @staticmethod
    def log_email_opened(
        lead_id: int,
        email_id: int,
        db: Session,
    ) -> Activity:
        """Log when an email is opened."""
        activity = Activity(
            lead_id=lead_id,
            activity_type="email_opened",
            description="Email opened",
            email_id=email_id,
            event_timestamp=datetime.utcnow(),
        )
        db.add(activity)
        db.commit()
        return activity

    @staticmethod
    def log_email_clicked(
        lead_id: int,
        email_id: int,
        link_url: Optional[str] = None,
        db: Session = None,
    ) -> Activity:
        """Log when a link in an email is clicked."""
        description = "Link clicked in email"
        if link_url:
            description += f": {link_url}"

        activity = Activity(
            lead_id=lead_id,
            activity_type="email_clicked",
            description=description,
            email_id=email_id,
            event_timestamp=datetime.utcnow(),
        )
        db.add(activity)
        db.commit()
        return activity

    @staticmethod
    def log_reply_received(
        lead_id: int,
        email_id: int,
        reply_content: str,
        db: Session,
    ) -> Activity:
        """Log when a reply is received from a lead."""
        activity = Activity(
            lead_id=lead_id,
            activity_type="reply_received",
            description=f"Reply received: {reply_content[:500]}",
            email_id=email_id,
            event_timestamp=datetime.utcnow(),
        )
        db.add(activity)
        db.commit()
        return activity

    @staticmethod
    def log_manual_activity(
        lead_id: int,
        activity_type: str,
        description: str,
        db: Session,
    ) -> Activity:
        """Log any manual activity."""
        activity = Activity(
            lead_id=lead_id,
            activity_type=activity_type,
            description=description,
            event_timestamp=datetime.utcnow(),
        )
        db.add(activity)
        db.commit()
        return activity

    @staticmethod
    def sync_to_crm(activity_id: int, crm_id: str, db: Session) -> Activity:
        """Mark activity as synced to CRM."""
        activity = db.query(Activity).filter(Activity.id == activity_id).first()
        if activity:
            activity.synced_to_crm = True
            activity.crm_id = crm_id
            db.commit()
        return activity

    @staticmethod
    def get_lead_timeline(lead_id: int, db: Session):
        """Get complete activity timeline for a lead."""
        activities = db.query(Activity).filter(
            Activity.lead_id == lead_id
        ).order_by(Activity.event_timestamp.desc()).all()

        return [
            {
                "id": a.id,
                "type": a.activity_type,
                "description": a.description,
                "timestamp": a.event_timestamp.isoformat() if a.event_timestamp else None,
                "synced_to_crm": a.synced_to_crm,
            }
            for a in activities
        ]
