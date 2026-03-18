"""Analytics service for campaign and performance metrics."""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy import func, and_
from sqlalchemy.orm import Session
from ..models import (
    OutreachCampaign,
    OutreachEmail,
    SentEmail,
    ReplyClassification,
    Activity,
    Lead,
)


class AnalyticsService:
    """Generate analytics and metrics for campaigns and leads."""

    @staticmethod
    def get_campaign_metrics(campaign_id: int, db: Session) -> Dict[str, Any]:
        """Get comprehensive metrics for a campaign."""
        campaign = (
            db.query(OutreachCampaign)
            .filter(OutreachCampaign.id == campaign_id)
            .first()
        )

        if not campaign:
            return {"error": "Campaign not found"}

        # Get campaign emails
        emails = (
            db.query(OutreachEmail)
            .filter(OutreachEmail.campaign_id == campaign_id)
            .all()
        )

        # Get sent emails
        sent_emails = (
            db.query(SentEmail)
            .join(OutreachEmail)
            .filter(OutreachEmail.campaign_id == campaign_id)
            .all()
        )

        # Calculate metrics
        total_emails = len(emails)
        total_sent = len(sent_emails)
        
        opened_count = len([e for e in sent_emails if e.opened_at])
        clicked_count = len([e for e in sent_emails if e.clicked_at])
        
        # Get replies
        reply_count = (
            db.query(ReplyClassification)
            .filter(
                ReplyClassification.message_id.in_(
                    [e.message_id for e in sent_emails]
                )
            )
            .count()
        )

        # Classification breakdown
        classifications = (
            db.query(
                ReplyClassification.classification,
                func.count(ReplyClassification.id).label("count"),
            )
            .filter(
                ReplyClassification.message_id.in_(
                    [e.message_id for e in sent_emails]
                )
            )
            .group_by(ReplyClassification.classification)
            .all()
        )

        return {
            "campaign_id": campaign_id,
            "campaign_name": campaign.name,
            "status": campaign.status,
            "created_at": campaign.created_at.isoformat() if campaign.created_at else None,
            "metrics": {
                "total_emails_prepared": total_emails,
                "total_emails_sent": total_sent,
                "opened_count": opened_count,
                "clicked_count": clicked_count,
                "reply_count": reply_count,
                "open_rate": (
                    round(opened_count / total_sent * 100, 2) if total_sent > 0 else 0
                ),
                "click_rate": (
                    round(clicked_count / total_sent * 100, 2) if total_sent > 0 else 0
                ),
                "reply_rate": (
                    round(reply_count / total_sent * 100, 2) if total_sent > 0 else 0
                ),
            },
            "reply_classification_breakdown": [
                {"classification": c[0], "count": c[1]} for c in classifications
            ],
        }

    @staticmethod
    def get_lead_performance(lead_id: int, db: Session) -> Dict[str, Any]:
        """Get engagement metrics for a lead."""
        lead = db.query(Lead).filter(Lead.id == lead_id).first()

        if not lead:
            return {"error": "Lead not found"}

        # Get emails sent to this lead
        sent_emails = (
            db.query(SentEmail)
            .join(OutreachEmail)
            .filter(OutreachEmail.lead_id == lead_id)
            .all()
        )

        # Get replies from this lead
        replies = (
            db.query(ReplyClassification)
            .filter(
                ReplyClassification.message_id.in_(
                    [e.message_id for e in sent_emails]
                )
            )
            .all()
        )

        # Get activities for this lead
        activities = (
            db.query(Activity)
            .filter(Activity.lead_id == lead_id)
            .order_by(Activity.event_timestamp.desc())
            .all()
        )

        # Calculate metrics
        total_emails = len(sent_emails)
        opened_count = len([e for e in sent_emails if e.opened_at])
        clicked_count = len([e for e in sent_emails if e.clicked_at])
        reply_count = len(replies)

        # Get the most recent reply classification
        latest_reply_classification = None
        if replies:
            latest_reply = sorted(replies, key=lambda x: x.received_at, reverse=True)[
                0
            ]
            latest_reply_classification = {
                "classification": latest_reply.classification,
                "sentiment": latest_reply.sentiment,
                "confidence": latest_reply.confidence,
                "received_at": latest_reply.received_at.isoformat()
                if latest_reply.received_at
                else None,
            }

        return {
            "lead_id": lead_id,
            "lead_name": f"{lead.first_name} {lead.last_name}",
            "email": lead.email,
            "company": lead.company_name,
            "contact_score": lead.contact_score,
            "metrics": {
                "total_emails_sent": total_emails,
                "opened_count": opened_count,
                "clicked_count": clicked_count,
                "reply_count": reply_count,
                "open_rate": (
                    round(opened_count / total_emails * 100, 2)
                    if total_emails > 0
                    else 0
                ),
                "click_rate": (
                    round(clicked_count / total_emails * 100, 2)
                    if total_emails > 0
                    else 0
                ),
                "reply_rate": (
                    round(reply_count / total_emails * 100, 2) if total_emails > 0 else 0
                ),
            },
            "latest_reply_classification": latest_reply_classification,
            "activity_count": len(activities),
            "recent_activities": [
                {
                    "type": a.activity_type,
                    "description": a.description,
                    "timestamp": a.event_timestamp.isoformat()
                    if a.event_timestamp
                    else None,
                }
                for a in activities[:5]
            ],
        }

    @staticmethod
    def get_email_template_performance(
        campaign_id: Optional[int] = None, db: Session = None
    ) -> Dict[str, Any]:
        """Analyze performance of different email templates."""
        query = db.query(OutreachEmail)

        if campaign_id:
            query = query.filter(OutreachEmail.campaign_id == campaign_id)

        emails = query.all()

        # Group by subject line patterns
        template_groups: Dict[str, List[OutreachEmail]] = {}
        for email in emails:
            # Use first 50 chars as template identifier
            template_key = email.subject[:50] if email.subject else "Unknown"
            if template_key not in template_groups:
                template_groups[template_key] = []
            template_groups[template_key].append(email)

        performance = []
        for template_key, template_emails in template_groups.items():
            sent_emails = (
                db.query(SentEmail)
                .filter(
                    SentEmail.outreach_email_id.in_(
                        [e.id for e in template_emails]
                    )
                )
                .all()
            )

            opened_count = len([e for e in sent_emails if e.opened_at])
            clicked_count = len([e for e in sent_emails if e.clicked_at])

            replies = (
                db.query(ReplyClassification)
                .filter(
                    ReplyClassification.message_id.in_(
                        [e.message_id for e in sent_emails]
                    )
                )
                .all()
            )

            interested_count = len(
                [r for r in replies if r.classification == "INTERESTED"]
            )

            total_sent = len(sent_emails)

            performance.append(
                {
                    "template": template_key,
                    "total_sent": total_sent,
                    "opened": opened_count,
                    "clicked": clicked_count,
                    "replies": len(replies),
                    "interested": interested_count,
                    "open_rate": (
                        round(opened_count / total_sent * 100, 2)
                        if total_sent > 0
                        else 0
                    ),
                    "click_rate": (
                        round(clicked_count / total_sent * 100, 2)
                        if total_sent > 0
                        else 0
                    ),
                    "interested_rate": (
                        round(interested_count / total_sent * 100, 2)
                        if total_sent > 0
                        else 0
                    ),
                }
            )

        return {
            "campaign_id": campaign_id,
            "template_count": len(performance),
            "templates": sorted(performance, key=lambda x: x["interested_rate"], reverse=True),
        }

    @staticmethod
    def get_investor_stage_distribution(
        campaign_id: Optional[int] = None, db: Session = None
    ) -> Dict[str, Any]:
        """Get distribution of investor stages in campaign."""
        query = (
            db.query(Lead, func.count(OutreachEmail.id).label("email_count"))
            .join(OutreachEmail)
            .group_by(Lead.id)
        )

        if campaign_id:
            query = query.filter(OutreachEmail.campaign_id == campaign_id)

        results = query.all()

        # Group by investment stage (or company size as proxy)
        stage_distribution = {}
        for lead, email_count in results:
            stage = lead.company_size or "Unknown"
            if stage not in stage_distribution:
                stage_distribution[stage] = {
                    "count": 0,
                    "total_score": 0,
                    "avg_score": 0,
                }
            stage_distribution[stage]["count"] += 1
            stage_distribution[stage]["total_score"] += lead.contact_score or 0

        # Calculate averages
        for stage in stage_distribution:
            count = stage_distribution[stage]["count"]
            stage_distribution[stage]["avg_score"] = (
                round(stage_distribution[stage]["total_score"] / count, 2)
                if count > 0
                else 0
            )

        return {
            "campaign_id": campaign_id,
            "stage_distribution": stage_distribution,
            "total_leads": sum(s["count"] for s in stage_distribution.values()),
        }

    @staticmethod
    def get_time_series_metrics(
        campaign_id: int, db: Session, days: int = 30
    ) -> Dict[str, Any]:
        """Get time-series data for campaign performance over time."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Get sends over time
        sends_by_date = (
            db.query(
                func.date(SentEmail.created_at).label("date"),
                func.count(SentEmail.id).label("count"),
            )
            .join(OutreachEmail)
            .filter(OutreachEmail.campaign_id == campaign_id)
            .filter(SentEmail.created_at >= cutoff_date)
            .group_by(func.date(SentEmail.created_at))
            .all()
        )

        # Get opens over time
        opens_by_date = (
            db.query(
                func.date(SentEmail.opened_at).label("date"),
                func.count(SentEmail.id).label("count"),
            )
            .join(OutreachEmail)
            .filter(OutreachEmail.campaign_id == campaign_id)
            .filter(SentEmail.opened_at.isnot(None))
            .filter(SentEmail.opened_at >= cutoff_date)
            .group_by(func.date(SentEmail.opened_at))
            .all()
        )

        # Get replies over time
        replies_by_date = (
            db.query(
                func.date(ReplyClassification.received_at).label("date"),
                func.count(ReplyClassification.id).label("count"),
            )
            .filter(
                ReplyClassification.message_id.in_(
                    db.query(SentEmail.message_id)
                    .join(OutreachEmail)
                    .filter(OutreachEmail.campaign_id == campaign_id)
                )
            )
            .filter(ReplyClassification.received_at >= cutoff_date)
            .group_by(func.date(ReplyClassification.received_at))
            .all()
        )

        return {
            "campaign_id": campaign_id,
            "period_days": days,
            "sends_by_date": [
                {"date": str(date), "count": count} for date, count in sends_by_date
            ],
            "opens_by_date": [
                {"date": str(date), "count": count} for date, count in opens_by_date
            ],
            "replies_by_date": [
                {"date": str(date), "count": count} for date, count in replies_by_date
            ],
        }
