#!/bin/bash
# Ghost Investor AI - End-to-End Manual Testing Guide
# 
# Run each section step-by-step in separate terminals or sequentially
# Prerequisites:
# - PostgreSQL running
# - Redis running  
# - FastAPI server: uvicorn src.ghost_investor_ai.main:app --reload
# - Celery worker: celery -A src.ghost_investor_ai.services.batch_jobs worker --loglevel=info

set -e

API="http://localhost:8000"
USER_EMAIL="test@example.com"
USER_PASSWORD="testpass123"
LEAD_EMAIL="your.email@gmail.com"  # *** CHANGE THIS TO YOUR ACTUAL EMAIL ***

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  GHOST INVESTOR AI - END-TO-END TEST GUIDE               ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"

# ============================================================================
# SETUP: Register/Login User
# ============================================================================
echo -e "\n${YELLOW}═══ SETUP: Register Test User ═══${NC}\n"

echo "Registering user..."
REGISTER_RESPONSE=$(curl -s -X POST "$API/api/auth/register" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$USER_EMAIL\",
    \"password\": \"$USER_PASSWORD\"
  }")

echo "Response: $REGISTER_RESPONSE"

echo "Logging in..."
LOGIN_RESPONSE=$(curl -s -X POST "$API/api/auth/login" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$USER_EMAIL\",
    \"password\": \"$USER_PASSWORD\"
  }")

ACCESS_TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.access_token')
USER_ID=$(echo $LOGIN_RESPONSE | jq -r '.user_id // .id')

echo -e "${GREEN}✓ Logged in${NC}"
echo "Access Token: ${ACCESS_TOKEN:0:20}..."
echo "User ID: $USER_ID"


# ============================================================================
# STEP 1: Gmail OAuth
# ============================================================================
echo -e "\n${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}STEP 1: 🔐 Gmail OAuth Setup${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}\n"

echo "Request Gmail authorization URL..."
AUTH_RESPONSE=$(curl -s -X POST "$API/api/email-accounts/authorize/gmail" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"authorization_url": "test"}')

AUTH_URL=$(echo $AUTH_RESPONSE | jq -r '.authorization_url')
STATE=$(echo $AUTH_RESPONSE | jq -r '.state')

echo -e "${YELLOW}Manual Step Required:${NC}"
echo "1. Open this URL in your browser:"
echo "   $AUTH_URL"
echo ""
echo "2. Grant permissions when prompted"
echo "3. You'll be redirected to a URL with a 'code' parameter"
echo "4. Copy the 'code' value and paste it below"
echo ""
read -p "Enter the authorization code: " AUTH_CODE

echo ""
echo "Completing OAuth flow..."
CALLBACK_RESPONSE=$(curl -s -X POST "$API/api/email-accounts/authorize/gmail/callback" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"code\": \"$AUTH_CODE\",
    \"state\": \"$STATE\"
  }")

EMAIL_ACCOUNT_ID=$(echo $CALLBACK_RESPONSE | jq -r '.email_account_id')

if [ "$EMAIL_ACCOUNT_ID" != "null" ]; then
  echo -e "${GREEN}✓ Gmail account authorized!${NC}"
  echo "Email Account ID: $EMAIL_ACCOUNT_ID"
else
  echo -e "${RED}✗ Gmail authorization failed${NC}"
  echo "Response: $CALLBACK_RESPONSE"
fi

# Verify email account in database
echo ""
echo "Verifying email account stored..."
EMAIL_ACCOUNTS=$(curl -s -X GET "$API/api/email-accounts/" \
  -H "Authorization: Bearer $ACCESS_TOKEN")

echo -e "${GREEN}✓ Email accounts in database:${NC}"
echo $EMAIL_ACCOUNTS | jq '.accounts'


# ============================================================================
# STEP 2: Send Test Email
# ============================================================================
echo -e "\n${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}STEP 2: 📩 Send a Test Email${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}\n"

echo "Submitting email send job..."
SEND_RESPONSE=$(curl -s -X POST "$API/api/batch/send-emails" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"recipient_email\": \"$LEAD_EMAIL\",
    \"subject\": \"Test Email from Ghost Investor AI\",
    \"body\": \"This is a test email to verify the system is working.\",
    \"email_account_id\": $EMAIL_ACCOUNT_ID
  }")

SEND_JOB_ID=$(echo $SEND_RESPONSE | jq -r '.job_id')
MESSAGE_ID=$(echo $SEND_RESPONSE | jq -r '.email_id // .message_id')

echo -e "${GREEN}✓ Email send job submitted${NC}"
echo "Job ID: $SEND_JOB_ID"
echo "Message ID: $MESSAGE_ID"

echo ""
echo "Waiting for email to send (checking job status)..."
sleep 3

JOB_STATUS=$(curl -s -X GET "$API/api/batch/job-status/$SEND_JOB_ID" \
  -H "Authorization: Bearer $ACCESS_TOKEN")

echo -e "${GREEN}✓ Job status:${NC}"
echo $JOB_STATUS | jq .

echo ""
echo -e "${YELLOW}Verification:${NC}"
echo "1. Check your inbox at: $LEAD_EMAIL"
echo "2. Look for email from your Gmail account"
echo "3. Confirm subject: 'Test Email from Ghost Investor AI'"


# ============================================================================
# STEP 3: Create Test Lead
# ============================================================================
echo -e "\n${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}STEP 3: 🧪 Create a Test Lead${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}\n"

echo "Creating test lead..."
LEAD_RESPONSE=$(curl -s -X POST "$API/api/leads/" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$LEAD_EMAIL\",
    \"first_name\": \"Stephen\",
    \"last_name\": \"Test\",
    \"company_name\": \"Ghost AI\",
    \"job_title\": \"Founder\",
    \"linkedin_url\": \"https://linkedin.com/in/test\",
    \"phone\": \"+1234567890\"
  }")

LEAD_ID=$(echo $LEAD_RESPONSE | jq -r '.id')

echo -e "${GREEN}✓ Lead created${NC}"
echo "Lead ID: $LEAD_ID"
echo $LEAD_RESPONSE | jq .


# ============================================================================
# STEP 4: Generate AI Email
# ============================================================================
echo -e "\n${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}STEP 4: 🧠 Generate AI Email${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}\n"

echo "Submitting email generation job..."
GEN_RESPONSE=$(curl -s -X POST "$API/api/batch/generate-emails" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"lead_ids\": [$LEAD_ID],
    \"tone\": \"professional\",
    \"template\": \"first_touch\"
  }")

GEN_JOB_ID=$(echo $GEN_RESPONSE | jq -r '.job_id')

echo -e "${GREEN}✓ Email generation job submitted${NC}"
echo "Job ID: $GEN_JOB_ID"

echo ""
echo "Waiting for AI to generate email..."
sleep 3

GEN_STATUS=$(curl -s -X GET "$API/api/batch/job-status/$GEN_JOB_ID" \
  -H "Authorization: Bearer $ACCESS_TOKEN")

echo -e "${GREEN}✓ Generation status:${NC}"
echo $GEN_STATUS | jq .

echo ""
echo -e "${YELLOW}Verification:${NC}"
echo "1. Email should be generated with personalization for "$LEAD_NAME""
echo "2. Check tone is professional"
echo "3. Should use first-touch template"


# ============================================================================
# STEP 5: Launch Campaign
# ============================================================================
echo -e "\n${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}STEP 5: 🚀 Launch Campaign${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}\n"

echo "Creating campaign..."
CAMPAIGN_RESPONSE=$(curl -s -X POST "$API/api/campaigns/" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"Test Campaign\",
    \"description\": \"End-to-end test campaign\",
    \"email_account_id\": $EMAIL_ACCOUNT_ID
  }")

CAMPAIGN_ID=$(echo $CAMPAIGN_RESPONSE | jq -r '.id')

echo -e "${GREEN}✓ Campaign created${NC}"
echo "Campaign ID: $CAMPAIGN_ID"

echo ""
echo "Adding lead to campaign..."
curl -s -X POST "$API/api/campaigns/$CAMPAIGN_ID/add-lead/$LEAD_ID" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}' | jq .

echo -e "${GREEN}✓ Lead added${NC}"

echo ""
echo "Scheduling campaign..."
SCHEDULE_RESPONSE=$(curl -s -X POST "$API/api/campaigns/$CAMPAIGN_ID/schedule" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"delay_seconds": 1}')

echo -e "${GREEN}✓ Campaign scheduled${NC}"
echo $SCHEDULE_RESPONSE | jq .


# ============================================================================
# STEP 6: Reply to Email
# ============================================================================
echo -e "\n${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}STEP 6: 📬 Reply to Email${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}\n"

echo -e "${YELLOW}Manual Step Required:${NC}"
echo "1. Open your email: $LEAD_EMAIL"
echo "2. Find the email from step 2 (Test Email from Ghost Investor AI)"
echo "3. Reply with something like:"
echo "   'This is interesting, can you send more info?'"
echo ""
read -p "Press ENTER after you've sent the reply... "

echo -e "${GREEN}✓ Waiting for reply to arrive in system...${NC}"
sleep 5


# ============================================================================
# STEP 7: Verify Reply Parsing
# ============================================================================
echo -e "\n${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}STEP 7: 🧠 Verify Reply Parsing${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}\n"

echo "Getting contact score..."
SCORE_RESPONSE=$(curl -s -X GET "$API/api/enrichment/score/$LEAD_ID" \
  -H "Authorization: Bearer $ACCESS_TOKEN")

echo -e "${GREEN}✓ Contact score:${NC}"
echo $SCORE_RESPONSE | jq .

echo ""
echo -e "${YELLOW}Verification:${NC}"
echo "1. Check confidence score is present"
echo "2. Check sentiment analysis"
echo "3. Look for classification (INTERESTED, QUESTION, etc.)"


# ============================================================================
# STEP 8: Activity Timeline
# ============================================================================
echo -e "\n${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}STEP 8: 🧾 Activity Timeline${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}\n"

echo "Getting activity timeline..."
ACTIVITY_RESPONSE=$(curl -s -X GET "$API/api/activities/lead/$LEAD_ID" \
  -H "Authorization: Bearer $ACCESS_TOKEN")

echo -e "${GREEN}✓ Activity timeline:${NC}"
echo $ACTIVITY_RESPONSE | jq '.activities | sort_by(.event_timestamp) | reverse | .[0:10]'

echo ""
echo -e "${YELLOW}You should see:${NC}"
echo "  • email_sent (from step 2)"
echo "  • email_generated (from step 4)"  
echo "  • campaign_created (from step 5)"
echo "  • reply_received (from step 6)"
echo "  • reply_classified (from step 7)"


# ============================================================================
# SUMMARY
# ============================================================================
echo -e "\n${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}TEST COMPLETE!${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"

echo ""
echo -e "${GREEN}Summary:${NC}"
echo "  Lead ID: $LEAD_ID"
echo "  Campaign ID: $CAMPAIGN_ID"
echo "  Email Account ID: $EMAIL_ACCOUNT_ID"

echo ""
echo -e "${GREEN}What to verify:${NC}"
echo "  ✓ Email arrived in inbox"
echo "  ✓ Reply was classified correctly"
echo "  ✓ Activity timeline shows all steps"
echo "  ✓ Contact score updated based on reply"

echo ""
