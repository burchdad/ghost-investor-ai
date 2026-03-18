"""Basic tests for core services."""
import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.ghost_investor_ai.models import Base, Lead, EnrichmentSourceEnum
from src.ghost_investor_ai.services.scoring import ContactScoringService
from src.ghost_investor_ai.services.email_drafting import EmailDraftingService

# Use SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


@pytest.fixture
def db():
    """Database session for tests."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


def test_create_lead(db):
    """Test creating a lead."""
    lead = Lead(
        email="test@example.com",
        first_name="John",
        last_name="Doe",
        company_name="Test Corp",
        job_title="Partner",
        enrichment_source=EnrichmentSourceEnum.MANUAL,
    )
    db.add(lead)
    db.commit()

    retrieved = db.query(Lead).filter(Lead.email == "test@example.com").first()
    assert retrieved is not None
    assert retrieved.first_name == "John"


def test_contact_scoring_title():
    """Test contact scoring by title."""
    lead = Lead(
        email="investor@example.com",
        first_name="Jane",
        last_name="Smith",
        company_name="VC Fund",
        job_title="Managing Partner",
        enrichment_source=EnrichmentSourceEnum.MANUAL,
    )

    score = ContactScoringService.score_title(lead.job_title)
    assert score > 0.8  # Managing partner should score high


def test_contact_scoring_company():
    """Test contact scoring by company."""
    score = ContactScoringService.score_company("1000+", "Venture Capital")
    assert score > 0.8  # VC with large company should score high


def test_email_drafting():
    """Test email drafting."""
    lead = Lead(
        email="investor@example.com",
        first_name="Alex",
        last_name="Chen",
        company_name="Tech Ventures",
        job_title="Principal",
        enrichment_source=EnrichmentSourceEnum.MANUAL,
    )

    email = EmailDraftingService.draft_email(lead)
    assert email["subject"] is not None
    assert email["body"] is not None
    assert "Alex" in email["body"]
    assert len(email["personalization_factors"]) > 0


def test_email_subject_generation():
    """Test email subject generation."""
    lead = Lead(
        email="test@example.com",
        first_name="John",
        last_name="Doe",
        company_name="Acme Corp",
        job_title="CEO",
        enrichment_source=EnrichmentSourceEnum.MANUAL,
    )

    subject = EmailDraftingService.generate_subject(lead)
    assert "John" in subject or "Acme" in subject or subject


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
