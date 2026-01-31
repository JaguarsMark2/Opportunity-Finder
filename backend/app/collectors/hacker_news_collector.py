"""Hacker News data collector using Algolia API.

Comprehensive market signal discovery — not just pain points but feature
requests, workarounds, integration gaps, tool comparisons, ideas, and
willingness-to-pay signals across Ask HN, Tell HN, and general discussions.
"""

import math
import os
import sys
import time
from datetime import UTC, datetime, timedelta
from typing import Any

import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .base_collector import BaseCollector, CollectorResult, register_collector

# Delay between Algolia requests to be a good citizen (seconds)
_REQUEST_DELAY = 0.3


@register_collector('hacker_news')
class HackerNewsCollector(BaseCollector):
    """Collector for Hacker News market signals using Algolia API.

    Searches broadly for opportunity signals: pain points, feature requests,
    workarounds, integration gaps, tool comparisons, and more.

    Configuration:
        custom_params: {
            'days_back': Number of days to look back (default: 30)
            'min_points': Minimum upvotes required (default: 3)
            'min_comments': Minimum comments required (default: 1)
            'signal_phrases': List of user-configured signal phrases
        }
    """

    API_URL = "https://hn.algolia.com/api/v1"

    # ── Search queries organised by signal type ──────────────────────
    SEARCH_QUERIES = [
        # ── Direct asks for solutions ──
        'Ask HN: How do you',
        'Ask HN: What do you use for',
        'Ask HN: Is there a tool',
        'Ask HN: Best way to',
        'Ask HN: Looking for',
        'Ask HN: What are you using',
        'Ask HN: How are you handling',
        'Ask HN: Anyone built',
        'Ask HN: What would you build',
        'Ask HN: What problems',

        # ── Frustration / pain signals ──
        'frustrated with',
        'annoyed by',
        'hate having to',
        'wish there was',
        'why is it so hard',
        'sick of',
        'waste of time',
        'broken workflow',
        'terrible experience',

        # ── Feature requests / gaps ──
        'need a better',
        'looking for alternative',
        'recommend a tool',
        'missing feature',
        'no good option',
        'nothing works well',
        'any alternative to',
        'replacement for',
        'switched from',
        'migrating away from',

        # ── Workaround signals ──
        'ended up building',
        'wrote a script to',
        'my workaround',
        'hack around',
        'built my own',
        'cobbled together',

        # ── Integration / automation gaps ──
        'integrate with',
        'no integration',
        'connect to',
        'automate',
        'manual process',
        'manually every',
        'hours every week',
        'spreadsheet',
        'copy paste',

        # ── Willingness to pay ──
        "I'd pay for",
        'paying too much for',
        'worth paying for',
        'shut up and take my money',
        'would pay',

        # ── Ideas / market discussions ──
        'someone should build',
        "why doesn't",
        'startup idea',
        'side project idea',
        'business opportunity',
        'underserved market',
        'gap in the market',

        # ── Tool comparisons / evaluations ──
        'compared to',
        'vs',
        'which is better',
        'pros and cons',
        'review of',

        # ── Building in public / validation ──
        'Tell HN:',
        'launched',
        'just shipped',
        'Show HN:',
    ]

    # Keywords that boost opportunity score
    OPPORTUNITY_INDICATORS = [
        'frustrated', 'annoying', 'tedious', 'painful', 'hate',
        'wish', 'need', 'looking for', 'alternative', 'better way',
        'how do you', 'what do you use', 'recommend', 'suggestion',
        'problem', 'issue', 'struggle', 'difficult', 'hard to',
        'workaround', 'hack', 'built my own', 'wrote a script',
        'integrate', 'automate', 'manual', 'repetitive',
        'pay for', 'worth', 'pricing', 'expensive', 'cheap',
        'missing', 'gap', 'no option', 'nothing works',
        'switched', 'migrated', 'replaced', 'moved away',
        'idea', 'opportunity', 'market', 'demand', 'growing',
    ]

    # Keywords that indicate NOT an opportunity (filter out)
    EXCLUDE_KEYWORDS = [
        'hiring', 'job', 'salary', 'interview', 'resume',
        'who is hiring', 'freelancer', 'remote job',
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
        **kwargs: Any,
    ) -> list[CollectorResult]:
        """Collect market signal posts from Hacker News.

        Args:
            days_back: Number of days to look back (default: 30)
            limit_per_query: Results per search query

        Returns:
            List of opportunity signal posts
        """
        custom_params = self.collector_config.custom_params
        days_back = custom_params.get('days_back', days_back)
        min_points = custom_params.get('min_points', 3)
        min_comments = custom_params.get('min_comments', 1)

        results: list[CollectorResult] = []
        seen_ids: set[str] = set()
        cutoff_timestamp = int((datetime.now(UTC) - timedelta(days=days_back)).timestamp())

        # ── 1. Ask HN posts (highest-signal discussions) ──
        ask_hn = self._search_tagged(
            'ask_hn', cutoff_timestamp, min_points, min_comments, pages=3,
        )
        for r in ask_hn:
            oid = r.metadata.get('object_id')
            if oid and oid not in seen_ids:
                seen_ids.add(oid)
                results.append(r)

        print(f"  [HN] Ask HN: {len(results)} posts")

        # ── 2. Tell HN posts (experience sharing) ──
        tell_hn_before = len(results)
        tell_hn = self._search_tagged(
            'show_hn', cutoff_timestamp, min_points, min_comments, pages=2,
        )
        for r in tell_hn:
            oid = r.metadata.get('object_id')
            if oid and oid not in seen_ids:
                seen_ids.add(oid)
                results.append(r)

        print(f"  [HN] Show HN: {len(results) - tell_hn_before} posts")

        # ── 3. Keyword searches ──
        keyword_before = len(results)
        all_queries = list(self.SEARCH_QUERIES)

        # Add user-configured signal phrases as queries
        signal_phrases = custom_params.get('signal_phrases', [])
        for sp in signal_phrases:
            phrase = sp if isinstance(sp, str) else sp.get('phrase', '')
            if phrase and phrase not in all_queries:
                all_queries.append(phrase)

        for query in all_queries:
            self._search_and_add(
                query, cutoff_timestamp, limit_per_query,
                min_points, min_comments, seen_ids, results,
            )

        print(f"  [HN] Keyword searches: {len(results) - keyword_before} posts")

        # ── 4. High-engagement recent stories ──
        hot_before = len(results)
        self._search_hot_stories(
            cutoff_timestamp, min_points=10, min_comments=10,
            seen_ids=seen_ids, results=results,
        )
        print(f"  [HN] Hot stories: {len(results) - hot_before} posts")

        print(f"[HN] Total collected: {len(results)} posts")
        return results

    # ── Search helpers ───────────────────────────────────────────────

    def _search_tagged(
        self,
        tag: str,
        cutoff_timestamp: int,
        min_points: int,
        min_comments: int,
        pages: int = 1,
    ) -> list[CollectorResult]:
        """Search HN by tag (ask_hn, show_hn, etc.) with pagination."""
        results: list[CollectorResult] = []

        for page in range(pages):
            try:
                params = {
                    'tags': tag,
                    'numericFilters': (
                        f'created_at_i>{cutoff_timestamp},'
                        f'points>{min_points},'
                        f'num_comments>{min_comments}'
                    ),
                    'hitsPerPage': 100,
                    'page': page,
                }
                response = requests.get(
                    f"{self.API_URL}/search",
                    params=params,
                    timeout=self.collector_config.timeout,
                )
                response.raise_for_status()
                hits = response.json().get('hits', [])

                if not hits:
                    break

                for hit in hits:
                    r = self._hit_to_result(hit, tag)
                    if r:
                        results.append(r)

                time.sleep(_REQUEST_DELAY)

            except Exception as e:
                print(f"  [HN] Error fetching {tag} page {page}: {e}")
                break

        return results

    def _search_and_add(
        self,
        query: str,
        cutoff_timestamp: int,
        limit: int,
        min_points: int,
        min_comments: int,
        seen_ids: set[str],
        results: list[CollectorResult],
    ) -> None:
        """Search for a query and append unique results."""
        try:
            hits = self._search(query, cutoff_timestamp, limit)

            for hit in hits:
                object_id = hit.get('objectID')
                if not object_id or object_id in seen_ids:
                    continue

                points = hit.get('points', 0) or 0
                comments = hit.get('num_comments', 0) or 0

                if points < min_points or comments < min_comments:
                    continue

                title = hit.get('title', '') or ''
                story_text = hit.get('story_text', '') or ''
                combined = f"{title} {story_text}".lower()

                if self._should_exclude(combined):
                    continue

                seen_ids.add(object_id)

                url = hit.get('url') or f"https://news.ycombinator.com/item?id={object_id}"
                opp_score = self._calculate_opportunity_score(combined, points, comments)

                results.append(CollectorResult(
                    title=self._normalize_text(title),
                    description=self._normalize_text(story_text[:1000]) if story_text else title,
                    url=url,
                    source_type='hacker_news',
                    engagement_metrics={
                        'upvotes': points,
                        'comments': comments,
                        'opportunity_score': opp_score,
                    },
                    metadata={
                        'author': hit.get('author'),
                        'created_at': hit.get('created_at'),
                        'object_id': object_id,
                        'is_ask_hn': title.lower().startswith('ask hn'),
                        'search_query': query,
                    },
                ))

            time.sleep(_REQUEST_DELAY)

        except Exception as e:
            print(f"  [HN] Error searching '{query[:30]}': {e}")

    def _search_hot_stories(
        self,
        cutoff_timestamp: int,
        min_points: int,
        min_comments: int,
        seen_ids: set[str],
        results: list[CollectorResult],
    ) -> None:
        """Fetch highly-engaged recent stories (front-page calibre)."""
        try:
            params = {
                'tags': 'story',
                'numericFilters': (
                    f'created_at_i>{cutoff_timestamp},'
                    f'points>{min_points},'
                    f'num_comments>{min_comments}'
                ),
                'hitsPerPage': 100,
            }
            response = requests.get(
                f"{self.API_URL}/search",
                params=params,
                timeout=self.collector_config.timeout,
            )
            response.raise_for_status()

            for hit in response.json().get('hits', []):
                object_id = hit.get('objectID')
                if not object_id or object_id in seen_ids:
                    continue

                title = hit.get('title', '') or ''
                story_text = hit.get('story_text', '') or ''
                combined = f"{title} {story_text}".lower()

                if self._should_exclude(combined):
                    continue

                # Only keep stories with opportunity indicators
                indicator_count = sum(
                    1 for ind in self.OPPORTUNITY_INDICATORS if ind in combined
                )
                if indicator_count == 0:
                    continue

                seen_ids.add(object_id)
                points = hit.get('points', 0) or 0
                comments = hit.get('num_comments', 0) or 0
                url = hit.get('url') or f"https://news.ycombinator.com/item?id={object_id}"
                opp_score = self._calculate_opportunity_score(combined, points, comments)

                results.append(CollectorResult(
                    title=self._normalize_text(title),
                    description=self._normalize_text(story_text[:1000]) if story_text else title,
                    url=url,
                    source_type='hacker_news',
                    engagement_metrics={
                        'upvotes': points,
                        'comments': comments,
                        'opportunity_score': opp_score,
                    },
                    metadata={
                        'author': hit.get('author'),
                        'created_at': hit.get('created_at'),
                        'object_id': object_id,
                        'is_ask_hn': False,
                        'search_query': 'hot_stories',
                    },
                ))

        except Exception as e:
            print(f"  [HN] Error fetching hot stories: {e}")

    # ── Low-level helpers ────────────────────────────────────────────

    def _hit_to_result(self, hit: dict, search_query: str) -> CollectorResult | None:
        """Convert an Algolia hit to a CollectorResult."""
        title = hit.get('title', '') or ''
        story_text = hit.get('story_text', '') or ''
        combined = f"{title} {story_text}".lower()

        if self._should_exclude(combined):
            return None

        points = hit.get('points', 0) or 0
        comments = hit.get('num_comments', 0) or 0
        object_id = hit.get('objectID')
        url = f"https://news.ycombinator.com/item?id={object_id}"
        opp_score = self._calculate_opportunity_score(combined, points, comments)

        return CollectorResult(
            title=self._normalize_text(title),
            description=self._normalize_text(story_text[:1000]) if story_text else title,
            url=url,
            source_type='hacker_news',
            engagement_metrics={
                'upvotes': points,
                'comments': comments,
                'opportunity_score': opp_score,
            },
            metadata={
                'author': hit.get('author'),
                'created_at': hit.get('created_at'),
                'object_id': object_id,
                'is_ask_hn': title.lower().startswith('ask hn'),
                'search_query': search_query,
            },
        )

    def _search(self, query: str, cutoff_timestamp: int, limit: int) -> list[dict]:
        """Execute a single Algolia search query."""
        params = {
            'query': query,
            'numericFilters': f'created_at_i>{cutoff_timestamp}',
            'hitsPerPage': limit,
        }
        response = requests.get(
            f"{self.API_URL}/search",
            params=params,
            timeout=self.collector_config.timeout,
        )
        response.raise_for_status()
        return response.json().get('hits', [])

    def _should_exclude(self, text: str) -> bool:
        """Check if content should be excluded."""
        return any(kw in text for kw in self.EXCLUDE_KEYWORDS)

    def _calculate_opportunity_score(self, text: str, points: int, comments: int) -> int:
        """Score 0-100 based on opportunity indicators + engagement."""
        score = 0

        # Indicator matches (up to 40)
        matches = sum(1 for ind in self.OPPORTUNITY_INDICATORS if ind in text)
        score += min(40, matches * 8)

        # Upvote score (up to 30, logarithmic)
        if points > 0:
            score += min(30, int(math.log(points + 1) * 8))

        # Comment score (up to 30, logarithmic)
        if comments > 0:
            score += min(30, int(math.log(comments + 1) * 8))

        return min(100, score)
