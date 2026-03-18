# Ghost Investor AI

AI-powered lead enrichment and investor outreach orchestration platform. Designed to integrate with orchestrator systems via REST API.

## Features

### Core Modules

- **Lead Import**: CSV, manual, and API-based lead imports
- **Enrichment Adapters**: Apollo, Clearbit, People Data Labs integration
- **Contact Scoring**: Multi-factor lead quality scoring
- **Email Drafting**: Personalized outreach email generation
- **Outreach Sequences**: Campaign management with follow-up cadence
- **Activity Logging**: Full interaction tracking and CRM sync
- **Investor Profiles**: Investment stage, sectors, and preference data

### MVP Outputs

- Enriched lead records with company and contact data
- "Best first outreach" personalized email drafts
- Configurable follow-up cadence (default: immediate, 2 days, 5 days)
- Investor profile summary
- Activity timeline and engagement metrics

## API Overview

### Leads
- `POST /api/leads/` - Create new lead
- `GET /api/leads/` - List leads
- `GET /api/leads/{lead_id}` - Get lead details
- `PUT /api/leads/{lead_id}` - Update lead
- `DELETE /api/leads/{lead_id}` - Delete lead
- `POST /api/leads/import/csv` - Bulk import from CSV

### Enrichment
- `POST /api/enrichment/enrich/{lead_id}` - Trigger enrichment
- `GET /api/enrichment/score/{lead_id}` - Get contact score
- `POST /api/enrichment/score/{lead_id}/recalculate` - Recalculate score

### Campaigns
- `POST /api/campaigns/` - Create campaign
- `GET /api/campaigns/{campaign_id}` - Get campaign details
- `POST /api/campaigns/{campaign_id}/add-lead/{lead_id}` - Add lead with generated email
- `POST /api/campaigns/{campaign_id}/schedule` - Schedule campaign sends
- `POST /api/campaigns/{campaign_id}/pause` - Pause campaign
- `POST /api/campaigns/{campaign_id}/resume` - Resume campaign

### Activities
- `POST /api/activities/` - Log activity
- `GET /api/activities/lead/{lead_id}` - Get lead timeline
- `POST /api/activities/{activity_id}/sync-crm` - Sync to CRM

## Quick Start

### Prerequisites
- Python 3.10+
- PostgreSQL 13+
- API keys (optional): Apollo, Clearbit, People Data Labs

### Installation

1. **Clone repository**
   ```bash
   git clone https://github.com/burchdad/ghost-investor-ai.git
   cd ghost-investor-ai
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your settings and API keys
   ```

5. **Initialize database**
   ```bash
   python cli.py db-init
   ```

6. **Run server**
   ```bash
   python cli.py run
   ```

   API will be available at `http://localhost:8000`
   Docs at `http://localhost:8000/docs`

### Docker Setup

```bash
docker-compose up -d
```

## Architecture

### Database Schema

- **leads** - Lead records with enrichment data
- **contact_scores** - Detailed scoring breakdown
- **outreach_emails** - Generated emails
- **outreach_campaigns** - Campaign metadata
- **follow_up_emails** - Follow-up sequence emails
- **activities** - Interaction log
- **investor_profiles** - Investment preference data

### Service Layer

- `EnrichmentService` - Coordinates enrichment adapters
- `ContactScoringService` - Multi-factor scoring logic
- `EmailDraftingService` - Email generation
- `OutreachSequenceService` - Campaign and sequence management
- `ActivityLoggingService` - Activity tracking and CRM sync
- `LeadImportService` - Lead ingestion

### API Design

- RESTful API with FastAPI
- Pydantic models for validation
- Async/await for non-blocking operations
- Background tasks for long-running operations
- Health check endpoint for orchestrator integration

## Orchestrator Integration

This service is designed to be called by an AI mission control orchestrator:

```bash
# Health check
curl http://localhost:8000/health

# Create lead
curl -X POST http://localhost:8000/api/leads/ \
  -H "Content-Type: application/json" \
  -d '{"email": "investor@example.com", "first_name": "John", ...}'

# Trigger enrichment
curl -X POST http://localhost:8000/api/enrichment/enrich/1

# Get contact score
curl http://localhost:8000/api/enrichment/score/1

# Create campaign
curl -X POST http://localhost:8000/api/campaigns/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Q1 Outreach", "description": "..."}'

# Add lead to campaign with email
curl -X POST http://localhost:8000/api/campaigns/1/add-lead/1

# Schedule campaign
curl -X POST http://localhost:8000/api/campaigns/1/schedule
```

## Configuration

Set environment variables or edit `.env`:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/ghost_investor_ai

# Enrichment API Keys
APOLLO_API_KEY=
CLEARBIT_API_KEY=
PEOPLE_DATA_LABS_API_KEY=

# Email Services
GMAIL_CLIENT_ID=
GMAIL_CLIENT_SECRET=
OUTLOOK_CLIENT_ID=
OUTLOOK_CLIENT_SECRET=

# CRM Integration
GHOSTCRM_API_KEY=
GHOSTCRM_BASE_URL=

# App Settings
ENVIRONMENT=production
DEBUG=False
LOG_LEVEL=INFO
```

## Development

### Project Structure
```
src/ghost_investor_ai/
├── __init__.py
├── config.py          # Configuration management
├── database.py        # Database setup
├── models.py          # SQLAlchemy models
├── main.py            # FastAPI app
├── services/          # Business logic
│   ├── enrichment.py
│   ├── scoring.py
│   ├── email_drafting.py
│   ├── outreach_sequence.py
│   └── activity_logging.py
└── api/               # API routes
    ├── routes_leads.py
    ├── routes_enrichment.py
    ├── routes_campaigns.py
    └── routes_activities.py
```

### Testing
```bash
pytest
pytest --cov=src
```

### Code Quality
```bash
black src/
ruff check src/
mypy src/
```

## Roadmap

### Phase 1: Launch Requirements

These features are essential for a functional investor outreach tool:

- [ ] **Email service integration (Gmail, Outlook)** - Core capability; enables actual sending and reply tracking
- [ ] **GhostCRM bi-directional sync** - Prevents data fragmentation; allows other Ghost modules (Marketing, Strategic Briefings) to reference the same records
- [ ] **Advanced AI email generation** - Customized intros, follow-up sequences, tone adaptation, deal-specific templates
- [ ] **Reply parsing and sentiment analysis** - Classifies responses (interested, not interested, later, unsubscribe); triggers automation
- [ ] **Rate limiting and authentication** - Essential for security, sender reputation, and API protection
- [ ] **Batch operations** - Bulk enrichment, generate multiple personalized emails, launch sequences at scale

### Phase 2: Scale Requirements

These enable operational visibility and ecosystem integration:

- [ ] **Analytics dashboard** - Shows: sent count, open/reply rates, positive reply %, follow-up conversion, investor stage distribution
- [ ] **Webhook support for events** - Triggers: email sent → update CRM, reply received → create task, investor marked interested → notify other modules

### Phase 3: Expansion

These enhance capability but can launch later:

- [ ] **LinkedIn data import (with compliance)** - Richer profiles, validation; can defer in favor of CSV + enrichment APIs early on
- [ ] **A/B testing framework** - Advanced once volume enables statistical rigor; lightweight variant tracking sufficient for v1

## License

MIT

## Support

For issues or questions, open an issue on GitHub or contact the team.