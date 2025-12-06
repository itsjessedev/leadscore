"""HubSpot CRM integration client."""

import logging
from datetime import datetime, timedelta
import httpx
from typing import List

from ..models import Lead, Activity, ActivityType, EngagementSummary
from ..config import get_settings

logger = logging.getLogger(__name__)


class HubSpotClient:
    """Client for HubSpot CRM API."""

    def __init__(self):
        self.settings = get_settings()
        self.api_key = self.settings.hubspot_api_key
        self.base_url = self.settings.hubspot_api_url
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def get_contacts(self, limit: int = 100) -> List[Lead]:
        """Fetch contacts from HubSpot."""
        if self.settings.demo_mode:
            return self._get_demo_contacts()

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/crm/v3/objects/contacts",
                    headers=self.headers,
                    params={"limit": limit},
                )
                response.raise_for_status()
                data = response.json()

                leads = []
                for contact in data.get("results", []):
                    leads.append(self._parse_contact(contact))
                return leads

        except Exception as e:
            logger.error(f"Error fetching contacts from HubSpot: {e}")
            return []

    async def get_contact_activities(self, contact_id: str) -> List[Activity]:
        """Fetch activities for a specific contact."""
        if self.settings.demo_mode:
            return self._get_demo_activities(contact_id)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/crm/v3/objects/contacts/{contact_id}/associations/activities",
                    headers=self.headers,
                )
                response.raise_for_status()
                data = response.json()

                activities = []
                for activity in data.get("results", []):
                    activities.append(self._parse_activity(contact_id, activity))
                return activities

        except Exception as e:
            logger.error(f"Error fetching activities for {contact_id}: {e}")
            return []

    def _parse_contact(self, contact_data: dict) -> Lead:
        """Parse HubSpot contact data into Lead model."""
        props = contact_data.get("properties", {})
        return Lead(
            id=contact_data["id"],
            email=props.get("email", f"contact{contact_data['id']}@example.com"),
            first_name=props.get("firstname"),
            last_name=props.get("lastname"),
            name=f"{props.get('firstname', '')} {props.get('lastname', '')}".strip()
            or None,
            company=props.get("company"),
            job_title=props.get("jobtitle"),
            phone=props.get("phone"),
            company_size=self._parse_company_size(props.get("numberofemployees")),
            deal_stage=props.get("lifecyclestage"),
            created_at=datetime.fromisoformat(
                props.get("createdate", datetime.utcnow().isoformat())
            ),
            last_activity=datetime.fromisoformat(
                props.get("lastmodifieddate", datetime.utcnow().isoformat())
            ),
        )

    def _parse_activity(self, contact_id: str, activity_data: dict) -> Activity:
        """Parse HubSpot activity data into Activity model."""
        activity_type_map = {
            "CALL": ActivityType.CRM_CALL,
            "MEETING": ActivityType.CRM_MEETING,
            "NOTE": ActivityType.CRM_NOTE,
            "EMAIL": ActivityType.CRM_EMAIL,
        }

        activity_type = activity_type_map.get(
            activity_data.get("type", "").upper(), ActivityType.CRM_NOTE
        )

        return Activity(
            id=activity_data.get("id", ""),
            lead_id=contact_id,
            activity_type=activity_type,
            timestamp=datetime.fromisoformat(
                activity_data.get("timestamp", datetime.utcnow().isoformat())
            ),
            metadata=activity_data.get("properties", {}),
            description=activity_data.get("properties", {}).get("hs_note_body"),
        )

    def _parse_company_size(self, size_str: str | None) -> int | None:
        """Parse company size string into integer."""
        if not size_str:
            return None
        try:
            # Handle ranges like "1-10", "11-50", etc.
            if "-" in str(size_str):
                return int(str(size_str).split("-")[1])
            return int(size_str)
        except (ValueError, AttributeError):
            return None

    def _get_demo_contacts(self) -> List[Lead]:
        """Generate demo contacts for testing."""
        now = datetime.utcnow()
        return [
            Lead(
                id="demo-1",
                email="sarah.johnson@techcorp.com",
                first_name="Sarah",
                last_name="Johnson",
                name="Sarah Johnson",
                company="TechCorp Industries",
                job_title="VP of Engineering",
                phone="+1-555-0101",
                company_size=250,
                deal_stage="opportunity",
                created_at=now - timedelta(days=30),
                last_activity=now - timedelta(hours=2),
                engagement=EngagementSummary(
                    email_opens=15,
                    email_clicks=8,
                    website_visits=12,
                    crm_activities=6,
                    last_email_open=now - timedelta(hours=2),
                    last_website_visit=now - timedelta(hours=4),
                    last_crm_activity=now - timedelta(days=1),
                ),
            ),
            Lead(
                id="demo-2",
                email="michael.chen@startupco.io",
                first_name="Michael",
                last_name="Chen",
                name="Michael Chen",
                company="StartupCo",
                job_title="CTO",
                phone="+1-555-0102",
                company_size=25,
                deal_stage="qualified",
                created_at=now - timedelta(days=15),
                last_activity=now - timedelta(days=7),
                engagement=EngagementSummary(
                    email_opens=3,
                    email_clicks=1,
                    website_visits=2,
                    crm_activities=1,
                    last_email_open=now - timedelta(days=7),
                    last_website_visit=now - timedelta(days=10),
                    last_crm_activity=now - timedelta(days=14),
                ),
            ),
            Lead(
                id="demo-3",
                email="jennifer.martinez@enterprise.com",
                first_name="Jennifer",
                last_name="Martinez",
                name="Jennifer Martinez",
                company="Enterprise Solutions Inc",
                job_title="Director of Sales",
                phone="+1-555-0103",
                company_size=5000,
                deal_stage="opportunity",
                created_at=now - timedelta(days=45),
                last_activity=now - timedelta(hours=1),
                engagement=EngagementSummary(
                    email_opens=22,
                    email_clicks=12,
                    website_visits=18,
                    crm_activities=10,
                    last_email_open=now - timedelta(hours=1),
                    last_website_visit=now - timedelta(hours=3),
                    last_crm_activity=now - timedelta(hours=6),
                ),
            ),
            Lead(
                id="demo-4",
                email="david.kim@smallbiz.net",
                first_name="David",
                last_name="Kim",
                name="David Kim",
                company="Small Business LLC",
                job_title="Owner",
                phone="+1-555-0104",
                company_size=5,
                deal_stage="subscriber",
                created_at=now - timedelta(days=60),
                last_activity=now - timedelta(days=30),
                engagement=EngagementSummary(
                    email_opens=1,
                    email_clicks=0,
                    website_visits=1,
                    crm_activities=0,
                    last_email_open=now - timedelta(days=30),
                    last_website_visit=now - timedelta(days=45),
                    last_crm_activity=None,
                ),
            ),
            Lead(
                id="demo-5",
                email="amanda.williams@growthco.com",
                first_name="Amanda",
                last_name="Williams",
                name="Amanda Williams",
                company="GrowthCo",
                job_title="Head of Marketing",
                phone="+1-555-0105",
                company_size=150,
                deal_stage="opportunity",
                created_at=now - timedelta(days=20),
                last_activity=now - timedelta(hours=12),
                engagement=EngagementSummary(
                    email_opens=10,
                    email_clicks=6,
                    website_visits=8,
                    crm_activities=4,
                    last_email_open=now - timedelta(hours=12),
                    last_website_visit=now - timedelta(hours=18),
                    last_crm_activity=now - timedelta(days=2),
                ),
            ),
        ]

    def _get_demo_activities(self, contact_id: str) -> List[Activity]:
        """Generate demo activities for testing."""
        now = datetime.utcnow()
        return [
            Activity(
                lead_id=contact_id,
                activity_type=ActivityType.CRM_CALL,
                timestamp=now - timedelta(days=1),
                description="Discovery call - discussed pain points",
            ),
            Activity(
                lead_id=contact_id,
                activity_type=ActivityType.CRM_EMAIL,
                timestamp=now - timedelta(days=2),
                description="Sent pricing information",
            ),
            Activity(
                lead_id=contact_id,
                activity_type=ActivityType.CRM_MEETING,
                timestamp=now - timedelta(days=7),
                description="Product demo",
            ),
        ]
