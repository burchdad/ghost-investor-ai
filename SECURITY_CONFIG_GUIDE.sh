#!/bin/bash

# Security Configuration Guide for Ghost Investor AI
# Last Updated: March 18, 2026

cat << 'EOF'

╔════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║               ⚠️  CONFIGURATION & SECURITY GUIDE                           ║
║                                                                            ║
║   How to safely add your real API credentials for production use           ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝

═════════════════════════════════════════════════════════════════════════════
CRITICAL SECURITY PRACTICES:
═════════════════════════════════════════════════════════════════════════════

✓ PROTECTED:
  • .env file - In .gitignore, never committed to repository
  • Local environment variables - Only on your machine
  • Docker secrets in production - Use Docker/Kubernetes secrets

✗ EXPOSED (BAD):
  • Credentials in .env.example - Use placeholders only!
  • Hard-coded secrets in source code - NEVER do this
  • Real keys in comments or documentation
  • Committing .env file to git


═════════════════════════════════════════════════════════════════════════════
STEP 1: GET YOUR REAL CREDENTIALS
═════════════════════════════════════════════════════════════════════════════

OPENAI API KEY:
───────────────
1. Go to: https://platform.openai.com/account/api-keys
2. Click "Create new secret key"
3. Copy the key (format: sk-...)
4. Store securely - you won't see it again!

Note: If you already have OpenAI credentials (like in .env.example),
you should REVOKE those immediately if they were exposed!


GMAIL OAUTH CREDENTIALS:
────────────────────────
1. Go to: https://console.cloud.google.com
2. Create a new project or select existing
3. Enable Gmail API:
   - APIs & Services → Library
   - Search for "Gmail API"
   - Click "Enable"
4. Create OAuth 2.0 credentials:
   - APIs & Services → Credentials
   - "Create Credentials" → "OAuth 2.0 Desktop Application"
   - Name it: "Ghost Investor AI"
   - Download credentials (keep secure!)
5. You'll get:
   - Client ID: look like "xxx.apps.googleusercontent.com"
   - Client Secret: starts with "GOCSPX-"


OTHER OPTIONAL SERVICES:
────────────────────────
APOLLO_API_KEY:        https://www.apollo.io/developers
CLEARBIT_API_KEY:      https://clearbit.com/api
PEOPLE_DATA_LABS_KEY:  https://www.peopledatalabs.com/api
LINKEDIN_API_KEY:      https://www.linkedin.com/developers


═════════════════════════════════════════════════════════════════════════════
STEP 2: UPDATE YOUR LOCAL .env FILE
═════════════════════════════════════════════════════════════════════════════

Guidelines:
───────────
• .env is ALREADY in .gitignore (safe to put real keys here)
• NEVER commit .env to repository
• Use for LOCAL development only
• For production, use environment variables or secrets manager


Format:
───────
# LLM - OpenAI (your real key)
OPENAI_API_KEY=sk-proj-your-actual-key-here

# Email Integration - Gmail (your real credentials)
GMAIL_CLIENT_ID=your-actual-client-id.apps.googleusercontent.com
GMAIL_CLIENT_SECRET=GOCSPX-your-actual-secret


Example .env file (with YOUR credentials):
───────────────────────────────────────────

DATABASE_URL=postgresql://user:password@postgres:5432/ghost_investor_ai

# API Keys - Enrichment (optional - leave as-is for testing)
APOLLO_API_KEY=test_apollo_key
CLEARBIT_API_KEY=test_clearbit_key
PEOPLE_DATA_LABS_API_KEY=test_pdl_key

# LLM - REPLACE WITH YOUR KEY
OPENAI_API_KEY=sk-proj-YOUR_ACTUAL_OPENAI_KEY_HERE

# Email Integration - Gmail - REPLACE WITH YOUR CREDENTIALS
GMAIL_CLIENT_ID=YOUR_ACTUAL_CLIENT_ID.apps.googleusercontent.com
GMAIL_CLIENT_SECRET=YOUR_ACTUAL_CLIENT_SECRET
GOOGLE_CREDENTIALS_JSON=credentials.json

# Email Integration - Outlook (optional)
OUTLOOK_CLIENT_ID=
OUTLOOK_CLIENT_SECRET=

# CRM Integration (stubbed - no changes needed)
GHOSTCRM_API_KEY=dummy_key_stubbed
GHOSTCRM_BASE_URL=http://localhost:9999

# LinkedIn (optional)
LINKEDIN_API_KEY=

# JWT Authentication (change in production)
JWT_SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Rate Limiting
RATE_LIMIT_EMAIL_PER_HOUR=50
RATE_LIMIT_UNIQUE_RECIPIENTS_PER_DAY=500

# Celery & Redis
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND_URL=redis://redis:6379/1

# App Config
ENVIRONMENT=development
DEBUG=True
LOG_LEVEL=INFO


═════════════════════════════════════════════════════════════════════════════
STEP 3: RESTART YOUR SERVICES
═════════════════════════════════════════════════════════════════════════════

After updating .env with real credentials:

docker-compose down
docker-compose up -d

The containers will reload with your new credentials.

Verify:
  curl http://localhost:8000/health


═════════════════════════════════════════════════════════════════════════════
STEP 4: TEST YOUR CONFIGURATION
═════════════════════════════════════════════════════════════════════════════

Run the test suite:

python TEST_END_TO_END.py

All 8 steps should now work (if credentials are valid):
  1. ✓ Gmail OAuth
  2. ✓ Send test email
  3. ✓ Create test lead
  4. ✓ Generate AI email (uses OpenAI)
  5. ✓ Launch campaign
  6. ✓ Reply to email
  7. ✓ Parse reply
  8. ✓ View activity timeline


═════════════════════════════════════════════════════════════════════════════
SECURITY CHECKLIST:
═════════════════════════════════════════════════════════════════════════════

Before committing anything:

☐ Is .env in .gitignore?          → git check-ignore .env
☐ Does .env.example have placeholders only?
☐ No real keys in any source files?  → grep -r "sk-proj-" src/
☐ No real keys in documentation?     → grep -r "GOCSPX-" *.md
☐ .env file exists and is filled with YOUR credentials?
☐ No .env file staged for commit?    → git status


═════════════════════════════════════════════════════════════════════════════
IF CREDENTIALS WERE EXPOSED:
═════════════════════════════════════════════════════════════════════════════

If you accidentally committed real keys to GitHub:

1. REVOKE the credentials immediately:
   • OpenAI: Delete the API key from your account
   • Gmail: Revoke OAuth tokens in Google Cloud Console
   • Any other services: Disable the exposed credentials

2. Generate new credentials:
   • Create new API keys
   • Update .env with new keys
   • Restart services

3. Clean git history (if needed):
   • Use: git-filter-repo or BFG repo cleaner
   • Or update commit with sanitized version
   • Force push only if you own the repo


═════════════════════════════════════════════════════════════════════════════
PRODUCTION DEPLOYMENT:
═════════════════════════════════════════════════════════════════════════════

NEVER hardcode credentials. Instead:

1. Use environment variables:
   export OPENAI_API_KEY="sk-..."
   export GMAIL_CLIENT_ID="..."

2. Use container secrets (Docker/Kubernetes):
   docker secret create openai_key -
   kubectl create secret generic api-keys --from-literal=openai_key=...

3. Use a secrets manager:
   • AWS Secrets Manager
   • HashiCorp Vault
   • Azure Key Vault
   • 1Password / LastPass


═════════════════════════════════════════════════════════════════════════════
FILES TO REMEMBER:
═════════════════════════════════════════════════════════════════════════════

Public (in git repository):
  • .env.example       ← Template with placeholders
  • .gitignore         ← Protects .env from commits
  • README.md          ← Setup instructions
  • All source code

Private (NOT in repository):
  • .env               ← Your real credentials
  • .env.local         ← Local overrides
  • credentials.json   ← Gmail OAuth credentials file
  • Any API keys


═════════════════════════════════════════════════════════════════════════════
QUICK START:
═════════════════════════════════════════════════════════════════════════════

1. Get credentials from services (see STEP 1 above)

2. Update .env:
   cp .env.example .env
   nano .env  # Add your real credentials

3. Restart services:
   docker-compose down && docker-compose up -d

4. Test:
   python TEST_END_TO_END.py

5. Verify it's not committed:
   git status
   # Should NOT show .env or credentials


═════════════════════════════════════════════════════════════════════════════

Questions? See:
  • TESTING_GUIDE.md        - Full testing reference
  • FINAL_TESTING_README.txt - Complete overview
  • README.md                - Project documentation

═════════════════════════════════════════════════════════════════════════════

EOF
