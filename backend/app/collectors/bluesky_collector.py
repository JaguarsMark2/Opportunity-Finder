"""Bluesky data collector using AT Protocol API."""

import os
import sys
from datetime import UTC, datetime, timedelta
from typing import Any

import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .base_collector import BaseCollector, CollectorResult, register_collector


@register_collector('bluesky')
class BlueskyCollector(BaseCollector):
    """Collector for Bluesky data using AT Protocol.

    Searches for startup and pain point related posts on Bluesky.
    Bluesky's API is free and doesn't require authentication for public searches.

    Configuration:
        api_keys: {
            'identifier': Bluesky handle (optional, for authenticated requests)
            'password': App password (optional, for authenticated requests)
        }
        custom_params: {
            'days_back': Number of days to look back (default: 7)
            'limit_per_query': Results per search query (default: 25)
            'search_queries': Custom search queries (optional)
        }
    """

    # Public API endpoint (no auth required for search)
    API_URL = "https://public.api.bsky.app/xrpc"

    # Auth API endpoint (if credentials provided)
    AUTH_API_URL = "https://bsky.social/xrpc"

    # Search queries for opportunities
    SEARCH_QUERIES = [
        'startup idea',
        'SaaS',
        'micro-SaaS',
        'looking for tool',
        'wish there was',
        'anyone know of',
        'building in public',
        'indie hacker',
        'side project',
        'problem with'
    ]

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize Bluesky collector."""
        super().__init__(config)
        self.session_token = None
        self._authenticate()

    def _authenticate(self) -> None:
        """Authenticate with Bluesky if credentials provided.

        Authentication is optional - public search works without it.
        But authenticated requests have higher rate limits.
        """
        api_keys = self.config.get('api_keys', {})
        identifier = api_keys.get('identifier')
        password = api_keys.get('password')

        if identifier and password:
            try:
                response = requests.post(
                    f"{self.AUTH_API_URL}/com.atproto.server.createSession",
                    json={
                        'identifier': identifier,
                        'password': password
                    },
                    timeout=10
                )
                if response.status_code == 200:
                    data = response.json()
                    self.session_token = data.get('accessJwt')
                    print(f"Bluesky: Authenticated as {identifier}")
                else:
                    print(f"Bluesky: Auth failed, using public API")
            except Exception as e:
                print(f"Bluesky: Auth error ({e}), using public API")

    def get_required_config_keys(self) -> list[str]:
        """Get required configuration keys.

        Returns:
            Empty list - authentication is optional
        """
        return []

    def collect(
        self,
        days_back: int = 7,
        limit_per_query: int = 25,
        **kwargs: Any
    ) -> list[CollectorResult]:
        """Collect posts from Bluesky.

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
        seen_uris = set()
        cutoff_date = datetime.now(UTC) - timedelta(days=days_back)

        headers = {}
        if self.session_token:
            headers['Authorization'] = f'Bearer {self.session_token}'

        for query in search_queries:
            try:
                # Use searchPosts endpoint
                params = {
                    'q': query,
                    'limit': limit_per_query,
                    'sort': 'latest'
                }

                response = requests.get(
                    f"{self.API_URL}/app.bsky.feed.searchPosts",
                    params=params,
                    headers=headers,
                    timeout=self.collector_config.timeout
                )

                if response.status_code != 200:
                    print(f"Bluesky search error for '{query}': {response.status_code}")
                    continue

                data = response.json()
                posts = data.get('posts', [])

                for post in posts:
                    try:
                        uri = post.get('uri', '')
                        if uri in seen_uris:
                            continue
                        seen_uris.add(uri)

                        # Parse post data
                        record = post.get('record', {})
                        text = record.get('text', '')
                        created_at_str = record.get('createdAt', '')

                        # Parse date
                        if created_at_str:
                            try:
                                created_at = datetime.fromisoformat(
                                    created_at_str.replace('Z', '+00:00')
                                )
                                if created_at < cutoff_date:
                                    continue
                            except ValueError:
                                pass

                        # Get engagement metrics
                        like_count = post.get('likeCount', 0)
                        reply_count = post.get('replyCount', 0)
                        repost_count = post.get('repostCount', 0)

                        # Get author info
                        author = post.get('author', {})
                        author_handle = author.get('handle', '')

                        # Build post URL
                        post_id = uri.split('/')[-1] if uri else ''
                        post_url = f"https://bsky.app/profile/{author_handle}/post/{post_id}"

                        result = CollectorResult(
                            title=text[:100] + ('...' if len(text) > 100 else ''),
                            description=text[:500],
                            url=post_url,
                            source_type='bluesky',
                            engagement_metrics={
                                'likes': like_count,
                                'replies': reply_count,
                                'reposts': repost_count,
                                'total_engagement': like_count + reply_count + repost_count
                            },
                            metadata={
                                'author': author_handle,
                                'created_at': created_at_str,
                                'uri': uri,
                                'search_query': query
                            }
                        )
                        results.append(result)

                    except Exception as e:
                        print(f"Error parsing Bluesky post: {e}")
                        continue

            except Exception as e:
                print(f"Error searching Bluesky for '{query}': {e}")
                continue

        return results
