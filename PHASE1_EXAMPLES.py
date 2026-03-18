"""Phase 1 Feature Examples - Email, Enrichment, AI Generation, Batch Jobs."""
import httpx
import asyncio
from typing import Dict, List

BASE_URL = "http://localhost:8000/api"

# Example auth token (would be obtained via login endpoint)
AUTH_TOKEN = "your-jwt-token-here"
HEADERS = {"Authorization": f"Bearer {AUTH_TOKEN}"}


async def example_1_authorize_gmail():
    """Step 1: Authorize Gmail account."""
    print("\n=== EXAMPLE 1: Authorize Gmail ===")
    
    async with httpx.AsyncClient() as client:
        # Get authorization URL
        response = await client.post(
            f"{BASE_URL}/email-accounts/authorize/gmail",
            headers=HEADERS,
        )
        
        if response.status_code == 200:
            auth_data = response.json()
            print(f"✓ Auth URL: {auth_data['authorization_url']}")
            print("  Open this URL in browser and authorize Ghost Investor AI")
            print("  You'll be redirected with a code...")
        else:
            print(f"✗ Error: {response.json()}")


async def example_2_enrich_leads():
    """Step 2: Enrich leads using Apollo."""
    print("\n=== EXAMPLE 2: Enrich Leads in Batch ===")
    
    async with httpx.AsyncClient() as client:
        # Submit batch enrichment
        response = await client.post(
            f"{BASE_URL}/batch/enrich-leads",
            json={
                "lead_ids": [1, 2, 3, 4, 5],
                "enrichment_source": "apollo",
            },
            headers=HEADERS,
        )
        
        if response.status_code == 200:
            job_data = response.json()
            job_id = job_data["job_id"]
            print(f"✓ Job submitted: {job_id}")
            print(f"  Enriching {job_data['lead_count']} leads...")
            
            # Poll for status
            await asyncio.sleep(2)
            response = await client.get(
                f"{BASE_URL}/batch/job-status/{job_id}",
                headers=HEADERS,
            )
            status_data = response.json()
            print(f"  Status: {status_data['status']}")
            if status_data.get("result"):
                print(f"  Result: {status_data['result']}")
        else:
            print(f"✗ Error: {response.json()}")


async def example_3_generate_emails():
    """Step 3: Generate personalized first-touch emails."""
    print("\n=== EXAMPLE 3: Generate AI Emails ===")
    
    async with httpx.AsyncClient() as client:
        # First create outreach emails in draft
        print("  Creating draft emails for leads...")
        # (This would be done in advance, assuming we have outreach_email_ids)
        
        # Submit batch email generation
        response = await client.post(
            f"{BASE_URL}/batch/generate-emails",
            json={
                "outreach_email_ids": [1, 2, 3],
                "email_type": "first_touch",
            },
            headers=HEADERS,
        )
        
        if response.status_code == 200:
            job_data = response.json()
            job_id = job_data["job_id"]
            print(f"✓ Generation job submitted: {job_id}")
            print(f"  Generating {job_data['email_count']} emails...")
            print(f"  Type: {job_data['email_type']}")
            
            # Poll status
            await asyncio.sleep(3)
            response = await client.get(
                f"{BASE_URL}/batch/job-status/{job_id}",
                headers=HEADERS,
            )
            status_data = response.json()
            print(f"  Status: {status_data['status']}")
            if status_data.get("result"):
                result = status_data["result"]
                print(f"  Successful: {result.get('successful')}")
                print(f"  Failed: {result.get('failed')}")
                print(f"  Estimated cost: ${result.get('total_cost', 0):.2f}")
        else:
            print(f"✗ Error: {response.json()}")


async def example_4_launch_campaign():
    """Step 4: Launch campaign (batch send emails)."""
    print("\n=== EXAMPLE 4: Launch Campaign ===")
    
    async with httpx.AsyncClient() as client:
        # Launch campaign - this triggers batch sending
        response = await client.post(
            f"{BASE_URL}/batch/launch-campaign",
            json={"campaign_id": 1},
            headers=HEADERS,
        )
        
        if response.status_code == 200:
            campaign_data = response.json()
            job_id = campaign_data["job_id"]
            print(f"✓ Campaign launching: {campaign_data['campaign_id']}")
            print(f"  Job ID: {job_id}")
            print(f"  Sending {campaign_data['email_count']} emails...")
            print(f"  Status: {campaign_data['status']}")
            
            # Monitor status
            for i in range(5):
                await asyncio.sleep(2)
                response = await client.get(
                    f"{BASE_URL}/batch/job-status/{job_id}",
                    headers=HEADERS,
                )
                status_data = response.json()
                print(f"  Poll {i+1}: {status_data['status']}")
                if status_data['status'] == "SUCCESS":
                    print(f"  ✓ Campaign sent! {status_data['result']}")
                    break
        else:
            print(f"✗ Error: {response.json()}")


async def example_5_check_email_status():
    """Step 5: Check sent email status and opens."""
    print("\n=== EXAMPLE 5: Track Email Opens ===")
    
    async with httpx.AsyncClient() as client:
        # Get campaign to see email status
        response = await client.get(
            f"{BASE_URL}/campaigns/1",
            headers=HEADERS,
        )
        
        if response.status_code == 200:
            campaign = response.json()
            print(f"✓ Campaign: {campaign['name']}")
            print(f"  Status: {campaign.get('status')}")
            print(f"  Total emails sent: {len(campaign.get('outreach_emails', []))}")
            
            # Check individual emails
            for email in campaign.get('outreach_emails', [])[:3]:
                print(f"\n  Email to {email.get('recipient')}:")
                print(f"    Subject: {email.get('subject')[:50]}...")
                print(f"    Sent: {email.get('sent_at')}")
                if email.get('opened_at'):
                    print(f"    Opened: {email.get('opened_at')}")
                if email.get('clicked_at'):
                    print(f"    Clicked: {email.get('clicked_at')}")
        else:
            print(f"✗ Error: {response.json()}")


async def example_6_reply_handling():
    """Step 6: Fetch and classify replies."""
    print("\n=== EXAMPLE 6: Handle Replies ===")
    
    async with httpx.AsyncClient() as client:
        # Fetch replies and classify them
        response = await client.post(
            f"{BASE_URL}/batch/fetch-replies",
            json={"account_id": 1},
            headers=HEADERS,
        )
        
        if response.status_code == 200:
            job_data = response.json()
            print(f"✓ Reply processing job submitted")
            
            # Wait and check status
            await asyncio.sleep(3)
            response = await client.get(
                f"{BASE_URL}/batch/job-status/{job_data['job_id']}",
                headers=HEADERS,
            )
            
            status_data = response.json()
            if status_data['status'] == 'SUCCESS':
                result = status_data['result']
                print(f"\nReply Classification Results:")
                print(f"  Total processed: {result.get('processed')}")
                print(f"  Classified: {result.get('classified')}")
                print(f"  Breakdowns by classification:")
                # Would show INTERESTED, NOT_INTERESTED, LATER, etc.
        else:
            print(f"✗ Error: {response.json()}")


async def example_7_crm_sync():
    """Step 7: Sync to GhostCRM."""
    print("\n=== EXAMPLE 7: CRM Sync ===")
    
    async with httpx.AsyncClient() as client:
        # Activities would be synced automatically, check status
        response = await client.get(
            f"{BASE_URL}/leads/1",
            headers=HEADERS,
        )
        
        if response.status_code == 200:
            lead = response.json()
            print(f"✓ Lead: {lead.get('first_name')} {lead.get('last_name')}")
            print(f"  Email: {lead.get('email')}")
            print(f"  Company: {lead.get('company_name')}")
            print(f"  Score: {lead.get('contact_score')}")
            print(f"\n  Activity log:")
            
            # Get activities
            response = await client.get(
                f"{BASE_URL}/activities?lead_id=1",
                headers=HEADERS,
            )
            
            if response.status_code == 200:
                activities = response.json()
                for activity in activities[:5]:
                    print(f"    {activity.get('activity_type')}: {activity.get('description')}")
                    print(f"      Synced to GhostCRM: {activity.get('crm_synced')}")
        else:
            print(f"✗ Error: {response.json()}")


async def workflow_complete_campaign():
    """Complete workflow: Import → Enrich → Generate → Send → Track."""
    print("\n" + "="*60)
    print("PHASE 1 COMPLETE WORKFLOW")
    print("="*60)
    
    print("\n1️⃣ Setup: Authorize Gmail account")
    await example_1_authorize_gmail()
    
    print("\n2️⃣ Import & Enrich: Add leads and enrich with Apollo")
    await example_2_enrich_leads()
    
    print("\n3️⃣ Generate: Create personalized first-touch emails with AI")
    await example_3_generate_emails()
    
    print("\n4️⃣ Launch: Send batch campaign")
    await example_4_launch_campaign()
    
    print("\n5️⃣ Track: Monitor opens and clicks")
    await example_5_check_email_status()
    
    print("\n6️⃣ Parse: Classify incoming replies")
    await example_6_reply_handling()
    
    print("\n7️⃣ Sync: View activities synced to GhostCRM")
    await example_7_crm_sync()
    
    print("\n" + "="*60)
    print("✓ WORKFLOW COMPLETE")
    print("="*60)


if __name__ == "__main__":
    print("""
    Ghost Investor AI - Phase 1 Examples
    
    Features demonstrated:
    • Email account authorization (Gmail/Outlook)
    • Batch lead enrichment
    • AI-powered email generation
    • Batch email sending with rate limiting
    • Email open/click tracking
    • Reply classification and sentiment analysis
    • Automatic GhostCRM synchronization
    
    Requirements:
    • Running API server: uvicorn src.ghost_investor_ai.main:app
    • Redis server: redis-server
    • Celery worker: celery -A src.ghost_investor_ai.services.batch_jobs worker
    
    Update BASE_URL and AUTH_TOKEN before running.
    """)
    
    # Run examples
    asyncio.run(workflow_complete_campaign())
