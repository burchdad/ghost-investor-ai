"""Lead enrichment adapters for multiple data sources."""
import httpx
import json
from typing import Optional, Dict, Any
from ..models import Lead, EnrichmentSourceEnum
from ..config import settings


class EnrichmentAdapter:
    """Base class for enrichment adapters."""

    async def enrich(self, lead: Lead) -> Optional[Dict[str, Any]]:
        """Enrich a lead with external data."""
        raise NotImplementedError


class ApolloEnrichmentAdapter(EnrichmentAdapter):
    """Apollo.io enrichment adapter."""

    def __init__(self):
        self.api_key = settings.apollo_api_key
        self.base_url = "https://api.apollo.io/v1"

    async def enrich(self, lead: Lead) -> Optional[Dict[str, Any]]:
        """Enrich lead using Apollo API."""
        if not self.api_key:
            return None

        try:
            async with httpx.AsyncClient() as client:
                params = {
                    "api_key": self.api_key,
                    "email": lead.email,
                }
                response = await client.get(
                    f"{self.base_url}/contacts/match",
                    params=params,
                    timeout=10.0,
                )
                
                if response.status_code == 200:
                    data = response.json()
                    contact = data.get("contact", {})

                    return {
                        "company_name": contact.get("organization_name"),
                        "company_website": contact.get("website_url"),
                        "company_size": contact.get("organization_size"),
                        "company_industry": contact.get("industry"),
                        "linkedin_url": contact.get("linkedin_url"),
                        "phone": contact.get("phone_numbers", [{}])[0].get("raw_number"),
                        "enrichment_source": EnrichmentSourceEnum.APOLLO,
                    }
        except Exception as e:
            print(f"Apollo enrichment failed for {lead.email}: {str(e)}")
            return None


class ClearbitEnrichmentAdapter(EnrichmentAdapter):
    """Clearbit enrichment adapter."""

    def __init__(self):
        self.api_key = settings.clearbit_api_key
        self.base_url = "https://person.clearbit.com/v2/combined"

    async def enrich(self, lead: Lead) -> Optional[Dict[str, Any]]:
        """Enrich lead using Clearbit API."""
        if not self.api_key:
            return None

        try:
            async with httpx.AsyncClient() as client:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                }
                response = await client.get(
                    self.base_url,
                    params={"email": lead.email},
                    headers=headers,
                    timeout=10.0,
                )

                if response.status_code == 200:
                    data = response.json()
                    company = data.get("company", {})

                    return {
                        "company_name": company.get("name"),
                        "company_website": company.get("domain"),
                        "company_size": company.get("employees"),
                        "company_industry": company.get("industry"),
                        "company_linkedin_url": company.get("linkedin", {}).get("url"),
                        "enrichment_source": EnrichmentSourceEnum.CLEARBIT,
                    }
        except Exception as e:
            print(f"Clearbit enrichment failed for {lead.email}: {str(e)}")
            return None


class PeopleDataLabsEnrichmentAdapter(EnrichmentAdapter):
    """People Data Labs enrichment adapter."""

    def __init__(self):
        self.api_key = settings.people_data_labs_api_key
        self.base_url = "https://api.peopledatalabs.com/v5/person/enrich"

    async def enrich(self, lead: Lead) -> Optional[Dict[str, Any]]:
        """Enrich lead using People Data Labs API."""
        if not self.api_key:
            return None

        try:
            async with httpx.AsyncClient() as client:
                params = {
                    "api_key": self.api_key,
                    "email": lead.email,
                }
                response = await client.get(
                    self.base_url,
                    params=params,
                    timeout=10.0,
                )

                if response.status_code == 200:
                    data = response.json()

                    company = data.get("company") or {}
                    work = data.get("work_history", [{}])[0] if data.get("work_history") else {}

                    return {
                        "company_name": company.get("name"),
                        "company_website": company.get("website"),
                        "company_size": company.get("size"),
                        "company_industry": company.get("industry"),
                        "phone": data.get("phone_numbers", [None])[0],
                        "linkedin_url": data.get("linkedin_url"),
                        "enrichment_source": EnrichmentSourceEnum.PEOPLE_DATA_LABS,
                    }
        except Exception as e:
            print(f"People Data Labs enrichment failed for {lead.email}: {str(e)}")
            return None


class EnrichmentService:
    """Main enrichment service coordinating multiple adapters."""

    def __init__(self):
        self.adapters = [
            ApolloEnrichmentAdapter(),
            ClearbitEnrichmentAdapter(),
            PeopleDataLabsEnrichmentAdapter(),
        ]

    async def enrich_lead(self, lead: Lead) -> bool:
        """
        Try enriching a lead with multiple sources.
        Returns True if enrichment was successful.
        """
        for adapter in self.adapters:
            enriched_data = await adapter.enrich(lead)
            if enriched_data:
                # Update lead with enriched data
                for key, value in enriched_data.items():
                    if hasattr(lead, key) and value:
                        setattr(lead, key, value)
                lead.is_enriched = True
                return True

        return False
