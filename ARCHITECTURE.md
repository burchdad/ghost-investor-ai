# Project Structure

```
ghost-investor-ai/
├── src/
│   └── ghost_investor_ai/
│       ├── __init__.py                    # Package initialization
│       ├── config.py                      # Configuration management
│       ├── database.py                    # Database session and engine setup
│       ├── models.py                      # SQLAlchemy ORM models
│       ├── main.py                        # FastAPI application factory
│       │
│       ├── services/                      # Business logic layer
│       │   ├── __init__.py               # LeadImportService
│       │   ├── enrichment.py             # Enrichment adapters (Apollo, Clearbit, PDL)
│       │   ├── scoring.py                # Contact scoring engine
│       │   ├── email_drafting.py         # Email generation
│       │   ├── outreach_sequence.py      # Campaign and sequence management
│       │   └── activity_logging.py       # Activity tracking
│       │
│       └── api/                           # API layer
│           ├── __init__.py               # Pydantic schemas
│           ├── routes_leads.py           # Lead CRUD endpoints
│           ├── routes_enrichment.py      # Enrichment endpoints
│           ├── routes_campaigns.py       # Campaign management endpoints
│           └── routes_activities.py      # Activity logging endpoints
│
├── alembic/                               # Database migrations
│   ├── env.py                            # Migration environment
│   ├── alembic.ini                       # Migration config
│   └── versions/                         # Migration scripts
│       └── 001_initial.py                # Initial schema
│
├── tests.py                              # Unit tests
├── examples.py                           # Example usage workflows
├── cli.py                                # CLI commands
├── Makefile                              # Development tasks
│
├── pyproject.toml                        # Python project metadata
├── requirements.txt                      # Python dependencies
├── .env.example                          # Environment variables template
├── .gitignore                            # Git ignore rules
│
├── Dockerfile                            # Docker image definition
├── docker-compose.yml                    # Docker Compose setup
│
├── README.md                             # Project documentation
├── API_GUIDE.md                          # API usage guide
└── ARCHITECTURE.md                       # This file
```

## Module Responsibilities

### Core Application
- **config.py**: Loads environment variables into a Settings object
- **database.py**: Creates SQLAlchemy engine, session factory, and dependency injection
- **models.py**: Defines ORM models for all data entities
- **main.py**: Sets up FastAPI app with middleware, routers, and lifecycle events

### Services (Business Logic)
Each service is responsible for a specific domain:

#### `services/__init__.py` - Lead Import Service
- Imports leads from CSV
- Handles manual lead creation batches
- Validates data and checks for duplicates
- Returns import statistics

#### `services/enrichment.py` - Enrichment Service
- **Adapters**: Apollo, Clearbit, People Data Labs
- Each adapter fetches data from external API
- Main service tries multiple adapters in sequence
- Updates lead with enriched data

#### `services/scoring.py` - Contact Scoring
- Scores leads on multiple factors:
  - Job title relevance
  - Company size and industry
  - Activity count
  - Email engagement
- Weighted scoring system
- Stores scores with reasoning

#### `services/email_drafting.py` - Email Generation
- Personalization factor extraction
- Subject line templates
- Email body generation
- Opening/body/closing combinations
- Follow-up email templates

#### `services/outreach_sequence.py` - Campaign Management
- Campaign creation and status tracking
- Follow-up sequence scheduling
- Send schedule calculation
- Campaign pause/resume

#### `services/activity_logging.py` - Activity Tracking
- Log various activity types:
  - email_sent, email_opened, email_clicked
  - reply_received, manual activities
- CRM sync tracking
- Timeline retrieval

### API (REST Layer)

#### `api/__init__.py` - Schemas
- Pydantic models for request/response validation
- Type safety and documentation
- Includes:
  - Lead schemas
  - Enrichment schemas
  - Campaign schemas
  - Activity schemas

#### `api/routes_*.py` - Endpoint Handlers
Each route file handles a domain:
- **routes_leads.py**: CRUD for leads, CSV import
- **routes_enrichment.py**: Enrichment triggering, scoring
- **routes_campaigns.py**: Campaign CRUD, lead assignment, scheduling
- **routes_activities.py**: Activity logging, timeline, CRM sync

All routes:
- Use dependency injection for database
- Return consistent response formats
- Include proper error handling
- Are tagged for documentation

## Data Flow

### Lead Import Flow
```
CSV/Manual Input → LeadImportService 
  → Validate → Check Duplicates 
  → Create Lead Objects 
  → Persist to DB 
  → Return Statistics
```

### Enrichment Flow
```
GET /enrich/{lead_id}
  → BackgroundTask
    → EnrichmentService.enrich_lead()
      → Try Apollo Adapter
      → Try Clearbit Adapter
      → Try PDL Adapter
      → Update Lead with First Success
    → ContactScoringService.calculate_score()
    → Persist to DB
```

### Campaign Outreach Flow
```
POST /campaigns/
  → Create OutreachCampaign
  
POST /campaigns/{id}/add-lead/{lead_id}
  → EmailDraftingService.draft_email(lead)
  → Create OutreachEmail
  → Create FollowUpEmails (sequence)
  → Return Email Preview

POST /campaigns/{id}/schedule
  → Update Status to SCHEDULED
  → Calculate Send Times
  → Return Send Schedule
```

### Activity Tracking Flow
```
Action (email sent, opened, etc.)
  → ActivityLoggingService.log_*()
  → Create Activity Record
  → Optional: Sync to CRM
  → Persist to DB
  
GET /activities/lead/{id}
  → Query All Activities
  → Sort by Timestamp
  → Return Timeline
```

## Database Schema

### Leads
- Core lead data (email, name, company, title)
- Enrichment metadata (source, is_enriched, enriched data)
- Scoring (contact_score, company_score, engagement_score)

### ContactScore
- Breakdown of scoring factors
- Detailed reasoning for score
- Time tracking for score recalculation

### OutreachEmail
- Drafted email content
- Personalization factors
- Send status and timestamp

### OutreachCampaign
- Campaign metadata and status
- Follow-up sequence definition (JSON)
- Campaign timeline (created, started, ended)

### FollowUpEmail
- Follow-up in sequence
- Delay calculation
- Individual send tracking

### Activity
- All interactions logged
- Timestamp and type
- CRM sync status

### InvestorProfile
- Investment preferences
- Recent activity
- Communication preferences

## API Design Principles

1. **RESTful**: Standard HTTP methods and status codes
2. **Documented**: OpenAPI/Swagger integration
3. **Versioned**: API v1 in base path
4. **Paginated**: List endpoints support skip/limit
5. **Validated**: Pydantic schema validation
6. **Error-aware**: Meaningful error messages
7. **Async-ready**: Async endpoints where beneficial

## Configuration

Environment variables loaded via `config.py`:
- Database URL (PostgreSQL)
- API keys for enrichment services
- Email service credentials
- CRM integration credentials
- Application settings (debug, logging)

See `.env.example` for all available options.

## Testing Strategy

- **Unit tests**: Service logic (`tests.py`)
- **Integration tests**: Database + services
- **API tests**: Endpoint behavior
- **Example workflows**: Real usage patterns

Run tests:
```bash
pytest                    # Run all tests
pytest --cov=src         # With coverage
pytest tests.py::test_*  # Specific tests
```

## Performance Considerations

1. **Database**: Connection pooling (10 connections, max 20 overflow)
2. **Enrichment**: Async HTTP calls, background tasks for long operations
3. **Pagination**: Limits on list endpoints (default 100)
4. **Indexing**: Indexed fields: email, lead_id, activity_type
5. **Caching**: Consider Redis for enrichment results

## Security Notes

1. **API**: Currently open - add authentication in production
2. **CORS**: Currently allows all origins - restrict as needed
3. **Database**: Use connection strings with credentials
4. **API Keys**: Load from environment only, never in code
5. **Rate Limiting**: Implement per-endpoint in production

## Deployment

### Local Development
```bash
make dev-install
make db-init
make run
```

### Docker
```bash
docker-compose up -d
```

### Production
- Use PostgreSQL (not SQLite)
- Set ENVIRONMENT=production
- Add authentication/authorization
- Configure CORS properly
- Set up monitoring/logging
- Use environment-specific config
- Consider load balancing
- Set up database backups
