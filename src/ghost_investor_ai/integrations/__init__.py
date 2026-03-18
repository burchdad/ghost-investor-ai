"""Integrations module."""
from .email_gmail import GmailService
from .email_outlook import OutlookService
from .email_service import EmailServiceCoordinator
from .crm_sync import GhostCRMSync

__all__ = [
    "GmailService",
    "OutlookService",
    "EmailServiceCoordinator",
    "GhostCRMSync",
]
