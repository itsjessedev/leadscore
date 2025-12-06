"""Background scheduler for periodic score updates."""

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from ..config import get_settings

logger = logging.getLogger(__name__)


class ScoringScheduler:
    """Manage scheduled score refresh tasks."""

    def __init__(self, score_refresh_callback):
        """
        Initialize scheduler.

        Args:
            score_refresh_callback: Async function to call on each refresh
        """
        self.settings = get_settings()
        self.scheduler = AsyncIOScheduler()
        self.score_refresh_callback = score_refresh_callback

    def start(self):
        """Start the scheduler."""
        interval_seconds = self.settings.score_refresh_interval

        self.scheduler.add_job(
            self.score_refresh_callback,
            trigger=IntervalTrigger(seconds=interval_seconds),
            id="score_refresh",
            name="Refresh lead scores",
            replace_existing=True,
        )

        self.scheduler.start()
        logger.info(
            f"Started scoring scheduler with {interval_seconds}s refresh interval"
        )

    def stop(self):
        """Stop the scheduler."""
        self.scheduler.shutdown()
        logger.info("Stopped scoring scheduler")

    def trigger_immediate_refresh(self):
        """Trigger an immediate score refresh (outside normal schedule)."""
        logger.info("Triggering immediate score refresh")
        self.scheduler.add_job(
            self.score_refresh_callback,
            id="immediate_refresh",
            replace_existing=True,
        )
