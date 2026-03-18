"""Reply parsing and classification using LLM."""
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from openai import AsyncOpenAI
from ..models import SentEmail, ReplyClassification, ReplyClassificationEnum
from ..config import settings
import json


class ReplyParsingService:
    """Parse and classify email replies for automatic routing."""

    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = "gpt-4"

    async def classify_reply(self, reply_body: str, subject: str = "") -> Dict[str, Any]:
        """Classify a reply email into categories."""
        system_prompt = """You are an expert at analyzing investor replies to outreach emails.
Classify the reply into ONE category and provide confidence 0-1.

Categories:
- INTERESTED: Positive signal, wants to learn more or meet
- NOT_INTERESTED: Explicit rejection or clear lack of interest
- LATER: Interested but timing not right ("too early", "revisit in X months")
- QUESTION: Asking clarifying questions, not a commitment
- UNSUBSCRIBE: Explicitly wants off the list
- UNCLEAR: Cannot determine intent

Also extract:
- Key points or objections
- Suggested follow-up actions
- Urgency level

Return as JSON: {
  "classification": "INTERESTED|NOT_INTERESTED|LATER|QUESTION|UNSUBSCRIBE|UNCLEAR",
  "confidence": 0.0-1.0,
  "sentiment": "positive|neutral|negative",
  "key_points": ["point1", "point2"],
  "suggested_action": "string",
  "requires_human_review": true/false
}"""

        user_message = f"""Classify this email reply:

Subject: {subject}

Body:
{reply_body}

Provide classification with confidence score."""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                temperature=0.3,
                max_tokens=400,
            )

            result_text = response.choices[0].message.content
            classification_data = self._parse_classification(result_text)

            return {
                "success": True,
                "classification": classification_data,
                "model": self.model,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment of reply."""
        system_prompt = """Analyze sentiment of the given text.
Return JSON: {
  "sentiment": "positive|neutral|negative",
  "score": -1.0 to 1.0,
  "emotion": "excited|interested|neutral|frustrated|angry|dismissive"
}"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text},
                ],
                temperature=0.2,
                max_tokens=200,
            )

            result_text = response.choices[0].message.content
            sentiment_data = self._parse_sentiment(result_text)

            return {"success": True, "sentiment": sentiment_data}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def extract_action_items(self, reply_body: str, lead_name: str) -> Dict[str, Any]:
        """Extract next steps or action items from reply."""
        system_prompt = """Extract action items and next steps from the reply email.
Return JSON: {
  "action_items": [
    {
      "action": "description",
      "timeline": "immediate|this_week|next_2_weeks|next_month|undefined",
      "owner": "us|them|shared"
    }
  ],
  "suggested_task": {
    "title": "Follow-up task",
    "description": "Detailed description",
    "due_date": "Days from now",
    "priority": "high|medium|low"
  }
}"""

        user_message = f"""Extract action items from this reply from {lead_name}:

{reply_body}"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                temperature=0.3,
                max_tokens=400,
            )

            result_text = response.choices[0].message.content
            action_data = self._parse_action_items(result_text)

            return {"success": True, "actions": action_data}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _parse_classification(self, response_text: str) -> Dict[str, Any]:
        """Parse classification response."""
        try:
            data = json.loads(response_text)
            return {
                "classification": data.get("classification", "UNCLEAR"),
                "confidence": float(data.get("confidence", 0.5)),
                "sentiment": data.get("sentiment", "neutral"),
                "key_points": data.get("key_points", []),
                "suggested_action": data.get("suggested_action", ""),
                "requires_human_review": data.get("requires_human_review", False),
            }
        except:
            return {
                "classification": "UNCLEAR",
                "confidence": 0.0,
                "sentiment": "neutral",
                "key_points": [],
                "suggested_action": "",
                "requires_human_review": True,
            }

    def _parse_sentiment(self, response_text: str) -> Dict[str, Any]:
        """Parse sentiment response."""
        try:
            data = json.loads(response_text)
            return {
                "sentiment": data.get("sentiment", "neutral"),
                "score": float(data.get("score", 0.0)),
                "emotion": data.get("emotion", "neutral"),
            }
        except:
            return {"sentiment": "neutral", "score": 0.0, "emotion": "neutral"}

    def _parse_action_items(self, response_text: str) -> Dict[str, Any]:
        """Parse action items response."""
        try:
            data = json.loads(response_text)
            return {
                "action_items": data.get("action_items", []),
                "suggested_task": data.get("suggested_task", {}),
            }
        except:
            return {"action_items": [], "suggested_task": {}}
