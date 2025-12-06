"""Lead scoring service using weighted features."""

import logging
from datetime import datetime, timedelta
from typing import List

from ..models import Lead, LeadScore, ScoreCategory
from ..config import get_settings

logger = logging.getLogger(__name__)


class LeadScorer:
    """Calculate lead scores based on engagement signals."""

    def __init__(self):
        self.settings = get_settings()
        self.weights = {
            "email_opens": self.settings.weight_email_opens,
            "email_clicks": self.settings.weight_email_clicks,
            "website_visits": self.settings.weight_website_visits,
            "crm_activities": self.settings.weight_crm_activities,
            "deal_stage": self.settings.weight_deal_stage,
            "company_size": self.settings.weight_company_size,
            "recency": self.settings.weight_recency,
        }

    async def score_lead(self, lead: Lead) -> LeadScore:
        """Calculate score for a single lead."""
        breakdown = {}
        total_score = 0.0

        # Email Opens (recent activity weighted more)
        email_opens_score = self._score_email_opens(lead)
        breakdown["email_opens"] = email_opens_score
        total_score += email_opens_score * self.weights["email_opens"]

        # Email Clicks
        email_clicks_score = self._score_email_clicks(lead)
        breakdown["email_clicks"] = email_clicks_score
        total_score += email_clicks_score * self.weights["email_clicks"]

        # Website Visits
        website_visits_score = self._score_website_visits(lead)
        breakdown["website_visits"] = website_visits_score
        total_score += website_visits_score * self.weights["website_visits"]

        # CRM Activities
        crm_activities_score = self._score_crm_activities(lead)
        breakdown["crm_activities"] = crm_activities_score
        total_score += crm_activities_score * self.weights["crm_activities"]

        # Deal Stage
        deal_stage_score = self._score_deal_stage(lead)
        breakdown["deal_stage"] = deal_stage_score
        total_score += deal_stage_score * self.weights["deal_stage"]

        # Company Size
        company_size_score = self._score_company_size(lead)
        breakdown["company_size"] = company_size_score
        total_score += company_size_score * self.weights["company_size"]

        # Recency
        recency_score = self._score_recency(lead)
        breakdown["recency"] = recency_score
        total_score += recency_score * self.weights["recency"]

        # Normalize to 0-100
        final_score = min(100.0, max(0.0, total_score * 100))

        # Categorize
        category = self._categorize_score(final_score)

        return LeadScore(
            lead=lead,
            score=round(final_score, 2),
            score_category=category,
            score_breakdown=breakdown,
        )

    async def score_leads(self, leads: List[Lead]) -> List[LeadScore]:
        """Score multiple leads."""
        scored_leads = []
        for lead in leads:
            scored_lead = await self.score_lead(lead)
            scored_leads.append(scored_lead)

        # Sort by score descending
        scored_leads.sort(key=lambda x: x.score, reverse=True)
        return scored_leads

    def _score_email_opens(self, lead: Lead) -> float:
        """Score based on email opens (0-1)."""
        opens = lead.engagement.email_opens
        if opens == 0:
            return 0.0

        # Boost for recent activity
        recency_boost = 1.0
        if lead.engagement.last_email_open:
            days_since = (datetime.utcnow() - lead.engagement.last_email_open).days
            if days_since <= 7:
                recency_boost = 1.5
            elif days_since <= 30:
                recency_boost = 1.2

        # Normalize (10+ opens = max score)
        base_score = min(1.0, opens / 10)
        return min(1.0, base_score * recency_boost)

    def _score_email_clicks(self, lead: Lead) -> float:
        """Score based on email clicks (0-1)."""
        clicks = lead.engagement.email_clicks
        # Normalize (5+ clicks = max score, clicks are more valuable than opens)
        return min(1.0, clicks / 5)

    def _score_website_visits(self, lead: Lead) -> float:
        """Score based on website visits (0-1)."""
        visits = lead.engagement.website_visits
        if visits == 0:
            return 0.0

        # Boost for recent visits
        recency_boost = 1.0
        if lead.engagement.last_website_visit:
            days_since = (datetime.utcnow() - lead.engagement.last_website_visit).days
            if days_since <= 3:
                recency_boost = 1.5
            elif days_since <= 7:
                recency_boost = 1.2

        # Normalize (8+ visits = max score)
        base_score = min(1.0, visits / 8)
        return min(1.0, base_score * recency_boost)

    def _score_crm_activities(self, lead: Lead) -> float:
        """Score based on CRM activities (0-1)."""
        activities = lead.engagement.crm_activities
        # Normalize (6+ activities = max score)
        return min(1.0, activities / 6)

    def _score_deal_stage(self, lead: Lead) -> float:
        """Score based on deal stage (0-1)."""
        stage_scores = {
            "subscriber": 0.2,
            "lead": 0.3,
            "marketing_qualified": 0.5,
            "qualified": 0.6,
            "opportunity": 0.8,
            "customer": 1.0,
        }
        stage = (lead.deal_stage or "").lower()
        return stage_scores.get(stage, 0.3)  # Default to lead stage

    def _score_company_size(self, lead: Lead) -> float:
        """Score based on company size (0-1)."""
        if not lead.company_size:
            return 0.3  # Neutral score for unknown

        size = lead.company_size
        # Scale: 1-10 employees = 0.3, 11-50 = 0.5, 51-200 = 0.7, 201-1000 = 0.9, 1000+ = 1.0
        if size <= 10:
            return 0.3
        elif size <= 50:
            return 0.5
        elif size <= 200:
            return 0.7
        elif size <= 1000:
            return 0.9
        else:
            return 1.0

    def _score_recency(self, lead: Lead) -> float:
        """Score based on last activity recency (0-1)."""
        if not lead.last_activity:
            return 0.0

        days_since = (datetime.utcnow() - lead.last_activity).days

        if days_since <= 1:
            return 1.0
        elif days_since <= 3:
            return 0.8
        elif days_since <= 7:
            return 0.6
        elif days_since <= 14:
            return 0.4
        elif days_since <= 30:
            return 0.2
        else:
            return 0.0

    def _categorize_score(self, score: float) -> ScoreCategory:
        """Categorize score into hot/warm/cold."""
        if score >= self.settings.hot_lead_threshold:
            return ScoreCategory.HOT
        elif score >= self.settings.warm_lead_threshold:
            return ScoreCategory.WARM
        else:
            return ScoreCategory.COLD
