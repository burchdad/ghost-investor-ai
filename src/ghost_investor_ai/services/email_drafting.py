"""Email drafting service using AI/templates."""
from typing import Dict, Any, Optional
from ..models import Lead
import json


class EmailDraftingService:
    """Generate personalized outreach emails."""

    # Email templates with personalization placeholders
    INVESTOR_OUTREACH_TEMPLATE = """Subject: {subject}

Hi {first_name},

{opening}

{body}

{closing}

Best regards"""

    @staticmethod
    def extract_personalization_factors(lead: Lead) -> Dict[str, Any]:
        """Extract key personalization factors from a lead."""
        factors = {
            "investor_stage": "unknown",
            "key_interests": [],
            "recent_focus": None,
            "company_alignment": None,
        }

        # Infer investor stage from title
        if lead.job_title:
            title_lower = lead.job_title.lower()
            if "seed" in title_lower or "angel" in title_lower:
                factors["investor_stage"] = "seed"
            elif "series" in title_lower:
                factors["investor_stage"] = "series"
            elif "partner" in title_lower:
                factors["investor_stage"] = "established"

        return factors

    @staticmethod
    def generate_subject(lead: Lead) -> str:
        """Generate a compelling subject line."""
        factors = EmailDraftingService.extract_personalization_factors(lead)

        subject_templates = [
            f"Quick thought for {lead.first_name} re: {lead.company_name}",
            f"Opportunity at intersection of {lead.company_industry or 'your space'}",
            f"Value-add opportunity for {lead.first_name}",
            f"Wanted to get {lead.first_name}'s perspective on something",
        ]

        # Select template (in production, use model selection logic)
        return subject_templates[0] if lead.first_name else "Let's Connect"

    @staticmethod
    def generate_opening(lead: Lead) -> str:
        """Generate personalized opening."""
        openings = []

        if lead.company_name and lead.job_title:
            openings.append(
                f"I've been impressed by {lead.company_name}'s recent work in {lead.company_industry or 'the space'}."
            )

        if lead.linkedin_url:
            openings.append(
                f"I came across your profile and noticed your background in {lead.job_title.lower()}."
            )

        openings.append(f"I'm reaching out to {lead.first_name or 'you'} because...")

        return openings[0] if openings else "I'm reaching out because I think there's a great opportunity to connect."

    @staticmethod
    def generate_body(lead: Lead) -> str:
        """Generate email body with value proposition."""
        body_points = [
            "We're building something in your area of focus that aligns with emerging market trends.",
            "Early signals suggest strong market demand and founder-investor fit.",
            "I'd love to get your perspective and explore a potential partnership.",
        ]

        return "\n\n".join(body_points)

    @staticmethod
    def generate_closing(lead: Lead) -> str:
        """Generate email closing."""
        closings = [
            "Happy to jump on a quick call if this resonates.",
            "Would love to get 15 minutes on your calendar if you're interested.",
            "Let me know if you'd like to chat more about this.",
        ]

        return closings[0]

    @classmethod
    def draft_email(cls, lead: Lead) -> Dict[str, Any]:
        """Generate a complete outreach email."""
        subject = cls.generate_subject(lead)
        opening = cls.generate_opening(lead)
        body = cls.generate_body(lead)
        closing = cls.generate_closing(lead)

        email_body = cls.INVESTOR_OUTREACH_TEMPLATE.format(
            subject=subject.replace("Subject: ", ""),
            first_name=lead.first_name or "there",
            opening=opening,
            body=body,
            closing=closing,
        )

        personalization_factors = cls.extract_personalization_factors(lead)

        return {
            "subject": subject,
            "body": email_body,
            "personalization_factors": personalization_factors,
        }

    @staticmethod
    def generate_follow_up(initial_email: Dict[str, Any], sequence_number: int) -> Dict[str, Any]:
        """Generate follow-up emails for a sequence."""
        follow_up_templates = {
            1: {
                "subject": "Re: {original_subject}",
                "body_prefix": "Just following up on my previous email—",
                "body_suffix": "Happy to answer any questions.",
            },
            2: {
                "subject": "One more thought on {topic}",
                "body_prefix": "I realized I didn't mention—",
                "body_suffix": "Would love to hear your thoughts.",
            },
            3: {
                "subject": "Last attempt: {original_subject}",
                "body_prefix": "This is my last follow-up, but—",
                "body_suffix": "No worries if the timing isn't right.",
            },
        }

        template = follow_up_templates.get(sequence_number, follow_up_templates[1])

        return {
            "subject": template["subject"],
            "body_prefix": template["body_prefix"],
            "body_suffix": template["body_suffix"],
        }
