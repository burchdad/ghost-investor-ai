"""Example usage and integration patterns."""
import httpx
import asyncio
import json


BASE_URL = "http://localhost:8000"


async def example_workflow():
    """Example of a complete lead enrichment and outreach workflow."""
    
    async with httpx.AsyncClient() as client:
        print("=== Ghost Investor AI Example Workflow ===\n")

        # 1. Create a lead
        print("1. Creating a new lead...")
        lead_data = {
            "email": "vp@techfund.com",
            "first_name": "Alex",
            "last_name": "Chen",
            "company_name": "TechFund Partners",
            "job_title": "Principal, Early Stage Ventures",
            "linkedin_url": "https://linkedin.com/in/alexchen",
            "phone": "+1-555-0123",
        }

        response = await client.post(f"{BASE_URL}/api/leads/", json=lead_data)
        if response.status_code != 200:
            print(f"Error: {response.json()}")
            return

        lead = response.json()
        lead_id = lead["id"]
        print(f"✓ Lead created: {lead_id}\n")

        # 2. Trigger enrichment
        print("2. Triggering enrichment...")
        response = await client.post(f"{BASE_URL}/api/enrichment/enrich/{lead_id}")
        print(f"✓ Enrichment started\n")

        # 3. Get contact score
        print("3. Getting contact score...")
        response = await client.get(f"{BASE_URL}/api/enrichment/score/{lead_id}")
        if response.status_code == 200:
            score = response.json()
            print(f"✓ Contact Score: {score['total_score']:.2f}/1.0")
            print(f"  - Title Score: {score['title_score']:.2f}")
            print(f"  - Company Score: {score['company_score']:.2f}")
            print(f"  - Reason: {score['score_reason']}\n")

        # 4. Create outreach campaign
        print("4. Creating outreach campaign...")
        campaign_data = {
            "name": "Q1 2026 Seed Investors",
            "description": "Outreach to early-stage VC investors",
            "follow_up_delays": [0, 48, 120],  # immediate, 2 days, 5 days
        }

        response = await client.post(f"{BASE_URL}/api/campaigns/", json=campaign_data)
        if response.status_code != 200:
            print(f"Error: {response.json()}")
            return

        campaign = response.json()
        campaign_id = campaign["id"]
        print(f"✓ Campaign created: {campaign_id}\n")

        # 5. Add lead to campaign (generates email)
        print("5. Adding lead to campaign with generated email...")
        response = await client.post(
            f"{BASE_URL}/api/campaigns/{campaign_id}/add-lead/{lead_id}"
        )
        if response.status_code != 200:
            print(f"Error: {response.json()}")
            return

        email_result = response.json()
        print(f"✓ Lead added to campaign")
        print(f"  Subject: {email_result['subject']}\n")

        # 6. Schedule campaign
        print("6. Scheduling campaign...")
        response = await client.post(f"{BASE_URL}/api/campaigns/{campaign_id}/schedule")
        schedule = response.json()
        print(f"✓ Campaign scheduled")
        print(f"  Total emails to send: {schedule['send_count']}\n")

        # 7. Log activity
        print("7. Logging activity (email sent)...")
        activity_data = {
            "lead_id": lead_id,
            "activity_type": "email_sent",
            "description": "Initial outreach sent via campaign Q1 2026 Seed Investors",
        }

        response = await client.post(f"{BASE_URL}/api/activities/", json=activity_data)
        activity = response.json()
        print(f"✓ Activity logged: {activity['id']}\n")

        # 8. Get lead timeline
        print("8. Getting lead timeline...")
        response = await client.get(f"{BASE_URL}/api/activities/lead/{lead_id}")
        timeline = response.json()
        print(f"✓ Lead timeline (last 3 activities):")
        for act in timeline["activities"][:3]:
            print(f"  - {act['type']}: {act['description'][:60]}...")

        print("\n=== Workflow Complete ===")


async def example_bulk_import():
    """Example of bulk importing leads from CSV."""
    
    csv_content = """email,first_name,last_name,company_name,job_title,linkedin_url,phone
investor1@fund.com,Jane,Smith,Venture Fund A,Partner,https://linkedin.com/in/janesmith,+1-555-0001
investor2@fund.com,Bob,Johnson,Tech Ventures,Managing Partner,https://linkedin.com/in/bobjohnson,+1-555-0002
investor3@fund.com,Sarah,Williams,Growth Capital,Principal,https://linkedin.com/in/sarahwilliams,+1-555-0003
"""

    async with httpx.AsyncClient() as client:
        print("=== Bulk Import Example ===\n")

        print("Importing leads from CSV...")
        response = await client.post(
            f"{BASE_URL}/api/leads/import/csv",
            json={"csv_content": csv_content},
        )

        result = response.json()
        print(f"✓ Import complete:")
        print(f"  - Imported: {result['imported']}")
        print(f"  - Skipped: {result['skipped']}")
        if result["errors"]:
            print(f"  - Errors: {len(result['errors'])}")
            for error in result["errors"][:3]:
                print(f"    • {error}")


async def example_list_leads():
    """Example of listing and filtering leads."""
    
    async with httpx.AsyncClient() as client:
        print("=== List Leads Example ===\n")

        response = await client.get(
            f"{BASE_URL}/api/leads/",
            params={"skip": 0, "limit": 10},
        )

        leads = response.json()
        print(f"Found {len(leads)} leads:\n")

        for lead in leads:
            print(f"• {lead['first_name']} {lead['last_name']}")
            print(f"  Email: {lead['email']}")
            print(f"  Company: {lead['company_name']}")
            print(f"  Contact Score: {lead['contact_score']:.2f}")
            print(f"  Enriched: {'Yes' if lead['is_enriched'] else 'No'}\n")


async def main():
    """Run examples."""
    print("Note: Make sure the API server is running at http://localhost:8000\n")

    try:
        # Health check
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/health")
            if response.status_code != 200:
                print("Error: API server is not responding")
                print("Start the server with: python cli.py run")
                return

        # Run examples
        await example_workflow()
        print("\n" + "=" * 50 + "\n")
        await example_bulk_import()

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
