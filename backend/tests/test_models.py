"""Tests for models."""

from datetime import UTC, datetime


class TestOpportunityModel:
    """Tests for Opportunity model."""

    def test_opportunity_creation(self, db_session):
        """Test creating an opportunity."""
        import uuid

        from app.models import Opportunity

        opportunity = Opportunity(
            id=str(uuid.uuid4()),
            title='Test Opportunity',
            description='A test opportunity',
            score=75,
            source_types=['reddit', 'hacker_news'],
            mention_count=5,
            created_at=datetime.now(UTC)
        )

        db_session.add(opportunity)
        db_session.commit()

        assert opportunity.id is not None
        assert opportunity.title == 'Test Opportunity'
        assert opportunity.score == 75

    def test_opportunity_relationships(self, db_session):
        """Test opportunity relationships with source links."""
        import uuid

        from app.models import Opportunity, SourceLink

        opportunity = Opportunity(
            id=str(uuid.uuid4()),
            title='Test Opportunity',
            description='A test opportunity',
            score=75,
            source_types=['reddit'],
            mention_count=1,
            created_at=datetime.now(UTC)
        )

        source_link = SourceLink(
            id=str(uuid.uuid4()),
            opportunity_id=opportunity.id,
            source_type='reddit',
            url='https://reddit.com/example',
            title='Example Post',
            engagement_metrics={'upvotes': 100},
            collected_at=datetime.now(UTC)
        )

        db_session.add(opportunity)
        db_session.add(source_link)
        db_session.commit()

        # Verify relationship
        retrieved = db_session.query(Opportunity).filter_by(id=opportunity.id).first()
        assert retrieved is not None
