"""Product Hunt data collector using GraphQL API."""

import os
import sys
from datetime import UTC, datetime, timedelta
from typing import Any

import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .base_collector import BaseCollector, CollectorResult, register_collector


@register_collector('product_hunt')
class ProductHuntCollector(BaseCollector):
    """Collector for Product Hunt data using GraphQL API.

    Collects new products with engagement metrics.

    Configuration:
        api_keys: {
            'api_token': Product Hunt API token
        }
        custom_params: {
            'days_back': Number of days to look back (default: 7)
            'limit': Maximum products to collect (default: 50)
        }
    """

    API_URL = "https://api.producthunt.com/v2/api/graphql"

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize Product Hunt collector."""
        super().__init__(config)
        self._authenticate()

    def _authenticate(self) -> None:
        """Set up API authentication."""
        api_keys = self.config.get('api_keys', {})
        if 'api_token' not in api_keys:
            raise ValueError("Missing required API key: api_token")

        self.headers = {
            'Authorization': f"Bearer {api_keys['api_token']}",
            'Content-Type': 'application/json'
        }

    def get_required_config_keys(self) -> list[str]:
        """Get required configuration keys.

        Returns:
            List of required API key names
        """
        return ['api_token']

    def collect(  # type: ignore[override]
        self,
        days_back: int = 7,
        limit: int = 50,
        **kwargs: Any
    ) -> list[CollectorResult]:
        """Collect recent products from Product Hunt.

        Args:
            days_back: Number of days to look back
            limit: Maximum products to collect

        Returns:
            List of collector results
        """
        # Get custom params
        custom_params = self.collector_config.custom_params
        if custom_params.get('days_back'):
            days_back = custom_params['days_back']
        if custom_params.get('limit'):
            limit = custom_params['limit']

        results = []

        # GraphQL query
        query = """
        query GetPosts($after: String) {
            posts(order: RANKING, first: %d) {
                edges {
                    node {
                        id
                        name
                        tagline
                        description
                        url
                        website
                        votesCount
                        commentsCount
                        featuredAt
                        topics {
                            edges {
                                node {
                                    name
                                }
                            }
                        }
                    }
                    cursor
                }
                pageInfo {
                    hasNextPage
                    endCursor
                }
            }
        }
        """ % limit

        try:
            response = requests.post(
                self.API_URL,
                json={'query': query},
                headers=self.headers,
                timeout=self.collector_config.timeout
            )
            response.raise_for_status()

            data = response.json()
            posts = data.get('data', {}).get('posts', {}).get('edges', [])

            for edge in posts:
                node = edge.get('node', {})

                # Skip if too old
                featured_at = node.get('featuredAt')
                if featured_at:
                    featured_date = datetime.fromisoformat(featured_at.replace('Z', '+00:00'))
                    if featured_date < datetime.now(UTC) - timedelta(days=days_back):
                        continue

                result = CollectorResult(
                    title=node.get('name', ''),
                    description=node.get('tagline', node.get('description', ''))[:500],
                    url=node.get('url', node.get('website', '')),
                    source_type='product_hunt',
                    engagement_metrics={
                        'votes': node.get('votesCount', 0),
                        'comments': node.get('commentsCount', 0)
                    },
                    metadata={
                        'topics': [t['node']['name'] for t in node.get('topics', {}).get('edges', [])],
                        'featured_at': featured_at
                    }
                )
                results.append(result)

        except Exception as e:
            print(f"Error collecting from Product Hunt: {e}")

        return results
