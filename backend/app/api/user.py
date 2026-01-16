"""User API endpoints.

Provides user profile and statistics endpoints.
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import desc, func

from app.db import SessionLocal
from app.models import Opportunity, User, UserOpportunity
from app.utils.rate_limit import rate_limit

user_bp = Blueprint('user', __name__, url_prefix='/api/v1/user')


@user_bp.route('/profile', methods=['GET'])
@jwt_required()
@rate_limit(limit=30, period=60)
def get_profile():
    """Get current user profile.

    Returns:
        User profile data
    """
    try:
        db = SessionLocal()
        user_id = get_jwt_identity()

        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            db.close()
            return jsonify({'error': 'User not found'}), 404

        response_data = {
            'id': user.id,
            'email': user.email,
            'role': user.role.value if hasattr(user.role, 'value') else user.role,
            'subscription_status': user.subscription_status.value if hasattr(user.subscription_status, 'value') else user.subscription_status,
            'subscription_tier_id': user.subscription_tier_id,
            'email_verified': user.email_verified,
            'created_at': user.created_at.isoformat() if user.created_at else None
        }

        db.close()

        return jsonify(response_data), 200

    except Exception as e:
        db.close()
        return jsonify({'error': str(e)}), 500


@user_bp.route('/profile', methods=['PATCH'])
@jwt_required()
@rate_limit(limit=10, period=60)
def update_profile():
    """Update current user profile.

    Currently minimal - can be extended with more fields.

    Request Body:
        { }
        (Add fields as needed)

    Returns:
        Updated profile data
    """
    try:
        db = SessionLocal()
        user_id = get_jwt_identity()

        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            db.close()
            return jsonify({'error': 'User not found'}), 404

        # Update fields (add as needed)
        # Currently no updatable fields - extend as required

        db.commit()
        db.refresh(user)

        response_data = {
            'id': user.id,
            'email': user.email,
            'role': user.role.value if hasattr(user.role, 'value') else user.role,
            'subscription_status': user.subscription_status.value if hasattr(user.subscription_status, 'value') else user.subscription_status,
            'subscription_tier_id': user.subscription_tier_id,
            'email_verified': user.email_verified,
            'created_at': user.created_at.isoformat() if user.created_at else None
        }

        db.close()

        return jsonify(response_data), 200

    except Exception as e:
        db.close()
        return jsonify({'error': str(e)}), 500


@user_bp.route('/stats', methods=['GET'])
@jwt_required()
@rate_limit(limit=10, period=60)
def get_user_stats():
    """Get current user's opportunity statistics.

    Returns:
        User's saved opportunities, tracking stats
    """
    try:
        db = SessionLocal()
        user_id = get_jwt_identity()

        # Count saved opportunities
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

        # Total tracked
        total_tracked = db.query(func.count(UserOpportunity.opportunity_id)).filter(
            UserOpportunity.user_id == user_id
        ).scalar() or 0

        db.close()

        return jsonify({
            'saved_count': saved_count,
            'status_counts': status_counts,
            'total_tracked': total_tracked
        }), 200

    except Exception as e:
        db.close()
        return jsonify({'error': str(e)}), 500


@user_bp.route('/saved', methods=['GET'])
@jwt_required()
@rate_limit(limit=20, period=60)
def get_saved_opportunities():
    """Get user's saved opportunities.

    Query Parameters:
        - limit: Results per page (default 20)
        - cursor: Pagination cursor

    Returns:
        Paginated list of saved opportunities
    """
    try:
        db = SessionLocal()
        user_id = get_jwt_identity()

        limit = int(request.args.get('limit', 20))
        cursor = request.args.get('cursor')

        # Build query
        query = db.query(Opportunity).join(
            UserOpportunity,
            and_(
                UserOpportunity.opportunity_id == Opportunity.id,
                UserOpportunity.user_id == user_id,
                UserOpportunity.is_saved is True
            )
        )

        total_count = query.count()

        # Apply cursor pagination
        if cursor:
            from app.api.opportunities import _decode_cursor
            cursor_data = _decode_cursor(cursor)
            if cursor_data:
                query = query.filter(
                    and_(
                        Opportunity.created_at <= datetime.fromisoformat(cursor_data['created_at']),
                        Opportunity.id != cursor_data['id']
                    )
                )

        # Order and limit
        query = query.order_by(desc(Opportunity.created_at), Opportunity.id).limit(limit)

        # Execute
        opportunities = query.all()

        # Build response
        results = []
        next_cursor = None

        for opp in opportunities:
            from app.api.opportunities import _encode_cursor
            results.append({
                'id': opp.id,
                'title': opp.title,
                'description': opp.description,
                'score': opp.score,
                'is_validated': opp.is_validated,
                'created_at': opp.created_at.isoformat() if opp.created_at else None
            })
            next_cursor = _encode_cursor(opp.id, opp.created_at)

        has_more = len(results) == limit and total_count > len(results)

        db.close()

        return jsonify({
            'data': results,
            'meta': {
                'next_cursor': next_cursor if has_more else None,
                'has_more': has_more,
                'total_count': total_count
            }
        }), 200

    except Exception as e:
        db.close()
        return jsonify({'error': str(e)}), 500


# Add necessary imports
from datetime import datetime

from sqlalchemy import and_
