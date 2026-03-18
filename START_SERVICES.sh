#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   GHOST INVESTOR AI - SERVICE STARTUP GUIDE                    ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo

echo -e "${YELLOW}You need to start 4 services in separate terminals.${NC}"
echo
echo -e "${YELLOW}Navigate to: /workspaces/ghost-investor-ai${NC}"
echo
echo -e "${GREEN}════ TERMINAL 1: PostgreSQL ════${NC}"
echo "Command:"
echo -e "${BLUE}docker run --name postgres-ghost -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=ghost_investor_ai -p 5432:5432 -d postgres:15${NC}"
echo
echo "Verify:"
echo -e "${BLUE}psql -h localhost -U postgres -d ghost_investor_ai -c '\\dt'${NC}"
echo

echo -e "${GREEN}════ TERMINAL 2: Redis ════${NC}"
echo "Command:"
echo -e "${BLUE}docker run --name redis-ghost -p 6379:6379 -d redis:7-alpine${NC}"
echo
echo "Verify:"
echo -e "${BLUE}redis-cli ping${NC}"
echo

echo -e "${GREEN}════ TERMINAL 3: FastAPI Server ════${NC}"
echo "Command:"
echo -e "${BLUE}cd /workspaces/ghost-investor-ai && uvicorn src.ghost_investor_ai.main:app --reload --host 0.0.0.0 --port 8000${NC}"
echo
echo "Verify:"
echo -e "${BLUE}curl http://localhost:8000/health${NC}"
echo

echo -e "${GREEN}════ TERMINAL 4: Celery Worker ════${NC}"
echo "Command:"
echo -e "${BLUE}cd /workspaces/ghost-investor-ai && celery -A src.ghost_investor_ai.services.batch_jobs worker --loglevel=info${NC}"
echo
echo "Verify:"
echo -e "${BLUE}Check for 'worker online' message in Celery logs${NC}"
echo

echo -e "${YELLOW}════════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}SETUP CHECKLIST:${NC}"
echo -e "${YELLOW}════════════════════════════════════════════════════════════════${NC}"
echo
echo "1. Copy .env.example to .env:"
echo -e "   ${BLUE}cp .env.example .env${NC}"
echo
echo "2. Edit .env with your credentials:"
echo -e "   ${BLUE}nano .env${NC}"
echo "   - Set GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET"
echo "   - Set OPENAI_API_KEY"
echo "   - Set DATABASE_URL (if using custom)"
echo "   - Set REDIS_URL (if using custom)"
echo
echo "3. Verify PostgreSQL is running:"
echo -e "   ${BLUE}psql -h localhost -U postgres -d ghost_investor_ai -c '\\dt'${NC}"
echo
echo "4. Verify Redis is running:"
echo -e "   ${BLUE}redis-cli ping${NC}"
echo "   Expected: PONG"
echo
echo "5. Verify FastAPI is running:"
echo -e "   ${BLUE}curl http://localhost:8000/health${NC}"
echo "   Expected: {\"status\": \"ok\"}"
echo
echo "6. Verify Celery is running:"
echo "   Check logs for: Ready to accept tasks"
echo
echo "7. Run tests:"
echo -e "   ${BLUE}python TEST_END_TO_END.py${NC}"
echo
echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}ALTERNATIVE: Quick Docker Compose (if available)${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"
echo
echo -e "${BLUE}docker-compose up -d${NC}"
echo

EOF
chmod +x /workspaces/ghost-investor-ai/START_SERVICES.sh
cat /workspaces/ghost-investor-ai/START_SERVICES.sh
