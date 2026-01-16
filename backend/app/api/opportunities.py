"""Opportunities API endpoints.

Provides CRUD operations for opportunities with filtering, search,
sorting, and pagination support.
"""

import base64
import json
from datetime import UTC, datetime, timedelta

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import and_, desc, func, or_

from app.db import SessionLocal
from app.models import Competitor, Opportunity, SourceLink, UserOpportunity
from app.schemas.opportunity import (
    OpportunityListSchema,
    OpportunityUpdateSchema,
)
from app.utils.rate_limit import rate_limit

opportunities_bp = Blueprint('opportunities', __name__, url_prefix='/api/v1/opportunities')


def _encode_cursor(opportunity_id: str, created_at: datetime) -> str:
    """Encode cursor for pagination.

    Args:
        opportunity_id: Opportunity ID
        created_at: Created timestamp

    Returns:
        Base64-encoded cursor string
    """
    data = {'id': opportunity_id, 'created_at': created_at.isoformat()}
    return base64.b64encode(json.dumps(data).encode()).decode()


def _decode_cursor(cursor: str) -> dict | None:
    """Decode cursor for pagination.

    Args:
        cursor: Base64-encoded cursor string

    Returns:
        Dict with id and created_at, or None if invalid
    """
    try:
        data = json.loads(base64.b64decode(cursor).decode())
        return data  # type: ignore[no-any-return]
    except Exception:
        return None


@opportunities_bp.route('', methods=['GET'])
@jwt_required()
@rate_limit(limit=60, period=60)
def list_opportunities():
    """List opportunities with filtering, search, sorting, and pagination.

    Query Parameters:
        - min_score: Minimum score (0-100)
        - max_score: Maximum score (0-100)
        - is_validated: Filter by validation status
        - sort: Sort order (score, -score, revenue, -revenue, mentions, -mentions, created_at, -created_at)
        - search: Full-text search query
        - time_range: Filter by time (day, week, month, year, all)
        - limit: Results per page (1-100, default 20)
        - cursor: Pagination cursor

    Returns:
        Paginated list of opportunities
    """
    try:
        db = SessionLocal()
        user_id = get_jwt_identity()

        # Parse query parameters
        schema = OpportunityListSchema()
        params = schema.load(request.args.to_dict())

        min_score = params.get('min_score')
        max_score = params.get('max_score')
        is_validated = params.get('is_validated')
        sort = params.get('sort', '-score')
        search = params.get('search')
        time_range = params.get('time_range', 'all')
        limit = params.get('limit', 20)
        cursor = params.get('cursor')

        # Build base query with user-specific data
        query = db.query(
            Opportunity,
            UserOpportunity.status.label('user_status'),
            UserOpportunity.notes.label('user_notes'),
            UserOpportunity.is_saved
        ).outerjoin(
            UserOpportunity,
            and_(
                UserOpportunity.opportunity_id == Opportunity.id,
                UserOpportunity.user_id == user_id
            )
        )

        # Apply filters
        if min_score is not None:
            query = query.filter(Opportunity.score >= min_score)

        if max_score is not None:
            query = query.filter(Opportunity.score <= max_score)

        if is_validated is not None:
            query = query.filter(Opportunity.is_validated == is_validated)

        # Time range filter
        if time_range != 'all':
            now = datetime.now(UTC)
            time_map = {
                'day': timedelta(days=1),
                'week': timedelta(weeks=1),
                'month': timedelta(days=30),
                'year': timedelta(days=365)
            }
            cutoff = now - time_map.get(time_range, timedelta(weeks=1))
            query = query.filter(Opportunity.created_at >= cutoff)

        # Full-text search
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Opportunity.title.ilike(search_term),
                    Opportunity.description.ilike(search_term),
                    Opportunity.problem.ilike(search_term),
                    Opportunity.solution.ilike(search_term),
                    Opportunity.target_market.ilike(search_term)
                )
            )

        # Apply cursor pagination
        if cursor:
            cursor_data = _decode_cursor(cursor)
            if cursor_data:
                query = query.filter(
                    and_(
                        Opportunity.created_at <= datetime.fromisoformat(cursor_data['created_at']),
                        Opportunity.id != cursor_data['id']
                    )
                )

        # Apply sorting
        sort_field = sort.lstrip('-')
        sort_desc = sort.startswith('-')

        if sort_field == 'score':
            order_by = desc(Opportunity.score) if sort_desc else Opportunity.score
        elif sort_field == 'revenue':
            order_by = desc(Opportunity.competitor_count) if sort_desc else Opportunity.competitor_count
        elif sort_field == 'mentions':
            order_by = desc(Opportunity.mention_count) if sort_desc else Opportunity.mention_count
        elif sort_field == 'created_at':
            order_by = desc(Opportunity.created_at) if sort_desc else Opportunity.created_at
        else:
            order_by = desc(Opportunity.score)

        query = query.order_by(order_by, Opportunity.id)

        # Get total count before pagination
        total_count = query.count()

        # Apply limit
        query = query.limit(limit)

        # Execute query
        results = query.all()

        # Build response
        opportunities = []
        next_cursor = None

        for row in results:
            opp, user_status, user_notes, is_saved = row

            opp_data = {
                'id': opp.id,
                'title': opp.title,
                'description': opp.description,
                'problem': opp.problem,
                'solution': opp.solution,
                'target_market': opp.target_market,
                'pricing_model': opp.pricing_model,
                'score': opp.score,
                'problem_score': opp.problem_score,
                'feasibility_score': opp.feasibility_score,
                'why_now_score': opp.why_now_score,
                'is_validated': opp.is_validated,
                'revenue_proof': opp.revenue_proof,
                'competitor_count': opp.competitor_count,
                'mention_count': opp.mention_count,
                'keyword_volume': opp.keyword_volume,
                'growth_rate': opp.growth_rate,
                'competition_level': opp.competition_level,
                'source_types': opp.source_types or [],
                'cluster_id': opp.cluster_id,
                'created_at': opp.created_at.isoformat() if opp.created_at else None,
                'updated_at': opp.updated_at.isoformat() if opp.updated_at else None,
                'user_status': user_status,
                'user_notes': user_notes,
                'is_saved': is_saved or False
            }

            opportunities.append(opp_data)

            # Set next cursor from last item
            next_cursor = _encode_cursor(opp.id, opp.created_at)

        db.close()

        has_more = len(opportunities) == limit and total_count > len(opportunities)

        return jsonify({
            'data': opportunities,
            'meta': {
                'next_cursor': next_cursor if has_more else None,
                'has_more': has_more,
                'total_count': total_count
            }
        }), 200

    except Exception as e:
        db.close()
        return jsonify({'error': str(e)}), 500


@opportunities_bp.route('/<opportunity_id>', methods=['GET'])
@jwt_required()
@rate_limit(limit=120, period=60)
def get_opportunity(opportunity_id: str):
    """Get single opportunity detail with competitors and sources.

    Args:
        opportunity_id: Opportunity ID

    Returns:
        Opportunity detail with competitors and source links
    """
    try:
        db = SessionLocal()
        user_id = get_jwt_identity()

        # Get opportunity with user data
        opp = db.query(Opportunity).filter(Opportunity.id == opportunity_id).first()

        if not opp:
            db.close()
            return jsonify({'error': 'Opportunity not found'}), 404

        # Get user-specific data
        user_opp = db.query(UserOpportunity).filter(
            and_(
                UserOpportunity.opportunity_id == opportunity_id,
                UserOpportunity.user_id == user_id
            )
        ).first()

        # Get competitors
        competitors = db.query(Competitor).filter(
            Competitor.opportunity_id == opportunity_id
        ).all()

        # Get source links
        source_links = db.query(SourceLink).filter(
            SourceLink.opportunity_id == opportunity_id
        ).all()

        # Build response
        response_data = {
            'id': opp.id,
            'title': opp.title,
            'description': opp.description,
            'problem': opp.problem,
            'solution': opp.solution,
            'target_market': opp.target_market,
            'pricing_model': opp.pricing_model,
            'score': opp.score,
            'problem_score': opp.problem_score,
            'feasibility_score': opp.feasibility_score,
            'why_now_score': opp.why_now_score,
            'is_validated': opp.is_validated,
            'revenue_proof': opp.revenue_proof,
            'competitor_count': opp.competitor_count,
            'mention_count': opp.mention_count,
            'keyword_volume': opp.keyword_volume,
            'growth_rate': opp.growth_rate,
            'competition_level': opp.competition_level,
            'source_types': opp.source_types or [],
            'cluster_id': opp.cluster_id,
            'created_at': opp.created_at.isoformat() if opp.created_at else None,
            'updated_at': opp.updated_at.isoformat() if opp.updated_at else None,
            'user_status': user_opp.status if user_opp else None,
            'user_notes': user_opp.notes if user_opp else None,
            'is_saved': user_opp.is_saved if user_opp else False,
            'competitors': [
                {
                    'id': c.id,
                    'name': c.name,
                    'url': c.url,
                    'description': c.description,
                    'revenue_est': c.revenue_est,
                    'pricing': c.pricing,
                    'features': c.features
                }
                for c in competitors
            ],
            'source_links': [
                {
                    'id': s.id,
                    'source_type': s.source_type,
                    'url': s.url,
                    'title': s.title,
                    'engagement_metrics': s.engagement_metrics,
                    'collected_at': s.collected_at.isoformat() if s.collected_at else None
                }
                for s in source_links
            ]
        }

        db.close()

        return jsonify(response_data), 200

    except Exception as e:
        db.close()
        return jsonify({'error': str(e)}), 500


@opportunities_bp.route('/<opportunity_id>', methods=['PATCH'])
@jwt_required()
@rate_limit(limit=30, period=60)
def update_opportunity(opportunity_id: str):
    """Update user-specific opportunity data (status, notes, saved).

    Args:
        opportunity_id: Opportunity ID

    Request Body:
        {
            "status": "new" | "investigating" | "interested" | "dismissed",
            "notes": "User notes about this opportunity",
            "is_saved": true/false
        }

    Returns:
        Updated opportunity data
    """
    try:
        schema = OpportunityUpdateSchema()
        data = schema.load(request.json)

        db = SessionLocal()
        user_id = get_jwt_identity()

        # Get opportunity
        opp = db.query(Opportunity).filter(Opportunity.id == opportunity_id).first()
        if not opp:
            db.close()
            return jsonify({'error': 'Opportunity not found'}), 404

        # Get or create user opportunity record
        user_opp = db.query(UserOpportunity).filter(
            and_(
                UserOpportunity.opportunity_id == opportunity_id,
                UserOpportunity.user_id == user_id
            )
        ).first()

        if not user_opp:
            user_opp = UserOpportunity(
                id=str(uuid.uuid4()),
                opportunity_id=opportunity_id,
                user_id=user_id
            )
            db.add(user_opp)

        # Update fields
        if 'status' in data:
            user_opp.status = data['status']

        if 'notes' in data:
            user_opp.notes = data['notes']

        if 'is_saved' in data:
            user_opp.is_saved = data['is_saved']

        db.commit()
        db.refresh(user_opp)

        response_data = {
            'id': opp.id,
            'user_status': user_opp.status,
            'user_notes': user_opp.notes,
            'is_saved': user_opp.is_saved
        }

        db.close()

        return jsonify(response_data), 200

    except Exception as e:
        db.close()
        return jsonify({'error': str(e)}), 500


@opportunities_bp.route('/stats', methods=['GET'])
@jwt_required()
@rate_limit(limit=10, period=60)
def get_stats():
    """Get opportunity statistics summary.

    Returns:
        Statistics including total count, validation count,
        average score, score distribution, top sources
    """
    try:
        db = SessionLocal()

        # Total opportunities
        total = db.query(func.count(Opportunity.id)).scalar() or 0

        # Validated count
        validated = db.query(func.count(Opportunity.id)).filter(
            Opportunity.is_validated is True
        ).scalar() or 0

        # Average score
        avg_score = db.query(func.avg(Opportunity.score)).filter(
            Opportunity.score.isnot(None)
        ).scalar() or 0

        # Score distribution
        score_ranges = {
            '0-20': 0, '21-40': 0, '41-60': 0, '61-80': 0, '81-100': 0
        }

        for opp in db.query(Opportunity.score).filter(Opportunity.score.isnot(None)):
            score = opp[0]
            if score <= 20:
                score_ranges['0-20'] += 1
            elif score <= 40:
                score_ranges['21-40'] += 1
            elif score <= 60:
                score_ranges['41-60'] += 1
            elif score <= 80:
                score_ranges['61-80'] += 1
            else:
                score_ranges['81-100'] += 1

        # Top sources
        source_counts = db.query(
            func.unnest(Opportunity.source_types).label('source'),
            func.count().label('count')
        ).filter(Opportunity.source_types.isnot(None)).group_by('source').order_by(
            desc('count')
        ).limit(5).all()

        top_sources = [
            {'source': row[0], 'count': row[1]}
            for row in source_counts
        ]

        # Recent opportunities (last 7 days)
        week_ago = datetime.now(UTC) - timedelta(days=7)
        recent = db.query(func.count(Opportunity.id)).filter(
            Opportunity.created_at >= week_ago
        ).scalar() or 0

        db.close()

        return jsonify({
            'total_opportunities': total,
            'validated_count': validated,
            'avg_score': round(avg_score, 2),
            'score_distribution': score_ranges,
            'top_sources': top_sources,
            'recent_count': recent
        }), 200

    except Exception as e:
        db.close()
        return jsonify({'error': str(e)}), 500


# Import uuid at module level
import uuid
