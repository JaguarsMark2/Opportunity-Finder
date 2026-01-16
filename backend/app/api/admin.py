"""Admin API endpoints for system administration."""


from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from marshmallow import ValidationError

from app.schemas.admin import (
    AnalyticsQuerySchema,
    AnalyticsResponseSchema,
    PricingTierCreateSchema,
    PricingTierResponseSchema,
    PricingTierUpdateSchema,
    ScoringConfigResponseSchema,
    ScoringThresholdsUpdateSchema,
    ScoringWeightsUpdateSchema,
    UserAdminResponseSchema,
    UserListQuerySchema,
    UserUpdateSchema,
)
from app.services import admin_service
from app.services.scoring_service import ScoringService
from app.utils.admin_helpers import admin_required

# Create blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/api/v1/admin')


# ============================================================================
# Pricing Tier Endpoints
# ============================================================================

@admin_bp.route('/pricing', methods=['GET'])
@admin_bp.route('/pricing/<string:tier_id>', methods=['GET'])
@jwt_required()
@admin_required()
def get_pricing_tiers(tier_id: str | None = None):
    """Get pricing tiers or specific tier by ID.

    Query Params:
        include_inactive: Include inactive tiers (default: false)

    Returns:
        JSON response with pricing tier(s)
    """
    try:
        include_inactive = request.args.get('include_inactive', 'false').lower() == 'true'

        if tier_id:
            # Get specific tier
            tiers, error = admin_service.list_pricing_tiers(include_inactive=True)
            if error:
                return jsonify({'error': error}), 500

            tier = next((t for t in tiers if t.id == tier_id), None)
            if not tier:
                return jsonify({'error': 'Pricing tier not found'}), 404

            schema = PricingTierResponseSchema()
            return jsonify({'data': schema.dump(tier)})

        else:
            # List all tiers
            tiers, error = admin_service.list_pricing_tiers(include_inactive=include_inactive)
            if error:
                return jsonify({'error': error}), 500

            schema = PricingTierResponseSchema(many=True)
            return jsonify({
                'data': {
                    'items': schema.dump(tiers),
                    'count': len(tiers)
                }
            })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/pricing', methods=['POST'])
@jwt_required()
@admin_required()
def create_pricing_tier():
    """Create a new pricing tier.

    Request Body:
        JSON object with pricing tier details

    Returns:
        JSON response with created tier
    """
    try:
        # Validate request
        schema = PricingTierCreateSchema()
        try:
            data = schema.load(request.get_json())
        except ValidationError as err:
            return jsonify({'error': 'Validation failed', 'details': err.messages}), 400

        # Create tier
        tier, error = admin_service.create_pricing_tier(data)
        if error:
            return jsonify({'error': error}), 400

        response_schema = PricingTierResponseSchema()
        return jsonify({'data': response_schema.dump(tier)}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/pricing/<string:tier_id>', methods=['PATCH', 'PUT'])
@jwt_required()
@admin_required()
def update_pricing_tier(tier_id: str):
    """Update a pricing tier.

    Args:
        tier_id: ID of tier to update

    Request Body:
        JSON object with fields to update

    Returns:
        JSON response with updated tier
    """
    try:
        # Validate request
        schema = PricingTierUpdateSchema()
        try:
            data = schema.load(request.get_json())
        except ValidationError as err:
            return jsonify({'error': 'Validation failed', 'details': err.messages}), 400

        if not data:
            return jsonify({'error': 'No valid fields to update'}), 400

        # Update tier
        tier, error = admin_service.update_pricing_tier(tier_id, data)
        if error:
            return jsonify({'error': error}), 400

        response_schema = PricingTierResponseSchema()
        return jsonify({'data': response_schema.dump(tier)})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/pricing/<string:tier_id>', methods=['DELETE'])
@jwt_required()
@admin_required()
def delete_pricing_tier(tier_id: str):
    """Delete a pricing tier.

    Args:
        tier_id: ID of tier to delete

    Returns:
        JSON response confirming deletion
    """
    try:
        # Check tier exists and has no users
        success, error = admin_service.delete_pricing_tier(tier_id)
        if error:
            return jsonify({'error': error}), 400

        return jsonify({'data': {'message': 'Pricing tier deleted successfully'}})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# User Management Endpoints
# ============================================================================

@admin_bp.route('/users', methods=['GET'])
@jwt_required()
@admin_required()
def list_users():
    """List users with optional filters.

    Query Params:
        search: Search by email
        role: Filter by role (user, admin)
        subscription_status: Filter by subscription status
        subscription_tier_id: Filter by tier
        is_email_verified: Filter by email verification
        limit: Results per page (default: 50)
        cursor: Pagination cursor

    Returns:
        JSON response with user list
    """
    try:
        # Validate query params
        try:
            params = UserListQuerySchema().load(request.args.to_dict())
        except ValidationError as err:
            return jsonify({'error': 'Validation failed', 'details': err.messages}), 400

        # Get users
        users, next_cursor, error = admin_service.list_users(
            search=params.get('search'),
            role=params.get('role'),
            subscription_status=params.get('subscription_status'),
            subscription_tier_id=params.get('subscription_tier_id'),
            is_email_verified=params.get('is_email_verified'),
            limit=params['limit'],
            cursor=params.get('cursor')
        )

        if error:
            return jsonify({'error': error}), 500

        schema = UserAdminResponseSchema(many=True)
        response_data = {
            'items': schema.dump(users),
            'count': len(users)
        }
        if next_cursor:
            response_data['next_cursor'] = next_cursor

        return jsonify({'data': response_data})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/users/<string:user_id>', methods=['GET'])
@jwt_required()
@admin_required()
def get_user_details(user_id: str):
    """Get detailed user information.

    Args:
        user_id: ID of user

    Returns:
        JSON response with user details
    """
    try:
        user_data, error = admin_service.get_user_details(user_id)
        if error:
            return jsonify({'error': error}), 404

        return jsonify({'data': user_data})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/users/<string:user_id>', methods=['PATCH', 'PUT'])
@jwt_required()
@admin_required()
def update_user(user_id: str):
    """Update user as admin.

    Args:
        user_id: ID of user to update

    Request Body:
        JSON object with fields to update (role, subscription_status, etc.)

    Returns:
        JSON response confirming update
    """
    try:
        # Validate request
        schema = UserUpdateSchema()
        try:
            data = schema.load(request.get_json())
        except ValidationError as err:
            return jsonify({'error': 'Validation failed', 'details': err.messages}), 400

        if not data:
            return jsonify({'error': 'No valid fields to update'}), 400

        # Update user
        success, error = admin_service.update_user(user_id, data)
        if error:
            return jsonify({'error': error}), 400

        return jsonify({'data': {'message': 'User updated successfully'}})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# Scoring Configuration Endpoints
# ============================================================================

@admin_bp.route('/scoring/config', methods=['GET'])
@jwt_required()
@admin_required()
def get_scoring_config():
    """Get current scoring configuration.

    Returns:
        JSON response with scoring weights and thresholds
    """
    try:
        scoring_service = ScoringService()

        config = {
            'weights': scoring_service.get_weights(),
            'thresholds': scoring_service.get_thresholds(),
            'last_updated': scoring_service.get_last_updated(),
            'updated_by': scoring_service.get_updated_by(),
        }

        schema = ScoringConfigResponseSchema()
        return jsonify({'data': schema.dump(config)})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/scoring/weights', methods=['PUT'])
@jwt_required()
@admin_required()
def update_scoring_weights():
    """Update scoring weights.

    Request Body:
        JSON object with weight fields (demand_weight, competition_weight, etc.)

    Returns:
        JSON response confirming update
    """
    try:
        # Validate request
        schema = ScoringWeightsUpdateSchema()
        try:
            data = schema.load(request.get_json())
        except ValidationError as err:
            return jsonify({'error': 'Validation failed', 'details': err.messages}), 400

        # Update weights
        scoring_service = ScoringService()
        user_id = get_jwt_identity()

        success, error = scoring_service.update_weights(data, user_id)
        if error:
            return jsonify({'error': error}), 400

        return jsonify({'data': {'message': 'Scoring weights updated successfully'}})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/scoring/thresholds', methods=['PUT'])
@jwt_required()
@admin_required()
def update_scoring_thresholds():
    """Update scoring thresholds.

    Request Body:
        JSON object with threshold fields

    Returns:
        JSON response confirming update
    """
    try:
        # Validate request
        schema = ScoringThresholdsUpdateSchema()
        try:
            data = schema.load(request.get_json())
        except ValidationError as err:
            return jsonify({'error': 'Validation failed', 'details': err.messages}), 400

        # Update thresholds
        scoring_service = ScoringService()
        user_id = get_jwt_identity()

        success, error = scoring_service.update_thresholds(data, user_id)
        if error:
            return jsonify({'error': error}), 400

        return jsonify({'data': {'message': 'Scoring thresholds updated successfully'}})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# Analytics Endpoints
# ============================================================================

@admin_bp.route('/analytics', methods=['GET'])
@jwt_required()
@admin_required()
def get_analytics():
    """Get analytics data for admin dashboard.

    Query Params:
        time_range: Time range for data (24h, 7d, 30d, 90d, all)

    Returns:
        JSON response with analytics data
    """
    try:
        # Validate query params
        try:
            params = AnalyticsQuerySchema().load(request.args.to_dict())
        except ValidationError as err:
            return jsonify({'error': 'Validation failed', 'details': err.messages}), 400

        # Get analytics
        analytics_data, error = admin_service.get_analytics(params['time_range'])
        if error:
            return jsonify({'error': error}), 500

        schema = AnalyticsResponseSchema()
        return jsonify({'data': schema.dump(analytics_data)})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# System Health Endpoints
# ============================================================================

@admin_bp.route('/health', methods=['GET'])
@jwt_required()
@admin_required()
def get_system_health():
    """Get system health status.

    Returns:
        JSON response with system health metrics
    """
    try:
        import time

        from app.db import get_db
        from app.redis_client import redis_client

        health_data = {
            'database': 'unknown',
            'redis': 'unknown',
            'timestamp': time.time()
        }

        # Check database
        try:
            db = next(get_db())
            db.execute('SELECT 1')
            health_data['database'] = 'healthy'
        except Exception:
            health_data['database'] = 'unhealthy'

        # Check redis
        try:
            redis_client.ping()
            health_data['redis'] = 'healthy'
        except Exception:
            health_data['redis'] = 'unhealthy'

        return jsonify({'data': health_data})

    except Exception as e:
        return jsonify({'error': str(e)}), 500
