"""Pytest configuration and fixtures."""

import sys
from pathlib import Path

import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def db_session():
    """Create a test database session using transaction rollback for isolation."""
    from app import models  # noqa: F401 - Import to register models
    from app.db import Base, SessionLocal, engine

    # Create all tables
    Base.metadata.create_all(bind=engine)

    # Connect and begin a transaction
    connection = engine.connect()
    transaction = connection.begin()

    # Bind the session to this connection
    session = SessionLocal(bind=connection)

    yield session

    # Rollback all changes
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def sample_opportunity_data():
    """Sample opportunity data for testing."""
    return {
        'title': 'AI-Powered SaaS Boilerplate',
        'description': 'A complete starter template for building AI-powered SaaS applications',
        'url': 'https://example.com/ai-saas',
        'source_type': 'product_hunt',
        'engagement_metrics': {
            'votes': 450,
            'comments': 85
        },
        'metadata': {
            'topics': ['AI', 'SaaS', 'Developer Tools']
        }
    }


@pytest.fixture
def sample_collector_result(sample_opportunity_data):
    """Sample CollectorResult for testing."""
    from app.collectors.base_collector import CollectorResult
    return CollectorResult(**sample_opportunity_data)
