"""Data collector service for orchestrating all collectors."""

import os
import sys
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.collectors import BaseCollector, get_available_collectors, get_enabled_collectors
from app.collectors.microns_collector import MicronsCollector
from app.models import Opportunity, Scan, SourceLink


class DataCollectorService:
    """Service for orchestrating data collection from all sources.

    This service manages data collection from multiple sources, handles
    deduplication, and stores results in the database.

    New sources can be added by:
    1. Creating a new collector class extending BaseCollector
    2. Using the @register_collector decorator
    3. Adding the source name to the enabled_sources config

    Example:
        # Run scan with specific sources
        service = DataCollectorService(db, config)
        result = service.run_scan(sources=['reddit', 'hacker_news'])

        # Run scan with all enabled sources
        result = service.run_scan()
    """

    def __init__(self, db: Session, config: dict[str, Any] | None = None):
        """Initialize data collector service.

        Args:
            db: Database session
            config: Configuration for collectors including:
                - enabled_sources: List of source names to enable
                - reddit: Config for Reddit collector
                - product_hunt: Config for Product Hunt collector
                - google_trends: Config for Google Trends collector
                - etc. (one key per source)
        """
        self.db = db
        self.config = config or {}

        # Get enabled sources from config or use all available
        self.enabled_sources = get_enabled_collectors(self.config)

        # Initialize collectors
        self.collectors = self._initialize_collectors()

    def _initialize_collectors(self) -> dict[str, BaseCollector]:
        """Initialize all enabled collectors.

        Returns:
            Dict of collector instances
        """
        collectors = {}

        for source_name in self.enabled_sources:
            try:
                # Get source-specific config
                source_config = self.config.get(source_name, {})
                source_config['collector_config'] = self.config.get('collector_config', {})

                # Create collector instance
                collector = BaseCollector.create_collector(source_name, source_config)

                # Only add if enabled and valid
                if collector.is_enabled():
                    is_valid, missing = collector.validate_config()
                    if is_valid:
                        collectors[source_name] = collector
                    else:
                        print(f"Collector {source_name} missing config: {missing}")
                else:
                    print(f"Collector {source_name} is disabled")

            except Exception as e:
                print(f"Error initializing {source_name} collector: {e}")
                continue

        return collectors

    def get_available_sources(self) -> list[str]:
        """Get list of all available sources.

        Returns:
            List of source names
        """
        return list(get_available_collectors().keys())

    def get_enabled_sources(self) -> list[str]:
        """Get list of currently enabled sources.

        Returns:
            List of enabled source names
        """
        return list(self.collectors.keys())

    def add_source(self, source_name: str, source_config: dict[str, Any] | None = None) -> bool:
        """Add a new source to the service.

        This allows dynamically adding new sources at runtime.

        Args:
            source_name: Name of the source to add
            source_config: Configuration for the source

        Returns:
            True if source was added successfully
        """
        try:
            source_config = source_config or {}
            source_config['collector_config'] = self.config.get('collector_config', {})

            collector = BaseCollector.create_collector(source_name, source_config)

            if collector.is_enabled():
                is_valid, missing = collector.validate_config()
                if not is_valid:
                    print(f"Cannot add {source_name}: missing config {missing}")
                    return False

                self.collectors[source_name] = collector
                print(f"Added source: {source_name}")
                return True
            else:
                print(f"Source {source_name} is disabled")
                return False

        except Exception as e:
            print(f"Error adding source {source_name}: {e}")
            return False

    def remove_source(self, source_name: str) -> bool:
        """Remove a source from the service.

        Args:
            source_name: Name of the source to remove

        Returns:
            True if source was removed
        """
        if source_name in self.collectors:
            del self.collectors[source_name]
            print(f"Removed source: {source_name}")
            return True
        return False

    def run_scan(self, sources: list[str] | None = None) -> dict[str, Any]:
        """Run a full data collection scan.

        Args:
            sources: List of sources to scan (None = all enabled)

        Returns:
            Scan results with counts
        """
        if sources is None:
            sources = list(self.collectors.keys())

        # Filter to only available collectors
        sources = [s for s in sources if s in self.collectors]

        # Create scan record
        scan = Scan(
            id=str(uuid.uuid4()),
            status='running',
            started_at=datetime.now(UTC),
            sources_processed={}
        )
        self.db.add(scan)
        self.db.commit()

        # Ensure sources_processed is not None (for type checking)
        assert scan.sources_processed is not None

        all_results = []

        try:
            # Collect from each source
            for source in sources:
                if source not in self.collectors:
                    continue

                print(f"Collecting from {source}...")
                collector = self.collectors[source]

                # Skip google_trends and microns - they're handled differently
                if source in ['google_trends', 'microns']:
                    scan.sources_processed[source] = {
                        'status': 'skipped',
                        'count': 0,
                        'message': 'Handled separately'
                    }
                    continue

                results = collector.collect()
                all_results.extend(results)

                scan.sources_processed[source] = {
                    'status': 'completed',
                    'count': len(results)
                }

                self.db.commit()

            # Calculate engagement scores using Microns collector
            microns_collector = MicronsCollector(self.config.get('microns', {}))
            opportunities_data = [
                {
                    'title': r.title,
                    'description': r.description,
                    'url': r.url,
                    'source_type': r.source_type,
                    'engagement_metrics': r.engagement_metrics
                }
                for r in all_results
            ]
            enriched_opportunities = microns_collector.collect(opportunities_data)

            # Store opportunities in database
            stored_count = 0
            for opp_data in enriched_opportunities:
                # Check for duplicates based on URL
                existing = self.db.query(SourceLink).filter(
                    SourceLink.url == opp_data['url']
                ).first()

                if existing:
                    continue

                # Create opportunity
                opportunity = Opportunity(
                    id=str(uuid.uuid4()),
                    title=opp_data['title'],
                    description=opp_data['description'],
                    score=None,  # Will be calculated by scoring service
                    source_types=[opp_data['source_type']],
                    mention_count=1,
                    created_at=datetime.now(UTC)
                )
                self.db.add(opportunity)

                # Create source link
                source_link = SourceLink(
                    id=str(uuid.uuid4()),
                    opportunity_id=opportunity.id,
                    source_type=opp_data['source_type'],
                    url=opp_data['url'],
                    title=opp_data['title'],
                    engagement_metrics={
                        'engagement_score': opp_data.get('engagement_score', 0),
                        'engagement_level': opp_data.get('engagement_level', 'LOW'),
                        **opp_data.get('engagement_metrics', {})
                    },
                    collected_at=datetime.now(UTC)
                )
                self.db.add(source_link)

                stored_count += 1

            self.db.commit()

            # Update scan
            scan.status = 'completed'
            scan.completed_at = datetime.now(UTC)
            scan.opportunities_found = stored_count
            scan.progress = 100
            self.db.commit()

            return {
                'scan_id': scan.id,
                'status': 'completed',
                'total_collected': len(all_results),
                'new_opportunities': stored_count,
                'sources': scan.sources_processed
            }

        except Exception as e:
            scan.status = 'failed'
            scan.error_message = str(e)
            scan.completed_at = datetime.now(UTC)
            self.db.commit()

            raise e

    def get_scan_status(self, scan_id: str) -> dict[str, Any]:
        """Get status of a scan.

        Args:
            scan_id: ID of the scan

        Returns:
            Scan status information
        """
        scan = self.db.query(Scan).filter(Scan.id == scan_id).first()

        if not scan:
            return {'error': 'Scan not found'}

        return {
            'scan_id': scan.id,
            'status': scan.status,
            'progress': scan.progress,
            'opportunities_found': scan.opportunities_found,
            'sources_processed': scan.sources_processed,
            'started_at': scan.started_at.isoformat() if scan.started_at else None,
            'completed_at': scan.completed_at.isoformat() if scan.completed_at else None,
            'error_message': scan.error_message
        }
