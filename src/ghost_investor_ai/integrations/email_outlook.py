"""Outlook/Microsoft Graph integration for sending and tracking emails."""
from typing import Optional, List, Dict, Any
from datetime import datetime
from msgraph.core import GraphClient
from azure.identity import ClientSecretCredential


class OutlookService:
    """Outlook/Microsoft Graph email service integration."""

    def __init__(self, access_token: str):
        """Initialize Outlook service."""
        self.access_token = access_token
        self.client = self._build_client()

    def _build_client(self) -> GraphClient:
        """Build Microsoft Graph client."""
        # The token should be pre-obtained via OAuth2 flow
        client = GraphClient(credential=lambda: self.access_token)
        return client

    async def send_email(
        self, to_email: str, subject: str, body: str, html: bool = True
    ) -> Dict[str, Any]:
        """Send email via Outlook."""
        try:
            message = {
                "subject": subject,
                "body": {
                    "contentType": "HTML" if html else "text",
                    "content": body,
                },
                "toRecipients": [
                    {
                        "emailAddress": {
                            "address": to_email,
                        }
                    }
                ],
            }

            response = self.client.post(
                "/me/sendMail",
                content={"message": message},
            ).json()

            return {
                "success": True,
                "message": "Email sent successfully",
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    async def get_inbox_messages(self, filter_query: str = "", max_results: int = 10) -> List[Dict[str, Any]]:
        """Fetch emails from inbox."""
        try:
            request = f"/me/mailFolders/inbox/messages?$top={max_results}"
            if filter_query:
                request += f"&$filter={filter_query}"

            response = self.client.get(request).json()
            messages = response.get("value", [])

            return [self._parse_message(msg) for msg in messages]
        except Exception as e:
            return []

    async def get_message_replies(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get all messages in a conversation."""
        try:
            request = f"/me/mailFolders/inbox/messages?$filter=conversationId eq '{conversation_id}'"
            response = self.client.get(request).json()
            messages = response.get("value", [])

            return [self._parse_message(msg) for msg in messages]
        except Exception:
            return []

    def _parse_message(self, message: Dict) -> Dict[str, Any]:
        """Parse Outlook message format."""
        return {
            "id": message.get("id"),
            "subject": message.get("subject"),
            "from": message.get("from", {}).get("emailAddress", {}).get("address"),
            "body": message.get("body", {}).get("content"),
            "received_date": message.get("receivedDateTime"),
            "conversation_id": message.get("conversationId"),
            "is_read": message.get("isRead"),
        }

    async def create_folder(self, folder_name: str) -> Optional[str]:
        """Create a folder for organizing outreach emails."""
        try:
            response = self.client.post(
                "/me/mailFolders",
                content={"displayName": folder_name},
            ).json()
            return response.get("id")
        except Exception:
            return None

    async def move_message_to_folder(self, message_id: str, folder_id: str) -> bool:
        """Move email to specific folder."""
        try:
            self.client.patch(
                f"/me/messages/{message_id}",
                content={"parentFolderId": folder_id},
            )
            return True
        except Exception:
            return False
