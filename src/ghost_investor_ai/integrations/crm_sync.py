"""GhostCRM bi-directional sync."""
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from ..models import Lead, Activity
from ..config import settings
import httpx
import json


class GhostCRMSync:
    """Bi-directional synchronization with GhostCRM."""

    def __init__(self):
        self.base_url = settings.ghostcrm_base_url
        self.api_key = settings.ghostcrm_api_key

    async def push_lead(self, lead: Lead) -> Dict[str, Any]:
        """Push lead to GhostCRM."""
        if not self.base_url or not self.api_key:
            return {"success": False, "error": "GhostCRM not configured"}

        try:
            payload = {
                "email": lead.email,
                "first_name": lead.first_name,
                "last_name": lead.last_name,
                "company_name": lead.company_name,
                "title": lead.job_title,
                "linkedin_url": lead.linkedin_url,
                "phone": lead.phone,
                "contact_score": lead.contact_score,
                "is_enriched": lead.is_enriched,
                "enrichment_source": lead.enrichment_source.value if lead.enrichment_source else None,
                "company_industry": lead.company_industry,
                "company_size": lead.company_size,
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/leads",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json=payload,
                    timeout=10.0,
                )

                if response.status_code in [200, 201]:
                    data = response.json()
                    return {
                        "success": True,
                        "crm_id": data.get("id"),
                        "synced_at": data.get("updated_at"),
                    }
                else:
                    return {
                        "success": False,
                        "error": f"CRM returned {response.status_code}",
                    }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def pull_lead(self, crm_id: str, db: Session) -> Optional[Lead]:
        """Fetch lead from GhostCRM and update local record."""
        if not self.base_url or not self.api_key:
            return None

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/leads/{crm_id}",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=10.0,
                )

                if response.status_code == 200:
                    crm_data = response.json()

                    # Find and update local lead
                    lead = db.query(Lead).filter(Lead.email == crm_data["email"]).first()
                    if lead:
                        lead.first_name = crm_data.get("first_name", lead.first_name)
                        lead.last_name = crm_data.get("last_name", lead.last_name)
                        lead.job_title = crm_data.get("title", lead.job_title)
                        # Update other fields as needed
                        db.commit()
                        return lead

        except Exception as e:
            pass

        return None

    async def push_activity(self, lead_id: int, activity: Activity) -> Dict[str, Any]:
        """Push activity to GhostCRM."""
        if not self.base_url or not self.api_key:
            return {"success": False, "error": "GhostCRM not configured"}

        try:
            payload = {
                "lead_id": lead_id,
                "type": activity.activity_type,
                "description": activity.description,
                "timestamp": activity.event_timestamp.isoformat() if activity.event_timestamp else None,
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/activities",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json=payload,
                    timeout=10.0,
                )

                if response.status_code in [200, 201]:
                    data = response.json()
                    return {
                        "success": True,
                        "crm_activity_id": data.get("id"),
                    }
                else:
                    return {"success": False, "error": f"CRM returned {response.status_code}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def create_task(
        self, lead_id: int, task_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create follow-up task in CRM."""
        if not self.base_url or not self.api_key:
            return {"success": False, "error": "GhostCRM not configured"}

        try:
            payload = {
                "lead_id": lead_id,
                "title": task_data.get("title"),
                "description": task_data.get("description"),
                "due_date": task_data.get("due_date"),
                "priority": task_data.get("priority", "medium"),
                "type": "email_follow_up",
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/tasks",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json=payload,
                    timeout=10.0,
                )

                if response.status_code in [200, 201]:
                    data = response.json()
                    return {
                        "success": True,
                        "task_id": data.get("id"),
                    }
                else:
                    return {"success": False, "error": f"CRM returned {response.status_code}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def sync_lead_status(self, lead_id: int, status: str) -> Dict[str, Any]:
        """Update lead status in CRM."""
        if not self.base_url or not self.api_key:
            return {"success": False, "error": "GhostCRM not configured"}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.patch(
                    f"{self.base_url}/api/leads/{lead_id}/status",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={"status": status},
                    timeout=10.0,
                )

                if response.status_code == 200:
                    return {"success": True}
                else:
                    return {"success": False, "error": f"CRM returned {response.status_code}"}

        except Exception as e:
            return {"success": False, "error": str(e)}
