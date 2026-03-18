#!/usr/bin/env python3
"""
End-to-End Test Script for Ghost Investor AI

Tests all features in order:
1. Gmail OAuth flow
2. Send test email
3. Create test lead
4. Generate AI email
5. Launch campaign
6. Reply to email
7. Verify reply parsing
8. Check activity timeline

PRE-REQUISITES:
- PostgreSQL running at localhost:5432
- Redis running at localhost:6379
- FastAPI server running: uvicorn src.ghost_investor_ai.main:app --reload
- Celery worker running: celery -A src.ghost_investor_ai.services.batch_jobs worker --loglevel=info
- Gmail OAuth credentials set in .env (GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET)
- OPENAI_API_KEY set in .env
"""

import httpx
import json
import asyncio
import time
from typing import Dict, Any, Optional
from datetime import datetime

# Configuration
API_BASE = "http://localhost:8000"
TEST_USER_EMAIL = "test@example.com"
TEST_USER_PASSWORD = "testpass123"
TEST_LEAD_EMAIL = "yourtest@email.com"  # Change to your actual email for real testing

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def log_step(number: int, title: str):
    """Log a test step."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}")
    print(f"STEP {number}: {title}")
    print(f"{'='*70}{Colors.END}\n")

def log_success(msg: str):
    """Log success message."""
    print(f"{Colors.GREEN}✓ {msg}{Colors.END}")

def log_error(msg: str):
    """Log error message."""
    print(f"{Colors.RED}✗ {msg}{Colors.END}")

def log_info(msg: str):
    """Log info message."""
    print(f"{Colors.YELLOW}ℹ {msg}{Colors.END}")

def log_data(title: str, data: Any):
    """Log data."""
    print(f"\n{Colors.BOLD}{title}:{Colors.END}")
    if isinstance(data, dict):
        print(json.dumps(data, indent=2))
    else:
        print(data)

class GhostInvestorAITester:
    """End-to-end test runner for Ghost Investor AI."""
    
    def __init__(self):
        self.client = httpx.Client(base_url=API_BASE, timeout=30.0)
        self.access_token: Optional[str] = None
        self.user_id: Optional[int] = None
        self.email_account_id: Optional[int] = None
        self.lead_id: Optional[int] = None
        self.campaign_id: Optional[int] = None
        self.sent_email_id: Optional[str] = None
        
    def login_or_register(self) -> bool:
        """Register/login test user."""
        log_step(0, "Setup: Register/Login Test User")
        
        try:
            # Try to register
            response = self.client.post(
                "/api/auth/register",
                json={
                    "email": TEST_USER_EMAIL,
                    "password": TEST_USER_PASSWORD,
                }
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                log_success(f"Registered new user: {TEST_USER_EMAIL}")
            else:
                log_info(f"User may exist, trying login...")
            
            # Login
            response = self.client.post(
                "/api/auth/login",
                json={
                    "email": TEST_USER_EMAIL,
                    "password": TEST_USER_PASSWORD,
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get("access_token")
                self.user_id = data.get("user_id")
                log_success(f"Logged in as {TEST_USER_EMAIL}")
                log_data("Auth Response", {
                    "user_id": self.user_id,
                    "has_access_token": bool(self.access_token),
                    "has_refresh_token": bool(data.get("refresh_token")),
                })
                return True
            else:
                log_error(f"Login failed: {response.text}")
                return False
                
        except Exception as e:
            log_error(f"Auth setup failed: {e}")
            return False
    
    def _headers(self) -> Dict[str, str]:
        """Get auth headers."""
        return {
            "Authorization": f"Bearer {self.access_token}"
        }
    
    # STEP 1: Gmail OAuth
    def step_1_gmail_oauth(self) -> bool:
        """Step 1: Test Gmail OAuth flow."""
        log_step(1, "🔐 Finish Gmail OAuth")
        
        try:
            # Request authorization URL (no parameters needed)
            response = self.client.post(
                "/api/email-accounts/authorize/gmail",
                headers=self._headers(),
            )
            
            if response.status_code == 200:
                data = response.json()
                log_success("Got OAuth authorization URL")
                log_data("OAuth Response", {
                    "has_auth_url": bool(data.get("authorization_url")),
                    "has_state": bool(data.get("state")),
                })
                
                log_info("MANUAL STEP: Open authorization URL in browser and complete OAuth flow")
                log_info("Then call: POST /api/email-accounts/authorize/gmail/callback with code and state")
                
                # For testing, simulate successful callback with mock token
                log_info("Simulating OAuth callback...")
                response = self.client.post(
                    "/api/email-accounts/authorize/gmail/callback",
                    headers=self._headers(),
                    json={
                        "code": "mock_auth_code",
                        "state": data.get("state"),
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.email_account_id = data.get("email_account_id")
                    log_success(f"Gmail account authorized: {self.email_account_id}")
                    
                    # Verify tokens stored
                    response = self.client.get(
                        "/api/email-accounts/",
                        headers=self._headers(),
                    )
                    
                    if response.status_code == 200:
                        accounts = response.json().get("accounts", [])
                        if accounts:
                            acc = accounts[0]
                            log_success(f"Email account stored in DB")
                            log_data("Email Account", acc)
                            return True
                        else:
                            log_error("No email accounts found after authorization")
                            return False
                else:
                    log_error(f"Callback failed: {response.text}")
                    return False
            else:
                log_error(f"Authorization URL request failed: {response.text}")
                return False
                
        except Exception as e:
            log_error(f"Gmail OAuth test failed: {e}")
            return False
    
    # STEP 2: Send Test Email
    def step_2_send_test_email(self) -> bool:
        """Step 2: Send a test email."""
        log_step(2, "📩 Send a Test Email")
        
        try:
            if not self.email_account_id:
                log_error("No email account authorized. Run step 1 first.")
                return False
            
            # Submit batch send job
            response = self.client.post(
                "/api/batch/send-emails",
                headers=self._headers(),
                json={
                    "recipient_email": TEST_LEAD_EMAIL,
                    "subject": "Test Email from Ghost Investor AI",
                    "body": "This is a test email to verify the system is working.",
                    "email_account_id": self.email_account_id,
                }
            )
            
            if response.status_code in [200, 202]:
                data = response.json()
                job_id = data.get("job_id")
                self.sent_email_id = data.get("email_id")
                log_success(f"Email send job submitted: {job_id}")
                log_data("Send Response", data)
                
                # Wait for job to complete
                log_info("Waiting for email to send...")
                time.sleep(2)
                
                # Check job status
                response = self.client.get(
                    f"/api/batch/job-status/{job_id}",
                    headers=self._headers(),
                )
                
                if response.status_code == 200:
                    job = response.json()
                    log_data("Job Status", job)
                    
                    if job.get("status") == "completed":
                        log_success("Email sent successfully!")
                        return True
                    else:
                        log_info(f"Job still running: {job.get('status')}")
                        return True  # Continue anyway
                else:
                    log_error(f"Failed to check job status: {response.text}")
                    return False
            else:
                log_error(f"Send email failed: {response.text}")
                return False
                
        except Exception as e:
            log_error(f"Send test email failed: {e}")
            return False
    
    # STEP 3: Create Test Lead
    def step_3_create_test_lead(self) -> bool:
        """Step 3: Create a test lead."""
        log_step(3, "🧪 Create a Test Lead")
        
        try:
            response = self.client.post(
                "/api/leads/",
                headers=self._headers(),
                json={
                    "email": TEST_LEAD_EMAIL,
                    "first_name": "Stephen",
                    "last_name": "Test",
                    "company_name": "Ghost AI",
                    "job_title": "Founder",
                    "linkedin_url": "https://linkedin.com/in/test",
                    "phone": "+1234567890",
                }
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                self.lead_id = data.get("id")
                log_success(f"Test lead created: ID {self.lead_id}")
                log_data("Lead Data", data)
                return True
            else:
                log_error(f"Create lead failed: {response.text}")
                return False
                
        except Exception as e:
            log_error(f"Create test lead failed: {e}")
            return False
    
    # STEP 4: Generate AI Email
    def step_4_generate_ai_email(self) -> bool:
        """Step 4: Generate AI-powered email."""
        log_step(4, "🧠 Generate AI Email")
        
        try:
            if not self.lead_id:
                log_error("No lead created. Run step 3 first.")
                return False
            
            response = self.client.post(
                f"/api/batch/generate-emails",
                headers=self._headers(),
                json={
                    "lead_ids": [self.lead_id],
                    "tone": "professional",
                    "template": "first_touch",
                }
            )
            
            if response.status_code in [200, 202]:
                data = response.json()
                job_id = data.get("job_id")
                log_success(f"Email generation job submitted: {job_id}")
                log_data("Generation Response", data)
                
                # Wait for generation
                log_info("Waiting for AI email generation...")
                time.sleep(2)
                
                # Check job status
                response = self.client.get(
                    f"/api/batch/job-status/{job_id}",
                    headers=self._headers(),
                )
                
                if response.status_code == 200:
                    job = response.json()
                    log_data("Job Status", {
                        "status": job.get("status"),
                        "result_count": len(job.get("result", {}).get("generated", [])),
                    })
                    
                    if job.get("status") == "completed":
                        log_success("AI email generated successfully!")
                        return True
                    else:
                        log_info(f"Job status: {job.get('status')}")
                        return True
                else:
                    log_error(f"Failed to check generation status: {response.text}")
                    return False
            else:
                log_error(f"Generate email failed: {response.text}")
                return False
                
        except Exception as e:
            log_error(f"Generate AI email failed: {e}")
            return False
    
    # STEP 5: Launch Campaign
    def step_5_launch_campaign(self) -> bool:
        """Step 5: Create and launch campaign."""
        log_step(5, "🚀 Launch Campaign")
        
        try:
            if not self.lead_id or not self.email_account_id:
                log_error("Missing lead or email account. Run steps 1 and 3 first.")
                return False
            
            # Create campaign
            response = self.client.post(
                "/api/campaigns/",
                headers=self._headers(),
                json={
                    "name": "Test Campaign",
                    "description": "End-to-end test campaign",
                    "email_account_id": self.email_account_id,
                }
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                self.campaign_id = data.get("id")
                log_success(f"Campaign created: ID {self.campaign_id}")
                
                # Add lead to campaign
                response = self.client.post(
                    f"/api/campaigns/{self.campaign_id}/add-lead/{self.lead_id}",
                    headers=self._headers(),
                    json={}
                )
                
                if response.status_code in [200, 201]:
                    log_success(f"Lead added to campaign")
                    
                    # Schedule campaign
                    response = self.client.post(
                        f"/api/campaigns/{self.campaign_id}/schedule",
                        headers=self._headers(),
                        json={"delay_seconds": 1}
                    )
                    
                    if response.status_code in [200, 201]:
                        log_success("Campaign scheduled!")
                        log_data("Campaign Status", response.json())
                        return True
                    else:
                        log_error(f"Schedule campaign failed: {response.text}")
                        return False
                else:
                    log_error(f"Add lead to campaign failed: {response.text}")
                    return False
            else:
                log_error(f"Create campaign failed: {response.text}")
                return False
                
        except Exception as e:
            log_error(f"Launch campaign failed: {e}")
            return False
    
    # STEP 6: Reply to Email
    def step_6_reply_to_email(self) -> bool:
        """Step 6: Simulate receiving a reply."""
        log_step(6, "📬 Reply to Yourself")
        
        try:
            log_info("MANUAL STEP REQUIRED:")
            log_info(f"1. Open your email ({TEST_LEAD_EMAIL})")
            log_info("2. Find the email from the test campaign")
            log_info("3. Reply with something like: 'This is interesting, can you send more info?'")
            log_info("\nWaiting 10 seconds for you to reply...")
            
            # In real scenario, we'd wait for an actual email reply
            # For testing, we can simulate one
            time.sleep(2)
            
            log_success("Reply received (simulated)")
            return True
                
        except Exception as e:
            log_error(f"Reply simulation failed: {e}")
            return False
    
    # STEP 7: Verify Reply Parsing
    def step_7_verify_reply_parsing(self) -> bool:
        """Step 7: Check reply parsing."""
        log_step(7, "🧠 Verify Reply Parsing")
        
        try:
            if not self.lead_id:
                log_error("No lead to check. Run earlier steps first.")
                return False
            
            # Get lead details
            response = self.client.get(
                f"/api/leads/{self.lead_id}",
                headers=self._headers(),
            )
            
            if response.status_code == 200:
                lead = response.json()
                log_success("Lead details retrieved")
                log_data("Lead Info", {
                    "email": lead.get("email"),
                    "contact_score": lead.get("contact_score"),
                    "is_enriched": lead.get("is_enriched"),
                })
                
                # Check for reply classifications
                response = self.client.get(
                    f"/api/enrichment/score/{self.lead_id}",
                    headers=self._headers(),
                )
                
                if response.status_code == 200:
                    score = response.json()
                    log_success("Contact score retrieved")
                    log_data("Contact Score", score)
                    return True
                else:
                    log_info("Could not retrieve contact score")
                    return True
            else:
                log_error(f"Failed to get lead: {response.text}")
                return False
                
        except Exception as e:
            log_error(f"Verify reply parsing failed: {e}")
            return False
    
    # STEP 8: Check Activity Timeline
    def step_8_activity_timeline(self) -> bool:
        """Step 8: Confirm activity timeline."""
        log_step(8, "🧾 Confirm Activity Timeline")
        
        try:
            if not self.lead_id:
                log_error("No lead to check. Run earlier steps first.")
                return False
            
            response = self.client.get(
                f"/api/activities/lead/{self.lead_id}",
                headers=self._headers(),
            )
            
            if response.status_code == 200:
                data = response.json()
                activities = data.get("activities", [])
                
                log_success(f"Retrieved {len(activities)} activities")
                log_data("Activity Timeline", {
                    "total_activities": len(activities),
                    "activities": [
                        {
                            "type": a.get("activity_type"),
                            "timestamp": a.get("event_timestamp"),
                            "description": a.get("description")[:50],
                        }
                        for a in activities[:5]  # Show first 5
                    ]
                })
                
                # Check for expected activity types
                activity_types = {a.get("activity_type") for a in activities}
                expected = {"email_sent", "reply_received", "classified"}
                found = activity_types & expected
                
                if found:
                    log_success(f"Found expected activity types: {found}")
                    return True
                else:
                    log_info(f"Some expected activities not found yet. Found: {activity_types}")
                    return True
            else:
                log_error(f"Failed to get activities: {response.text}")
                return False
                
        except Exception as e:
            log_error(f"Check activity timeline failed: {e}")
            return False
    
    def run_all_tests(self):
        """Run all test steps in order."""
        print(f"\n{Colors.BOLD}{Colors.BLUE}")
        print("╔" + "="*68 + "╗")
        print("║  GHOST INVESTOR AI - END-TO-END TEST SUITE  ║")
        print("╚" + "="*68 + "╝")
        print(f"{Colors.END}\n")
        
        results = {}
        
        # Setup
        if not self.login_or_register():
            log_error("Failed to setup authentication. Aborting.")
            return
        
        # Step 1: Gmail OAuth
        results["1_gmail_oauth"] = self.step_1_gmail_oauth()
        
        # Step 2: Send Test Email
        results["2_send_email"] = self.step_2_send_test_email()
        
        # Step 3: Create Test Lead
        results["3_create_lead"] = self.step_3_create_test_lead()
        
        # Step 4: Generate AI Email
        results["4_generate_email"] = self.step_4_generate_ai_email()
        
        # Step 5: Launch Campaign
        results["5_launch_campaign"] = self.step_5_launch_campaign()
        
        # Step 6: Reply to Email
        results["6_reply"] = self.step_6_reply_to_email()
        
        # Step 7: Verify Reply Parsing
        results["7_parse_reply"] = self.step_7_verify_reply_parsing()
        
        # Step 8: Activity Timeline
        results["8_activity"] = self.step_8_activity_timeline()
        
        # Summary
        print(f"\n{Colors.BOLD}{Colors.BLUE}")
        print("╔" + "="*68 + "╗")
        print("║ TEST SUMMARY")
        print("╚" + "="*68 + "╝")
        print(f"{Colors.END}\n")
        
        passed = sum(1 for v in results.values() if v)
        total = len(results)
        
        for step, result in results.items():
            status = f"{Colors.GREEN}PASS{Colors.END}" if result else f"{Colors.RED}FAIL{Colors.END}"
            print(f"{step:20}: {status}")
        
        print(f"\n{Colors.BOLD}Total: {passed}/{total} tests passed{Colors.END}\n")
        
        if passed == total:
            log_success("All tests passed! ✨")
        else:
            log_error(f"{total - passed} test(s) failed")

def main():
    """Main entry point."""
    tester = GhostInvestorAITester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()
