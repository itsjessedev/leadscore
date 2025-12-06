"""ML-based scoring model (simplified weighted features approach)."""

import logging
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from typing import List, Dict

from ..models import Lead

logger = logging.getLogger(__name__)


class ScoringModel:
    """
    Machine learning scoring model.

    This is a simplified implementation using weighted features.
    In production, this could be replaced with a trained model
    that learns from historical conversion data.
    """

    def __init__(self, weights: Dict[str, float]):
        """
        Initialize model with feature weights.

        Args:
            weights: Dictionary mapping feature names to weights (should sum to 1.0)
        """
        self.weights = weights
        self.scaler = MinMaxScaler()
        self._is_fitted = False

    def fit(self, leads: List[Lead]) -> None:
        """
        Fit the scaler to historical lead data.

        In a real ML implementation, this would train a model
        on historical leads and their conversion outcomes.
        """
        if not leads:
            logger.warning("No leads provided for fitting")
            return

        features = self._extract_features(leads)
        if len(features) > 0:
            self.scaler.fit(features)
            self._is_fitted = True
            logger.info(f"Fitted scaler on {len(leads)} leads")

    def predict_score(self, lead: Lead) -> float:
        """
        Predict score for a single lead.

        Returns:
            Score from 0-100
        """
        features = self._extract_features([lead])
        if len(features) == 0:
            return 0.0

        if self._is_fitted:
            features = self.scaler.transform(features)
        else:
            # Normalize on-the-fly if not fitted
            features = features / (features.max(axis=0) + 1e-10)

        # Calculate weighted score
        weighted_features = features[0] * list(self.weights.values())
        score = np.sum(weighted_features) * 100

        return min(100.0, max(0.0, score))

    def _extract_features(self, leads: List[Lead]) -> np.ndarray:
        """
        Extract feature vectors from leads.

        Features (in order matching weights):
        - email_opens_recent
        - email_click_rate
        - website_visits
        - crm_activities
        - deal_stage_score
        - company_size_score
        - recency_score
        """
        feature_matrix = []

        for lead in leads:
            features = [
                lead.engagement.email_opens,  # Raw count
                lead.engagement.email_clicks,  # Raw count
                lead.engagement.website_visits,  # Raw count
                lead.engagement.crm_activities,  # Raw count
                self._encode_deal_stage(lead.deal_stage),  # Categorical -> numeric
                lead.company_size or 0,  # Raw size
                self._calculate_recency_days(lead),  # Days since last activity
            ]
            feature_matrix.append(features)

        return np.array(feature_matrix, dtype=float)

    def _encode_deal_stage(self, stage: str | None) -> float:
        """Encode deal stage as numeric value."""
        stage_map = {
            "subscriber": 20,
            "lead": 30,
            "marketing_qualified": 50,
            "qualified": 60,
            "opportunity": 80,
            "customer": 100,
        }
        return stage_map.get((stage or "").lower(), 30)

    def _calculate_recency_days(self, lead: Lead) -> float:
        """Calculate days since last activity (inverted so recent = higher)."""
        if not lead.last_activity:
            return 0.0

        from datetime import datetime

        days = (datetime.utcnow() - lead.last_activity).days
        # Invert: recent activity = higher value
        return max(0, 30 - days)
