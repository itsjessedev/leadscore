"""API routes for LeadScore."""

from .leads import router as leads_router
from .alerts import router as alerts_router

__all__ = ["leads_router", "alerts_router"]
