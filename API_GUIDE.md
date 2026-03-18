# API Usage Guide

## Overview

The Ghost Investor AI API provides RESTful endpoints for lead management, enrichment, outreach campaigning, and activity tracking.

## Authentication

Currently, the API is open (no authentication). In production, implement API keys or OAuth 2.0.

## Endpoints Reference

### Lead Management

#### Create Lead
```http
POST /api/leads/
Content-Type: application/json

{
  "email": "investor@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "company_name": "Venture Fund",
  "job_title": "Partner",
  "linkedin_url": "https://linkedin.com/in/johndoe",
  "phone": "+1-555-0123"
}
```

Response:
```json
{
  "id": 1,
  "email": "investor@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "company_name": "Venture Fund",
  "job_title": "Partner",
  "contact_score": 0.0,
  "company_score": 0.0,
  "is_enriched": false,
  "created_at": "2026-03-18T12:00:00"
}
```

#### List Leads
```http
GET /api/leads/?skip=0&limit=10
```

#### Get Lead Details
```http
GET /api/leads/1
```

#### Update Lead
```http
PUT /api/leads/1
Content-Type: application/json

{
  "email": "investor@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "company_name": "Venture Fund",
  "job_title": "Managing Partner",
  "linkedin_url": "https://linkedin.com/in/johndoe",
  "phone": "+1-555-0123"
}
```

#### Delete Lead
```http
DELETE /api/leads/1
```

#### Bulk Import from CSV
```http
POST /api/leads/import/csv
Content-Type: application/json

{
  "csv_content": "email,first_name,last_name,company_name,job_title\ninvestor1@example.com,Jane,Smith,Tech VC,Partner\ninvestor2@example.com,Bob,Johnson,Growth Capital,Principal"
}
```

### Enrichment

#### Trigger Enrichment
Enrichment runs in the background and fetches data from Apollo, Clearbit, or People Data Labs.

```http
POST /api/enrichment/enrich/1
```

Response:
```json
{
  "status": "enrichment_started",
  "lead_id": 1
}
```

#### Get Contact Score
```http
GET /api/enrichment/score/1
```

Response:
```json
{
  "lead_id": 1,
  "title_score": 0.9,
  "company_score": 0.85,
  "activity_score": 0.0,
  "engagement_score": 0.0,
  "total_score": 0.6875,
  "score_reason": "Strong investor title (score: 0.90) | Relevant company (score: 0.85)"
}
```

#### Recalculate Score
```http
POST /api/enrichment/score/1/recalculate
```

### Campaigns

#### Create Campaign
```http
POST /api/campaigns/
Content-Type: application/json

{
  "name": "Q1 2026 Seed Investors",
  "description": "Outreach to early-stage VC investors",
  "follow_up_delays": [0, 48, 120]
}
```

Response:
```json
{
  "id": 1,
  "name": "Q1 2026 Seed Investors",
  "status": "draft",
  "email_count": 0,
  "created_at": "2026-03-18T12:00:00"
}
```

#### Get Campaign
```http
GET /api/campaigns/1
```

#### Add Lead to Campaign
Automatically generates personalized email for the lead.

```http
POST /api/campaigns/1/add-lead/1
```

Response:
```json
{
  "email_id": 1,
  "lead_id": 1,
  "subject": "Quick thought for John re: Venture Fund",
  "added_at": "2026-03-18T12:00:00"
}
```

#### Schedule Campaign
Mark campaign as scheduled and get send schedule.

```http
POST /api/campaigns/1/schedule
```

Response:
```json
{
  "campaign_id": 1,
  "status": "scheduled",
  "send_count": 3,
  "schedule": [
    {
      "email_id": 1,
      "lead_email": "investor@example.com",
      "subject": "Quick thought for John re: Venture Fund",
      "body": "...",
      "send_at": "immediately"
    },
    {
      "email_id": 2,
      "lead_email": "investor@example.com",
      "subject": "Follow-up #1: ...",
      "body": "...",
      "send_at": "2026-03-20T12:00:00"
    }
  ]
}
```

#### Pause Campaign
```http
POST /api/campaigns/1/pause
```

#### Resume Campaign
```http
POST /api/campaigns/1/resume
```

### Activities

#### Log Activity
```http
POST /api/activities/
Content-Type: application/json

{
  "lead_id": 1,
  "activity_type": "email_sent",
  "description": "Initial outreach sent via campaign Q1 2026 Seed Investors"
}
```

Response:
```json
{
  "id": 1,
  "lead_id": 1,
  "activity_type": "email_sent",
  "description": "Initial outreach sent via campaign Q1 2026 Seed Investors",
  "event_timestamp": "2026-03-18T12:00:00",
  "synced_to_crm": false
}
```

#### Get Lead Timeline
```http
GET /api/activities/lead/1
```

Response:
```json
{
  "lead_id": 1,
  "activities": [
    {
      "id": 1,
      "type": "email_sent",
      "description": "Initial outreach sent via campaign...",
      "timestamp": "2026-03-18T12:00:00",
      "synced_to_crm": false
    }
  ]
}
```

#### Sync Activity to CRM
```http
POST /api/activities/1/sync-crm?crm_id=crm_activity_123
```

## Common Workflows

### Complete Lead Enrichment

1. Create lead
   ```bash
   curl -X POST http://localhost:8000/api/leads/ \
     -H "Content-Type: application/json" \
     -d '{"email": "...", "first_name": "...", ...}'
   ```

2. Trigger enrichment
   ```bash
   curl -X POST http://localhost:8000/api/enrichment/enrich/1
   ```

3. Check score
   ```bash
   curl http://localhost:8000/api/enrichment/score/1
   ```

### Campaign Outreach

1. Create campaign
2. Add leads to campaign
3. Schedule campaign
4. Track activity

## Error Handling

The API returns standard HTTP status codes:

- `200` - Success
- `201` - Created
- `400` - Bad Request
- `404` - Not Found
- `500` - Server Error

Error responses include details:
```json
{
  "detail": "Lead with this email already exists"
}
```

## Rate Limiting

Currently unlimited. Production deployment should implement rate limiting via FastAPI middleware.

## CORS Configuration

CORS is enabled for all origins (`allow_origins=["*"]`). For production, restrict to specific domains.

## Pagination

List endpoints support pagination via `skip` and `limit` query parameters (default: skip=0, limit=100).

## Testing

Use the provided `examples.py` script:
```bash
python examples.py
```

Or use cURL:
```bash
curl -X GET http://localhost:8000/health
```
