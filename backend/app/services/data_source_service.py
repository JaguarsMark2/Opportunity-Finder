"""Data source management service.

Handles configuration, enabling/disabling, and testing of data sources.
"""

import os
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.collectors import get_available_collectors
from app.models import SystemSettings


# Default data source configurations
DEFAULT_DATA_SOURCES = {
    'reddit': {
        'name': 'Reddit',
        'description': 'Reddit posts from startup/business subreddits',
        'is_enabled': False,
        'requires_auth': True,
        'config_fields': ['client_id', 'client_secret', 'user_agent'],
        'config': {
            'client_id': '',
            'client_secret': '',
            'user_agent': 'OpportunityFinder/1.0'
        },
        'docs_url': 'https://www.reddit.com/prefs/apps'
    },
    'hacker_news': {
        'name': 'Hacker News',
        'description': 'HN posts via Algolia API (no auth required)',
        'is_enabled': True,
        'requires_auth': False,
        'config_fields': [],
        'config': {},
        'docs_url': 'https://hn.algolia.com/api'
    },
    'indie_hackers': {
        'name': 'Indie Hackers',
        'description': 'Product listings from Indie Hackers (web scraping)',
        'is_enabled': True,
        'requires_auth': False,
        'config_fields': [],
        'config': {},
        'docs_url': 'https://www.indiehackers.com/products'
    },
    'product_hunt': {
        'name': 'Product Hunt',
        'description': 'New product launches from Product Hunt',
        'is_enabled': False,
        'requires_auth': True,
        'config_fields': ['api_token'],
        'config': {
            'api_token': ''
        },
        'docs_url': 'https://api.producthunt.com/v2/docs'
    },
    'google_trends': {
        'name': 'Google Trends',
        'description': 'Keyword trends via SerpAPI',
        'is_enabled': False,
        'requires_auth': True,
        'config_fields': ['serpapi_key'],
        'config': {
            'serpapi_key': ''
        },
        'docs_url': 'https://serpapi.com/'
    },
    'bluesky': {
        'name': 'Bluesky',
        'description': 'Posts from Bluesky social network',
        'is_enabled': False,
        'requires_auth': False,
        'config_fields': ['identifier', 'password'],
        'config': {
            'identifier': '',
            'password': ''
        },
        'docs_url': 'https://bsky.app/'
    },
    'mastodon': {
        'name': 'Mastodon',
        'description': 'Posts from Mastodon instances (federated)',
        'is_enabled': False,
        'requires_auth': False,
        'config_fields': ['access_token', 'instance'],
        'config': {
            'access_token': '',
            'instance': 'https://mastodon.social'
        },
        'docs_url': 'https://docs.joinmastodon.org/api/'
    }
}


class DataSourceService:
    """Service for managing data source configurations."""

    SETTINGS_KEY = 'data_sources'

    def __init__(self, db: Session):
        """Initialize data source service.

        Args:
            db: Database session
        """
        self.db = db

    def get_all_sources(self) -> dict[str, dict]:
        """Get all data sources with their configurations.

        Returns:
            Dict of source_id -> source config
        """
        # Get stored config
        settings = self.db.query(SystemSettings).filter(
            SystemSettings.key == self.SETTINGS_KEY
        ).first()

        if settings and settings.value:
            sources = settings.value
        else:
            sources = DEFAULT_DATA_SOURCES.copy()

        # Merge with defaults for any new sources
        for source_id, default_config in DEFAULT_DATA_SOURCES.items():
            if source_id not in sources:
                sources[source_id] = default_config

        # Check if collectors exist
        available = get_available_collectors()
        for source_id in sources:
            sources[source_id]['collector_available'] = source_id in available

        return sources

    def get_source(self, source_id: str) -> dict | None:
        """Get a single data source configuration.

        Args:
            source_id: Source identifier

        Returns:
            Source config or None
        """
        sources = self.get_all_sources()
        return sources.get(source_id)

    def update_source_config(self, source_id: str, config: dict) -> tuple[dict | None, str | None]:
        """Update configuration for a data source.

        Args:
            source_id: Source identifier
            config: New configuration values

        Returns:
            Tuple of (updated_source, error_message)
        """
        sources = self.get_all_sources()

        if source_id not in sources:
            return None, f"Unknown source: {source_id}"

        # Update config fields
        source = sources[source_id]
        if 'config' not in source:
            source['config'] = {}

        for key, value in config.items():
            if key in source.get('config_fields', []) or key in source.get('config', {}):
                source['config'][key] = value

        # Save to database
        self._save_sources(sources)

        # Also update environment variables for immediate use
        self._update_env_vars(source_id, source['config'])

        return source, None

    def enable_source(self, source_id: str) -> tuple[bool, str | None]:
        """Enable a data source.

        Args:
            source_id: Source identifier

        Returns:
            Tuple of (success, error_message)
        """
        sources = self.get_all_sources()

        if source_id not in sources:
            return False, f"Unknown source: {source_id}"

        sources[source_id]['is_enabled'] = True
        self._save_sources(sources)

        return True, None

    def disable_source(self, source_id: str) -> tuple[bool, str | None]:
        """Disable a data source.

        Args:
            source_id: Source identifier

        Returns:
            Tuple of (success, error_message)
        """
        sources = self.get_all_sources()

        if source_id not in sources:
            return False, f"Unknown source: {source_id}"

        sources[source_id]['is_enabled'] = False
        self._save_sources(sources)

        return True, None

    def test_source(self, source_id: str) -> dict:
        """Test connectivity for a data source.

        Args:
            source_id: Source identifier

        Returns:
            Test result with success status and message
        """
        sources = self.get_all_sources()

        if source_id not in sources:
            return {
                'success': False,
                'message': f"Unknown source: {source_id}",
                'items_found': 0
            }

        source = sources[source_id]

        # Check if source requires auth and config is missing or has placeholder values
        if source.get('requires_auth', False):
            # Placeholder values that indicate unconfigured API keys
            PLACEHOLDER_PATTERNS = ['your_', 'dev_', 'test_', 'example', 'xxx', 'changeme', 'placeholder']

            def is_valid_config_value(v):
                if not v or not isinstance(v, str) or not v.strip():
                    return False
                v_lower = v.lower()
                return not any(pattern in v_lower for pattern in PLACEHOLDER_PATTERNS)

            config_values = source.get('config', {})
            has_valid_config = any(is_valid_config_value(v) for v in config_values.values())

            # Also check environment variables
            env_has_valid_config = False
            env_mapping = {
                'reddit': ['REDDIT_CLIENT_ID', 'REDDIT_CLIENT_SECRET'],
                'product_hunt': ['PRODUCT_HUNT_TOKEN'],
                'google_trends': ['SERPAPI_KEY'],
            }
            if source_id in env_mapping:
                env_values = [os.getenv(key, '') for key in env_mapping[source_id]]
                env_has_valid_config = all(is_valid_config_value(v) for v in env_values)

            if not has_valid_config and not env_has_valid_config:
                return {
                    'success': False,
                    'message': f"API keys required. Please configure {source_id} with real credentials.",
                    'items_found': 0
                }

        # Get collector class
        available_collectors = get_available_collectors()
        if source_id not in available_collectors:
            return {
                'success': False,
                'message': f"Collector not implemented for: {source_id}",
                'items_found': 0
            }

        collector_class = available_collectors[source_id]

        try:
            # Build config for collector
            config = self._build_collector_config(source_id, source)

            # Initialize collector
            collector = collector_class(config)

            # Try to collect a small sample
            if hasattr(collector, 'collect'):
                # Limit to small sample for testing
                results = collector.collect(limit=10, limit_per_query=5, days_back=14)

                if isinstance(results, list):
                    if len(results) > 0:
                        return {
                            'success': True,
                            'message': f"Connected and found {len(results)} items.",
                            'items_found': len(results),
                            'sample': [
                                {'title': r.title[:50], 'url': r.url}
                                for r in results[:3]
                            ]
                        }
                    else:
                        # Connected but found nothing - might be an issue
                        return {
                            'success': False,
                            'message': "Connected but found 0 items. API may be rate-limited or search returned no results.",
                            'items_found': 0,
                            'sample': []
                        }
                elif isinstance(results, dict):
                    # Google Trends returns dict
                    if len(results) > 0:
                        return {
                            'success': True,
                            'message': f"Connected and retrieved {len(results)} keywords.",
                            'items_found': len(results),
                            'sample': list(results.keys())[:3]
                        }
                    else:
                        return {
                            'success': False,
                            'message': "Connected but retrieved no data.",
                            'items_found': 0
                        }
                else:
                    return {
                        'success': False,
                        'message': "Unexpected response format from collector.",
                        'items_found': 0
                    }
            else:
                return {
                    'success': False,
                    'message': "Collector missing collect method",
                    'items_found': 0
                }

        except ValueError as e:
            # Usually missing API key
            return {
                'success': False,
                'message': f"Configuration error: {str(e)}",
                'items_found': 0
            }
        except Exception as e:
            return {
                'success': False,
                'message': f"Connection failed: {str(e)}",
                'items_found': 0
            }

    def get_enabled_sources(self) -> list[str]:
        """Get list of enabled source IDs.

        Returns:
            List of enabled source IDs
        """
        sources = self.get_all_sources()
        return [sid for sid, cfg in sources.items() if cfg.get('is_enabled', False)]

    def _save_sources(self, sources: dict) -> None:
        """Save sources configuration to database.

        Args:
            sources: Sources configuration dict
        """
        # Remove transient fields before saving
        save_sources = {}
        for source_id, source in sources.items():
            save_sources[source_id] = {
                k: v for k, v in source.items()
                if k != 'collector_available'
            }

        settings = self.db.query(SystemSettings).filter(
            SystemSettings.key == self.SETTINGS_KEY
        ).first()

        if settings:
            settings.value = save_sources
            settings.updated_at = datetime.now(UTC)
        else:
            settings = SystemSettings(
                key=self.SETTINGS_KEY,
                value=save_sources
            )
            self.db.add(settings)

        self.db.commit()

    def _build_collector_config(self, source_id: str, source: dict) -> dict:
        """Build collector configuration from source settings.

        Args:
            source_id: Source identifier
            source: Source configuration

        Returns:
            Collector config dict
        """
        config = {
            'api_keys': source.get('config', {}),
            'custom_params': {
                'limit': 5,  # Small limit for testing
                'days_back': 7
            }
        }

        # Also check environment variables
        env_mapping = {
            'reddit': {
                'client_id': 'REDDIT_CLIENT_ID',
                'client_secret': 'REDDIT_CLIENT_SECRET',
                'user_agent': 'REDDIT_USER_AGENT'
            },
            'product_hunt': {
                'api_token': 'PRODUCT_HUNT_TOKEN'
            },
            'google_trends': {
                'serpapi_key': 'SERPAPI_KEY'
            },
            'bluesky': {
                'identifier': 'BLUESKY_IDENTIFIER',
                'password': 'BLUESKY_PASSWORD'
            },
            'mastodon': {
                'access_token': 'MASTODON_ACCESS_TOKEN',
                'instance': 'MASTODON_INSTANCE'
            }
        }

        if source_id in env_mapping:
            for config_key, env_key in env_mapping[source_id].items():
                env_value = os.getenv(env_key)
                if env_value and not config['api_keys'].get(config_key):
                    config['api_keys'][config_key] = env_value

        return config

    def _update_env_vars(self, source_id: str, config: dict) -> None:
        """Update environment variables from config.

        Note: This only affects the current process.
        For persistence, update the .env file.

        Args:
            source_id: Source identifier
            config: Configuration values
        """
        env_mapping = {
            'reddit': {
                'client_id': 'REDDIT_CLIENT_ID',
                'client_secret': 'REDDIT_CLIENT_SECRET',
                'user_agent': 'REDDIT_USER_AGENT'
            },
            'product_hunt': {
                'api_token': 'PRODUCT_HUNT_TOKEN'
            },
            'google_trends': {
                'serpapi_key': 'SERPAPI_KEY'
            },
            'bluesky': {
                'identifier': 'BLUESKY_IDENTIFIER',
                'password': 'BLUESKY_PASSWORD'
            },
            'mastodon': {
                'access_token': 'MASTODON_ACCESS_TOKEN',
                'instance': 'MASTODON_INSTANCE'
            }
        }

        if source_id in env_mapping:
            for config_key, env_key in env_mapping[source_id].items():
                if config.get(config_key):
                    os.environ[env_key] = config[config_key]
