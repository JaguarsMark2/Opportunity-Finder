"""Scan API endpoints.

Provides endpoints for triggering manual scans and checking scan progress.
"""

from datetime import UTC

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import func

from app.db import SessionLocal
from app.models import Scan, User
from app.tasks.scan_tasks import get_scan_status, run_scan
from app.utils.auth_helpers import admin_required
from app.utils.rate_limit import rate_limit

scan_bp = Blueprint('scan', __name__, url_prefix='/api/v1/scan')


@scan_bp.route('', methods=['POST'])
@jwt_required()
@rate_limit(limit=3, period=3600)
def trigger_scan():
    """Trigger a new data collection scan.

    Admin only - rate limited to 3 per hour.

    Request Body (optional):
        {
            "sources": ["reddit", "hacker_news"]  # Optional: specific sources
        }

    Returns:
        Scan ID for tracking progress
    """
    try:
        # Check if user is admin
        db = SessionLocal()
        user_id = get_jwt_identity()
        user = db.query(User).filter(User.id == user_id).first()

        if not user or user.role.value != 'admin':
            db.close()
            return jsonify({'error': 'Admin access required'}), 403

        # Get sources from request
        data = request.json or {}
        sources = data.get('sources')

        db.close()

        # Trigger async scan
        task = run_scan.apply_async(args=[sources])

        return jsonify({
            'message': 'Scan started',
            'scan_id': task.id,
            'status': 'running'
        }), 202

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@scan_bp.route('/<scan_id>', methods=['GET'])
@jwt_required()
@rate_limit(limit=30, period=60)
def get_scan_progress(scan_id: str):
    """Get scan progress by ID.

    Args:
        scan_id: Celery task ID

    Returns:
        Current scan status and progress
    """
    try:
        # Try to get from Redis first (real-time progress)
        status = get_scan_status(scan_id)

        if 'error' in status:
            # Fall back to database
            db = SessionLocal()
            scan = db.query(Scan).filter(Scan.id == scan_id).first()

            if not scan:
                db.close()
                return jsonify({'error': 'Scan not found'}), 404

            status = {
                'scan_id': scan.id,
                'status': scan.status,
                'progress': scan.progress,
                'opportunities_found': scan.opportunities_found,
                'sources_processed': scan.sources_processed,
                'error_message': scan.error_message,
                'started_at': scan.started_at.isoformat() if scan.started_at else None,
                'completed_at': scan.completed_at.isoformat() if scan.completed_at else None
            }

            db.close()

        return jsonify(status), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@scan_bp.route('/recent', methods=['GET'])
@jwt_required()
@admin_required
@rate_limit(limit=10, period=60)
def get_recent_scans():
    """Get recent scan history.

    Admin only.

    Query Parameters:
        - limit: Number of scans to return (default 10)

    Returns:
        List of recent scans
    """
    try:
        db = SessionLocal()

        limit = int(request.args.get('limit', 10))

        scans = db.query(Scan).order_by(
            Scan.started_at.desc()
        ).limit(limit).all()

        results = []
        for scan in scans:
            results.append({
                'id': scan.id,
                'status': scan.status,
                'progress': scan.progress,
                'opportunities_found': scan.opportunities_found,
                'sources_processed': scan.sources_processed,
                'error_message': scan.error_message,
                'started_at': scan.started_at.isoformat() if scan.started_at else None,
                'completed_at': scan.completed_at.isoformat() if scan.completed_at else None
            })

        db.close()

        return jsonify({'scans': results}), 200

    except Exception as e:
        db.close()
        return jsonify({'error': str(e)}), 500


@scan_bp.route('/stats', methods=['GET'])
@jwt_required()
@admin_required
@rate_limit(limit=10, period=60)
def get_scan_stats():
    """Get scan statistics.

    Admin only.

    Returns:
        Summary statistics
    """
    try:
        db = SessionLocal()

        # Total scans
        total = db.query(func.count(Scan.id)).scalar() or 0

        # Recent scans (last 24 hours)
        from datetime import datetime, timedelta
        day_ago = datetime.now(UTC) - timedelta(days=1)
        recent = db.query(func.count(Scan.id)).filter(
            Scan.started_at >= day_ago
        ).scalar() or 0

        # Status breakdown
        status_counts = {}
        for status in ['running', 'completed', 'failed']:
            count = db.query(func.count(Scan.id)).filter(
                Scan.status == status
            ).scalar() or 0
            status_counts[status] = count

        # Total opportunities found
        total_opportunities = db.query(Scan).filter(
            Scan.status == 'completed'
        ).with_entities(
            func.sum(Scan.opportunities_found)
        ).scalar() or 0

        db.close()

        return jsonify({
            'total_scans': total,
            'recent_scans': recent,
            'status_breakdown': status_counts,
            'total_opportunities_found': total_opportunities
        }), 200

    except Exception as e:
        db.close()
        return jsonify({'error': str(e)}), 500
