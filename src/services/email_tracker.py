"""Email engagement tracking service."""

import logging
from datetime import datetime, timedelta
from typing import Dict

logger = logging.getLogger(__name__)


class EmailTracker:
    """Track email engagement metrics."""

    def __init__(self):
        # In production, this would connect to email tracking service
        # (e.g., SendGrid, Mailgun, or custom tracking)
        self._engagement_cache: Dict[str, dict] = {}

    async def get_email_engagement(self, lead_id: str) -> dict:
        """Get email engagement metrics for a lead."""
        # In demo mode or production, return engagement data
        if lead_id in self._engagement_cache:
            return self._engagement_cache[lead_id]

        # Default engagement data
        return {
            "total_sent": 0,
            "total_opens": 0,
            "total_clicks": 0,
            "total_replies": 0,
            "recent_opens_7d": 0,
            "recent_clicks_7d": 0,
            "last_open": None,
            "last_click": None,
            "open_rate": 0.0,
            "click_rate": 0.0,
        }

    async def track_open(self, lead_id: str, email_id: str) -> None:
        """Record an email open event."""
        logger.info(f"Email opened: lead={lead_id}, email={email_id}")
        engagement = await self.get_email_engagement(lead_id)
        engagement["total_opens"] += 1
        engagement["recent_opens_7d"] += 1
        engagement["last_open"] = datetime.utcnow()
        self._engagement_cache[lead_id] = engagement

    async def track_click(self, lead_id: str, email_id: str, link_url: str) -> None:
        """Record an email link click event."""
        logger.info(
            f"Email link clicked: lead={lead_id}, email={email_id}, url={link_url}"
        )
        engagement = await self.get_email_engagement(lead_id)
        engagement["total_clicks"] += 1
        engagement["recent_clicks_7d"] += 1
        engagement["last_click"] = datetime.utcnow()
        self._engagement_cache[lead_id] = engagement

    async def track_reply(self, lead_id: str, email_id: str) -> None:
        """Record an email reply event."""
        logger.info(f"Email replied: lead={lead_id}, email={email_id}")
        engagement = await self.get_email_engagement(lead_id)
        engagement["total_replies"] += 1
        self._engagement_cache[lead_id] = engagement

    def calculate_rates(self, engagement: dict) -> dict:
        """Calculate open and click-through rates."""
        total_sent = engagement.get("total_sent", 0)
        if total_sent == 0:
            return {**engagement, "open_rate": 0.0, "click_rate": 0.0}

        open_rate = engagement.get("total_opens", 0) / total_sent
        click_rate = engagement.get("total_clicks", 0) / total_sent

        return {
            **engagement,
            "open_rate": round(open_rate, 3),
            "click_rate": round(click_rate, 3),
        }
