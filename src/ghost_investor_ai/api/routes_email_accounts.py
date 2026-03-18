"""API routes for email account management."""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import EmailAccount, User, EmailProviderEnum
from ..auth import get_current_user
from ..database import get_db
from ..config import settings
import httpx

router = APIRouter(prefix="/api/email-accounts", tags=["email"])


class EmailAccountSchema:
    """Email account request/response schemas."""
    
    user_email: str
    provider: str  # gmail or outlook


@router.post("/authorize/gmail")
async def authorize_gmail(
    authorization_url: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get Gmail OAuth authorization URL."""
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(status_code=400, detail="Gmail not configured")

    from google_auth_oauthlib.flow import InstalledAppFlow
    
    flow = InstalledAppFlow.from_client_secrets_file(
        settings.google_credentials_json,
        scopes=["https://www.googleapis.com/auth/gmail.modify"],
    )
    
    auth_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
    )
    
    return {
        "authorization_url": auth_url,
        "state": state,
    }


@router.post("/authorize/gmail/callback")
async def gmail_callback(
    code: str,
    state: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Handle Gmail OAuth callback."""
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(status_code=400, detail="Gmail not configured")

    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
        
        flow = InstalledAppFlow.from_client_secrets_file(
            settings.google_credentials_json,
            scopes=["https://www.googleapis.com/auth/gmail.modify"],
        )
        
        flow.fetch_token(code=code)
        credentials = flow.credentials
        
        # Store in database
        email_account = EmailAccount(
            user_id=current_user.id,
            email_address=current_user.email,
            provider=EmailProviderEnum.GMAIL,
            oauth_token=credentials.token,
            refresh_token=credentials.refresh_token,
        )
        
        db.add(email_account)
        db.commit()
        
        return {
            "success": True,
            "message": "Gmail account authorized",
            "email_account_id": email_account.id,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/")
async def list_email_accounts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List email accounts for current user."""
    accounts = (
        db.query(EmailAccount)
        .filter(EmailAccount.user_id == current_user.id)
        .all()
    )
    
    return {
        "accounts": [
            {
                "id": acc.id,
                "email": acc.email_address,
                "provider": acc.provider.value,
                "authorized_at": acc.created_at.isoformat(),
            }
            for acc in accounts
        ]
    }


@router.delete("/{account_id}")
async def delete_email_account(
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove an email account."""
    account = (
        db.query(EmailAccount)
        .filter(
            EmailAccount.id == account_id,
            EmailAccount.user_id == current_user.id,
        )
        .first()
    )
    
    if not account:
        raise HTTPException(status_code=404, detail="Email account not found")
    
    db.delete(account)
    db.commit()
    
    return {"success": True, "message": "Email account deleted"}


@router.post("/{account_id}/test-connection")
async def test_email_connection(
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Test email account connection."""
    account = (
        db.query(EmailAccount)
        .filter(
            EmailAccount.id == account_id,
            EmailAccount.user_id == current_user.id,
        )
        .first()
    )
    
    if not account:
        raise HTTPException(status_code=404, detail="Email account not found")
    
    try:
        if account.provider == EmailProviderEnum.GMAIL:
            from ..integrations.email_gmail import GmailService
            
            service = GmailService(account.oauth_token, account.refresh_token)
            # Simple test: fetch message list
            messages = await service.get_messages(max_results=1)
            return {"success": True, "message": "Gmail connection successful"}
        
        elif account.provider == EmailProviderEnum.OUTLOOK:
            from ..integrations.email_outlook import OutlookService
            
            service = OutlookService(account.oauth_token)
            messages = await service.get_inbox_messages(max_results=1)
            return {"success": True, "message": "Outlook connection successful"}
        
        else:
            return {"success": False, "message": "Unknown provider"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}
