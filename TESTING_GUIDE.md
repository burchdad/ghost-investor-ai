# Ghost Investor AI - End-to-End Testing Guide

Complete step-by-step guide for testing all Ghost Investor AI features from lead enrichment to email campaign execution.

## Prerequisites

Before running tests, ensure you have:

### System Services Running

```bash
# Terminal 1: PostgreSQL
# Make sure PostgreSQL 13+ is running on localhost:5432
psql -U postgres -d ghost_investor_ai

# Terminal 2: Redis
# Make sure Redis 7+ is running on localhost:6379
redis-cli ping

# Terminal 3: FastAPI Server
cd /workspaces/ghost-investor-ai
source venv/bin/activate
uvicorn src.ghost_investor_ai.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 4: Celery Worker (for background jobs)
cd /workspaces/ghost-investor-ai
source venv/bin/activate
celery -A src.ghost_investor_ai.services.batch_jobs worker --loglevel=info
```

### Environment Configuration

1. Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

2. Set required credentials in `.env`:
```env
# Gmail OAuth (required for email testing)
GMAIL_CLIENT_ID=your_gmail_client_id
GMAIL_CLIENT_SECRET=your_gmail_client_secret

# OpenAI (required for AI email generation)
OPENAI_API_KEY=your_openai_api_key

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/ghost_investor_ai
```

3. Initialize database:
```bash
python -c "from src.ghost_investor_ai.database import Base, engine; Base.metadata.create_all(bind=engine)"
```

## Testing Options

### Option A: Automated Python Test (Recommended for CI/CD)

Use the Python test script for automated testing:

```bash
# Run all 8 steps automatically
python TEST_END_TO_END.py
```

**What It Tests:**
1. ✅ User registration and login
2. ✅ Gmail OAuth flow
3. ✅ Email sending
4. ✅ Lead creation
5. ✅ AI email generation
6. ✅ Campaign creation and scheduling
7. ✅ Reply parsing (simulated)
8. ✅ Activity timeline verification

**Output:**
- Color-coded test results
- Detailed JSON responses for each step
- Summary of passed/failed tests

### Option B: Manual Bash Testing (Recommended for Development)

Use the bash script for interactive testing with real email:

```bash
# Make script executable
chmod +x TEST_MANUAL_STEPS.sh

# Run with manual email steps
./TEST_MANUAL_STEPS.sh
```

**Key Differences from Python Test:**
- Requires you to manually complete Gmail OAuth in browser
- Requires you to reply to the test email manually
- Great for end-to-end verification with real emails
- Better for understanding each step

### Option C: Manual cURL Commands

Test individual endpoints one at a time:

```bash
# Set variables
API="http://localhost:8000"
EMAIL="test@example.com"
PASSWORD="testpass123"

# 1. Register user
curl -X POST "$API/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"'$EMAIL'","password":"'$PASSWORD'"}'

# 2. Login
TOKEN=$(curl -s -X POST "$API/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"'$EMAIL'","password":"'$PASSWORD'"}' | jq -r '.access_token')

# 3. Create lead
curl -X POST "$API/api/leads/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email":"lead@example.com",
    "first_name":"John",
    "last_name":"Doe",
    "company_name":"Acme Inc",
    "job_title":"CEO"
  }'
```

## 8-Step Testing Workflow

### STEP 1: 🔐 Gmail OAuth Setup

**Objective:** Authorize Gmail account for email sending

**Manual Process:**
1. Call `POST /api/email-accounts/authorize/gmail`
2. Receive authorization URL
3. Open URL in browser and grant permissions
4. Copy authorization code
5. Call `POST /api/email-accounts/authorize/gmail/callback` with code
6. Verify tokens stored in database

**Expected Results:**
- ✅ Access token received
- ✅ Refresh token stored in DB
- ✅ Email account linked to user

**Database Check:**
```bash
curl -X GET "http://localhost:8000/api/email-accounts/" \
  -H "Authorization: Bearer $TOKEN" | jq .accounts
```

### STEP 2: 📩 Send a Test Email

**Objective:** Verify email sending capability

**Command:**
```bash
curl -X POST "http://localhost:8000/api/batch/send-emails" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "recipient_email":"your.email@gmail.com",
    "subject":"Test Email from Ghost Investor AI",
    "body":"This is a test email to verify the system is working.",
    "email_account_id": 1
  }'
```

**Expected Results:**
- ✅ Job submitted (returns job_id)
- ✅ Email arrives in inbox within 30 seconds
- ✅ Message ID stored in database
- ✅ Activity logged

**Verification:**
1. Check inbox for email
2. Verify sender is your authorized Gmail account
3. Check subject line matches
4. Check job status: `GET /api/batch/job-status/{job_id}`

### STEP 3: 🧪 Create a Test Lead

**Objective:** Add prospect to system

**Command:**
```bash
curl -X POST "http://localhost:8000/api/leads/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email":"yourtest@email.com",
    "first_name":"Stephen",
    "last_name":"Test",
    "company_name":"Ghost AI",
    "job_title":"Founder",
    "linkedin_url":"https://linkedin.com/in/test",
    "phone":"+1234567890"
  }'
```

**Expected Results:**
- ✅ Lead created with ID
- ✅ Contact score calculated
- ✅ Stored in database
- ✅ Enrichment data populated

**Response Fields to Check:**
- `id` - Lead ID for future requests
- `contact_score` - Initial scoring
- `is_enriched` - Enrichment status
- `created_at` - Timestamp

### STEP 4: 🧠 Generate AI Email

**Objective:** Use GPT-4 to generate personalized email

**Command:**
```bash
curl -X POST "http://localhost:8000/api/batch/generate-emails" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "lead_ids":[1],
    "tone":"professional",
    "template":"first_touch"
  }'
```

**Expected Results:**
- ✅ Job submitted (returns job_id)
- ✅ AI generates personalized email
- ✅ Email stored in database
- ✅ Personalization factors logged

**Verification:**
1. Check job status: `GET /api/batch/job-status/{job_id}`
2. Email should:
   - Use recipient's name
   - Reference company name
   - Match professional tone
   - Use first-touch template structure

### STEP 5: 🚀 Launch Campaign

**Objective:** Create campaign and schedule email sends

**Steps:**

1. **Create Campaign:**
```bash
curl -X POST "http://localhost:8000/api/campaigns/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name":"Test Campaign",
    "description":"End-to-end test campaign",
    "email_account_id":1
  }'
```

2. **Add Lead to Campaign:**
```bash
curl -X POST "http://localhost:8000/api/campaigns/{campaign_id}/add-lead/{lead_id}" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}'
```

3. **Schedule Campaign:**
```bash
curl -X POST "http://localhost:8000/api/campaigns/{campaign_id}/schedule" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"delay_seconds":1}'
```

**Expected Results:**
- ✅ Campaign created
- ✅ Lead added to campaign
- ✅ Campaign scheduled
- ✅ Emails queued for sending
- ✅ Activity logged

### STEP 6: 📬 Reply to Email

**Objective:** Send manual reply to test system

**Process:**
1. Open inbox (your Gmail account)
2. Find email from step 2: "Test Email from Ghost Investor AI"
3. Click Reply
4. Type response like: *"This is interesting, can you send more info?"*
5. Send reply

**System Processing:**
- Gmail webhook receives reply (or system polls for new emails)
- Reply is parsed and classified
- Classification stored in database
- Activity logged
- Lead score updated

### STEP 7: 🧠 Verify Reply Parsing

**Objective:** Confirm reply was correctly classified

**Command:**
```bash
curl -X GET "http://localhost:8000/api/enrichment/score/{lead_id}" \
  -H "Authorization: Bearer $TOKEN" | jq .
```

**Expected Results:**
- ✅ Classification: `INTERESTED` or `QUESTION`
- ✅ Confidence score present
- ✅ Sentiment analysis present
- ✅ Contact score updated
- ✅ Key points extracted

**Response Fields:**
```json
{
  "lead_id": 1,
  "title_score": 0.8,
  "company_score": 0.75,
  "activity_score": 0.9,
  "engagement_score": 0.95,
  "total_score": 0.85,
  "score_reason": "High engagement with positive sentiment"
}
```

### STEP 8: 🧾 Activity Timeline

**Objective:** Verify complete activity log

**Command:**
```bash
curl -X GET "http://localhost:8000/api/activities/lead/{lead_id}" \
  -H "Authorization: Bearer $TOKEN" | jq '.activities | sort_by(.event_timestamp)'
```

**Expected Activity Chain:**
```
1. email_sent - Initial contact
2. email_delivered - Confirmation
3. email_opened - Recipient opened email
4. reply_received - Reply came in
5. classified - System classified reply
6. contact_score_updated - Score recalculated
```

**Verification Checklist:**
- ✅ All events present
- ✅ Timestamps in correct order
- ✅ Descriptions populated
- ✅ Activity types logged correctly
- ✅ Synced to CRM status (if applicable)

## Common Issues & Solutions

### Issue: "Connection refused" on API calls
**Solution:**
```bash
# Check FastAPI is running
curl http://localhost:8000/health

# If not running, start it:
uvicorn src.ghost_investor_ai.main:app --reload
```

### Issue: Gmail OAuth fails
**Solution:**
1. Verify `GMAIL_CLIENT_ID` and `GMAIL_CLIENT_SECRET` in `.env`
2. Check OAuth credentials are for "Desktop" app type
3. Ensure redirect URI is configured correctly in Google Cloud Console
4. Try again with: `include_granted_scopes="true"`

### Issue: Email not arriving
**Solution:**
1. Check job status: `GET /api/batch/job-status/{job_id}`
2. Check email account credentials valid
3. Check Gmail rate limiting (50 emails/hour max)
4. Check spam/junk folder
5. Verify SMTP connection works: `POST /api/email-accounts/{id}/test-connection`

### Issue: AI email generation fails
**Solution:**
1. Verify `OPENAI_API_KEY` in `.env`
2. Check API quota not exceeded
3. Check lead has required fields (name, company, title)
4. Check job status for detailed error

### Issue: Reply not classified
**Solution:**
1. Check email arrived (Step 6 verification)
2. Wait 30-60 seconds for system to poll for replies
3. Check job status for parsing errors
4. Verify lead email is correct in database

### Issue: Celery worker not processing jobs
**Solution:**
```bash
# Verify worker is running
ps aux | grep celery

# Check Redis connection
redis-cli ping  # Should return PONG

# Restart worker:
celery -A src.ghost_investor_ai.services.batch_jobs worker --loglevel=info
```

## Test Data Cleanup

To reset for a fresh test run:

```bash
# Reset database (WARNING: deletes all data)
python -c "
from src.ghost_investor_ai.database import Base, engine
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
print('Database reset')
"

# Or delete specific test user:
psql -U postgres -d ghost_investor_ai -c "DELETE FROM users WHERE email = 'test@example.com';"
```

## Performance Benchmarks

Expected performance for each step:

| Step | Operation | Expected Time | Notes |
|------|-----------|----------------|-------|
| 1 | Gmail OAuth | 5-10 sec | Manual browser interaction |
| 2 | Send Email | 2-5 sec | Depends on Gmail API |
| 3 | Create Lead | <1 sec | Local database insert |
| 4 | Generate Email | 5-15 sec | Depends on OpenAI API |
| 5 | Launch Campaign | <2 sec | Local operations |
| 6 | Reply Email | Variable | Manual action + system polling |
| 7 | Parse Reply | 10-30 sec | Depends on OpenAI API |
| 8 | Check Timeline | <1 sec | Database query |

**Total End-to-End Time:** 30-60 minutes (mostly manual/waiting)

## Success Criteria

✅ All tests pass when:

1. **Gmail OAuth** 
   - Access token obtained
   - Refresh token stored
   - Email account appears in list

2. **Email Sending**
   - Email arrives in inbox
   - Subject and body match
   - Activity logged

3. **Lead Creation**
   - Lead visible in database
   - Contact score calculated
   - Enrichment status set

4. **AI Generation**
   - Email generated within 15 seconds
   - Personalization includes recipient name
   - Professional tone applied

5. **Campaign**
   - Campaign created and scheduled
   - Lead added successfully
   - Status shows "scheduled"

6. **Reply**
   - Reply arrives in inbox
   - System detects within 60 seconds

7. **Classification**
   - Reply classified as INTERESTED or QUESTION
   - Confidence score > 0.7
   - Contact score updated upward

8. **Timeline**
   - All 8 events present
   - Chronological order correct
   - Descriptions complete

## Next Steps

After completing all 8 steps:

1. **Review Metrics:**
   - Open rate (if email was opened)
   - Reply rate (100% in test)
   - Classification accuracy
   - Average response time

2. **Test Variations:**
   - Different email tones (casual, friendly, formal)
   - Multiple recipients in campaign
   - Follow-up sequences

3. **Stress Testing:**
   - Send 10+ emails in sequence
   - Verify rate limiting works
   - Check database scaling

4. **Integration Testing:**
   - Verify webhook events
   - Test CRM sync
   - Check activity logging

## Support

For issues or questions:
- Check logs: `tail -f logs/app.log`
- Check worker logs: `grep ERROR celery.log`
- Review API responses for detailed error messages
- Check database: `psql -U postgres -d ghost_investor_ai`
