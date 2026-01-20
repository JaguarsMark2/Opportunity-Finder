"""Dashboard API endpoint.

Provides a unified dashboard endpoint that aggregates user profile,
user statistics, recent opportunities, and global stats.
"""

from datetime import UTC, datetime, timedelta

from flask import Blueprint, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import and_, desc, func

from app.db import SessionLocal
from app.models import Opportunity, User, UserOpportunity
from app.utils.rate_limit import rate_limit

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api/v1/dashboard')


@dashboard_bp.route('', methods=['GET'])
@jwt_required()
@rate_limit(limit=30, period=60)
def get_dashboard():
    """Get dashboard data for authenticated user.

    Returns aggregated data including:
    - User profile information
    - User opportunity statistics
    - Recent opportunities (first page)
    - Global opportunity statistics

    Returns:
        Dashboard data object
    """
    db = None
    try:
        db = SessionLocal()
        user_id = get_jwt_identity()

        # Get user profile
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            db.close()
            return jsonify({'error': 'User not found'}), 404

        # User profile data
        profile = {
            'id': user.id,
            'email': user.email,
            'role': user.role.value if hasattr(user.role, 'value') else user.role,
            'email_verified': user.email_verified,
            'subscription_status': user.subscription_status.value if hasattr(user.subscription_status, 'value') else user.subscription_status,
            'subscription_tier_id': user.subscription_tier_id,
        }

        # User statistics
        saved_count = db.query(func.count(UserOpportunity.opportunity_id)).filter(
            and_(
                UserOpportunity.user_id == user_id,
                UserOpportunity.is_saved is True
            )
        ).scalar() or 0

        # Count by status
        status_counts = {}
        for status in ['new', 'investigating', 'interested', 'dismissed']:
            count = db.query(func.count(UserOpportunity.opportunity_id)).filter(
                and_(
                    UserOpportunity.user_id == user_id,
                    UserOpportunity.status == status
                )
            ).scalar() or 0
            status_counts[status] = count

        total_tracked = db.query(func.count(UserOpportunity.opportunity_id)).filter(
            UserOpportunity.user_id == user_id
        ).scalar() or 0

        user_stats = {
            'saved_count': saved_count,
            'status_counts': status_counts,
            'total_tracked': total_tracked
        }

        # Recent opportunities (first page - top 10)
        week_ago = datetime.now(UTC) - timedelta(days=7)
        recent_opps = db.query(
            Opportunity,
            UserOpportunity.status.label('user_status'),
            UserOpportunity.saved.label('is_saved')
        ).outerjoin(
            UserOpportunity,
            and_(
                UserOpportunity.opportunity_id == Opportunity.id,
                UserOpportunity.user_id == user_id
            )
        ).filter(
            Opportunity.created_at >= week_ago
        ).order_by(
            desc(Opportunity.created_at)
        ).limit(10).all()

        recent_opportunities = []
        for opp, user_status, is_saved in recent_opps:
            recent_opportunities.append({
                'id': opp.id,
                'title': opp.title,
                'description': opp.description[:200] if opp.description else None,
                'score': opp.score,
                'is_validated': opp.is_validated,
                'source_types': opp.source_types,
                'revenue_proof': opp.revenue_proof,
                'competition_level': opp.competition_level,
                'created_at': opp.created_at.isoformat() if opp.created_at else None,
                'user_status': user_status,
                'is_saved': is_saved is True
            })

        # Global statistics
        total_opportunities = db.query(func.count(Opportunity.id)).scalar() or 0
        validated_count = db.query(func.count(Opportunity.id)).filter(
            Opportunity.is_validated is True
        ).scalar() or 0
        avg_score = db.query(func.avg(Opportunity.score)).filter(
            Opportunity.score.isnot(None)
        ).scalar() or 0

        # Recent global opportunities count (last 7 days)
        recent_global_count = db.query(func.count(Opportunity.id)).filter(
            Opportunity.created_at >= week_ago
        ).scalar() or 0

        global_stats = {
            'total_opportunities': total_opportunities,
            'validated_count': validated_count,
            'avg_score': round(avg_score, 2),
            'recent_count': recent_global_count
        }

        db.close()

        return jsonify({
            'profile': profile,
            'user_stats': user_stats,
            'recent_opportunities': recent_opportunities,
            'global_stats': global_stats
        }), 200

    except Exception as e:
        if db is not None:
            db.close()
        return jsonify({'error': str(e)}), 500
