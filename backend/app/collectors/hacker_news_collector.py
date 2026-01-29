"""Hacker News data collector using Algolia API.

Focuses on finding PAIN POINTS and unmet needs, not promotional posts.
Targets "Ask HN" posts where people are seeking solutions.
"""

import os
import sys
from datetime import UTC, datetime, timedelta
from typing import Any

import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .base_collector import BaseCollector, CollectorResult, register_collector


@register_collector('hacker_news')
class HackerNewsCollector(BaseCollector):
    """Collector for Hacker News pain points using Algolia API.

    Focuses on "Ask HN" posts and discussions where people express
    problems, frustrations, and unmet needs - real opportunity signals.

    Configuration:
        custom_params: {
            'days_back': Number of days to look back (default: 30)
            'min_points': Minimum upvotes required (default: 5)
            'min_comments': Minimum comments required (default: 2)
        }
    """

    API_URL = "https://hn.algolia.com/api/v1"

    # Pain point search queries - these find people with PROBLEMS
    PAIN_POINT_QUERIES = [
        # Direct asks for solutions
        'Ask HN: How do you',
        'Ask HN: What do you use for',
        'Ask HN: Is there a tool',
        'Ask HN: Best way to',
        'Ask HN: Looking for',

        # Frustration signals
        'frustrated with',
        'annoyed by',
        'hate having to',
        'wish there was',
        'why is it so hard',

        # Unmet needs
        'need a better',
        'looking for alternative',
        'recommend a tool',
        'how do you handle',
        'struggling with',
    ]

    # Keywords that indicate a real pain point (boost score)
    PAIN_INDICATORS = [
        'frustrated', 'annoying', 'tedious', 'painful', 'hate',
        'wish', 'need', 'looking for', 'alternative', 'better way',
        'how do you', 'what do you use', 'recommend', 'suggestion',
        'problem', 'issue', 'struggle', 'difficult', 'hard to'
    ]

    # Keywords that indicate NOT an opportunity (filter out)
    EXCLUDE_KEYWORDS = [
        'hiring', 'job', 'salary', 'interview', 'resume',
        'who is hiring', 'freelancer', 'remote job',
        'launched', 'show hn', 'my startup', 'i built',
    ]

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize HN collector."""
        super().__init__(config)

    def _authenticate(self) -> None:
        """No authentication required for Algolia HN API."""
        pass

    def get_required_config_keys(self) -> list[str]:
        """No API keys required."""
        return []

    def collect(
        self,
        days_back: int = 30,
        limit_per_query: int = 50,
        **kwargs: Any
    ) -> list[CollectorResult]:
        """Collect pain point posts from Hacker News.

        Args:
            days_back: Number of days to look back (default: 30)
            limit_per_query: Results per search query

        Returns:
            List of validated pain point opportunities
        """
        custom_params = self.collector_config.custom_params
        days_back = custom_params.get('days_back', days_back)
        min_points = custom_params.get('min_points', 5)
        min_comments = custom_params.get('min_comments', 2)

        results = []
        seen_ids = set()
        cutoff_timestamp = int((datetime.now(UTC) - timedelta(days=days_back)).timestamp())

        # First, get "Ask HN" posts specifically (these are gold)
        ask_hn_results = self._search_ask_hn(cutoff_timestamp, min_points, min_comments)
        for result in ask_hn_results:
            if result.metadata.get('object_id') not in seen_ids:
                seen_ids.add(result.metadata.get('object_id'))
                results.append(result)

        # Then search for pain point keywords
        for query in self.PAIN_POINT_QUERIES:
            try:
                hits = self._search(query, cutoff_timestamp, limit_per_query)

                for hit in hits:
                    object_id = hit.get('objectID')
                    if object_id in seen_ids:
                        continue

                    # Filter by engagement
                    points = hit.get('points', 0) or 0
                    comments = hit.get('num_comments', 0) or 0

                    if points < min_points or comments < min_comments:
                        continue

                    # Get full text
                    title = hit.get('title', '') or ''
                    story_text = hit.get('story_text', '') or ''
                    combined_text = f"{title} {story_text}".lower()

                    # Skip excluded content (jobs, promos)
                    if self._should_exclude(combined_text):
                        continue

                    # Calculate pain point score
                    pain_score = self._calculate_pain_score(combined_text, points, comments)

                    if pain_score < 30:  # Minimum threshold
                        continue

                    seen_ids.add(object_id)

                    # Build HN URL for self-posts
                    url = hit.get('url') or f"https://news.ycombinator.com/item?id={object_id}"

                    result = CollectorResult(
                        title=self._normalize_text(title),
                        description=self._normalize_text(story_text[:1000]) if story_text else title,
                        url=url,
                        source_type='hacker_news',
                        engagement_metrics={
                            'upvotes': points,
                            'comments': comments,
                            'pain_score': pain_score,
                        },
                        metadata={
                            'author': hit.get('author'),
                            'created_at': hit.get('created_at'),
                            'object_id': object_id,
                            'is_ask_hn': title.lower().startswith('ask hn'),
                            'search_query': query,
                        }
                    )
                    results.append(result)

            except Exception as e:
                print(f"Error searching HN for '{query}': {e}")
                continue

        print(f"HN Collector: Found {len(results)} pain point opportunities")
        return results

    def _search_ask_hn(
        self,
        cutoff_timestamp: int,
        min_points: int,
        min_comments: int
    ) -> list[CollectorResult]:
        """Search specifically for Ask HN posts.

        These are the highest quality pain point signals.
        """
        results = []

        try:
            params = {
                'tags': 'ask_hn',
                'numericFilters': f'created_at_i>{cutoff_timestamp},points>{min_points},num_comments>{min_comments}',
                'hitsPerPage': 100,
            }

            response = requests.get(
                f"{self.API_URL}/search",
                params=params,
                timeout=self.collector_config.timeout
            )
            response.raise_for_status()

            hits = response.json().get('hits', [])

            for hit in hits:
                title = hit.get('title', '') or ''
                story_text = hit.get('story_text', '') or ''
                combined_text = f"{title} {story_text}".lower()

                # Skip job posts and promos
                if self._should_exclude(combined_text):
                    continue

                points = hit.get('points', 0) or 0
                comments = hit.get('num_comments', 0) or 0
                object_id = hit.get('objectID')

                pain_score = self._calculate_pain_score(combined_text, points, comments)

                url = f"https://news.ycombinator.com/item?id={object_id}"

                result = CollectorResult(
                    title=self._normalize_text(title),
                    description=self._normalize_text(story_text[:1000]) if story_text else title,
                    url=url,
                    source_type='hacker_news',
                    engagement_metrics={
                        'upvotes': points,
                        'comments': comments,
                        'pain_score': pain_score,
                    },
                    metadata={
                        'author': hit.get('author'),
                        'created_at': hit.get('created_at'),
                        'object_id': object_id,
                        'is_ask_hn': True,
                        'search_query': 'ask_hn',
                    }
                )
                results.append(result)

        except Exception as e:
            print(f"Error fetching Ask HN posts: {e}")

        return results

    def _search(self, query: str, cutoff_timestamp: int, limit: int) -> list[dict]:
        """Execute a search query."""
        params = {
            'query': query,
            'numericFilters': f'created_at_i>{cutoff_timestamp}',
            'hitsPerPage': limit,
        }

        response = requests.get(
            f"{self.API_URL}/search",
            params=params,
            timeout=self.collector_config.timeout
        )
        response.raise_for_status()

        return response.json().get('hits', [])

    def _should_exclude(self, text: str) -> bool:
        """Check if content should be excluded."""
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.EXCLUDE_KEYWORDS)

    def _calculate_pain_score(self, text: str, points: int, comments: int) -> int:
        """Calculate a pain point score based on content and engagement.

        Score 0-100:
        - Pain indicators in text: up to 40 points
        - Upvotes: up to 30 points (logarithmic)
        - Comments: up to 30 points (logarithmic)
        """
        import math

        score = 0
        text_lower = text.lower()

        # Pain indicator score (up to 40 points)
        pain_matches = sum(1 for indicator in self.PAIN_INDICATORS if indicator in text_lower)
        score += min(40, pain_matches * 10)

        # Upvote score (up to 30 points, logarithmic)
        if points > 0:
            # 10 points = 15, 50 points = 25, 100+ points = 30
            score += min(30, int(math.log(points + 1) * 8))

        # Comment score (up to 30 points, logarithmic)
        if comments > 0:
            # 5 comments = 13, 20 comments = 24, 50+ comments = 30
            score += min(30, int(math.log(comments + 1) * 8))

        return min(100, score)
