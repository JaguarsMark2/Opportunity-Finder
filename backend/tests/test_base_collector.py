"""Tests for base_collector module."""

from app.collectors.base_collector import (
    BaseCollector,
    CollectorConfig,
    CollectorResult,
    register_collector,
)


class MockCollector(BaseCollector):
    """Mock collector for testing."""

    def __init__(self, config=None):
        super().__init__(config)
        self.source_name = 'mock'

    def _authenticate(self):
        pass

    def get_required_config_keys(self):
        return []

    def collect(self, **kwargs):
        return [
            CollectorResult(
                title='Test',
                description='Test description',
                url='https://example.com',
                source_type='mock'
            )
        ]


class TestBaseCollector:
    """Tests for BaseCollector class."""

    def test_collector_initialization(self):
        """Test collector initialization with config."""
        config = {
            'collector_config': {
                'enabled': True,
                'rate_limit': 30,
                'timeout': 60
            }
        }
        collector = MockCollector(config)
        assert collector.is_enabled() is True
        assert collector.collector_config.rate_limit == 30

    def test_collector_registry(self):
        """Test collector registry functionality."""
        # Check that mock collector is not in registry yet
        assert 'mock_test' not in BaseCollector.get_registered_collectors()

        # Register a new collector
        @register_collector('mock_test')
        class TestCollector(BaseCollector):
            def _authenticate(self):
                pass

            def get_required_config_keys(self):
                return []

            def collect(self, **kwargs):
                return []

        # Check that it's now registered
        assert 'mock_test' in BaseCollector.get_registered_collectors()

    def test_create_collector(self):
        """Test dynamic collector creation."""
        @register_collector('dynamic_test')
        class DynamicCollector(BaseCollector):
            def _authenticate(self):
                pass

            def get_required_config_keys(self):
                return []

            def collect(self, **kwargs):
                return []

        collector = BaseCollector.create_collector('dynamic_test')
        assert isinstance(collector, DynamicCollector)

    def test_collect_method(self):
        """Test collect method returns results."""
        collector = MockCollector()
        results = collector.collect()
        assert len(results) == 1
        assert results[0].title == 'Test'
        assert results[0].source_type == 'mock'


class TestCollectorResult:
    """Tests for CollectorResult dataclass."""

    def test_collector_result_creation(self):
        """Test creating a collector result."""
        result = CollectorResult(
            title='Test Title',
            description='Test Description',
            url='https://example.com',
            source_type='test',
            engagement_metrics={'views': 100}
        )

        assert result.title == 'Test Title'
        assert result.engagement_metrics['views'] == 100

    def test_collector_result_to_dict(self):
        """Test converting collector result to dictionary."""
        result = CollectorResult(
            title='Test Title',
            description='Test Description',
            url='https://example.com',
            source_type='test'
        )

        result_dict = result.to_dict()
        assert result_dict['title'] == 'Test Title'
        assert result_dict['source_type'] == 'test'
        assert 'collected_at' in result_dict


class TestCollectorConfig:
    """Tests for CollectorConfig dataclass."""

    def test_default_config(self):
        """Test default configuration values."""
        config = CollectorConfig()
        assert config.enabled is True
        assert config.rate_limit == 60
        assert config.timeout == 30

    def test_custom_config(self):
        """Test custom configuration values."""
        config = CollectorConfig(
            enabled=False,
            rate_limit=30,
            timeout=60
        )
        assert config.enabled is False
        assert config.rate_limit == 30
        assert config.timeout == 60
