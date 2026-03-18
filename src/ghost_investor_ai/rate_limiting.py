"""Rate limiting and throttling."""
from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import HTTPException, status

# Initialize limiter
limiter = Limiter(key_func=get_remote_address)

# Rate limit tiers
RATE_LIMITS = {
    "default": "100/minute",          # General API
    "auth": "5/minute",               # Authentication attempts
    "email_send": "100/hour",         # Email sends per hour
    "enrichment": "50/hour",          # Enrichment requests per hour
    "batch": "10/hour",               # Batch job submissions per hour
    "search": "60/minute",            # Search/query operations
}

# Email sending limits (sender reputation protection)
MAX_EMAILS_PER_HOUR = 50
MAX_UNIQUE_RECIPIENTS_PER_DAY = 500
MAX_SENDS_PER_BATCH = 1000


def check_email_rate_limit(emails_sent_today: int, emails_sent_this_hour: int) -> bool:
    """Check if email send would violate rate limits."""
    if emails_sent_this_hour >= MAX_EMAILS_PER_HOUR:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Email limit reached: {MAX_EMAILS_PER_HOUR}/hour",
        )

    if emails_sent_today >= MAX_UNIQUE_RECIPIENTS_PER_DAY:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Daily email limit reached: {MAX_UNIQUE_RECIPIENTS_PER_DAY}/day",
        )

    return True
