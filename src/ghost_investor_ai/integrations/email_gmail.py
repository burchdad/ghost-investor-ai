"""Gmail API integration for sending and tracking emails."""
import base64
import json
from typing import Optional, List, Dict, Any
from datetime import datetime
from email.mime.text import MIMEText
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


class GmailService:
    """Gmail API email service integration."""

    SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]

    def __init__(self, oauth_token: str, refresh_token: Optional[str] = None):
        """Initialize Gmail service with OAuth credentials."""
        self.oauth_token = oauth_token
        self.refresh_token = refresh_token
        self.service = self._build_service()

    def _build_service(self):
        """Build Gmail API service client."""
        creds = Credentials(token=self.oauth_token, refresh_token=self.refresh_token)
        return build("gmail", "v1", credentials=creds)

    async def send_email(self, to_email: str, subject: str, body: str, html: bool = False) -> Dict[str, Any]:
        """Send an email via Gmail API."""
        try:
            message = MIMEText(body, "html" if html else "plain")
            message["to"] = to_email
            message["subject"] = subject

            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
            send_message = {"raw": raw}

            result = self.service.users().messages().send(userId="me", body=send_message).execute()

            return {
                "success": True,
                "message_id": result.get("id"),
                "thread_id": result.get("threadId"),
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    async def get_messages(self, query: str = "", max_results: int = 10) -> List[Dict[str, Any]]:
        """Fetch emails matching query."""
        try:
            results = (
                self.service.users()
                .messages()
                .list(userId="me", q=query, maxResults=max_results)
                .execute()
            )
            messages = results.get("messages", [])

            detailed_messages = []
            for message in messages:
                msg = (
                    self.service.users()
                    .messages()
                    .get(userId="me", id=message["id"], format="full")
                    .execute()
                )
                detailed_messages.append(self._parse_message(msg))

            return detailed_messages
        except Exception as e:
            return []

    async def get_replies_to_email(self, original_message_id: str) -> List[Dict[str, Any]]:
        """Get replies to a sent email (uses thread)."""
        try:
            original = (
                self.service.users()
                .messages()
                .get(userId="me", id=original_message_id, format="minimal")
                .execute()
            )
            thread_id = original.get("threadId")

            thread = (
                self.service.users()
                .threads()
                .get(userId="me", id=thread_id)
                .execute()
            )
            messages = thread.get("messages", [])

            # Return all messages after the original
            replies = []
            found_original = False
            for msg in messages:
                if msg["id"] == original_message_id:
                    found_original = True
                elif found_original:
                    replies.append(self._parse_message(msg))

            return replies
        except Exception as e:
            return []

    def _parse_message(self, message: Dict) -> Dict[str, Any]:
        """Parse Gmail message format into readable structure."""
        headers = message["payload"]["headers"]
        subject = next((h["value"] for h in headers if h["name"] == "Subject"), "")
        from_addr = next((h["value"] for h in headers if h["name"] == "From"), "")
        date_str = next((h["value"] for h in headers if h["name"] == "Date"), "")

        body = ""
        if "parts" in message["payload"]:
            for part in message["payload"]["parts"]:
                if part["mimeType"] == "text/plain":
                    data = part["body"].get("data", "")
                    body = base64.urlsafe_b64decode(data).decode() if data else ""
                    break
        else:
            data = message["payload"]["body"].get("data", "")
            body = base64.urlsafe_b64decode(data).decode() if data else ""

        return {
            "id": message["id"],
            "thread_id": message.get("threadId"),
            "subject": subject,
            "from": from_addr,
            "date": date_str,
            "body": body,
            "labels": message.get("labelIds", []),
        }

    async def add_label(self, message_id: str, label_name: str):
        """Add label to message (for tracking outreach emails)."""
        try:
            label_id = await self._get_or_create_label(label_name)
            self.service.users().messages().modify(
                userId="me",
                id=message_id,
                body={"addLabelIds": [label_id]},
            ).execute()
            return True
        except Exception:
            return False

    async def _get_or_create_label(self, label_name: str) -> str:
        """Get label ID or create it if doesn't exist."""
        labels = self.service.users().labels().list(userId="me").execute()
        for label in labels["labels"]:
            if label["name"] == label_name:
                return label["id"]

        # Create label if not found
        new_label = self.service.users().labels().create(
            userId="me",
            body={"name": label_name},
        ).execute()
        return new_label["id"]
