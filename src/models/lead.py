"""Lead data models."""

from datetime import datetime
from enum import Enum
from pydantic import BaseModel, EmailStr, Field


class ScoreCategory(str, Enum):
    """Lead score categories."""

    HOT = "hot"
    WARM = "warm"
    COLD = "cold"


class EngagementSummary(BaseModel):
    """Summary of lead engagement metrics."""

    email_opens: int = 0
    email_clicks: int = 0
    website_visits: int = 0
    crm_activities: int = 0
    last_email_open: datetime | None = None
    last_website_visit: datetime | None = None
    last_crm_activity: datetime | None = None


class Lead(BaseModel):
    """Lead/Contact information."""

    id: str
    email: EmailStr
    name: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    company: str | None = None
    job_title: str | None = None
    phone: str | None = None
    company_size: int | None = None
    deal_stage: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime | None = None
    engagement: EngagementSummary = Field(default_factory=EngagementSummary)


class LeadScore(BaseModel):
    """Lead with calculated score."""

    lead: Lead
    score: float = Field(ge=0, le=100, description="Score from 0-100")
    score_category: ScoreCategory
    score_breakdown: dict[str, float] = Field(
        default_factory=dict, description="Individual feature contributions"
    )
    calculated_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def id(self) -> str:
        """Get lead ID."""
        return self.lead.id

    @property
    def email(self) -> str:
        """Get lead email."""
        return self.lead.email

    @property
    def name(self) -> str:
        """Get lead name."""
        return self.lead.name or f"{self.lead.first_name} {self.lead.last_name}"

    @property
    def company(self) -> str | None:
        """Get lead company."""
        return self.lead.company
