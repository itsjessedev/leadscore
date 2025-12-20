"""Tests for lead scoring functionality."""

import pytest
from datetime import datetime, timedelta

from src.models import Lead, EngagementSummary
from src.services import LeadScorer
from src.config import get_settings


@pytest.fixture
def scorer():
    """Create a LeadScorer instance."""
    return LeadScorer()


@pytest.fixture
def high_engagement_lead():
    """Create a lead with high engagement."""
    now = datetime.utcnow()
    return Lead(
        id="test-high",
        email="high@test.com",
        name="High Engagement",
        company="Test Corp",
        deal_stage="opportunity",
        company_size=500,
        last_activity=now - timedelta(hours=2),
        engagement=EngagementSummary(
            email_opens=15,
            email_clicks=8,
            website_visits=12,
            crm_activities=6,
            last_email_open=now - timedelta(hours=2),
            last_website_visit=now - timedelta(hours=4),
            last_crm_activity=now - timedelta(hours=6),
        ),
    )


@pytest.fixture
def low_engagement_lead():
    """Create a lead with low engagement."""
    now = datetime.utcnow()
    return Lead(
        id="test-low",
        email="low@test.com",
        name="Low Engagement",
        company="Small Co",
        deal_stage="subscriber",
        company_size=5,
        last_activity=now - timedelta(days=45),
        engagement=EngagementSummary(
            email_opens=1,
            email_clicks=0,
            website_visits=1,
            crm_activities=0,
            last_email_open=now - timedelta(days=45),
            last_website_visit=None,
            last_crm_activity=None,
        ),
    )


@pytest.mark.asyncio
async def test_score_high_engagement_lead(scorer, high_engagement_lead):
    """Test scoring of high engagement lead."""
    result = await scorer.score_lead(high_engagement_lead)

    assert result.score >= 70, "High engagement lead should score >= 70"
    assert result.score_category.value in ["hot", "warm"]
    assert "email_opens" in result.score_breakdown
    assert "email_clicks" in result.score_breakdown


@pytest.mark.asyncio
async def test_score_low_engagement_lead(scorer, low_engagement_lead):
    """Test scoring of low engagement lead."""
    result = await scorer.score_lead(low_engagement_lead)

    assert result.score < 50, "Low engagement lead should score < 50"
    assert result.score_category.value == "cold"


@pytest.mark.asyncio
async def test_score_multiple_leads(scorer, high_engagement_lead, low_engagement_lead):
    """Test scoring multiple leads."""
    leads = [high_engagement_lead, low_engagement_lead]
    results = await scorer.score_leads(leads)

    assert len(results) == 2
    # Should be sorted by score (high to low)
    assert results[0].score >= results[1].score


def test_email_opens_scoring(scorer):
    """Test email opens contribute to score."""
    lead_no_opens = Lead(
        id="test-1",
        email="test1@test.com",
        engagement=EngagementSummary(email_opens=0),
    )
    lead_many_opens = Lead(
        id="test-2",
        email="test2@test.com",
        engagement=EngagementSummary(
            email_opens=20, last_email_open=datetime.utcnow() - timedelta(days=1)
        ),
    )

    score_no_opens = scorer._score_email_opens(lead_no_opens)
    score_many_opens = scorer._score_email_opens(lead_many_opens)

    assert score_no_opens == 0.0
    assert score_many_opens > 0.5


def test_recency_scoring(scorer):
    """Test recency affects score."""
    now = datetime.utcnow()

    lead_recent = Lead(
        id="test-1", email="test1@test.com", last_activity=now - timedelta(hours=1)
    )
    lead_old = Lead(
        id="test-2", email="test2@test.com", last_activity=now - timedelta(days=60)
    )

    score_recent = scorer._score_recency(lead_recent)
    score_old = scorer._score_recency(lead_old)

    assert score_recent > 0.8
    assert score_old == 0.0


def test_deal_stage_scoring(scorer):
    """Test deal stage contributes appropriately."""
    lead_customer = Lead(
        id="test-1", email="test1@test.com", deal_stage="customer"
    )
    lead_subscriber = Lead(
        id="test-2", email="test2@test.com", deal_stage="subscriber"
    )

    score_customer = scorer._score_deal_stage(lead_customer)
    score_subscriber = scorer._score_deal_stage(lead_subscriber)

    assert score_customer > score_subscriber


def test_company_size_scoring(scorer):
    """Test company size scoring."""
    assert scorer._score_company_size(Lead(id="1", email="a@b.com", company_size=5)) == 0.3
    assert scorer._score_company_size(Lead(id="2", email="c@d.com", company_size=100)) == 0.7
    assert scorer._score_company_size(Lead(id="3", email="e@f.com", company_size=2000)) == 1.0


@pytest.mark.asyncio
async def test_score_boundaries(scorer):
    """Test that scores stay within 0-100 range."""
    # Create extreme case lead
    now = datetime.utcnow()
    extreme_lead = Lead(
        id="extreme",
        email="extreme@test.com",
        company_size=10000,
        deal_stage="customer",
        last_activity=now,
        engagement=EngagementSummary(
            email_opens=100,
            email_clicks=50,
            website_visits=100,
            crm_activities=50,
            last_email_open=now,
            last_website_visit=now,
            last_crm_activity=now,
        ),
    )

    result = await scorer.score_lead(extreme_lead)
    assert 0 <= result.score <= 100


def test_settings_weight_validation():
    """Test that feature weights are validated."""
    settings = get_settings()
    # Should not raise exception if weights sum to 1.0
    settings.validate_weights()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
