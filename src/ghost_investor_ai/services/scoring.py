"""Contact scoring service."""
from .models import Lead, ContactScore
from sqlalchemy.orm import Session


class ContactScoringService:
    """Score leads based on multiple criteria."""

    # Scoring weights
    TITLE_SCORE_WEIGHT = 0.25
    COMPANY_SCORE_WEIGHT = 0.25
    ACTIVITY_SCORE_WEIGHT = 0.25
    ENGAGEMENT_SCORE_WEIGHT = 0.25

    # Keywords indicating strong investment titles
    STRONG_INVESTOR_TITLES = {
        "partner": 0.9,
        "managing partner": 1.0,
        "principal": 0.85,
        "founder": 0.95,
        "investor": 0.8,
        "venture": 0.85,
        "director": 0.7,
        "associate": 0.6,
    }

    # Company size scoring
    COMPANY_SIZE_SCORES = {
        "1-10": 0.5,
        "11-50": 0.6,
        "51-200": 0.75,
        "201-500": 0.8,
        "501-1000": 0.85,
        "1000+": 0.9,
    }

    @staticmethod
    def score_title(title: str) -> float:
        """Score job title for investor relevance."""
        if not title:
            return 0.0

        title_lower = title.lower()
        for keyword, score in ContactScoringService.STRONG_INVESTOR_TITLES.items():
            if keyword in title_lower:
                return score

        return 0.3  # Default low score for unknown titles

    @staticmethod
    def score_company(company_size: str, industry: str) -> float:
        """Score company for relevance."""
        score = 0.5  # baseline

        if company_size:
            size_score = ContactScoringService.COMPANY_SIZE_SCORES.get(company_size, 0.5)
            score = (score + size_score) / 2

        # Industries related to tech/venture
        tech_industries = {
            "venture capital": 1.0,
            "private equity": 0.9,
            "technology": 0.75,
            "software": 0.75,
            "fintech": 0.8,
            "biotech": 0.75,
            "startups": 0.75,
        }

        if industry:
            industry_lower = industry.lower()
            for ind_keyword, ind_score in tech_industries.items():
                if ind_keyword in industry_lower:
                    score = (score + ind_score) / 2
                    break

        return min(score, 1.0)

    @staticmethod
    def score_activity(lead: Lead) -> float:
        """Score based on documented activities."""
        if not lead.activities:
            return 0.0

        activity_count = len(lead.activities)
        # Score increases with more interactions, capped at 1.0
        return min(activity_count * 0.1, 1.0)

    @staticmethod
    def score_engagement(lead: Lead) -> float:
        """Score based on email engagement metrics."""
        if not lead.outreach_emails:
            return 0.0

        total_opens = sum(
            email.lead.activities.__len__() 
            for email in lead.outreach_emails 
            if email.is_sent
        )
        engagement = min((total_opens * 0.2), 1.0)
        return engagement

    @classmethod
    def calculate_score(cls, lead: Lead, db: Session) -> ContactScore:
        """Calculate comprehensive contact score."""
        title_score = cls.score_title(lead.job_title or "")
        company_score = cls.score_company(lead.company_size, lead.company_industry or "")
        activity_score = cls.score_activity(lead)
        engagement_score = cls.score_engagement(lead)

        total_score = (
            (title_score * cls.TITLE_SCORE_WEIGHT)
            + (company_score * cls.COMPANY_SCORE_WEIGHT)
            + (activity_score * cls.ACTIVITY_SCORE_WEIGHT)
            + (engagement_score * cls.ENGAGEMENT_SCORE_WEIGHT)
        )

        reason_parts = []
        if title_score > 0.5:
            reason_parts.append(f"Strong investor title (score: {title_score:.2f})")
        if company_score > 0.6:
            reason_parts.append(f"Relevant company (score: {company_score:.2f})")
        if activity_score > 0:
            reason_parts.append(f"Has documented activity (score: {activity_score:.2f})")

        # Create or update score record
        contact_score = db.query(ContactScore).filter(
            ContactScore.lead_id == lead.id
        ).first()

        if not contact_score:
            contact_score = ContactScore(lead_id=lead.id)

        contact_score.title_score = title_score
        contact_score.company_score = company_score
        contact_score.activity_score = activity_score
        contact_score.engagement_score = engagement_score
        contact_score.total_score = total_score
        contact_score.score_reason = " | ".join(reason_parts)

        # Update lead's scores
        lead.contact_score = total_score
        lead.company_score = company_score
        lead.engagement_score = engagement_score

        db.add(contact_score)
        db.commit()

        return contact_score
