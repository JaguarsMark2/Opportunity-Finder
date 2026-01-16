"""Hacker News data collector using Algolia API."""

import os
import sys
from datetime import UTC, datetime, timedelta
from typing import Any

import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .base_collector import BaseCollector, CollectorResult, register_collector


@register_collector('hacker_news')
class HackerNewsCollector(BaseCollector):
    """Collector for Hacker News data using Algolia API.

    Searches for startup and pain point related posts.

    Configuration:
        custom_params: {
            'days_back': Number of days to look back (default: 7)
            'limit_per_query': Results per search query (default: 20)
            'search_queries': Custom search queries (optional)
        }
    """

    API_URL = "https://hn.algolia.com/api/v1"

    # Search queries for opportunities
    SEARCH_QUERIES = [
        'startup idea',
        'SaaS',
        'micro-SaaS',
        'looking for tool',
        'wish there was',
        'anyone know of',
        'recommendation for',
        'problem with',
        'build startup',
        'side project'
    ]

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize HN collector."""
        super().__init__(config)

    def _authenticate(self) -> None:
        """No authentication required for Algolia HN API."""
        pass

    def get_required_config_keys(self) -> list[str]:
        """Get required configuration keys.

        Returns:
            Empty list - no API keys required
        """
        return []

    def collect(  # type: ignore[override]
        self,
        days_back: int = 7,
        limit_per_query: int = 20,
        **kwargs: Any
    ) -> list[CollectorResult]:
        """Collect posts from Hacker News.

        Args:
            days_back: Number of days to look back
            limit_per_query: Results per search query

        Returns:
            List of collector results
        """
        # Get custom params
        custom_params = self.collector_config.custom_params
        if custom_params.get('days_back'):
            days_back = custom_params['days_back']
        if custom_params.get('limit_per_query'):
            limit_per_query = custom_params['limit_per_query']

        search_queries = custom_params.get('search_queries', self.SEARCH_QUERIES)

        results = []
        cutoff_timestamp = int((datetime.now(UTC) - timedelta(days=days_back)).timestamp())

        for query in search_queries:
            try:
                params = {
                    'query': query,
                    'numericFilters': f'created_at_i>{cutoff_timestamp}',
                    'hitsPerPage': limit_per_query,
                    'tags': 'story'
                }

                response = requests.get(
                    f"{self.API_URL}/search",
                    params=params,
                    timeout=self.collector_config.timeout
                )
                response.raise_for_status()

                data = response.json()
                hits = data.get('hits', [])

                for hit in hits:
                    if not hit.get('url'):
                        continue

                    result = CollectorResult(
                        title=self._normalize_text(hit.get('title', '')),
                        description=hit.get('url', '')[:500],
                        url=hit.get('url', ''),
                        source_type='hacker_news',
                        engagement_metrics={
                            'points': hit.get('points', 0),
                            'comments': hit.get('num_comments', 0)
                        },
                        metadata={
                            'author': hit.get('author'),
                            'created_at': hit.get('created_at'),
                            'object_id': hit.get('objectID')
                        }
                    )
                    results.append(result)

            except Exception as e:
                print(f"Error searching HN for '{query}': {e}")
                continue

        return results
