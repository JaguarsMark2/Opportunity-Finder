"""Data source collectors package.

This package contains collectors for various data sources including:
- Reddit
- Indie Hackers
- Product Hunt
- Hacker News
- Google Trends
- Bluesky
- Mastodon
- Microns (social engagement aggregation)

New collectors can be added by:
1. Creating a new class extending BaseCollector
2. Using the @register_collector decorator
3. Implementing the required abstract methods

Example:
    from .base_collector import BaseCollector, register_collector

    @register_collector('my_source')
    class MySourceCollector(BaseCollector):
        def collect(self, **kwargs):
            # Implementation here
            pass
"""


from .base_collector import BaseCollector, CollectorConfig, CollectorResult, register_collector
from .bluesky_collector import BlueskyCollector
from .google_trends_collector import GoogleTrendsCollector
from .hacker_news_collector import HackerNewsCollector
from .indie_hackers_collector import IndieHackersCollector
from .mastodon_collector import MastodonCollector
from .microns_collector import MicronsCollector
from .product_hunt_collector import ProductHuntCollector

# Import all collectors to register them
from .reddit_collector import RedditCollector

__all__ = [
    'BaseCollector',
    'CollectorResult',
    'CollectorConfig',
    'register_collector',
    'RedditCollector',
    'IndieHackersCollector',
    'ProductHuntCollector',
    'HackerNewsCollector',
    'GoogleTrendsCollector',
    'BlueskyCollector',
    'MastodonCollector',
    'MicronsCollector',
]

# Get all available collectors
def get_available_collectors() -> dict:
    """Get all available collectors.

    Returns:
        Dictionary mapping source names to collector classes
    """
    return BaseCollector.get_registered_collectors()


def get_enabled_collectors(config: dict | None = None) -> list:
    """Get list of enabled collectors.

    Args:
        config: Configuration dict with enabled_sources list

    Returns:
        List of enabled collector names
    """
    if config and 'enabled_sources' in config:
        return [s for s in config['enabled_sources'] if s in get_available_collectors()]
    return list(get_available_collectors().keys())
