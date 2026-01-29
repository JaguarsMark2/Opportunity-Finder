"""Mastodon data collector using Mastodon API.

Mastodon is a federated network, so we search across multiple popular instances.
The API is free and public search doesn't require authentication on most instances.
"""

import os
import sys
from datetime import UTC, datetime, timedelta
from typing import Any

import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .base_collector import BaseCollector, CollectorResult, register_collector


@register_collector('mastodon')
class MastodonCollector(BaseCollector):
    """Collector for Mastodon data across multiple instances.

    Searches for startup and pain point related posts on Mastodon.
    Uses public API endpoints that don't require authentication.

    Configuration:
        api_keys: {
            'access_token': Optional access token for higher rate limits
            'instance': Primary instance URL (default: mastodon.social)
        }
        custom_params: {
            'days_back': Number of days to look back (default: 7)
            'limit_per_query': Results per search query (default: 20)
            'search_queries': Custom search queries (optional)
            'instances': List of instances to search (optional)
        }
    """

    # Default instances to search (tech-focused)
    DEFAULT_INSTANCES = [
        'https://mastodon.social',
        'https://hachyderm.io',       # Tech workers
        'https://fosstodon.org',      # FOSS community
        'https://indieweb.social',    # Indie web/makers
    ]

    # Search queries for opportunities
    SEARCH_QUERIES = [
        'startup',
        'SaaS',
        'indie hacker',
        'side project',
        'building in public',
        'looking for tool',
        'wish there was',
        'micro saas'
    ]

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize Mastodon collector."""
        super().__init__(config)
        self.access_token = None
        self.primary_instance = 'https://mastodon.social'
        self._authenticate()

    def _authenticate(self) -> None:
        """Set up authentication if access token provided.

        Authentication is optional but provides higher rate limits.
        """
        api_keys = self.config.get('api_keys', {})
        self.access_token = api_keys.get('access_token')
        if api_keys.get('instance'):
            self.primary_instance = api_keys['instance'].rstrip('/')

    def get_required_config_keys(self) -> list[str]:
        """Get required configuration keys.

        Returns:
            Empty list - authentication is optional
        """
        return []

    def collect(
        self,
        days_back: int = 7,
        limit_per_query: int = 20,
        **kwargs: Any
    ) -> list[CollectorResult]:
        """Collect posts from Mastodon instances.

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
        instances = custom_params.get('instances', self.DEFAULT_INSTANCES)

        results = []
        seen_urls = set()
        cutoff_date = datetime.now(UTC) - timedelta(days=days_back)

        # Search each instance
        for instance in instances:
            instance = instance.rstrip('/')

            headers = {'Accept': 'application/json'}
            if self.access_token and instance == self.primary_instance:
                headers['Authorization'] = f'Bearer {self.access_token}'

            for query in search_queries:
                try:
                    # Use v2 search API
                    params = {
                        'q': query,
                        'type': 'statuses',
                        'limit': limit_per_query,
                        'resolve': 'false'
                    }

                    response = requests.get(
                        f"{instance}/api/v2/search",
                        params=params,
                        headers=headers,
                        timeout=self.collector_config.timeout
                    )

                    if response.status_code != 200:
                        # Some instances may not allow public search
                        continue

                    data = response.json()
                    statuses = data.get('statuses', [])

                    for status in statuses:
                        try:
                            url = status.get('url', '')
                            if url in seen_urls:
                                continue
                            seen_urls.add(url)

                            # Parse date
                            created_at_str = status.get('created_at', '')
                            if created_at_str:
                                try:
                                    created_at = datetime.fromisoformat(
                                        created_at_str.replace('Z', '+00:00')
                                    )
                                    if created_at < cutoff_date:
                                        continue
                                except ValueError:
                                    pass

                            # Get content (strip HTML)
                            content = status.get('content', '')
                            content = self._strip_html(content)

                            # Get engagement metrics
                            favourites_count = status.get('favourites_count', 0)
                            reblogs_count = status.get('reblogs_count', 0)
                            replies_count = status.get('replies_count', 0)

                            # Get author info
                            account = status.get('account', {})
                            author_handle = account.get('acct', '')
                            author_display = account.get('display_name', author_handle)

                            result = CollectorResult(
                                title=content[:100] + ('...' if len(content) > 100 else ''),
                                description=content[:500],
                                url=url,
                                source_type='mastodon',
                                engagement_metrics={
                                    'favourites': favourites_count,
                                    'reblogs': reblogs_count,
                                    'replies': replies_count,
                                    'total_engagement': favourites_count + reblogs_count + replies_count
                                },
                                metadata={
                                    'author': author_handle,
                                    'author_display': author_display,
                                    'created_at': created_at_str,
                                    'instance': instance,
                                    'search_query': query,
                                    'language': status.get('language')
                                }
                            )
                            results.append(result)

                        except Exception as e:
                            print(f"Error parsing Mastodon status: {e}")
                            continue

                except requests.exceptions.Timeout:
                    print(f"Mastodon timeout for {instance}")
                    continue
                except Exception as e:
                    print(f"Error searching Mastodon ({instance}) for '{query}': {e}")
                    continue

        return results

    def _strip_html(self, html: str) -> str:
        """Strip HTML tags from content.

        Args:
            html: HTML content

        Returns:
            Plain text content
        """
        import re
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', ' ', html)
        # Decode HTML entities
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&quot;', '"')
        text = text.replace('&#39;', "'")
        text = text.replace('&nbsp;', ' ')
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text
