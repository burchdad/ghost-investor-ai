# Ghost Investor AI - Testing Workflow Visualization

## Complete End-to-End Test Workflow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    GHOST INVESTOR AI - E2E TEST WORKFLOW                    │
└─────────────────────────────────────────────────────────────────────────────┘

SETUP: Prerequisites Running
┌─────────────────────────────────────────────────────────────────────────────┐
│ Terminal 1          │ Terminal 2        │ Terminal 3          │ Terminal 4  │
│ PostgreSQL          │ Redis             │ FastAPI             │ Celery      │
│ localhost:5432      │ localhost:6379    │ localhost:8000      │ Worker      │
│ ✓ Running          │ ✓ Running        │ ✓ Running          │ ✓ Running  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓

CHOOSE TEST METHOD
┌─────────────────────────────────────────────────────────────────────────────┐
│  [A] Automated                 │ [B] Interactive              │ [C] Manual   │
│  python TEST_END_TO_END.py     │ ./TEST_MANUAL_STEPS.sh      │ cURL cmds   │
│  ✓ 5 min, no email needed      │ ✓ 30 min, real emails       │ Per-endpoint│
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓

STEP 1: 🔐 Gmail OAuth
┌──────────────────────────────────────────────────────────────────┐
│ POST /api/email-accounts/authorize/gmail                        │
│ ↓                                                                │
│ Receive: authorization_url + state                              │
│ ↓                                                                │
│ [USER ACTION] Open URL → Grant permissions → Get code           │
│ ↓                                                                │
│ POST /api/email-accounts/authorize/gmail/callback (code, state) │
│ ↓                                                                │
│ Database: EmailAccount{token, refresh_token} stored             │
│ ✓ Result: Gmail OAuth complete, tokens secured                 │
└──────────────────────────────────────────────────────────────────┘
                                    ↓

STEP 2: 📩 Send Test Email
┌──────────────────────────────────────────────────────────────────┐
│ POST /api/batch/send-emails                                      │
│ {recipient, subject, body, email_account_id}                     │
│ ↓                                                                │
│ [SYSTEM] Celery job submitted (job_id returned)                 │
│ ↓                                                                │
│ [SYSTEM] Gmail API sends email                                  │
│ ↓                                                                │
│ [INBOX] Email arrives (15-30 seconds)                           │
│ ↓                                                                │
│ Database: Activity{type: email_sent} logged                      │
│ ✓ Result: Email in your inbox!                                  │
└──────────────────────────────────────────────────────────────────┘
                                    ↓

STEP 3: 🧪 Create Test Lead
┌──────────────────────────────────────────────────────────────────┐
│ POST /api/leads/                                                 │
│ {email, first_name, last_name, company, title, ...}             │
│ ↓                                                                │
│ [SYSTEM] Lead enrichment triggered                              │
│ ↓                                                                │
│ [SYSTEM] Contact score calculated (multi-factor)                │
│ ↓                                                                │
│ Database: Lead{id, contact_score, is_enriched} stored           │
│ ✓ Result: Lead in system with initial scoring                   │
└──────────────────────────────────────────────────────────────────┘
                                    ↓

STEP 4: 🧠 Generate AI Email
┌──────────────────────────────────────────────────────────────────┐
│ POST /api/batch/generate-emails                                  │
│ {lead_ids, tone, template}                                       │
│ ↓                                                                │
│ [SYSTEM] Celery job submitted                                   │
│ ↓                                                                │
│ [OPENAI] GPT-4 generates personalized email                     │
│          Include: recipient name, company, specific details      │
│ ↓                                                                │
│ [SYSTEM] Apply tone (professional/casual/friendly)              │
│ ↓                                                                │
│ Database: OutreachEmail{subject, body, is_generated} stored     │
│ ✓ Result: AI-personalized email ready to send                   │
└──────────────────────────────────────────────────────────────────┘
                                    ↓

STEP 5: 🚀 Launch Campaign
┌──────────────────────────────────────────────────────────────────┐
│ POST /api/campaigns/                                             │
│ {name, description, email_account_id}                           │
│ ↓                                                                │
│ POST /api/campaigns/{id}/add-lead/{lead_id}                     │
│ ↓                                                                │
│ POST /api/campaigns/{id}/schedule                               │
│ ↓                                                                │
│ [SYSTEM] Batch send job queued                                  │
│ ↓                                                                │
│ Database: Campaign{status: scheduled} stored                     │
│ Database: Activity{type: campaign_scheduled} logged              │
│ ✓ Result: Campaign ready for execution                          │
└──────────────────────────────────────────────────────────────────┘
                                    ↓

STEP 6: 📬 Reply to Email
┌──────────────────────────────────────────────────────────────────┐
│ [USER ACTION REQUIRED!]                                          │
│                                                                  │
│ 1. Open your email inbox                                        │
│ 2. Find: "Test Email from Ghost Investor AI"                   │
│ 3. Click: Reply                                                 │
│ 4. Type: "This is interesting, can you send more info?"        │
│ 5. Send: Reply                                                  │
│ ↓                                                                │
│ [SYSTEM] Polls Gmail or receives webhook                        │
│ ↓                                                                │
│ [SYSTEM] Reply detected and extracted                           │
│ ↓                                                                │
│ Database: SentEmail updated with reply info                     │
│ Database: Activity{type: reply_received} logged                 │
│ ✓ Result: Reply received in system                              │
└──────────────────────────────────────────────────────────────────┘
                                    ↓

STEP 7: 🧠 Verify Reply Parsing
┌──────────────────────────────────────────────────────────────────┐
│ GET /api/enrichment/score/{lead_id}                             │
│ ↓                                                                │
│ [SYSTEM] LLM analyzes reply text                                │
│          - Classification: INTERESTED, QUESTION, NOT_INTERESTED, │
│                            LATER, UNSUBSCRIBE, UNCLEAR            │
│          - Sentiment: positive, neutral, negative               │
│          - Confidence: 0.0 - 1.0                                │
│          - Key points extracted                                 │
│ ↓                                                                │
│ [SYSTEM] Score recalculated based on engagement                 │
│ ↓                                                                │
│ Database: ReplyClassification stored                            │
│ Database: Lead.contact_score updated (upward!)                  │
│ Database: Activity{type: reply_classified} logged               │
│ ✓ Result: Reply intelligently classified & scored               │
└──────────────────────────────────────────────────────────────────┘
                                    ↓

STEP 8: 🧾 Confirm Activity Timeline
┌──────────────────────────────────────────────────────────────────┐
│ GET /api/activities/lead/{lead_id}                              │
│ ↓                                                                │
│ Timeline shows (chronological):                                 │
│ ┌─ Activity 1: campaign_created        (ts: 1710XXX)           │
│ ├─ Activity 2: email_generated         (ts: 1710XXX)           │
│ ├─ Activity 3: email_queued            (ts: 1710XXX)           │
│ ├─ Activity 4: email_sent              (ts: 1710XXX)           │
│ ├─ Activity 5: email_delivered         (ts: 1710XXX)           │
│ ├─ Activity 6: email_opened            (ts: 1710XXX)           │
│ ├─ Activity 7: reply_received          (ts: 1710XXX)           │
│ ├─ Activity 8: reply_classified        (ts: 1710XXX)           │
│ └─ Activity 9: contact_score_updated   (ts: 1710XXX)           │
│ ↓                                                                │
│ Database: All activities verified and sequenced                 │
│ ✓ Result: Complete audit trail available                        │
└──────────────────────────────────────────────────────────────────┘
                                    ↓

✅ ALL TESTS COMPLETE!

┌─────────────────────────────────────────────────────────────────────────────┐
│                           TEST RESULTS SUMMARY                              │
├─────────────────────────────────────────────────────────────────────────────┤
│ ✅ Step 1: Gmail OAuth                           [PASS]                    │
│ ✅ Step 2: Email Sending                         [PASS]                    │
│ ✅ Step 3: Lead Creation                         [PASS]                    │
│ ✅ Step 4: AI Email Generation                   [PASS]                    │
│ ✅ Step 5: Campaign Launch                       [PASS]                    │
│ ✅ Step 6: Reply Received                        [PASS]                    │
│ ✅ Step 7: Reply Classification                  [PASS]                    │
│ ✅ Step 8: Activity Timeline                     [PASS]                    │
├─────────────────────────────────────────────────────────────────────────────┤
│ Total: 8/8 PASSED                                                          │
│ Duration: 30-60 minutes (mostly manual steps)                              │
│ Status: ✅ SYSTEM READY FOR PRODUCTION                                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## System Architecture During Test

```
┌───────────────────────────────────────────────────────────────────┐
│                          YOUR BROWSER                            │
│  (Gmail OAuth, Email Inbox, Reply Composition)                   │
└───────────────────────────────────────────────────────────────────┘
                           ↕ (Manual)
┌───────────────────────────────────────────────────────────────────┐
│                      FastAPI Server (Port 8000)                  │
│  ├─ /api/email-accounts/* (Gmail OAuth)                         │
│  ├─ /api/leads/* (Lead management)                              │
│  ├─ /api/batch/* (Background job submission)                    │
│  ├─ /api/campaigns/* (Campaign management)                      │
│  ├─ /api/activities/* (Activity logging)                        │
│  ├─ /api/enrichment/* (Scoring & enrichment)                    │
│  └─ /api/analytics/* (Metrics & insights)                       │
└───────────────────────────────────────────────────────────────────┘
         ↕                    ↕                    ↕
    ┌────────┐          ┌──────────┐        ┌───────────┐
    │PostgreSQL         │  Redis    │        │  Celery   │
    │Database           │  Cache    │        │  Worker   │
    │                   │  Queue    │        │           │
    │- Users            │           │        │ Jobs:     │
    │- Leads            │ - Tasks   │        │ - Send    │
    │- Emails           │ - Session │        │ - Generate│
    │- Campaigns        │ - Locks   │        │ - Enrich  │
    │- Activities       │           │        │ - Parse   │
    │- Classifications  │           │        │           │
    └────────┘          └──────────┘        └───────────┘
         ↕                                        ↕
         └────────────────────┬───────────────────┘
                              ↓
                   ┌─────────────────────┐
                   │  External APIs      │
                   ├─────────────────────┤
                   │ Gmail API           │
                   │ (OAuth, Send, Poll) │
                   │                     │
                   │ OpenAI API          │
                   │ (GPT-4 Generation)  │
                   │                     │
                   │ LLM Service         │
                   │ (Classification)    │
                   └─────────────────────┘
```

---

## Data Flow During Each Step

### Step 2: Email Sending Flow
```
POST /api/batch/send-emails
    ↓
FastAPI validates request
    ↓
Creates Celery task
    ↓
Stores in Redis queue
    ↓
Celery worker picks up task
    ↓
Retrieves Gmail credentials from DB
    ↓
Calls Gmail API
    ↓
Email sent
    ↓
Updates SentEmail record
    ↓
Logs Activity entry
    ↓
Returns job_id to user
    ↓
Job shows "completed" in status
    ↓
✓ Email in user's inbox
```

### Step 4: AI Email Generation Flow
```
POST /api/batch/generate-emails
    ↓
FastAPI validates request + retrieves lead data
    ↓
Creates Celery task with lead details
    ↓
Stores in Redis queue
    ↓
Celery worker picks up task
    ↓
Constructs OpenAI prompt with:
  - Recipient name & title
  - Company info
  - Requested tone
  - Email template
    ↓
Calls OpenAI GPT-4 API
    ↓
Receives generated email
    ↓
Stores OutreachEmail record
    ↓
Logs Activity entry
    ↓
Job shows "completed" in status
    ↓
✓ Email ready for sending
```

### Step 7: Reply Classification Flow
```
Reply received in inbox
    ↓
[Webhook or polling] System detects reply
    ↓
Extracts reply text
    ↓
Stores as ReplyClassification entry
    ↓
Triggers LLM classification task
    ↓
Constructs classification prompt:
  - Reply text
  - Context (recipient, company)
  - Classification categories
    ↓
Calls OpenAI API for:
  - Classification (INTERESTED/QUESTION/etc)
  - Sentiment (positive/neutral/negative)
  - Confidence score
  - Key points extraction
    ↓
Stores results
    ↓
Recalculates Lead contact_score
    ↓
Updates Lead.contact_score (↑ if interested)
    ↓
Logs Activity entry: reply_classified
    ↓
✓ Reply analyzed and scored
```

---

## Expected Response Time by Component

```
Component              Latency         Notes
─────────────────────────────────────────────────────────────────
Gmail OAuth            5-10 sec        Manual browser action
Gmail API send         2-5 sec         Depends on Gmail
Database insert        <1 msec         Local
OpenAI GPT-4 call      10-20 sec       API dependent
LLM classification     15-30 sec       API dependent
Email polling          1-60 sec        Depends on polling frequency
Activity query         <10 msec        Database index
─────────────────────────────────────────────────────────────────
Total (per step)       ~1-60 sec       Varies by component
Total (8 steps)        30-60 min       Includes manual actions
```

---

## Database State After Each Step

### After Step 1 (Gmail OAuth)
- EmailAccount created (with tokens)
- User linked to email account

### After Step 2 (Send Email)
- SentEmail created
- Activity logged: email_sent

### After Step 3 (Create Lead)
- Lead created
- Activity logged: lead_created

### After Step 4 (Generate Email)
- OutreachEmail created
- Campaign created
- Activity logged: email_generated

### After Step 5 (Launch Campaign)
- Campaign status: scheduled
- Activity logged: campaign_scheduled

### After Step 6 (Reply Received)
- ReplyClassification created (pending)
- Activity logged: reply_received

### After Step 7 (Reply Classified)
- ReplyClassification updated (with classification)
- Lead.contact_score updated
- Activity logged: reply_classified

### After Step 8 (Activity Check)
- All 8+ activities visible
- Timeline consistent
- All relationships verified

---

## Success Metrics

✅ **Test Passes When:**
- All API endpoints respond with 200/201 status
- Email arrives within 30 seconds
- AI generates email within 20 seconds
- Classification completed within 30 seconds
- All database records created and linked
- Activity timeline shows all 8+ events
- Response times within benchmarks
- No error/exception messages

---

## Quick Troubleshooting

If Step X fails, run:

```
Step 1 (OAuth) fails:
  └─ Check: GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET in .env
  └─ Verify: OAuth redirect URI in Google Cloud Console
  └─ Test: curl http://localhost:8000/health

Step 2 (Send Email) fails:
  └─ Check: Email account authorized (Step 1 pass?)
  └─ Verify: job status
  └─ Test: curl /api/batch/job-status/{job_id}

Step 4 (AI Generation) fails:
  └─ Check: OPENAI_API_KEY in .env
  └─ Verify: Lead has required fields
  └─ Test: Check OpenAI quota/balance

Step 7 (Classification) fails:
  └─ Check: Reply actually received
  └─ Verify: Email polling working
  └─ Test: Check Celery worker logs
```

See **TESTING_GUIDE.md** for full troubleshooting guide.

---

**Ready to test? Start with:**

```bash
# Option A: Automated
python TEST_END_TO_END.py

# Option B: Interactive
./TEST_MANUAL_STEPS.sh
```

✅ **All systems ready. Good luck!** 🚀
