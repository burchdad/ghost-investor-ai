# Ghost Investor Outreach: Technical Roadmap

## Strategic Overview

Investor Outreach is a **coordinating module** in Ghost, not a standalone CRM. It takes input from multiple Ghost services, processes outreach, and feeds results back to the ecosystem.

### Data Flow Architecture

```
INPUT SOURCES:
├── Underwriter (deal context)
├── Strategic Briefings (company intel)
├── GhostCRM (lead state, notes, tasks)
└── Lead Manifest (contact lists)

    ↓

GHOST INVESTOR OUTREACH:
├── Enrich (Apollo, Clearbit, PDL)
├── Score (relevance to investment)
├── Generate (AI email)
├── Send (Gmail, Outlook)
├── Parse Replies (sentiment, action)
└── Batch Manage

    ↓

OUTPUT TARGETS:
├── GhostCRM (bi-directional sync)
├── Events (webhooks)
├── Analytics

```

## Phase 1: Launch Requirements (Weeks 1-8)

### 1.1 Email Service Integration (Weeks 1-3)

**Why first?** Without email capability, this is just a data enrichment tool.

#### Gmail Integration
```python
# src/ghost_investor_ai/integrations/email/gmail.py
class GmailService:
    """Gmail API integration for sending and reply tracking."""
    
    async def send_email(lead_id: int, email_data: dict) -> dict
    async def get_replies(lead_id: int, since: datetime) -> List[dict]
    async def mark_opened(message_id: str) -> bool
    async def get_reply_thread(lead_id: int) -> List[dict]
```

**Implementation:**
- OAuth2 flow for user authentication
- Send drafts via Gmail API
- Track opens via pixel tracking (or Gmail metadata)
- Read replies from labeled folder
- Log sent emails with Gmail message ID

**Data Model:**
```python
# Add to models.py
class EmailAccount(Base):
    __tablename__ = "email_accounts"
    id = Column(Integer, primary_key=True)
    user_email = Column(String(255), unique=True)
    provider = Column(Enum(EmailProvider))  # gmail, outlook
    oauth_token = Column(String(2048), encrypted=True)
    refresh_token = Column(String(2048), encrypted=True)
    is_active = Column(Boolean, default=True)

class SentEmail(Base):
    __tablename__ = "sent_emails"
    id = Column(Integer, primary_key=True)
    outreach_email_id = Column(Integer, ForeignKey("outreach_emails.id"))
    email_account_id = Column(Integer, ForeignKey("email_accounts.id"))
    message_id = Column(String(255))  # Gmail message ID
    sent_at = Column(DateTime)
    opened_at = Column(DateTime, nullable=True)
    open_count = Column(Integer, default=0)
    reply_received_at = Column(DateTime, nullable=True)
    reply_message_id = Column(String(255))
    provider = Column(Enum(EmailProvider))
```

#### Outlook Integration
- Similar OAuth2 flow
- Graph API for sending/reading
- Integration with Microsoft tracking

**API Endpoints:**
```
POST /api/email/accounts/authorize?provider=gmail
GET /api/email/accounts/
POST /api/email/send/{email_id}
GET /api/email/status/{email_id}
GET /api/email/replies/{lead_id}
```

### 1.2 GhostCRM Bi-directional Sync (Weeks 2-4)

**Why critical?** Prevents data fragmentation; other Ghost modules depend on authoritative CRM records.

#### Sync Architecture

```python
# src/ghost_investor_ai/integrations/crm/ghostcrm.py
class GhostCRMSyncService:
    """Bi-directional sync with GhostCRM."""
    
    async def push_lead(lead: Lead) -> dict
        """Create/update lead in GhostCRM."""
        # Maps Ghost Investor Outreach fields to CRM
        # Handle conflicts (last-write-wins or merge)
    
    async def pull_lead(crm_id: str) -> Lead
        """Fetch lead from CRM and update local."""
    
    async def push_activity(activity: Activity) -> dict
        """Log interaction in CRM."""
    
    async def push_task(task_data: dict) -> dict
        """Create follow-up task for investor/deal team."""
    
    async def sync_status(lead: Lead) -> dict
        """Update lead status in CRM (contacted, interested, etc.)."""
```

#### Data Sync Rules

```
Direction: PUSH (Investor Outreach → CRM)
- Lead enrichment results
- Email sent events
- Reply parsing results
- Suggested next actions

Direction: PULL (CRM → Investor Outreach)
- Lead status changes
- Manual notes/tags
- Do-not-contact flags
- Deal/briefing context

Direction: BOTH (Bi-directional)
- Contact information updates
- Preferred communication method
- Last contact timestamp
```

**Implementation:**
- Webhook handler for CRM changes (push to Investor Outreach)
- Scheduled sync job (pull CRM updates)
- Conflict resolution strategy (define per field)
- Audit trail for all sync events

### 1.3 Advanced AI Email Generation (Weeks 3-5)

**Why essential?** This is the core value prop—hyper-personalized outreach at scale.

#### Email Generation Tiers

```python
# src/ghost_investor_ai/services/ai_email_generation.py

class AIEmailService:
    """Generate context-aware emails using LLM."""
    
    async def generate_first_touch(
        lead: Lead,
        deal_context: dict,  # From Underwriter
        briefing: dict,      # From Strategic Briefings
    ) -> EmailTemplate
    
    async def generate_follow_up(
        initial_email: OutreachEmail,
        reply: Optional[dict],  # If replied
        lead_context: dict,
    ) -> EmailTemplate
    
    async def generate_reengagement(
        lead: Lead,
        reason: str,  # "no_reply", "interested_later", etc.
    ) -> EmailTemplate
    
    async def generate_deal_specific_blast(
        deal: dict,
        investor_segment: List[Lead],
    ) -> List[EmailTemplate]
```

#### Prompt Strategy (LLM)

**First-touch template:**
```
You are an investor relations specialist. Generate a personalized cold outreach email.

INVESTOR CONTEXT:
- Name: {lead.first_name} {lead.last_name}
- Title: {lead.job_title}
- Company: {lead.company_name}
- Focus: {investor_profile.key_interests}

DEAL CONTEXT:
- Company: {deal.company_name}
- Stage: {deal.stage}
- Sector: {deal.sector}
- Key strength: {deal.value_prop}

BRIEFING:
{briefing_summary}

Generate a 3-paragraph email that:
1. Opens with specific insight about investor (not generic)
2. Connects deal to investor's known interests
3. Ends with soft ask (call, brief meeting, etc.)

Tone: Professional but warm. Demonstrate actual knowledge.
```

**Reply context template:**
```
ORIGINAL EMAIL:
{original_email}

INVESTOR REPLY:
{reply_text}

LEAD CONTEXT:
- Investor stage: {investor_profile.stage}
- Previous interactions: {activity_summary}

Generate appropriate follow-up that:
- Acknowledges their specific point
- Provides next value add
- Moves toward call/meeting

Keep to 2 paragraphs. Maintain conversation thread.
```

#### LLM Provider Options
- **OpenAI** (GPT-4): Most capable, ~$0.03-0.06/email
- **Anthropic Claude**: Good, slightly cheaper
- **Local Llama 2**: Open source, self-hosted
- **Cohere**: API-based alternative

**Data Model:**
```python
class EmailTemplate(Base):
    __tablename__ = "email_templates"
    id = Column(Integer, primary_key=True)
    type = Column(Enum(EmailType))  # first_touch, follow_up, reengagement
    lead_id = Column(Integer, ForeignKey("leads.id"))
    context = Column(JSON)  # Briefing, deal, investor data used
    subject = Column(String(255))
    body = Column(Text)
    ai_model = Column(String(50))  # gpt-4, claude-3, etc.
    confidence_score = Column(Float)  # 0-1 quality metric
    human_edited = Column(Boolean, default=False)
    created_at = Column(DateTime)
```

### 1.4 Reply Parsing & Sentiment Analysis (Weeks 4-6)

**Why early?** Critical for automation and knowing who to re-engage.

#### Classification Engine

```python
# src/ghost_investor_ai/services/reply_parsing.py

class ReplyParsingService:
    """Parse investor replies and extract intent."""
    
    async def classify_reply(
        original_email: str,
        reply_text: str,
        lead_context: dict,
    ) -> ReplyClassification
        """
        Returns: {
            category: "interested" | "not_interested" | "later" | "question" | "unsubscribe",
            confidence: 0.0-1.0,
            sentiment: "positive" | "neutral" | "negative",
            key_phrases: ["phrase1", "phrase2"],
            next_action: "call", "send_info", "pause", "end",
            urgency: "high" | "medium" | "low",
            reasoning: str,
        }
        """
    
    async def extract_action_items(reply_text: str) -> List[str]
        """Extract investor requests/questions."""
    
    async def generate_task(
        classification: ReplyClassification,
        lead: Lead,
    ) -> Task
        """Create CRM task based on reply."""
```

#### Classification Rules

```
IF reply contains: ("interested", "let's chat", "call", schedule)
  → Category: "interested"
  → Next Action: "call"
  → Urgency: "high"

IF reply contains: ("not right now", "maybe later", "future")
  → Category: "later"
  → Next Action: "schedule_followup"
  → Urgency: "low"

IF reply contains: ("not interested", "pass", "not a fit")
  → Category: "not_interested"
  → Next Action: "end"
  → Urgency: "none"

IF reply is: question marks OR specific asks
  → Category: "question"
  → Next Action: "send_answer"
  → Urgency: "high"

IF contains: unsubscribe patterns
  → Category: "unsubscribe"
  → Next Action: "remove"
  → Urgency: "immediate"
```

**Detection Approach:**
1. LLM-based (most accurate): ~$0.01 per reply
2. Regex + keyword rules: Fast, good baseline
3. Hybrid: Rules first, LLM if uncertain

**Data Model:**
```python
class ReplyClassification(Base):
    __tablename__ = "reply_classifications"
    id = Column(Integer, primary_key=True)
    activity_id = Column(Integer, ForeignKey("activities.id"))
    lead_id = Column(Integer, ForeignKey("leads.id"))
    
    category = Column(String(50))  # interested, not_interested, later, question, unsubscribe
    confidence = Column(Float)
    sentiment = Column(String(20))  # positive, neutral, negative
    key_phrases = Column(JSON)
    next_action = Column(String(50))
    urgency = Column(String(20))
    
    auto_task_created = Column(Boolean, default=False)
    task_id = Column(String(255))  # CRM task ID
    created_at = Column(DateTime)
```

### 1.5 Rate Limiting & Authentication (Weeks 1-2, Before Launch)

**Why essential?** Protects sender reputation, prevents abuse, secures APIs.

#### Authentication

```python
# src/ghost_investor_ai/auth.py

class JWTAuthService:
    """JWT-based auth for API."""
    
    async def authenticate_user(email: str, password: str) -> Token
    async def refresh_token(refresh_token: str) -> Token
    async def verify_token(token: str) -> User

# Add to routes
from fastapi.security import HTTPBearer, HTTPAuthCredentials

security = HTTPBearer()

@router.post("/leads/")
async def create_lead(
    lead: LeadCreate,
    credentials: HTTPAuthCredentials = Depends(security),
):
    user = await verify_token(credentials.credentials)
    # ... create lead
```

#### Rate Limiting

```python
# src/ghost_investor_ai/rate_limiting.py

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

# Apply per-endpoint
@router.post("/email/send/{email_id}")
@limiter.limit("100/hour")  # 100 sends per hour
async def send_email(email_id: int, ...):
    pass

# Per-user limits
@limiter.limit("1000/day")  # 1000 API calls per day
async def api_handler(...):
    pass

# Email sending limits (sender reputation)
MAX_SENDS_PER_HOUR = 50  # Gmail/Outlook limits
MAX_UNIQUE_RECIPIENTS_PER_DAY = 200
```

#### Security Headers

```python
# Add to main.py
from fastapi.middleware import TrustedHostMiddleware

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*.yourdomain.com"]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,  # Restricted list
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

### 1.6 Batch Operations (Weeks 5-6)

**Why critical?** Enables founder/operator to work at scale.

#### Batch API

```python
# src/ghost_investor_ai/api/routes_batch.py

@router.post("/batch/enrich-leads")
async def batch_enrich(request: BatchEnrichRequest):
    """
    request: {
        lead_ids: [1, 2, 3, ...],
        force_refresh: false,
    }
    Returns: {job_id: "uuid", status: "queued", estimated_time: 120}
    """
    job = await enrich_job_queue.add(request.lead_ids)
    return {"job_id": job.id, "status": "queued"}

@router.post("/batch/generate-emails")
async def batch_generate_emails(request: BatchEmailRequest):
    """
    request: {
        lead_ids: [1, 2, 3, ...],
        tone: "professional",
    }
    """
    job = await email_generation_queue.add(request)

@router.post("/batch/launch-campaign")
async def batch_launch_campaign(request: BatchCampaignRequest):
    """
    request: {
        campaign_id: 1,
        lead_ids: [1, 2, 3, ...],
        send_schedule: {"immediate": 50, "delay_hours_2": 50},
    }
    """

@router.get("/batch/status/{job_id}")
async def batch_job_status(job_id: str):
    """Check async batch job progress."""

@router.post("/batch/update-crm/{job_id}")
async def batch_sync_to_crm(job_id: str):
    """After batch operation, push results to CRM."""
```

#### Job Queue (Redis/Celery)

```python
# src/ghost_investor_ai/tasks.py
from celery import Celery

celery_app = Celery('ghost_investor_ai')

@celery_app.task
def enrich_leads_batch(lead_ids: List[int]):
    """Background job: enrich multiple leads."""
    results = []
    for lead_id in lead_ids:
        lead = db.query(Lead).get(lead_id)
        enriched = await EnrichmentService.enrich_lead(lead)
        results.append(enriched)
    return results

@celery_app.task
def generate_emails_batch(lead_ids: List[int], tone: str):
    """Background job: generate emails for multiple leads."""
    for lead_id in lead_ids:
        lead = db.query(Lead).get(lead_id)
        email = AIEmailService.generate_first_touch(lead)
        # ...
```

---

## Phase 2: Scale Requirements (Weeks 7-10)

### 2.1 Analytics Dashboard

**Goal:** Operational visibility for campaign performance.

#### Key Metrics

```python
class CampaignAnalytics:
    total_sent: int
    open_rate: float  # Replied / Sent
    positive_reply_rate: float  # "Interested" / Replied
    follow_up_conversion: float  # Meetings booked / Sent
    investor_stage_distribution: dict  # {stage: count}
    average_response_time: timedelta
    
    # By investor
    top_responders: List[Lead]
    most_interested_stage: str
    
    # Trends
    engagement_trend: List[float]  # 7-day rolling average
    best_send_times: dict  # {hour: reply_rate}
```

#### Dashboard Endpoints

```
GET /api/analytics/campaigns/{campaign_id}/summary
GET /api/analytics/campaigns/{campaign_id}/by-day
GET /api/analytics/campaigns/{campaign_id}/investor-breakdown
GET /api/analytics/lead/{lead_id}/interaction-history
GET /api/analytics/overall-performance?start_date=&end_date=
```

### 2.2 Webhook Support

```python
# src/ghost_investor_ai/webhooks.py

WEBHOOK_EVENTS = {
    "email.sent": "Outreach sent",
    "email.opened": "Investor opened email",
    "email.replied": "Reply received",
    "reply.classified": "Reply categorized (interested/etc)",
    "task.created": "CRM task created",
    "lead.updated": "Lead context changed",
    "campaign.completed": "Campaign finished",
}

@router.post("/webhooks/register")
async def register_webhook(url: str, events: List[str]):
    """
    Register webhook URL for events.
    Events: email.sent, email.replied, task.created, etc.
    """

async def send_webhook(event: str, data: dict):
    """Deliver webhook to registered targets."""
    for webhook in get_webhooks(event):
        await client.post(webhook.url, json={
            "event": event,
            "timestamp": datetime.now().isoformat(),
            "data": data,
        })
```

---

## Phase 3: Expansion (Weeks 11+)

### 3.1 LinkedIn Data Import

- Careful compliance review (Terms of Service)
- Consider: Are CSV + enrichment APIs sufficient for MVP?
- Defer until volume justifies complexity

### 3.2 A/B Testing

- Lightweight variant tracking for v1
- Full framework after campaign volume enables statistical power

---

## Integration Points with Ghost Ecosystem

### With Underwriter
```
Investor Outreach reads:
- Deal metadata (company, stage, sector, valuation)
- Key strengths/differentiators
- Target investor list

Investor Outreach sends:
- Email open/reply events (for deal analytics)
- Investor interest classification
- Follow-up conversions
```

### With Strategic Briefings
```
Investor Outreach reads:
- Briefing summary (competition, market, positioning)
- Key talking points per investor segment

Investor Outreach sends:
- Investor intent data (for briefing refinement)
- Successful messaging hooks
```

### With GhostCRM
```
Bi-directional:
- Lead status, notes, communication history
- Task management
- Interaction timestamps
- Do-not-contact flags
```

---

## Technology Stack for Features

| Feature | Primary Tech | Secondary |
|---------|------------|-----------|
| Email Integration | Gmail/Outlook API | Twilio SendGrid |
| CRM Sync | REST API + Webhooks | GraphQL |
| AI Email Gen | OpenAI GPT-4 | Anthropic Claude |
| Reply Parsing | LLM + Regex | Transformers (local) |
| Batch Jobs | Celery + Redis | Bull (Node) |
| Analytics | PostgreSQL + Aggregates | TimescaleDB |
| Webhooks | HTTPx (async) | Python-webhook |

---

## Success Metrics

### Phase 1 Complete
- ✅ Can send personalized emails at scale
- ✅ Replies auto-classified with 80%+ accuracy
- ✅ CRM stays in sync (no data fragmentation)
- ✅ API rate limits prevent abuse
- ✅ Batch jobs process 100+ leads in <5 min

### Phase 2 Complete
- ✅ Dashboard shows >30% reply rate for warm lists
- ✅ Webhooks reliably trigger CRM updates
- ✅ Operational team uses analytics for decision-making

### Phase 3 Complete
- ✅ A/B testing shows statistically significant wins
- ✅ LinkedIn imports provide richer investor data

---

## Migration Timeline

```
Week 1-2:   Auth + Rate Limiting (foundation)
Week 1-3:   Gmail Integration (core)
Week 2-4:   GhostCRM Sync (data integrity)
Week 3-5:   AI Email Generation (value prop)
Week 4-6:   Reply Parsing (automation)
Week 5-6:   Batch Operations (scale)
Week 6:     Phase 1 Launch ✅

Week 7-8:   Analytics Dashboard
Week 8-9:   Webhook Support
Week 9-10:  Testing, optimization, docs
Week 10:    Phase 2 Launch ✅

Week 11+:   LinkedIn Import (optional)
            A/B Testing Framework (optional)
```

Each phase is a launchable product unto itself. Phase 1 = functional MVP. Phase 2 = production-grade. Phase 3 = expansion.
