"""Application configuration."""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Demo Mode
    demo_mode: bool = True

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = False

    # HubSpot Integration
    hubspot_api_key: str = ""
    hubspot_api_url: str = "https://api.hubapi.com"

    # Slack Integration
    slack_webhook_url: str = ""
    slack_channel: str = "#sales-alerts"

    # Scoring Configuration
    score_refresh_interval: int = 3600  # seconds
    hot_lead_threshold: int = 75
    warm_lead_threshold: int = 50

    # Feature Weights
    weight_email_opens: float = 0.25
    weight_email_clicks: float = 0.20
    weight_website_visits: float = 0.20
    weight_crm_activities: float = 0.15
    weight_deal_stage: float = 0.10
    weight_company_size: float = 0.05
    weight_recency: float = 0.05

    # Database (optional)
    database_url: str | None = None

    # Redis (optional)
    redis_url: str | None = None

    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False

    def validate_weights(self) -> None:
        """Ensure all weights sum to 1.0."""
        total = (
            self.weight_email_opens
            + self.weight_email_clicks
            + self.weight_website_visits
            + self.weight_crm_activities
            + self.weight_deal_stage
            + self.weight_company_size
            + self.weight_recency
        )
        if abs(total - 1.0) > 0.001:
            raise ValueError(f"Feature weights must sum to 1.0, got {total}")


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    settings = Settings()
    settings.validate_weights()
    return settings
