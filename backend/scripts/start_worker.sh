#!/bin/bash
# Celery Worker Startup Script
# Starts worker with all required queues for Opportunity Finder

set -euo pipefail

# Activate virtual environment
source .venv/bin/activate

# Set PYTHONPATH for imports
export PYTHONPATH=.

# Start Celery worker with all required queues
# Queues: scans, scoring, emails, and default celery queue
celery -A app.celery_app worker --loglevel=info -Q scans,scoring,emails,celery
