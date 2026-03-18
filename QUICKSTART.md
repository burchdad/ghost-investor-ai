# Getting Started

## Quick Setup (5 minutes)

### Prerequisites
- Python 3.10 or higher
- PostgreSQL 13+ OR Docker & Docker Compose

### Option 1: Local Setup (without Docker)

1. **Clone and navigate**
   ```bash
   cd ghost-investor-ai
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   make dev-install
   # OR: pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your database URL and API keys
   ```

5. **Initialize database**
   ```bash
   make db-init
   # OR: python cli.py db-init
   ```

6. **Start server**
   ```bash
   make run
   # OR: python cli.py run
   ```

Server running at: http://localhost:8000
API docs at: http://localhost:8000/docs

### Option 2: Docker Setup (Recommended)

1. **Clone and navigate**
   ```bash
   cd ghost-investor-ai
   ```

2. **Start containers**
   ```bash
   docker-compose up -d
   ```

   This automatically:
   - Starts PostgreSQL database
   - Initializes database schema
   - Starts FastAPI server in watch mode

3. **Verify it's working**
   ```bash
   curl http://localhost:8000/health
   ```

4. **View API docs**
   Open http://localhost:8000/docs in your browser

## First Steps

### 1. Create a Sample Lead

```bash
curl -X POST http://localhost:8000/api/leads/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "investor@example.com",
    "first_name": "Jane",
    "last_name": "Smith",
    "company_name": "Venture Fund",
    "job_title": "Managing Partner",
    "linkedin_url": "https://linkedin.com/in/janesmith",
    "phone": "+1-555-0123"
  }'
```

Response will include `id: 1` for the created lead.

### 2. Trigger Enrichment (requires API keys)

```bash
curl -X POST http://localhost:8000/api/enrichment/enrich/1
```

This triggers background enrichment from Apollo, Clearbit, or People Data Labs.

### 3. Check Contact Score

```bash
curl http://localhost:8000/api/enrichment/score/1
```

### 4. Create an Outreach Campaign

```bash
curl -X POST http://localhost:8000/api/campaigns/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Q1 2026 Outreach",
    "description": "Initial outreach to seed investors",
    "follow_up_delays": [0, 48, 120]
  }'
```

### 5. Add Lead to Campaign (generates email)

```bash
curl -X POST http://localhost:8000/api/campaigns/1/add-lead/1
```

### 6. Schedule Campaign

```bash
curl -X POST http://localhost:8000/api/campaigns/1/schedule
```

### 7. Log Activity

```bash
curl -X POST http://localhost:8000/api/activities/ \
  -H "Content-Type: application/json" \
  -d '{
    "lead_id": 1,
    "activity_type": "email_sent",
    "description": "Initial outreach sent"
  }'
```

### 8. View Lead Timeline

```bash
curl http://localhost:8000/api/activities/lead/1
```

## Running Examples

```bash
# Run example workflows (requires server running)
python examples.py
```

This will:
1. Create a lead
2. Trigger enrichment
3. Get contact score
4. Create a campaign
5. Add lead to campaign
6. Schedule sends
7. Log activities
8. Get lead timeline

## Common Commands

```bash
# Development
make dev-install          # Install with dev tools
make lint                # Check code quality
make format              # Auto-format code
make test                # Run tests
make test-cov            # Tests with coverage

# Database
make db-init             # Initialize database
make db-drop             # Drop all tables (careful!)

# Running
make run                 # Start development server
make docker-up           # Start Docker containers
make docker-down         # Stop Docker containers
make docker-logs         # View server logs

# Code quality
black src/               # Format code
ruff check src/          # Lint code
mypy src/                # Type check
```

## Project Files to Know

- **README.md**: Project overview and features
- **API_GUIDE.md**: Complete API reference
- **ARCHITECTURE.md**: System design and data flow
- **examples.py**: Example usage patterns
- **tests.py**: Unit tests and test patterns

## Adding API Keys

1. Get API keys from:
   - Apollo: https://apollo.io/
   - Clearbit: https://clearbit.com/
   - People Data Labs: https://www.peopledatalabs.com/

2. Add to `.env`:
   ```env
   APOLLO_API_KEY=your-key-here
   CLEARBIT_API_KEY=your-key-here
   PEOPLE_DATA_LABS_API_KEY=your-key-here
   ```

3. Restart server and enrichment will work!

## Troubleshooting

### Database connection error
```
ERROR: could not connect to server
```

Solution: Check DATABASE_URL in `.env` is correct:
```env
DATABASE_URL=postgresql://user:password@localhost:5432/ghost_investor_ai
```

### Port already in use
```
Address already in use: ('0.0.0.0', 8000)
```

Solution: Use different port:
```bash
python cli.py run --port 8001
```

### Module import errors
```
ModuleNotFoundError: No module named 'src.ghost_investor_ai'
```

Solution: Make sure you're in the project root and venv is activated:
```bash
cd ghost-investor-ai
source venv/bin/activate
```

### Docker container won't start
```
docker-compose up          # Check logs
docker-compose down        # Clean up
docker-compose up -d       # Restart
```

## Database Browser (Optional)

To inspect the database:

```bash
# Using psql (PostgreSQL client)
psql postgresql://user:password@localhost:5432/ghost_investor_ai

# Then:
\dt                    # List tables
SELECT * FROM leads;   # View leads
```

Or use a GUI tool like [pgAdmin](https://www.pgadmin.org/) or [DBeaver](https://dbeaver.io/)

## Next Steps

1. **Read API_GUIDE.md** for complete endpoint documentation
2. **Read ARCHITECTURE.md** for system design
3. **Explore examples.py** for usage patterns
4. **Add authentication** for production use
5. **Configure email services** (Gmail, Outlook)
6. **Connect to GhostCRM** for bi-directional sync
7. **Set up monitoring** and error tracking

## Need Help?

- Check the documentation files
- Review examples in `examples.py`
- Look at API docs at http://localhost:8000/docs
- Check test cases in `tests.py`

Happy building!
