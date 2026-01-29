"""Scoring API endpoints."""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from app.db import SessionLocal
from app.schemas.scoring import UpdateThresholdsSchema, UpdateWeightsSchema
from app.services.scoring_service import ScoringService
from app.utils.auth_helpers import admin_required
from app.utils.rate_limit import rate_limit

scoring_bp = Blueprint('scoring', __name__, url_prefix='/api/v1/scoring')


@scoring_bp.route('/opportunity/<opportunity_id>/score', methods=['POST'])
@rate_limit(limit=30, period=60)
def score_opportunity(opportunity_id: str):
    """Score a single opportunity.

    Args:
        opportunity_id: ID of the opportunity to score

    Returns:
        Scoring results with breakdown
    """
    try:
        db = SessionLocal()
        service = ScoringService(db)

        result = service.score_opportunity(opportunity_id)
        db.close()

        return jsonify(result), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception:
        return jsonify({'error': 'Scoring failed'}), 500


@scoring_bp.route('/rescore-all', methods=['POST'])
@admin_required
@rate_limit(limit=5, period=3600)
def rescore_all():
    """Rescore all opportunities.

    Admin only - use after updating weights.
    """
    try:
        db = SessionLocal()
        service = ScoringService(db)

        result = service.rescore_all()
        db.close()

        return jsonify(result), 200

    except Exception:
        return jsonify({'error': 'Rescoring failed'}), 500


@scoring_bp.route('/config', methods=['GET'])
def get_config():
    """Get current scoring configuration.

    Returns:
        Current weights and thresholds
    """
    try:
        db = SessionLocal()
        service = ScoringService(db)

        config = service.get_scoring_config()
        db.close()

        return jsonify(config), 200

    except Exception:
        return jsonify({'error': 'Failed to get config'}), 500


@scoring_bp.route('/weights', methods=['PUT'])
@admin_required
def update_weights():
    """Update scoring weights.

    Admin only - weights must sum to 1.0.

    Request body:
        {
            "demand_frequency": 0.25,
            "revenue_proof": 0.35,
            "competition": 0.20,
            "build_complexity": 0.20
        }
    """
    try:
        schema = UpdateWeightsSchema()
        data = schema.load(request.json)

        db = SessionLocal()
        service = ScoringService(db)

        updated = service.update_weights(data)
        db.close()

        return jsonify({
            'message': 'Weights updated successfully',
            'weights': updated
        }), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception:
        return jsonify({'error': 'Failed to update weights'}), 500


@scoring_bp.route('/thresholds', methods=['PUT'])
@admin_required
def update_thresholds():
    """Update validation thresholds.

    Admin only.

    Request body:
        {
            "min_revenue_mrr": 1000,
            "min_mentions": 20,
            "min_competitors": 1
        }
    """
    try:
        schema = UpdateThresholdsSchema()
        data = schema.load(request.json)

        db = SessionLocal()
        service = ScoringService(db)

        updated = service.update_thresholds(data)
        db.close()

        return jsonify({
            'message': 'Thresholds updated successfully',
            'thresholds': updated
        }), 200

    except Exception:
        return jsonify({'error': 'Failed to update thresholds'}), 500


@scoring_bp.route('/formula', methods=['GET'])
def get_formula():
    """Get scoring formula documentation.

    Returns:
        Explanation of scoring algorithm
    """
    return jsonify({
        'formula': 'Total Score = (Demand × 0.25) + (Revenue × 0.35) + (Competition × 0.20) + (Complexity × 0.20)',
        'criteria': {
            'demand_frequency': {
                'weight': 0.25,
                'description': 'Based on mention count across sources',
                'calculation': 'Mentions / 100 (logarithmic scaling for 100+)'
            },
            'revenue_proof': {
                'weight': 0.35,
                'description': 'Based on competitor revenue data',
                'calculation': 'Revenue ratio × 50 + MRR bonus (25/40/50 for 1k/5k/10k+)'
            },
            'competition': {
                'weight': 0.20,
                'description': 'Inverted - fewer competitors is better',
                'calculation': '100 (0) / 80 (1) / 60 (2-3) / 40 (4-5) / 20 (6-10) / 10 (11+)'
            },
            'build_complexity': {
                'weight': 0.20,
                'description': 'Lower complexity is better',
                'calculation': 'Base 50 - high complexity × 15 - medium × 5 + low × 10'
            }
        },
        'validation_criteria': {
            'min_competitors': 'At least 1 existing solution',
            'min_mentions': '20+ mentions across sources',
            'min_revenue_mrr': '£1,000+ MRR from competitors',
            'b2b_focus': 'B2B target market (keyword analysis)'
        },
        'recommendations': {
            '80+ validated': 'Build immediately - All signals green, revenue proof confirmed',
            '80+ unvalidated': 'Strong candidate - validate with landing page before building',
            '60-79 validated': 'Strong candidate - validate with landing page before building',
            '60-79 unvalidated': 'Promising but needs validation - test with landing page first',
            '40-59': 'High risk - need unique angle, proceed with caution',
            '20-39': 'Reject - insufficient validation, do not build',
            '0-19': 'Reject - minimal data, do not build'
        }
    }), 200
