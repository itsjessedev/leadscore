"""Lead scoring API endpoints."""

import logging
from fastapi import APIRouter, HTTPException, Depends
from typing import List

from ..models import LeadScore
from ..services import HubSpotClient, LeadScorer
from ..config import get_settings, Settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/leads", tags=["leads"])

# Dependency injection
def get_hubspot_client(settings: Settings = Depends(get_settings)):
    return HubSpotClient()

def get_scorer(settings: Settings = Depends(get_settings)):
    return LeadScorer()


@router.get("/", response_model=List[LeadScore])
async def get_all_leads(
    hubspot: HubSpotClient = Depends(get_hubspot_client),
    scorer: LeadScorer = Depends(get_scorer),
):
    """
    Get all leads with their scores.

    Returns leads sorted by score (highest first).
    """
    try:
        # Fetch leads from HubSpot
        leads = await hubspot.get_contacts()

        # Score all leads
        scored_leads = await scorer.score_leads(leads)

        return scored_leads

    except Exception as e:
        logger.error(f"Error fetching leads: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{lead_id}", response_model=LeadScore)
async def get_lead_score(
    lead_id: str,
    hubspot: HubSpotClient = Depends(get_hubspot_client),
    scorer: LeadScorer = Depends(get_scorer),
):
    """Get score for a specific lead by ID."""
    try:
        # Fetch all leads (in production, would fetch single lead)
        leads = await hubspot.get_contacts()
        lead = next((l for l in leads if l.id == lead_id), None)

        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")

        # Score the lead
        scored_lead = await scorer.score_lead(lead)
        return scored_lead

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching lead {lead_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/refresh")
async def refresh_scores(
    hubspot: HubSpotClient = Depends(get_hubspot_client),
    scorer: LeadScorer = Depends(get_scorer),
):
    """
    Trigger manual refresh of all lead scores.

    This will recalculate scores for all leads immediately.
    """
    try:
        leads = await hubspot.get_contacts()
        scored_leads = await scorer.score_leads(leads)

        hot_count = sum(1 for sl in scored_leads if sl.score_category.value == "hot")
        warm_count = sum(1 for sl in scored_leads if sl.score_category.value == "warm")

        return {
            "status": "success",
            "total_leads": len(scored_leads),
            "hot_leads": hot_count,
            "warm_leads": warm_count,
            "cold_leads": len(scored_leads) - hot_count - warm_count,
        }

    except Exception as e:
        logger.error(f"Error refreshing scores: {e}")
        raise HTTPException(status_code=500, detail=str(e))
