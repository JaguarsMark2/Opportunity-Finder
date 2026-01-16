"""Google Trends data collector using SerpAPI."""

import os
import sys
from typing import Any

import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .base_collector import BaseCollector, register_collector


@register_collector('google_trends')
class GoogleTrendsCollector(BaseCollector):
    """Collector for Google Trends data using SerpAPI.

    Provides keyword volume and growth metrics.

    Configuration:
        api_keys: {
            'serpapi_key': SerpAPI key
        }
        custom_params: {
            'keywords': List of keywords to analyze
            'date_range': Date range for trends (default: 'today 12-m')
        }
    """

    API_URL = "https://serpapi.com/search.json"

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize Google Trends collector."""
        super().__init__(config)
        self._authenticate()

    def _authenticate(self) -> None:
        """Set up API authentication."""
        api_keys = self.config.get('api_keys', {})
        if 'serpapi_key' not in api_keys:
            raise ValueError("Missing required API key: serpapi_key")

        self.api_key = api_keys['serpapi_key']

    def get_required_config_keys(self) -> list[str]:
        """Get required configuration keys.

        Returns:
            List of required API key names
        """
        return ['serpapi_key']

    def collect(  # type: ignore[override]
        self,
        keywords: list[str] | None = None,
        **kwargs: Any
    ) -> dict[str, dict[str, Any]]:
        """Collect Google Trends data for keywords.

        Note: This returns a dict of metrics, not CollectorResult objects,
        as it's used to enrich opportunities from other sources.

        Args:
            keywords: List of keywords to analyze

        Returns:
            Dict mapping keywords to their metrics
        """
        # Get custom params
        custom_params = self.collector_config.custom_params
        if keywords is None:
            keywords = custom_params.get('keywords', [
                'micro saas',
                'startup idea',
                'saas boilerplate',
                'indie hacker',
                'side project',
                'passive income'
            ])

        results = {}

        for keyword in keywords:
            try:
                params = {
                    'engine': 'google_trends',
                    'q': keyword,
                    'api_key': self.api_key,
                    'date': custom_params.get('date_range', 'today 12-m')
                }

                response = requests.get(self.API_URL, params=params, timeout=self.collector_config.timeout)
                response.raise_for_status()

                data = response.json()
                trends_data = self._parse_trends_data(data)

                results[keyword] = {
                    'volume': trends_data.get('avg_volume', 'N/A'),
                    'growth': trends_data.get('growth_rate', 'N/A'),
                    'trend_over_time': trends_data.get('timeline', [])
                }

            except Exception as e:
                print(f"Error collecting trends for '{keyword}': {e}")
                results[keyword] = {'volume': 'N/A', 'growth': 'N/A'}

        return results

    def _parse_trends_data(self, data: dict) -> dict[str, Any]:
        """Parse trends data from SerpAPI response.

        Args:
            data: SerpAPI response

        Returns:
            Parsed metrics
        """
        timeline = data.get('timeline_data', [])

        if not timeline:
            return {}

        values = [t.get('values', [0])[0] for t in timeline if t.get('values')]

        if not values:
            return {}

        avg_volume = sum(values) / len(values)

        # Calculate growth rate
        if len(values) >= 2:
            first_value = values[0] if values[0] > 0 else 1
            growth_rate = ((values[-1] - first_value) / first_value) * 100
        else:
            growth_rate = 0

        return {
            'avg_volume': f"{int(avg_volume)}K" if avg_volume >= 1000 else str(int(avg_volume)),
            'growth_rate': f"+{int(growth_rate)}%" if growth_rate > 0 else f"{int(growth_rate)}%",
            'timeline': timeline
        }
