"""Lead import service for handling CSV, manual, and API imports."""
import csv
import io
from typing import List, Optional
from sqlalchemy.orm import Session
from ..models import Lead, EnrichmentSourceEnum


class LeadImportService:
    """Handle lead imports from multiple sources."""

    @staticmethod
    def import_from_csv(csv_content: str, db: Session) -> dict:
        """
        Import leads from CSV content.
        
        Expected columns: email, first_name, last_name, company_name, job_title, linkedin_url, phone
        """
        csv_reader = csv.DictReader(io.StringIO(csv_content))
        imported = 0
        skipped = 0
        errors = []

        for row in csv_reader:
            try:
                # Validate required fields
                if not row.get("email"):
                    skipped += 1
                    errors.append(f"Row {imported + skipped + 1}: Missing email")
                    continue

                # Check if lead already exists
                existing = db.query(Lead).filter(Lead.email == row["email"]).first()
                if existing:
                    skipped += 1
                    continue

                lead = Lead(
                    email=row["email"],
                    first_name=row.get("first_name", ""),
                    last_name=row.get("last_name", ""),
                    company_name=row.get("company_name", ""),
                    job_title=row.get("job_title", ""),
                    linkedin_url=row.get("linkedin_url", ""),
                    phone=row.get("phone", ""),
                    enrichment_source=EnrichmentSourceEnum.MANUAL,
                )
                db.add(lead)
                imported += 1

            except Exception as e:
                errors.append(f"Row {imported + skipped + 1}: {str(e)}")
                skipped += 1

        db.commit()

        return {
            "imported": imported,
            "skipped": skipped,
            "errors": errors,
            "total_processed": imported + skipped,
        }

    @staticmethod
    def import_manual(leads_data: List[dict], db: Session) -> dict:
        """Import leads provided as a list of dictionaries."""
        imported = 0
        skipped = 0

        for lead_data in leads_data:
            # Validate required fields
            if not lead_data.get("email"):
                skipped += 1
                continue

            # Check if lead already exists
            existing = db.query(Lead).filter(Lead.email == lead_data["email"]).first()
            if existing:
                skipped += 1
                continue

            lead = Lead(
                email=lead_data["email"],
                first_name=lead_data.get("first_name", ""),
                last_name=lead_data.get("last_name", ""),
                company_name=lead_data.get("company_name", ""),
                job_title=lead_data.get("job_title", ""),
                linkedin_url=lead_data.get("linkedin_url", ""),
                phone=lead_data.get("phone", ""),
                enrichment_source=EnrichmentSourceEnum.MANUAL,
            )
            db.add(lead)
            imported += 1

        db.commit()

        return {
            "imported": imported,
            "skipped": skipped,
        }
