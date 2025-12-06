"""LeadScore FastAPI application."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .api import leads_router, alerts_router
from .services import ScoringScheduler, HubSpotClient, LeadScorer, SlackNotifier

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = None


async def scheduled_score_refresh():
    """Callback function for scheduled score refresh."""
    logger.info("Running scheduled score refresh")
    try:
        hubspot = HubSpotClient()
        scorer = LeadScorer()
        notifier = SlackNotifier()

        # Fetch and score leads
        leads = await hubspot.get_contacts()
        scored_leads = await scorer.score_leads(leads)

        # Send notifications for hot leads
        hot_leads = [sl for sl in scored_leads if sl.score_category.value == "hot"]
        for hot_lead in hot_leads:
            await notifier.notify_hot_lead(hot_lead)

        # Send summary
        hot_count = len(hot_leads)
        warm_count = sum(1 for sl in scored_leads if sl.score_category.value == "warm")
        await notifier.notify_score_update(len(scored_leads), hot_count, warm_count)

        logger.info(
            f"Score refresh complete: {len(scored_leads)} leads, {hot_count} hot, {warm_count} warm"
        )

    except Exception as e:
        logger.error(f"Error during scheduled score refresh: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global scheduler
    settings = get_settings()

    # Startup
    logger.info("Starting LeadScore application")
    logger.info(f"Demo mode: {settings.demo_mode}")

    # Start scheduler
    scheduler = ScoringScheduler(scheduled_score_refresh)
    scheduler.start()

    yield

    # Shutdown
    logger.info("Shutting down LeadScore application")
    if scheduler:
        scheduler.stop()


# Create FastAPI app
app = FastAPI(
    title="LeadScore",
    description="Intelligent lead scoring system",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(leads_router)
app.include_router(alerts_router)


@app.get("/")
async def root():
    """Root endpoint."""
    settings = get_settings()
    return {
        "name": "LeadScore",
        "version": "1.0.0",
        "description": "Intelligent lead scoring system",
        "demo_mode": settings.demo_mode,
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/metrics")
async def metrics():
    """Metrics endpoint (Prometheus-compatible)."""
    # In production, would return actual metrics
    return {
        "leads_total": 0,
        "leads_hot": 0,
        "leads_warm": 0,
        "leads_cold": 0,
        "score_refresh_count": 0,
        "slack_notifications_sent": 0,
    }


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "src.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
    )
