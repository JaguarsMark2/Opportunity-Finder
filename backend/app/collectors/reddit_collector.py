"""Reddit data collector using PRAW."""

import os
import sys
from datetime import UTC, datetime, timedelta
from typing import Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .base_collector import BaseCollector, CollectorResult, register_collector


@register_collector('reddit')
class RedditCollector(BaseCollector):
    """Collector for Reddit data using PRAW.

    Monitors subreddits for pain points and opportunity ideas.

    Configuration:
        api_keys: {
            'client_id': Reddit app client ID
            'client_secret': Reddit app client secret
            'user_agent': User agent string
        }
        custom_params: {
            'subreddits': List of subreddits to monitor (optional)
            'limit': Posts per subreddit (default: 100)
            'time_filter': Time filter (day, week, month, year, all)
        }
    """

    # Default subreddits to monitor
    DEFAULT_SUBREDDITS = [
        'entrepreneur',
        'startups',
        'sideproject',
        'SaaSProject',
        'microsaas',
        'IndieHackers',
        'Entrepreneur',
        'smallbusiness',
        'freelance',
        'coding'
    ]

    # Keywords indicating pain points or opportunities
    PAIN_POINT_KEYWORDS = [
        'i wish', 'i hate', 'i need', 'looking for', 'anyone know',
        'how do i', 'is there a way to', 'why doesnt', 'it would be great if',
        'frustrated with', 'tired of', 'annoying that', 'problem with',
        'struggling with', 'help me find', 'recommendation for', 'suggestion for'
    ]

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize Reddit collector.

        Args:
            config: Configuration dictionary with API keys and custom params
        """
        super().__init__(config)
        self._authenticate()

    def _authenticate(self) -> None:
        """Authenticate with Reddit API."""
        required_keys = self.get_required_config_keys()
        api_keys = self.config.get('api_keys', {})

        for key in required_keys:
            if key not in api_keys:
                raise ValueError(f"Missing required API key: {key}")

        import praw
        self.reddit = praw.Reddit(
            client_id=api_keys['client_id'],
            client_secret=api_keys['client_secret'],
            user_agent=api_keys['user_agent'],
            ratelimit_seconds=300  # Be conservative with rate limits
        )

    def get_required_config_keys(self) -> list[str]:
        """Get required configuration keys.

        Returns:
            List of required API key names
        """
        return ['client_id', 'client_secret', 'user_agent']

    def collect(  # type: ignore[override]
        self,
        subreddit_names: list[str] | None = None,
        time_filter: str = 'week',
        limit: int = 100,
        **kwargs: Any
    ) -> list[CollectorResult]:
        """Collect posts from subreddits.

        Args:
            subreddit_names: List of subreddits to monitor (defaults to DEFAULT_SUBREDDITS)
            time_filter: Time period ('day', 'week', 'month', 'year', 'all')
            limit: Maximum posts per subreddit

        Returns:
            List of collector results
        """
        # Get custom params if available
        custom_params = self.collector_config.custom_params
        if subreddit_names is None:
            subreddit_names = custom_params.get('subreddits', self.DEFAULT_SUBREDDITS)
        if custom_params.get('limit'):
            limit = custom_params['limit']
        if custom_params.get('time_filter'):
            time_filter = custom_params['time_filter']

        results = []
        time_map = {
            'day': timedelta(days=1),
            'week': timedelta(weeks=1),
            'month': timedelta(days=30),
            'year': timedelta(days=365),
            'all': timedelta(days=3650)
        }
        time_delta = time_map.get(time_filter, timedelta(weeks=1))
        cutoff_time = datetime.now(UTC) - time_delta

        for subreddit_name in subreddit_names:
            try:
                subreddit = self.reddit.subreddit(subreddit_name)

                # Get new posts
                for post in subreddit.new(limit=limit):
                    post_time = datetime.fromtimestamp(post.created_utc, tz=UTC)

                    # Skip if too old
                    if post_time < cutoff_time:
                        continue

                    # Check if post contains pain point keywords
                    title_lower = post.title.lower()
                    self_lower = post.selftext.lower() if post.selftext else ''
                    combined = title_lower + ' ' + self_lower

                    is_pain_point = any(keyword in combined for keyword in self.PAIN_POINT_KEYWORDS)

                    # Collect all posts from target subreddits, or pain point posts
                    if subreddit_name in self.DEFAULT_SUBREDDITS[:5] or is_pain_point:
                        result = CollectorResult(
                            title=self._normalize_text(post.title),
                            description=self._normalize_text(post.selftext[:500] if post.selftext else ''),
                            url=f"https://reddit.com{post.permalink}",
                            source_type='reddit',
                            engagement_metrics={
                                'upvotes': post.ups,
                                'comments': post.num_comments,
                                'upvote_ratio': post.upvote_ratio,
                                'subreddit': subreddit_name
                            },
                            metadata={
                                'author': str(post.author) if post.author else '[deleted]',
                                'created_utc': post.created_utc,
                                'is_pain_point': is_pain_point
                            }
                        )
                        results.append(result)

            except Exception as e:
                print(f"Error collecting from r/{subreddit_name}: {e}")
                continue

        return results
