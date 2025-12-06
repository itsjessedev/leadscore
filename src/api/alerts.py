"""Alert configuration API endpoints."""

import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/alerts", tags=["alerts"])


class AlertConfig(BaseModel):
    """Alert configuration settings."""

    hot_threshold: int = Field(ge=0, le=100, description="Score threshold for hot leads")
    warm_threshold: int = Field(ge=0, le=100, description="Score threshold for warm leads")
    enable_slack: bool = Field(description="Enable Slack notifications")


@router.get("/config", response_model=AlertConfig)
async def get_alert_config():
    """Get current alert configuration."""
    settings = get_settings()
    return AlertConfig(
        hot_threshold=settings.hot_lead_threshold,
        warm_threshold=settings.warm_lead_threshold,
        enable_slack=bool(settings.slack_webhook_url),
    )


@router.post("/config", response_model=AlertConfig)
async def update_alert_config(config: AlertConfig):
    """
    Update alert configuration.

    Note: This updates in-memory config only.
    For persistent changes, update the .env file.
    """
    settings = get_settings()

    # Validate thresholds
    if config.warm_threshold >= config.hot_threshold:
        raise HTTPException(
            status_code=400,
            detail="Warm threshold must be less than hot threshold",
        )

    # Update settings (in-memory only)
    settings.hot_lead_threshold = config.hot_threshold
    settings.warm_lead_threshold = config.warm_threshold

    logger.info(
        f"Updated alert config: hot={config.hot_threshold}, warm={config.warm_threshold}"
    )

    return config


@router.post("/test")
async def test_slack_alert():
    """
    Send a test Slack notification.

    Useful for verifying Slack webhook configuration.
    """
    from ..services import SlackNotifier
    from ..models import Lead, LeadScore, ScoreCategory, EngagementSummary
    from datetime import datetime

    settings = get_settings()

    if not settings.slack_webhook_url:
        raise HTTPException(
            status_code=400, detail="Slack webhook URL not configured"
        )

    # Create test lead
    test_lead = Lead(
        id="test-123",
        email="test@example.com",
        name="Test Lead",
        company="Test Company",
        job_title="Test Title",
        deal_stage="opportunity",
        engagement=EngagementSummary(
            email_opens=10, email_clicks=5, website_visits=8, crm_activities=3
        ),
    )

    test_score = LeadScore(
        lead=test_lead,
        score=85.0,
        score_category=ScoreCategory.HOT,
        score_breakdown={},
    )

    notifier = SlackNotifier()
    success = await notifier.notify_hot_lead(test_score)

    if success:
        return {"status": "success", "message": "Test alert sent to Slack"}
    else:
        raise HTTPException(status_code=500, detail="Failed to send test alert")
