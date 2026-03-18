"""GhostCRM bi-directional sync (STUB)."""
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from ..models import Lead, Activity

class GhostCRMSync:
    """Bi-directional synchronization with GhostCRM (STUB)."""

    def __init__(self):
        pass

    async def push_lead(self, lead: Lead) -> Dict[str, Any]:
        """Push lead to GhostCRM (stub)."""
        print(f"CRM SYNC (stub): Pushing lead {lead.email}")
        return {
            "success": True,
            "crm_id": f"crm_{lead.id}",
            "synced_at": None,
        }

    async def pull_lead(self, crm_id: str, db: Session) -> Optional[Lead]:
        """Fetch lead from GhostCRM (stub)."""
        print(f"CRM SYNC (stub): Pulling lead {crm_id}")
        return None

    async def push_activity(self, lead_id: int, activity: Activity) -> Dict[str, Any]:
        """Push activity to GhostCRM (stub)."""
        print(f"CRM SYNC (stub): Pushing activity for lead {lead_id}: {activity.activity_type}")
        return {
            "success": True,
            "crm_activity_id": f"activity_{activity.id}",
        }

    async def create_task(
        self, lead_id: int, task_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create follow-up task in CRM (stub)."""
        print(f"CRM SYNC (stub): Creating task for lead {lead_id}: {task_data.get('title')}")
        return {
            "success": True,
            "task_id": f"task_{lead_id}",
        }

    async def sync_lead_status(self, lead_id: int, status: str) -> Dict[str, Any]:
        """Update lead status in CRM (stub)."""
        print(f"CRM SYNC (stub): Syncing lead {lead_id} status to {status}")
        return {"success": True}
