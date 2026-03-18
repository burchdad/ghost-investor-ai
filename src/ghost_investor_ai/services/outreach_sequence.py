"""Outreach sequence management."""
from datetime import datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from .models import OutreachCampaign, OutreachEmail, FollowUpEmail, OutreachStatusEnum, Lead
import json


class FollowUpSequence:
    """Defines follow-up schedule."""

    def __init__(self, delays: List[int]):
        """
        Initialize sequence with delays (in hours).
        Example: [0, 24, 72, 168] = immediate, 1 day, 3 days, 1 week
        """
        self.delays = delays

    def to_json(self) -> str:
        """Serialize to JSON."""
        return json.dumps({"delays": self.delays})

    @classmethod
    def from_json(cls, json_str: str) -> "FollowUpSequence":
        """Deserialize from JSON."""
        data = json.loads(json_str)
        return cls(data["delays"])

    @classmethod
    def default_sequence(cls) -> "FollowUpSequence":
        """Default follow-up cadence: immediate, 2 days, 5 days."""
        return cls([0, 48, 120])


class OutreachSequenceService:
    """Manage outreach campaigns and sequences."""

    @staticmethod
    def create_campaign(
        name: str,
        description: str,
        follow_up_sequence: FollowUpSequence,
        db: Session,
    ) -> OutreachCampaign:
        """Create a new outreach campaign."""
        campaign = OutreachCampaign(
            name=name,
            description=description,
            status=OutreachStatusEnum.DRAFT,
            follow_up_sequence=follow_up_sequence.to_json(),
        )
        db.add(campaign)
        db.commit()
        db.refresh(campaign)
        return campaign

    @staticmethod
    def add_lead_to_campaign(
        campaign_id: int,
        lead_id: int,
        email_data: Dict[str, Any],
        db: Session,
    ) -> OutreachEmail:
        """Add a lead to a campaign with generated email."""
        outreach_email = OutreachEmail(
            lead_id=lead_id,
            subject=email_data["subject"],
            body=email_data["body"],
            personalization_factors=json.dumps(email_data.get("personalization_factors", {})),
        )
        db.add(outreach_email)
        db.flush()

        # Create follow-up emails if sequence is defined
        campaign = db.query(OutreachCampaign).filter(OutreachCampaign.id == campaign_id).first()
        if campaign and campaign.follow_up_sequence:
            sequence = FollowUpSequence.from_json(campaign.follow_up_sequence)

            # Skip first delay (it's the initial email)
            for idx, delay in enumerate(sequence.delays[1:], start=1):
                follow_up = FollowUpEmail(
                    initial_email_id=outreach_email.id,
                    sequence_number=idx,
                    delay_hours_from_previous=(
                        sequence.delays[idx] - sequence.delays[idx - 1]
                    ),
                    subject=f"Follow-up #{idx}: {email_data['subject']}",
                    body=f"[Follow-up email #{idx}]\n\n{email_data['body']}",
                )
                db.add(follow_up)

        db.commit()
        db.refresh(outreach_email)
        return outreach_email

    @staticmethod
    def schedule_sends(campaign_id: int, db: Session) -> Dict[str, Any]:
        """
        Mark campaign as scheduled and calculate send times.
        Returns send schedule for integration with email service.
        """
        campaign = db.query(OutreachCampaign).filter(
            OutreachCampaign.id == campaign_id
        ).first()

        if not campaign:
            return {"error": "Campaign not found"}

        campaign.status = OutreachStatusEnum.SCHEDULED
        campaign.started_at = datetime.utcnow()

        db.commit()

        send_schedule = []
        for email in campaign.emails:
            send_schedule.append({
                "email_id": email.id,
                "lead_email": email.lead.email,
                "subject": email.subject,
                "body": email.body,
                "send_at": "immediately",
            })

            for follow_up in email.follow_ups:
                send_at = datetime.utcnow() + timedelta(
                    hours=follow_up.delay_hours_from_previous
                )
                send_schedule.append({
                    "email_id": follow_up.id,
                    "lead_email": email.lead.email,
                    "subject": follow_up.subject,
                    "body": follow_up.body,
                    "send_at": send_at.isoformat(),
                })

        return {
            "campaign_id": campaign_id,
            "status": "scheduled",
            "send_count": len(send_schedule),
            "schedule": send_schedule,
        }

    @staticmethod
    def get_active_campaigns(db: Session) -> List[OutreachCampaign]:
        """Get all active campaigns."""
        return db.query(OutreachCampaign).filter(
            OutreachCampaign.status.in_([
                OutreachStatusEnum.SCHEDULED,
                OutreachStatusEnum.IN_PROGRESS,
            ])
        ).all()

    @staticmethod
    def pause_campaign(campaign_id: int, db: Session) -> OutreachCampaign:
        """Pause a campaign."""
        campaign = db.query(OutreachCampaign).filter(
            OutreachCampaign.id == campaign_id
        ).first()
        if campaign:
            campaign.status = OutreachStatusEnum.PAUSED
            db.commit()
            db.refresh(campaign)
        return campaign

    @staticmethod
    def resume_campaign(campaign_id: int, db: Session) -> OutreachCampaign:
        """Resume a paused campaign."""
        campaign = db.query(OutreachCampaign).filter(
            OutreachCampaign.id == campaign_id
        ).first()
        if campaign:
            campaign.status = OutreachStatusEnum.IN_PROGRESS
            db.commit()
            db.refresh(campaign)
        return campaign
