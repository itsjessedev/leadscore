"""Slack notification service for hot leads."""

import logging
import httpx
from datetime import datetime

from ..models import LeadScore
from ..config import get_settings

logger = logging.getLogger(__name__)


class SlackNotifier:
    """Send Slack notifications for high-priority leads."""

    def __init__(self):
        self.settings = get_settings()
        self.webhook_url = self.settings.slack_webhook_url
        self.channel = self.settings.slack_channel

    async def notify_hot_lead(self, lead_score: LeadScore) -> bool:
        """Send Slack alert for a hot lead."""
        if self.settings.demo_mode:
            logger.info(f"[DEMO] Would send Slack alert for hot lead: {lead_score.email}")
            return True

        if not self.webhook_url:
            logger.warning("Slack webhook URL not configured")
            return False

        try:
            message = self._format_hot_lead_message(lead_score)
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.webhook_url,
                    json=message,
                    timeout=10.0,
                )
                response.raise_for_status()
                logger.info(f"Sent Slack alert for hot lead: {lead_score.email}")
                return True

        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
            return False

    async def notify_score_update(self, total_leads: int, hot_count: int, warm_count: int) -> bool:
        """Send summary notification after score refresh."""
        if self.settings.demo_mode:
            logger.info(
                f"[DEMO] Would send score update: {total_leads} leads, {hot_count} hot, {warm_count} warm"
            )
            return True

        if not self.webhook_url:
            return False

        try:
            message = self._format_summary_message(total_leads, hot_count, warm_count)
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.webhook_url,
                    json=message,
                    timeout=10.0,
                )
                response.raise_for_status()
                logger.info("Sent score update summary to Slack")
                return True

        except Exception as e:
            logger.error(f"Failed to send summary notification: {e}")
            return False

    def _format_hot_lead_message(self, lead_score: LeadScore) -> dict:
        """Format hot lead alert message."""
        lead = lead_score.lead
        return {
            "channel": self.channel,
            "username": "LeadScore Bot",
            "icon_emoji": ":fire:",
            "attachments": [
                {
                    "color": "#ff0000",
                    "title": f"🔥 Hot Lead Alert - Score: {lead_score.score}",
                    "fields": [
                        {"title": "Name", "value": lead.name or "N/A", "short": True},
                        {"title": "Company", "value": lead.company or "N/A", "short": True},
                        {"title": "Email", "value": lead.email, "short": True},
                        {"title": "Job Title", "value": lead.job_title or "N/A", "short": True},
                        {"title": "Deal Stage", "value": lead.deal_stage or "N/A", "short": True},
                        {
                            "title": "Score",
                            "value": f"{lead_score.score}/100",
                            "short": True,
                        },
                    ],
                    "footer": "LeadScore",
                    "footer_icon": "https://platform.slack-edge.com/img/default_application_icon.png",
                    "ts": int(datetime.utcnow().timestamp()),
                }
            ],
        }

    def _format_summary_message(self, total: int, hot: int, warm: int) -> dict:
        """Format score update summary message."""
        return {
            "channel": self.channel,
            "username": "LeadScore Bot",
            "icon_emoji": ":chart_with_upwards_trend:",
            "text": f"Lead scores updated: {total} total leads",
            "attachments": [
                {
                    "color": "#36a64f",
                    "fields": [
                        {"title": "Hot Leads", "value": str(hot), "short": True},
                        {"title": "Warm Leads", "value": str(warm), "short": True},
                        {"title": "Cold Leads", "value": str(total - hot - warm), "short": True},
                    ],
                    "footer": "LeadScore",
                    "ts": int(datetime.utcnow().timestamp()),
                }
            ],
        }
