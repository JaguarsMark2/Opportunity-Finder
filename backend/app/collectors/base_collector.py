"""Base collector class and common data structures for data source collectors."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass
class CollectorResult:
    """Normalized result from any collector.

    Attributes:
        title: Title or headline of the opportunity
        description: Description or content
        url: URL to the source
        source_type: Type of source (reddit, product_hunt, etc.)
        engagement_metrics: Dictionary of engagement metrics
        metadata: Additional metadata about the source
        collected_at: When the data was collected
    """

    title: str
    description: str
    url: str
    source_type: str
    engagement_metrics: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    collected_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation of the result
        """
        return {
            'title': self.title,
            'description': self.description,
            'url': self.url,
            'source_type': self.source_type,
            'engagement_metrics': self.engagement_metrics,
            'metadata': self.metadata,
            'collected_at': self.collected_at.isoformat()
        }


@dataclass
class CollectorConfig:
    """Configuration for a collector.

    Attributes:
        enabled: Whether the collector is enabled
        rate_limit: Rate limit in requests per minute
        timeout: Request timeout in seconds
        retry_count: Number of retries on failure
        api_keys: API keys required for the collector
        custom_params: Custom parameters for the collector
    """

    enabled: bool = True
    rate_limit: int = 60
    timeout: int = 30
    retry_count: int = 3
    api_keys: dict[str, str] = field(default_factory=dict)
    custom_params: dict[str, Any] = field(default_factory=dict)


class BaseCollector(ABC):
    """Abstract base class for all data source collectors.

    This class defines the common interface that all collectors must implement.
    New data sources can be added by extending this class.

    Example:
        class MyCustomCollector(BaseCollector):
            def __init__(self, config: Dict[str, Any] = None):
                super().__init__(config)
                self.source_name = 'my_custom_source'

            def _authenticate(self) -> None:
                # Implement authentication
                pass

            def collect(self, **kwargs) -> List[CollectorResult]:
                # Implement collection logic
                pass
    """

    # Class-level registry for automatic discovery
    _registry: dict[str, type] = {}

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize collector with configuration.

        Args:
            config: Collector-specific configuration including API keys, rate limits, etc.
        """
        self.config: dict[str, Any] = config or {}
        self.collector_config = CollectorConfig(**self.config.get('collector_config', {}))
        # Automatically set source_name from class name
        self.source_name = self.__class__.__name__.replace('Collector', '').lower()

    @classmethod
    def register(cls, source_name: str, collector_class: type) -> None:
        """Register a collector in the registry.

        This allows for dynamic collector discovery and loading.

        Args:
            source_name: Name of the source (e.g., 'reddit', 'product_hunt')
            collector_class: The collector class to register
        """
        cls._registry[source_name] = collector_class

    @classmethod
    def get_registered_collectors(cls) -> dict[str, type]:
        """Get all registered collectors.

        Returns:
            Dictionary mapping source names to collector classes
        """
        return cls._registry.copy()

    @classmethod
    def create_collector(cls, source_name: str, config: dict[str, Any] | None = None) -> 'BaseCollector':
        """Create a collector instance by source name.

        This allows for dynamic instantiation of collectors.

        Args:
            source_name: Name of the source
            config: Configuration for the collector

        Returns:
            Collector instance

        Raises:
            ValueError: If source is not registered
        """
        if source_name not in cls._registry:
            raise ValueError(f"Unknown source: {source_name}. Available: {list(cls._registry.keys())}")

        collector_class = cls._registry[source_name]
        return collector_class(config)  # type: ignore[no-any-return]

    @abstractmethod
    def collect(self, **kwargs) -> list[CollectorResult]:
        """Collect data from the source.

        Args:
            **kwargs: Source-specific parameters (e.g., limit, time_range, keywords)

        Returns:
            List of normalized collector results

        Raises:
            ConnectionError: If collection fails
        """
        pass

    @abstractmethod
    def _authenticate(self) -> None:
        """Authenticate with the source API.

        This method should establish any necessary connections or API clients.

        Raises:
            ConnectionError: If authentication fails
        """
        pass

    def is_enabled(self) -> bool:
        """Check if this collector is enabled.

        Returns:
            True if collector is enabled and has required config
        """
        return self.collector_config.enabled

    def validate_config(self) -> tuple[bool, list[str]]:
        """Validate collector configuration.

        Returns:
            Tuple of (is_valid, list_of_missing_keys)
        """
        required_keys = self.get_required_config_keys()
        missing_keys = []

        for key in required_keys:
            if key not in self.config.get('api_keys', {}) and key not in self.config:
                missing_keys.append(key)

        return (len(missing_keys) == 0, missing_keys)

    @abstractmethod
    def get_required_config_keys(self) -> list[str]:
        """Get list of required configuration keys.

        Returns:
            List of required config key names
        """
        pass

    def _normalize_text(self, text: str) -> str:
        """Normalize text by removing extra whitespace.

        Args:
            text: Raw text

        Returns:
            Normalized text
        """
        if not text:
            return ''
        return ' '.join(text.split())

    def _extract_keywords(self, text: str) -> list[str]:
        """Extract keywords from text (basic implementation).

        Args:
            text: Input text

        Returns:
            List of keywords
        """
        if not text:
            return []

        # Simple keyword extraction - can be enhanced with NLP
        words = text.lower().split()
        # Filter out common words
        stopwords = {
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'could', 'should', 'may', 'might', 'must', 'shall', 'can',
            'need', 'for', 'of', 'at', 'by', 'from', 'in', 'on', 'to', 'with',
            'and', 'or', 'but', 'not', 'this', 'that', 'these', 'those'
        }
        return [w for w in words if len(w) > 3 and w not in stopwords]

    def get_source_info(self) -> dict[str, Any]:
        """Get information about this collector.

        Returns:
            Dictionary with collector metadata
        """
        return {
            'source_name': self.source_name,
            'enabled': self.is_enabled(),
            'config_valid': self.validate_config()[0],
            'rate_limit': self.collector_config.rate_limit,
            'timeout': self.collector_config.timeout
        }


def register_collector(source_name: str):
    """Decorator to register a collector class.

    Usage:
        @register_collector('reddit')
        class RedditCollector(BaseCollector):
            ...

    Args:
        source_name: Name of the source to register
    """
    def decorator(collector_class: type) -> type:
        BaseCollector.register(source_name, collector_class)
        return collector_class
    return decorator
