"""Celery tasks for data collection and scanning.

Async tasks for running data collection scans, scoring opportunities,
and managing scan progress tracking.
"""

import os
import sys
import uuid
from datetime import UTC, datetime

from celery import Task

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.celery_app import celery_app
from app.db import SessionLocal
from app.models import Opportunity, Scan
from app.redis_client import redis_client
from app.services.data_collector_service import DataCollectorService
from app.services.scoring_service import ScoringService


class ScanTask(Task):
    """Base task for scan operations with progress tracking."""

    def __init__(self):
        self._db = None

    @property
    def db(self):
        """Lazy database session."""
        if self._db is None:
            self._db = SessionLocal()
        return self._db

    def after_return(self, *args, **kwargs):
        """Close database session after task completes."""
        if self._db is not None:
            self._db.close()
            self._db = None

    def update_progress(self, scan_id: str, progress: int, status: str | None = None, message: str | None = None):
        """Update scan progress in Redis and database.

        Args:
            scan_id: Scan ID
            progress: Progress percentage (0-100)
            status: Scan status
            message: Status message
        """
        # Update Redis for real-time polling
        progress_key = f"scan_progress:{scan_id}"
        redis_client.hset(
            progress_key,
            mapping={
                'progress': progress,
                'status': status or 'running',
                'message': message or '',
                'updated_at': datetime.now(UTC).isoformat()
            }
        )
        redis_client.expire(progress_key, 86400)  # Expire after 24 hours

        # Update database
        if self.db:
            scan = self.db.query(Scan).filter(Scan.id == scan_id).first()
            if scan:
                scan.progress = progress
                if status:
                    scan.status = status
                if message:
                    scan.error_message = message
                self.db.commit()


@celery_app.task(base=ScanTask, bind=True)
def run_scan(self, sources: list | None = None):
    """Run data collection scan asynchronously.

    Args:
        self: Task instance
        sources: List of sources to scan (None = all enabled)

    Returns:
        Scan results
    """
    db = self.db

    # Create scan record
    scan_id = self.request.id
    scan = Scan(
        id=scan_id,
        status='running',
        started_at=datetime.now(UTC),
        sources_processed={},
        progress=0
    )
    db.add(scan)
    db.commit()

    self.update_progress(scan_id, 5, 'running', 'Initializing data collection service')

    try:
        # Load collector config from environment
        config = {
            'reddit': {
                'api_keys': {
                    'client_id': os.getenv('REDDIT_CLIENT_ID'),
                    'client_secret': os.getenv('REDDIT_CLIENT_SECRET'),
                    'user_agent': os.getenv('REDDIT_USER_AGENT', 'OpportunityFinder/1.0')
                }
            },
            'product_hunt': {
                'api_keys': {
                    'api_token': os.getenv('PRODUCT_HUNT_TOKEN')
                }
            },
            'google_trends': {
                'api_keys': {
                    'serpapi_key': os.getenv('SERPAPI_KEY')
                }
            }
        }

        self.update_progress(scan_id, 10, 'running', 'Starting data collection')

        # Run scan
        service = DataCollectorService(db, config)
        result = service.run_scan(sources)

        # Update progress
        self.update_progress(scan_id, 90, 'running', 'Scan complete, updating database')

        # Score new opportunities
        self.update_progress(scan_id, 95, 'running', 'Scoring opportunities')

        # Get newly created opportunities
        new_opportunities = db.query(Opportunity).filter(
            Opportunity.score.is_(None)
        ).limit(100).all()

        scored_count = 0
        for opp in new_opportunities:
            try:
                scoring_service = ScoringService(db)
                scoring_service.score_opportunity(opp.id)
                scored_count += 1
            except Exception as e:
                print(f"Error scoring opportunity {opp.id}: {e}")

        # Final update
        self.update_progress(scan_id, 100, 'completed', f'Scan complete: {result["new_opportunities"]} new, {scored_count} scored')

        return {
            'scan_id': scan_id,
            'status': 'completed',
            **result,
            'scored': scored_count
        }

    except Exception as e:
        self.update_progress(scan_id, 0, 'failed', str(e))
        raise


@celery_app.task(base=ScanTask, bind=True)
def run_full_scan(self):
    """Run full scan of all enabled sources.

    Scheduled task that runs every 6 hours.

    Args:
        self: Task instance

    Returns:
        Scan results
    """
    return run_scan.apply_async(args=[None]).get()


@celery_app.task(base=ScanTask, bind=True)
def score_opportunity(self, opportunity_id: str):
    """Score a single opportunity asynchronously.

    Args:
        self: Task instance
        opportunity_id: Opportunity ID

    Returns:
        Scoring results
    """
    db = self.db
    service = ScoringService(db)

    result = service.score_opportunity(opportunity_id)

    return {
        'opportunity_id': opportunity_id,
        'score': result['score'],
        'is_validated': result['is_validated']
    }


@celery_app.task(base=ScanTask, bind=True)
def score_new_opportunities(self):
    """Score all unscored opportunities.

    Scheduled task that runs every hour.

    Args:
        self: Task instance

    Returns:
        Summary of scored opportunities
    """
    db = self.db

    # Get unscored opportunities
    unscored = db.query(Opportunity).filter(
        Opportunity.score.is_(None)
    ).limit(500).all()

    scored_count = 0
    validated_count = 0

    for opp in unscored:
        try:
            service = ScoringService(db)
            result = service.score_opportunity(opp.id)
            scored_count += 1
            if result['is_validated']:
                validated_count += 1
        except Exception as e:
            print(f"Error scoring opportunity {opp.id}: {e}")
            continue

    return {
        'scored': scored_count,
        'validated': validated_count,
        'remaining': db.query(Opportunity).filter(Opportunity.score.is_(None)).count()
    }


@celery_app.task
def get_scan_status(scan_id: str):
    """Get status of a scan from Redis.

    Args:
        scan_id: Scan ID

    Returns:
        Scan status information
    """
    progress_key = f"scan_progress:{scan_id}"
    data = redis_client.hgetall(progress_key)

    if not data:
        return {'error': 'Scan not found'}

    return {
        'scan_id': scan_id,
        'progress': int(data.get('progress', 0)),
        'status': data.get('status', 'unknown'),
        'message': data.get('message', ''),
        'updated_at': data.get('updated_at')
    }
