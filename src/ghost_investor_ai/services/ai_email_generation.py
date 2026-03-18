"""AI-powered email generation using OpenAI GPT-4."""
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from openai import AsyncOpenAI
from ..models import Lead, OutreachEmail, EmailTypeEnum
from ..config import settings
import re


class AIEmailGenerationService:
    """Generate personalized, contextual emails via LLM."""

    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = "gpt-4"
        self.max_retries = 3

    async def generate_first_touch_email(
        self, lead: Lead, deal_brief: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate first outreach email."""
        system_prompt = """You are an expert investor outreach specialist. 
Write concise, professional first-touch emails that:
- Immediately establish credibility and relevance
- Reference specific context about the recipient (company, industry, role)
- Clearly state the ask (e.g., brief call, strategic briefing)
- Keep to 2-3 short paragraphs
- End with specific next steps, not generic "let me know"

Format response as JSON: {"subject": "...", "body": "..."}"""

        user_message = f"""Generate a first-touch email to: 
{lead.first_name} {lead.last_name}
Title: {lead.job_title}
Company: {lead.company_name}
Industry: {lead.company_industry}
Company Size: {lead.company_size}
LinkedIn: {lead.linkedin_url}

Context: {deal_brief or 'Potential investor networking opportunity'}

Make it personalized and compelling."""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                temperature=0.7,
                max_tokens=500,
            )

            result = response.choices[0].message.content
            email_data = self._parse_email_response(result)

            return {
                "success": True,
                "subject": email_data["subject"],
                "body": email_data["body"],
                "type": EmailTypeEnum.FIRST_TOUCH,
                "model": self.model,
                "cost_estimate": self._estimate_cost(response.usage),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def generate_followup_email(
        self, lead: Lead, previous_email_body: str, context: str = ""
    ) -> Dict[str, Any]:
        """Generate follow-up email based on prior outreach."""
        system_prompt = """You are an expert investor outreach specialist.
Write effective follow-up emails that:
- Reference the original email without being too deferential
- Add new value or information since last contact
- Maintain professional tone but increase urgency slightly
- Keep to 1-2 short paragraphs
- Include a specific call-to-action with timeline

Format response as JSON: {"subject": "...", "body": "..."}"""

        user_message = f"""Generate a follow-up email to:
{lead.first_name} {lead.last_name}
Title: {lead.job_title}
Company: {lead.company_name}

Previous email:
{previous_email_body}

Additional context: {context or 'Continuing investor pipeline development'}

Create a compelling follow-up that references the earlier contact."""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                temperature=0.7,
                max_tokens=400,
            )

            result = response.choices[0].message.content
            email_data = self._parse_email_response(result)

            return {
                "success": True,
                "subject": email_data["subject"],
                "body": email_data["body"],
                "type": EmailTypeEnum.FOLLOW_UP,
                "model": self.model,
                "cost_estimate": self._estimate_cost(response.usage),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def generate_reengagement_email(
        self, lead: Lead, dormant_days: int = 30
    ) -> Dict[str, Any]:
        """Generate re-engagement email for leads not recently contacted."""
        system_prompt = """You are an expert investor outreach specialist.
Write re-engagement emails that:
- Acknowledge the time passage without apology
- Reference market developments or new deal opportunity
- Offer fresh value proposition
- Create urgency with new information/context
- Keep to 2-3 short paragraphs

Format response as JSON: {"subject": "...", "body": "..."}"""

        user_message = f"""Generate a re-engagement email to:
{lead.first_name} {lead.last_name}
Title: {lead.job_title}
Company: {lead.company_name}

Last contacted: {dormant_days} days ago

Create a compelling re-engagement that positions this as a new opportunity, 
not just a follow-up on old contact."""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                temperature=0.7,
                max_tokens=450,
            )

            result = response.choices[0].message.content
            email_data = self._parse_email_response(result)

            return {
                "success": True,
                "subject": email_data["subject"],
                "body": email_data["body"],
                "type": EmailTypeEnum.REENGAGEMENT,
                "model": self.model,
                "cost_estimate": self._estimate_cost(response.usage),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _parse_email_response(self, response_text: str) -> Dict[str, str]:
        """Extract subject and body from LLM response."""
        try:
            # Try to parse as JSON
            import json
            data = json.loads(response_text)
            return {
                "subject": data.get("subject", ""),
                "body": data.get("body", ""),
            }
        except:
            # Fallback: extract from text patterns
            lines = response_text.strip().split("\n")
            subject = ""
            body = ""

            for line in lines:
                if line.startswith("Subject:"):
                    subject = line.replace("Subject:", "").strip()
                elif line.startswith("Body:"):
                    # Everything after is body
                    idx = response_text.index("Body:")
                    body = response_text[idx + 5:].strip()
                    break

            return {"subject": subject or "Investor Opportunity", "body": body or response_text}

    def _estimate_cost(self, usage) -> float:
        """Estimate API cost for this request."""
        # GPT-4: $0.03/1K input, $0.06/1K output
        input_cost = (usage.prompt_tokens / 1000) * 0.03
        output_cost = (usage.completion_tokens / 1000) * 0.06
        return round(input_cost + output_cost, 4)
