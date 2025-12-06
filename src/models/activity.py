"""Activity tracking models."""

from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class ActivityType(str, Enum):
    """Types of lead activities."""

    EMAIL_OPEN = "email_open"
    EMAIL_CLICK = "email_click"
    EMAIL_REPLY = "email_reply"
    WEBSITE_VISIT = "website_visit"
    CRM_CALL = "crm_call"
    CRM_MEETING = "crm_meeting"
    CRM_NOTE = "crm_note"
    CRM_EMAIL = "crm_email"
    DEAL_STAGE_CHANGE = "deal_stage_change"


class Activity(BaseModel):
    """Individual lead activity/engagement event."""

    id: str = Field(default_factory=lambda: str(datetime.utcnow().timestamp()))
    lead_id: str
    activity_type: ActivityType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict = Field(default_factory=dict)
    description: str | None = None

    class Config:
        use_enum_values = True
