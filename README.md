# LeadScore

**CRM + Email → Prioritized Leads**

Intelligent lead scoring system that analyzes CRM activity, email engagement, and website visits to generate prioritized lead lists with real-time Slack alerts for hot leads.

## Problem

Sales teams often waste valuable time chasing cold leads while genuinely interested prospects go unnoticed. Without a systematic way to prioritize leads based on engagement signals, hot opportunities can grow stale.

## Solution

LeadScore analyzes multiple engagement signals from your CRM, email tracking, and website analytics to automatically score and prioritize leads. The system:

- Pulls contact and activity data from HubSpot CRM
- Tracks email engagement (opens, clicks, replies)
- Monitors website visit patterns
- Applies machine learning-based scoring algorithm
- Sends real-time Slack alerts when leads become "hot"
- Provides API for integration with dashboards and workflows

## Tech Stack

- **Backend**: Python 3.11, FastAPI
- **CRM Integration**: HubSpot API
- **Notifications**: Slack API
- **ML/Scoring**: Scikit-learn, custom weighted features
- **Data Storage**: PostgreSQL (optional, can run in-memory)
- **Deployment**: Docker, Docker Compose

## Features

- **Multi-Signal Scoring**: Combines CRM activities, email engagement, and web visits
- **Real-Time Alerts**: Instant Slack notifications for high-priority leads
- **Scheduled Updates**: Automatic score recalculation on configurable intervals
- **REST API**: Query leads, scores, and configure alert thresholds
- **Demo Mode**: Run without real integrations using mock data
- **Production Ready**: Containerized, tested, configurable

## Quick Start

### Demo Mode (No External Services Required)

```bash
# Clone and setup
git clone <repo-url>
cd leadscore

# Install dependencies
pip install -r requirements.txt

# Run in demo mode
DEMO_MODE=true python -m src.main

# Access API at http://localhost:8000
# Visit http://localhost:8000/docs for interactive API documentation
```

### Production Setup

1. **Environment Configuration**

```bash
cp .env.example .env
# Edit .env with your credentials
```

Required environment variables:
```
HUBSPOT_API_KEY=your_hubspot_api_key
SLACK_WEBHOOK_URL=your_slack_webhook_url
DEMO_MODE=false
SCORE_REFRESH_INTERVAL=3600  # seconds
HOT_LEAD_THRESHOLD=75  # score threshold for alerts
```

2. **Docker Deployment**

```bash
docker-compose up -d
```

3. **Manual Installation**

```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations (if using PostgreSQL)
# python -m alembic upgrade head

# Start server
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

## API Documentation

### Get All Leads with Scores

```bash
GET /api/leads

# Example response
{
  "leads": [
    {
      "id": "12345",
      "email": "prospect@company.com",
      "name": "Jane Doe",
      "company": "Acme Corp",
      "score": 85,
      "score_category": "hot",
      "last_activity": "2024-01-15T10:30:00Z",
      "engagement_summary": {
        "email_opens": 12,
        "email_clicks": 5,
        "website_visits": 8,
        "crm_activities": 15
      }
    }
  ]
}
```

### Get Single Lead Score

```bash
GET /api/leads/{lead_id}
```

### Trigger Manual Score Refresh

```bash
POST /api/leads/refresh
```

### Update Alert Configuration

```bash
POST /api/alerts/config
Content-Type: application/json

{
  "hot_threshold": 80,
  "warm_threshold": 60,
  "enable_slack": true
}
```

## Scoring Algorithm

LeadScore uses a weighted feature model that considers:

| Signal | Weight | Description |
|--------|--------|-------------|
| Recent Email Opens | 25% | Opens in last 7 days |
| Email Clicks | 20% | Click-through rate |
| Website Visits | 20% | Frequency and recency |
| CRM Activities | 15% | Calls, meetings, notes |
| Deal Stage | 10% | Position in sales pipeline |
| Company Size | 5% | Employee count |
| Recency Factor | 5% | Time since last interaction |

**Score Categories:**
- **Hot (75-100)**: Immediate follow-up required, Slack alert sent
- **Warm (50-74)**: High priority, follow up within 24 hours
- **Cold (0-49)**: Low priority, periodic nurture campaigns

## Architecture

```
┌─────────────┐
│   HubSpot   │
│     CRM     │
└──────┬──────┘
       │
       ├──────────────┐
       │              │
┌──────▼──────┐  ┌───▼────────┐
│   Email     │  │  Website   │
│  Tracking   │  │  Analytics │
└──────┬──────┘  └───┬────────┘
       │             │
       └──────┬──────┘
              │
       ┌──────▼───────┐
       │   Scoring    │
       │   Engine     │
       └──────┬───────┘
              │
       ┌──────▼───────┐
       │   FastAPI    │
       │     API      │
       └──────┬───────┘
              │
       ┌──────▼───────┐
       │    Slack     │
       │    Alerts    │
       └──────────────┘
```

## Development

### Running Tests

```bash
pytest tests/
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint
flake8 src/ tests/

# Type checking
mypy src/
```

## Configuration

All configuration is managed through environment variables. See `.env.example` for a complete list of options.

### Scoring Weights Customization

Edit `src/ml/model.py` to adjust feature weights:

```python
WEIGHTS = {
    'email_opens_recent': 0.25,
    'email_click_rate': 0.20,
    'website_visits': 0.20,
    'crm_activities': 0.15,
    'deal_stage': 0.10,
    'company_size': 0.05,
    'recency': 0.05
}
```

### Alert Thresholds

Adjust in `.env`:
```
HOT_LEAD_THRESHOLD=75
WARM_LEAD_THRESHOLD=50
```

## Deployment

### Docker

```bash
docker build -t leadscore:latest .
docker run -p 8000:8000 --env-file .env leadscore:latest
```

### Docker Compose

```bash
docker-compose up -d
```

Includes:
- LeadScore API service
- PostgreSQL database (optional)
- Redis for caching (optional)

## Monitoring

The API includes health check endpoints:

```bash
GET /health
GET /metrics  # Prometheus-compatible metrics
```

## Limitations & Future Enhancements

**Current Limitations:**
- Single-tenant (one company/CRM instance)
- Scoring model is static (not adaptive)
- Limited to HubSpot CRM

**Planned Enhancements:**
- Multi-tenant support
- Adaptive ML model that learns from conversion data
- Support for Salesforce, Pipedrive, other CRMs
- Lead segmentation and custom scoring profiles
- Historical score tracking and trend analysis
- Bi-directional sync (update CRM with scores)

## License

MIT

## Contact

Built by Jesse Eldridge
Portfolio: [itsjesse.dev](https://itsjesse.dev)
# Scoring model
