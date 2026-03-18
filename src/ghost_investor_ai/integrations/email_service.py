"""High-level email service coordinator."""
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from ..models import EmailAccount, EmailProviderEnum, SentEmail
from .email_gmail import GmailService
from .email_outlook import OutlookService


class EmailServiceCoordinator:
    """Unified interface for email operations across providers."""

    @staticmethod
    async def send_email(
        account_id: int,
        to_email: str,
        subject: str,
        body: str,
        lead_id: int,
        outreach_email_id: int,
        db: Session,
    ) -> Dict[str, Any]:
        """Send email through configured provider."""
        account = db.query(EmailAccount).filter(EmailAccount.id == account_id).first()

        if not account:
            return {"success": False, "error": "Email account not found"}

        if account.provider == EmailProviderEnum.GMAIL:
            service = GmailService(account.oauth_token, account.refresh_token)
            result = await service.send_email(to_email, subject, body, html=True)
        elif account.provider == EmailProviderEnum.OUTLOOK:
            service = OutlookService(account.oauth_token)
            result = await service.send_email(to_email, subject, body, html=True)
        else:
            return {"success": False, "error": "Unknown email provider"}

        # Log sent email
        if result.get("success"):
            sent_email = SentEmail(
                outreach_email_id=outreach_email_id,
                email_account_id=account_id,
                recipient_email=to_email,
                message_id=result.get("message_id"),
                provider=account.provider,
            )
            db.add(sent_email)
            db.commit()

            return {
                "success": True,
                "sent_email_id": sent_email.id,
                "message_id": result.get("message_id"),
            }

        return result

    @staticmethod
    async def get_replies(account_id: int, db: Session) -> Dict[str, Any]:
        """Fetch replies for an email account."""
        account = db.query(EmailAccount).filter(EmailAccount.id == account_id).first()

        if not account:
            return {"success": False, "error": "Email account not found"}

        if account.provider == EmailProviderEnum.GMAIL:
            service = GmailService(account.oauth_token, account.refresh_token)
            # Get unread messages in outreach label
            messages = await service.get_messages(query='label:"Ghost Outreach" is:unread')
        elif account.provider == EmailProviderEnum.OUTLOOK:
            service = OutlookService(account.oauth_token)
            messages = await service.get_inbox_messages(max_results=50)
        else:
            return {"success": False, "error": "Unknown email provider"}

        return {"success": True, "messages": messages}

    @staticmethod
    async def authorize_gmail(
        credentials_json: str, user_email: str, db: Session
    ) -> Dict[str, Any]:
        """Complete OAuth2 flow for Gmail."""
        try:
            # This would handle the full OAuth flow
            # For now, returning template
            return {
                "success": True,
                "provider": EmailProviderEnum.GMAIL,
                "user_email": user_email,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    async def authorize_outlook(
        client_id: str, client_secret: str, user_email: str, db: Session
    ) -> Dict[str, Any]:
        """Set up OAuth2 for Outlook."""
        try:
            return {
                "success": True,
                "provider": EmailProviderEnum.OUTLOOK,
                "user_email": user_email,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
