"""Microns (social engagement) data collector."""

import os
import sys
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .base_collector import BaseCollector, register_collector


@register_collector('microns')
class MicronsCollector(BaseCollector):
    """Collector for aggregated social engagement metrics.

    Aggregates engagement data across sources to calculate
    "microns" (engagement scores).

    Configuration:
        custom_params: {
            'source_weights': Custom weights for each source
            'engagement_weights': Custom weights for engagement metrics
        }
    """

    # Source weights for engagement calculation
    SOURCE_WEIGHTS = {
        'reddit': 1.0,
        'indie_hackers': 1.2,
        'product_hunt': 1.5,
        'hacker_news': 1.3
    }

    # Engagement component weights
    ENGAGEMENT_WEIGHTS = {
        'upvotes': 0.4,
        'comments': 0.3,
        'shares': 0.2,
        'external_links': 0.1
    }

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize Microns collector."""
        super().__init__(config)

        # Apply custom weights if provided
        custom_params = self.collector_config.custom_params
        if custom_params.get('source_weights'):
            self.SOURCE_WEIGHTS.update(custom_params['source_weights'])
        if custom_params.get('engagement_weights'):
            self.ENGAGEMENT_WEIGHTS.update(custom_params['engagement_weights'])

    def _authenticate(self) -> None:
        """No authentication required."""
        pass

    def get_required_config_keys(self) -> list[str]:
        """Get required configuration keys.

        Returns:
            Empty list - no API keys required
        """
        return []

    def collect(  # type: ignore[override]
        self,
        opportunities: list[dict[str, Any]] | None = None,
        **kwargs: Any
    ) -> list[dict[str, Any]]:
        """Calculate engagement scores for opportunities.

        Args:
            opportunities: List of opportunities with engagement data

        Returns:
            Opportunities with added engagement scores
        """
        if opportunities is None:
            return []

        results = []

        for opp in opportunities:
            engagement_score = self._calculate_engagement(opp)

            opp_with_score = opp.copy()
            opp_with_score['engagement_score'] = engagement_score
            opp_with_score['engagement_level'] = self._classify_engagement(engagement_score)

            results.append(opp_with_score)

        return results

    def _calculate_engagement(self, opp: dict[str, Any]) -> float:
        """Calculate engagement score for an opportunity.

        Args:
            opp: Opportunity data

        Returns:
            Engagement score (microns)
        """
        source_type = opp.get('source_type', 'reddit')
        metrics = opp.get('engagement_metrics', {})

        # Get source weight
        source_weight = self.SOURCE_WEIGHTS.get(source_type, 1.0)

        # Calculate components
        score = 0.0

        # Upvotes/points
        upvotes = metrics.get('upvotes', metrics.get('votes', metrics.get('points', 0)))
        score += upvotes * self.ENGAGEMENT_WEIGHTS['upvotes']

        # Comments
        comments = metrics.get('comments', 0)
        score += comments * self.ENGAGEMENT_WEIGHTS['comments']

        # Apply source weight
        final_score = score * source_weight

        return round(final_score, 2)

    def _classify_engagement(self, score: float) -> str:
        """Classify engagement level.

        Args:
            score: Engagement score

        Returns:
            Engagement level (LOW, MEDIUM, HIGH)
        """
        if score < 50:
            return 'LOW'
        elif score < 200:
            return 'MEDIUM'
        else:
            return 'HIGH'
