"""Celery application configuration for background tasks.

Configures Celery with Redis broker for asynchronous task processing
including data collection scans, email notifications, and opportunity scoring.
"""

import os
import sys

from celery import Celery
from celery.schedules import crontab

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings

# Create Celery app
celery_app = Celery(
    'opportunity_finder',
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        'app.tasks.scan_tasks',
        'app.tasks.email_tasks',
    ]
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,

    # Task routing (disabled for simpler dev setup - all tasks use default queue)
    # To enable queue separation in production, uncomment and run worker with:
    # celery -A app.celery_app worker -Q celery,scans,scoring,emails
    # task_routes={
    #     'app.tasks.scan_tasks.run_scan': {'queue': 'scans'},
    #     'app.tasks.scan_tasks.score_opportunity': {'queue': 'scoring'},
    #     'app.tasks.email_tasks.send_alert_email': {'queue': 'emails'},
    # },

    # Task execution limits
    task_soft_time_limit=1800,  # 30 minutes soft limit
    task_time_limit=3600,        # 1 hour hard limit
    task_acks_late=True,         # Acknowledge after task completes

    # Retry settings
    task_autoretry_for=(Exception,),
    task_retry_delay=60,          # Retry after 1 minute
    task_max_retries=3,

    # Result backend
    result_expires=86400,         # Results expire after 24 hours

    # Worker settings
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
)

# Celery Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    # Run full scan every 6 hours
    'run-full-scan': {
        'task': 'app.tasks.scan_tasks.run_full_scan',
        'schedule': crontab(hour='*/6'),  # Every 6 hours
        'options': {
            'expires': 3600,  # Task expires after 1 hour
        }
    },

    # Score new opportunities every hour
    'score-new-opportunities': {
        'task': 'app.tasks.scan_tasks.score_new_opportunities',
        'schedule': crontab(minute=0),  # Every hour
    },

    # Send daily digest emails at 9 AM UTC
    'send-daily-digest': {
        'task': 'app.tasks.email_tasks.send_daily_digest',
        'schedule': crontab(hour=9, minute=0),
    },
}


@celery_app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery setup.

    Args:
        self: Task instance

    Returns:
        Test result
    """
    print(f'Request: {self.request!r}')
    return 'Celery is working!'


if __name__ == '__main__':
    celery_app.start()
