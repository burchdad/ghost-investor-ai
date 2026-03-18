"""SQLAlchemy models for core entities."""
from sqlalchemy import Column, String, Integer, Float, Text, DateTime, Boolean, Enum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

from .database import Base


class EnrichmentSourceEnum(str, enum.Enum):
    """Enrichment service sources."""
    APOLLO = "apollo"
    CLEARBIT = "clearbit"
    PEOPLE_DATA_LABS = "people_data_labs"
    LINKEDIN = "linkedin"
    MANUAL = "manual"


class OutreachStatusEnum(str, enum.Enum):
    """Outreach campaign status."""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    PAUSED = "paused"


class EmailTypeEnum(str, enum.Enum):
    """Email types for outreach."""
    FIRST_TOUCH = "first_touch"
    FOLLOW_UP = "follow_up"
    REENGAGEMENT = "reengagement"


class EmailProviderEnum(str, enum.Enum):
    """Email provider types."""
    GMAIL = "gmail"
    OUTLOOK = "outlook"


class User(Base):
    """User account for system access."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, index=True)
    password_hash = Column(String(255))
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now(), server_default=func.now())
    
    # Relationships
    email_accounts = relationship("EmailAccount", back_populates="user")
    campaigns = relationship("OutreachCampaign", back_populates="user")


class Lead(Base):
    """Lead record with enrichment data."""
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, index=True)
    first_name = Column(String(100))
    last_name = Column(String(100))
    company_name = Column(String(255), index=True)
    job_title = Column(String(255))
    linkedin_url = Column(String(500))
    phone = Column(String(20))
    
    # Enrichment data
    company_website = Column(String(500))
    company_size = Column(String(50))
    company_industry = Column(String(255))
    company_revenue = Column(String(100))
    company_linkedin_url = Column(String(500))
    
    # Scoring
    contact_score = Column(Float, default=0.0)
    company_score = Column(Float, default=0.0)
    engagement_score = Column(Float, default=0.0)
    
    # Metadata
    enrichment_source = Column(Enum(EnrichmentSourceEnum))
    is_enriched = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now(), server_default=func.now())
    
    # Relationships
    activities = relationship("Activity", back_populates="lead", cascade="all, delete-orphan")
    outreach_emails = relationship("OutreachEmail", back_populates="lead", cascade="all, delete-orphan")


class ContactScore(Base):
    """Detailed contact scoring breakdown."""
    __tablename__ = "contact_scores"

    id = Column(Integer, primary_key=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), index=True)
    
    # Scoring factors
    title_score = Column(Float, default=0.0)
    company_score = Column(Float, default=0.0)
    activity_score = Column(Float, default=0.0)
    engagement_score = Column(Float, default=0.0)
    
    total_score = Column(Float, default=0.0)
    score_reason = Column(Text)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now(), server_default=func.now())


class OutreachEmail(Base):
    """Generated outreach emails."""
    __tablename__ = "outreach_emails"

    id = Column(Integer, primary_key=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), index=True)
    campaign_id = Column(Integer, ForeignKey("outreach_campaigns.id"), nullable=True, index=True)
    
    subject = Column(String(255))
    body = Column(Text)
    personalization_factors = Column(Text)  # JSON field
    
    # Email generation tracking
    email_type = Column(String(50))  # first_touch, follow_up, reengagement
    is_generated = Column(Boolean, default=False)
    generated_at = Column(DateTime, nullable=True)
    deal_brief = Column(Text, nullable=True)
    previous_email_body = Column(Text, nullable=True)
    
    # Metadata
    sent_at = Column(DateTime, nullable=True)
    is_sent = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now(), server_default=func.now())
    
    # Relationships
    lead = relationship("Lead", back_populates="outreach_emails")
    campaign = relationship("OutreachCampaign", back_populates="emails")
    follow_ups = relationship("FollowUpEmail", back_populates="initial_email")


class OutreachCampaign(Base):
    """Campaign tracking for sequences."""
    __tablename__ = "outreach_campaigns"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    email_account_id = Column(Integer, ForeignKey("email_accounts.id"), nullable=True)
    
    name = Column(String(255))
    description = Column(Text)
    status = Column(Enum(OutreachStatusEnum), default=OutreachStatusEnum.DRAFT)
    
    # Campaign settings
    lead_count = Column(Integer, default=0)
    initial_delay_hours = Column(Integer, default=0)
    follow_up_sequence = Column(Text)  # JSON field with follow-up cadence
    batch_job_id = Column(String(255), nullable=True)  # Celery task ID
    
    created_at = Column(DateTime, server_default=func.now())
    started_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, onupdate=func.now(), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="campaigns")
    emails = relationship("OutreachEmail", back_populates="campaign")


class FollowUpEmail(Base):
    """Follow-up emails in a sequence."""
    __tablename__ = "follow_up_emails"

    id = Column(Integer, primary_key=True)
    initial_email_id = Column(Integer, ForeignKey("outreach_emails.id"), index=True)
    
    sequence_number = Column(Integer)
    delay_hours_from_previous = Column(Integer)
    subject = Column(String(255))
    body = Column(Text)
    
    sent_at = Column(DateTime, nullable=True)
    is_sent = Column(Boolean, default=False)
    
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    initial_email = relationship("OutreachEmail", back_populates="follow_ups")


class Activity(Base):
    """Activity log for tracking interactions."""
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), index=True)
    
    activity_type = Column(String(50), index=True)  # email_sent, email_opened, email_clicked, reply_received, etc.
    description = Column(Text)
    
    # Email-specific
    email_id = Column(Integer, nullable=True)
    email_open_count = Column(Integer, default=0)
    email_click_count = Column(Integer, default=0)
    
    # CRM sync
    synced_to_crm = Column(Boolean, default=False)
    crm_id = Column(String(255), nullable=True)
    
    created_at = Column(DateTime, server_default=func.now())
    event_timestamp = Column(DateTime, nullable=True)
    
    # Relationships
    lead = relationship("Lead", back_populates="activities")


class InvestorProfile(Base):
    """Investor profile summary for outreach."""
    __tablename__ = "investor_profiles"

    id = Column(Integer, primary_key=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), unique=True, index=True)
    
    # Profile data
    investment_stage = Column(String(100))  # seed, series_a, growth, etc.
    investment_sectors = Column(Text)  # JSON array
    average_check_size = Column(String(100))
    typical_portfolio_size = Column(Integer)
    
    # Historical activity
    recent_investments = Column(Text)  # JSON array
    portfolio_companies = Column(Text)  # JSON array
    
    # Messaging
    key_interests = Column(Text)  # JSON array
    communication_preference = Column(String(50))  # email, linkedin, phone
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now(), server_default=func.now())


class EmailAccount(Base):
    """Email account for sending outreach."""
    __tablename__ = "email_accounts"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    email_address = Column(String(255), unique=True, index=True)
    provider = Column(Enum(EmailProviderEnum))
    
    # OAuth tokens (encrypted in production)
    oauth_token = Column(Text)
    refresh_token = Column(Text)
    token_expires_at = Column(DateTime)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now(), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="email_accounts")


class SentEmail(Base):
    """Tracking for sent emails."""
    __tablename__ = "sent_emails"

    id = Column(Integer, primary_key=True)
    outreach_email_id = Column(Integer, ForeignKey("outreach_emails.id"), index=True)
    email_account_id = Column(Integer, ForeignKey("email_accounts.id"))
    
    recipient_email = Column(String(255), index=True)
    message_id = Column(String(255))  # Provider-specific message ID
    provider = Column(Enum(EmailProviderEnum))
    
    sent_at = Column(DateTime, server_default=func.now())
    opened_at = Column(DateTime, nullable=True)
    open_count = Column(Integer, default=0)
    clicked_at = Column(DateTime, nullable=True)
    click_count = Column(Integer, default=0)
    reply_received_at = Column(DateTime, nullable=True)
    reply_message_id = Column(String(255), nullable=True)
    
    created_at = Column(DateTime, server_default=func.now())


class ReplyClassificationEnum(str, enum.Enum):
    """Reply classification categories."""
    INTERESTED = "interested"
    NOT_INTERESTED = "not_interested"
    LATER = "later"
    QUESTION = "question"
    UNSUBSCRIBE = "unsubscribe"
    UNKNOWN = "unknown"


class ReplyClassification(Base):
    """Parsed email reply with classification."""
    __tablename__ = "reply_classifications"

    id = Column(Integer, primary_key=True)
    message_id = Column(String(255), index=True)
    sender_email = Column(String(255), index=True)
    
    subject = Column(String(255))
    body = Column(Text)
    
    classification = Column(String(50), index=True)  # INTERESTED, NOT_INTERESTED, LATER, QUESTION, UNSUBSCRIBE, UNCLEAR
    confidence = Column(Float)  # 0-1 confidence score
    sentiment = Column(String(20))  # positive, neutral, negative
    key_points = Column(Text)  # JSON array
    suggested_action = Column(String(255))
    requires_human_review = Column(Boolean, default=False)
    
    received_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class WebhookEndpoint(Base):
    """Registered webhook endpoint."""
    __tablename__ = "webhook_endpoints"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, index=True)  # User who registered this webhook
    endpoint_url = Column(String(500), index=True)
    
    # Events this webhook subscribes to
    events = Column(Text)  # JSON array of event types
    secret_key = Column(String(255))  # For signature verification
    
    is_active = Column(Boolean, default=True)
    retry_count = Column(Integer, default=0)
    last_error = Column(Text, nullable=True)
    last_delivered_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now(), server_default=func.now())
    
    # Relationships
    events_rel = relationship("WebhookEvent", back_populates="webhook_endpoint")


class WebhookEvent(Base):
    """Event queued for webhook delivery."""
    __tablename__ = "webhook_events"

    id = Column(Integer, primary_key=True)
    webhook_endpoint_id = Column(Integer, ForeignKey("webhook_endpoints.id"), index=True)
    
    event_type = Column(String(100), index=True)  # email.sent, reply.received, etc.
    payload = Column(Text)  # JSON payload
    
    status = Column(String(50), default="pending")  # pending, pending_retry, delivered, failed
    error_message = Column(Text, nullable=True)
    
    delivered_at = Column(DateTime, nullable=True)
    retry_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now(), server_default=func.now())
    
    # Relationships
    webhook_endpoint = relationship("WebhookEndpoint", back_populates="events_rel")
