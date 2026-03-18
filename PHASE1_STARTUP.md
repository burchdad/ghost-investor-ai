"""PHASE 1 STARTUP GUIDE

Quick start for running Ghost Investor AI Phase 1 locally.

## Prerequisites

- Python 3.10+
- PostgreSQL 13+
- Redis 7+
- Docker & Docker Compose (optional, recommended)
- Gmail & Outlook OAuth credentials (optional for email)
- OpenAI API key

## Option 1: Run with Docker Compose (Recommended)

### Step 1: Setup Environment
```bash
cd /workspaces/ghost-investor-ai
cp .env.example .env

# Edit .env with your credentials:
# - OPENAI_API_KEY
# - GMAIL_CLIENT_ID & GMAIL_CLIENT_SECRET
# - JWT_SECRET_KEY (can be any string)
nano .env
```

### Step 2: Start Services
```bash
# This starts: PostgreSQL, Redis, API, Celery Worker
docker-compose up -d

# Check services
docker-compose ps

# View logs
docker-compose logs -f
```

### Step 3: Initialize Database
```bash
# Run migrations
docker exec ghost_investor_ai_api alembic upgrade head

# Or create tables
docker exec ghost_investor_ai_api python -c "
from src.ghost_investor_ai.database import Base, engine
Base.metadata.create_all(bind=engine)
print('Tables created')
"
```

### Step 4: Test API
```bash
# Health check
curl http://localhost:8000/health

# You should see: {"status":"ok"}
```

---

## Option 2: Run Locally (Manual Setup)

### Step 1: Install Dependencies
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate

# Install requirements
pip install -r requirements.txt
```

### Step 2: Setup Database
```bash
# Start PostgreSQL (if not already running)
# macOS: brew services start postgresql
# Linux: sudo systemctl start postgresql
# Windows: Use PostgreSQL app or WSL

# Create database
createdb ghost_investor_ai

# Update DATABASE_URL in .env if needed
DATABASE_URL=postgresql://localhost/ghost_investor_ai
```

### Step 3: Setup Redis
```bash
# Start Redis (if not already running)
# macOS: brew services start redis
# Linux: sudo systemctl start redis-server
# Docker: docker run -d -p 6379:6379 redis:7-alpine
```

### Step 4: Setup Environment
```bash
cp .env.example .env

# Edit .env with:
# - OPENAI_API_KEY (for email generation)
# - GMAIL credentials (optional)
# - JWT_SECRET_KEY
# - Database connections

nano .env
```

### Step 5: Create Tables
```bash
export PYTHONPATH=./src

python -c "
from ghost_investor_ai.database import Base, engine
Base.metadata.create_all(bind=engine)
print('✓ Database tables created')
"
```

### Step 6: Start Services (3 terminals)

**Terminal 1: FastAPI Server**
```bash
export PYTHONPATH=./src
uvicorn src.ghost_investor_ai.main:app --reload --port 8000
# Should see: Uvicorn running on http://127.0.0.1:8000
```

**Terminal 2: Celery Worker**
```bash
export PYTHONPATH=./src
celery -A src.ghost_investor_ai.services.batch_jobs worker --loglevel=info
# Should see: ready to accept tasks
```

**Terminal 3: Redis CLI (optional, for monitoring)**
```bash
redis-cli
> MONITOR  # See all Redis commands
```

---

## Verify Setup

### 1. Check API Health
```bash
curl http://localhost:8000/health
# Response: {"status":"ok"}
```

### 2. Check Celery Connection
```bash
# In celery worker terminal, you should see:
# celery@your-machine ready to accept tasks
```

### 3. Check Redis Connection
```bash
redis-cli ping
# Response: PONG
```

---

## Create Test Data

### Script to Create Sample Leads
```python
# test_data.py
from src.ghost_investor_ai.database import SessionLocal
from src.ghost_investor_ai.models import Lead, User, OutreachCampaign
from datetime import datetime

db = SessionLocal()

# Create test user
user = User(
    email="test@example.com",
    password_hash="hashed",
)
db.add(user)
db.commit()

# Create sample leads
leads = [
    Lead(
        email="sarah@techcorp.com",
        first_name="Sarah",
        last_name="Chen",
        company_name="TechCorp Ventures",
        job_title="Partner",
        company_industry="Technology",
        company_size="50-100",
    ),
    Lead(
        email="james@ventures.com",
        first_name="James",
        last_name="Wilson",
        company_name="Strategic Ventures",
        job_title="Investment Director",
        company_industry="Finance",
        company_size="100+",
    ),
]

for lead in leads:
    db.add(lead)
    db.commit()
    print(f"✓ Created lead: {lead.email}")

# Create sample campaign
campaign = OutreachCampaign(
    user_id=user.id,
    name="Q1 Investor Outreach",
    description="First touch to strategic investors",
    lead_count=2,
)
db.add(campaign)
db.commit()

print(f"✓ Created campaign: {campaign.name}")
```

Run it:
```bash
python test_data.py
```

---

## First Workflow: Complete Campaign

### 1. Authorize Gmail
```bash
curl -X POST http://localhost:8000/api/email-accounts/authorize/gmail \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"

# Copy the authorization_url and open in browser
# Grant permissions
# You'll get redirected with a code
```

### 2. Enrich Leads
```bash
curl -X POST http://localhost:8000/api/batch/enrich-leads \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "lead_ids": [1, 2],
    "enrichment_source": "apollo"
  }'

# Response: {"job_id": "task-xyz", "status": "submitted", "lead_count": 2}
```

### 3. Check Job Status
```bash
curl http://localhost:8000/api/batch/job-status/task-xyz \
  -H "Authorization: Bearer YOUR_TOKEN"

# Polling: keep checking until status is "SUCCESS"
```

### 4. Generate Emails
```bash
curl -X POST http://localhost:8000/api/batch/generate-emails \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "outreach_email_ids": [1, 2],
    "email_type": "first_touch"
  }'
```

### 5. Send Emails (Launch Campaign)
```bash
curl -X POST http://localhost:8000/api/batch/launch-campaign \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"campaign_id": 1}'
```

---

## Troubleshooting

### Issue: "Cannot find module 'src.ghost_investor_ai'"
**Solution:**
```bash
export PYTHONPATH=./src
# Add this to shell rc file to persist
```

### Issue: "Connection refused to localhost:5432"
**Solution:**
```bash
# Check if PostgreSQL is running
psql -U postgres -d ghost_investor_ai -c "SELECT 1"

# If not running, start it
# macOS: brew services start postgresql
# Linux: sudo systemctl start postgresql
```

### Issue: "Cannot connect to redis://localhost:6379"
**Solution:**
```bash
# Check if Redis is running
redis-cli ping

# If not, start it
# macOS: brew services start redis
# Docker: docker run -d -p 6379:6379 redis:7-alpine
```

### Issue: Celery tasks not processing
**Solutions:**
1. Check Celery worker is running
2. Check Redis connection: redis-cli PING
3. Check logs: celery log output
4. Check task in Redis: redis-cli KEYS celery\\*

### Issue: OPENAI_API_KEY errors
**Solution:**
```bash
# Make sure .env has valid OpenAI key
OPENAI_API_KEY=sk-your-actual-key-here

# Verify it's loaded
python -c "from src.ghost_investor_ai.config import settings; print(settings.openai_api_key)"
```

---

## Environment Variables Reference

```bash
# Required
DATABASE_URL=postgresql://user:password@localhost/ghost_investor_ai
OPENAI_API_KEY=sk-your-key
JWT_SECRET_KEY=your-secret-key

# Optional but recommended
GMAIL_CLIENT_ID=your-client-id
GMAIL_CLIENT_SECRET=your-secret
GHOSTCRM_API_KEY=your-key
GHOSTCRM_BASE_URL=https://crm.example.com

# Celery (defaults work for local)
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND_URL=redis://localhost:6379/1
```

---

## Next Steps

1. Read PHASE1_EXAMPLES.py for complete workflow examples
2. Consult API_GUIDE.md for endpoint documentation
3. Check ARCHITECTURE.md for system design
4. See ROADMAP.md for Phase 2 upcoming features

---

## Support

Having issues? Check:
1. Logs in docker-compose: `docker-compose logs api`
2. Celery worker logs
3. Redis monitor: `redis-cli MONITOR`
4. Database: `psql -d ghost_investor_ai -c "\\dt"`

Happy deploying! 🚀
"""