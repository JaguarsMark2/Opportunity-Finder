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
from app.utils.admin_helpers import DEV_ADMIN_ID, DEV_MODE, admin_required

# Create blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/api/v1/admin')


# ============================================================================
# Pricing Tier Endpoints
# ============================================================================

@admin_bp.route('/pricing', methods=['GET'])
@admin_bp.route('/pricing/<string:tier_id>', methods=['GET'])
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
@admin_required()
def get_scoring_config():
    """Get current scoring configuration.

    Returns:
        JSON response with scoring weights and thresholds
    """
    try:
        from app.db import SessionLocal

        db = SessionLocal()
        try:
            scoring_service = ScoringService(db)

            config = {
                'weights': scoring_service.weights,
                'thresholds': scoring_service.thresholds,
                'enabled_criteria': scoring_service.enabled_criteria,
            }

            schema = ScoringConfigResponseSchema()
            return jsonify({'data': schema.dump(config)})

        finally:
            db.close()

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/scoring/weights', methods=['PUT'])
@admin_required()
def update_scoring_weights():
    """Update scoring weights.

    Request Body:
        JSON object with weight fields (demand_weight, competition_weight, etc.)

    Returns:
        JSON response confirming update
    """
    try:
        from app.db import SessionLocal

        # Validate request
        schema = ScoringWeightsUpdateSchema()
        try:
            data = schema.load(request.get_json())
        except ValidationError as err:
            return jsonify({'error': 'Validation failed', 'details': err.messages}), 400

        db = SessionLocal()
        try:
            # Update weights
            scoring_service = ScoringService(db)
            scoring_service.update_weights(data)

            return jsonify({'data': {'message': 'Scoring weights updated successfully'}})
        finally:
            db.close()

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/scoring/thresholds', methods=['PUT'])
@admin_required()
def update_scoring_thresholds():
    """Update scoring thresholds.

    Request Body:
        JSON object with threshold fields

    Returns:
        JSON response confirming update
    """
    try:
        from app.db import SessionLocal

        # Validate request
        schema = ScoringThresholdsUpdateSchema()
        try:
            data = schema.load(request.get_json())
        except ValidationError as err:
            return jsonify({'error': 'Validation failed', 'details': err.messages}), 400

        db = SessionLocal()
        try:
            # Update thresholds
            scoring_service = ScoringService(db)
            scoring_service.update_thresholds(data)

            return jsonify({'data': {'message': 'Scoring thresholds updated successfully'}})
        finally:
            db.close()

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/scoring/criteria', methods=['PUT'])
@admin_required()
def update_scoring_criteria():
    """Update enabled scoring criteria.

    Request Body:
        JSON object with criteria boolean fields (upvotes, mentions, etc.)

    Returns:
        JSON response confirming update
    """
    try:
        from app.db import SessionLocal

        # Get criteria from request
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No criteria provided'}), 400

        # Update enabled criteria
        db = SessionLocal()
        try:
            scoring_service = ScoringService(db)
            scoring_service.update_enabled_criteria(data)

            return jsonify({'data': {'message': 'Scoring criteria updated successfully'}})

        finally:
            db.close()

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# Analytics Endpoints
# ============================================================================

@admin_bp.route('/analytics', methods=['GET'])
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
            from sqlalchemy import text

            db = next(get_db())
            db.execute(text('SELECT 1'))
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


# ============================================================================
# Data Purge Endpoints
# ============================================================================

@admin_bp.route('/purge-opportunities', methods=['POST'])
@admin_required()
def purge_opportunities():
    """Delete all opportunities, source links, pending posts, and scans.

    Wipes the pipeline clean so the next scan starts fresh.

    Returns:
        JSON response with counts of deleted records
    """
    try:
        from app.db import get_db
        from app.models import Opportunity, PendingPost, Scan, SourceLink

        db = next(get_db())

        source_links_count = db.query(SourceLink).count()
        db.query(SourceLink).delete()

        opportunities_count = db.query(Opportunity).count()
        db.query(Opportunity).delete()

        pending_count = db.query(PendingPost).count()
        db.query(PendingPost).delete()

        scans_count = db.query(Scan).count()
        db.query(Scan).delete()

        db.commit()

        return jsonify({
            'data': {
                'deleted': {
                    'opportunities': opportunities_count,
                    'source_links': source_links_count,
                    'pending_posts': pending_count,
                    'scans': scans_count,
                },
                'message': 'All pipeline data purged successfully.'
            }
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# Data Source Management Endpoints
# ============================================================================

@admin_bp.route('/data-sources', methods=['GET'])
@admin_required()
def list_data_sources():
    """Get all data sources with their configurations.

    Returns:
        JSON response with all data sources
    """
    try:
        from app.db import SessionLocal
        from app.services.data_source_service import DataSourceService

        db = SessionLocal()
        try:
            service = DataSourceService(db)
            sources = service.get_all_sources()

            # Format for frontend
            result = []
            for source_id, config in sources.items():
                result.append({
                    'id': source_id,
                    'name': config.get('name', source_id),
                    'description': config.get('description', ''),
                    'is_enabled': config.get('is_enabled', False),
                    'requires_auth': config.get('requires_auth', False),
                    'config_fields': config.get('config_fields', []),
                    'config': {k: ('••••••••' if 'secret' in k.lower() or 'password' in k.lower() or 'token' in k.lower() or 'key' in k.lower() else v) for k, v in config.get('config', {}).items()},
                    'has_config': bool(any(v for v in config.get('config', {}).values())),
                    'collector_available': config.get('collector_available', False),
                    'docs_url': config.get('docs_url', '')
                })

            return jsonify({'data': result})

        finally:
            db.close()

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/data-sources/<source_id>', methods=['GET'])
@admin_required()
def get_data_source(source_id: str):
    """Get a single data source configuration.

    Args:
        source_id: Source identifier

    Returns:
        JSON response with source configuration
    """
    try:
        from app.db import SessionLocal
        from app.services.data_source_service import DataSourceService

        db = SessionLocal()
        try:
            service = DataSourceService(db)
            source = service.get_source(source_id)

            if not source:
                return jsonify({'error': f'Unknown source: {source_id}'}), 404

            return jsonify({'data': {
                'id': source_id,
                **source
            }})

        finally:
            db.close()

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/data-sources/<source_id>/config', methods=['PUT'])
@admin_required()
def update_data_source_config(source_id: str):
    """Update configuration for a data source.

    Args:
        source_id: Source identifier

    Request Body:
        JSON object with configuration values

    Returns:
        JSON response confirming update
    """
    try:
        from app.db import SessionLocal
        from app.services.data_source_service import DataSourceService

        data = request.get_json()
        if not data:
            return jsonify({'error': 'No configuration provided'}), 400

        db = SessionLocal()
        try:
            service = DataSourceService(db)
            updated, error = service.update_source_config(source_id, data)

            if error:
                return jsonify({'error': error}), 400

            return jsonify({
                'data': {
                    'message': f'Configuration updated for {source_id}',
                    'source_id': source_id
                }
            })

        finally:
            db.close()

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/data-sources/<source_id>/enable', methods=['POST'])
@admin_required()
def enable_data_source(source_id: str):
    """Enable a data source.

    Args:
        source_id: Source identifier

    Returns:
        JSON response confirming enablement
    """
    try:
        from app.db import SessionLocal
        from app.services.data_source_service import DataSourceService

        db = SessionLocal()
        try:
            service = DataSourceService(db)
            success, error = service.enable_source(source_id)

            if error:
                return jsonify({'error': error}), 400

            return jsonify({
                'data': {
                    'message': f'{source_id} enabled',
                    'source_id': source_id,
                    'is_enabled': True
                }
            })

        finally:
            db.close()

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/data-sources/<source_id>/disable', methods=['POST'])
@admin_required()
def disable_data_source(source_id: str):
    """Disable a data source.

    Args:
        source_id: Source identifier

    Returns:
        JSON response confirming disablement
    """
    try:
        from app.db import SessionLocal
        from app.services.data_source_service import DataSourceService

        db = SessionLocal()
        try:
            service = DataSourceService(db)
            success, error = service.disable_source(source_id)

            if error:
                return jsonify({'error': error}), 400

            return jsonify({
                'data': {
                    'message': f'{source_id} disabled',
                    'source_id': source_id,
                    'is_enabled': False
                }
            })

        finally:
            db.close()

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/data-sources/<source_id>/test', methods=['POST'])
@admin_required()
def test_data_source(source_id: str):
    """Test connectivity for a data source.

    Args:
        source_id: Source identifier

    Returns:
        JSON response with test results
    """
    try:
        from app.db import SessionLocal
        from app.services.data_source_service import DataSourceService

        db = SessionLocal()
        try:
            service = DataSourceService(db)
            result = service.test_source(source_id)

            return jsonify({'data': result})

        finally:
            db.close()

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# AI Configuration Endpoints
# ============================================================================

@admin_bp.route('/ai/config', methods=['GET'])
@admin_required()
def get_ai_config():
    """Get AI service configuration.

    Returns:
        JSON response with AI config (API key masked)
    """
    try:
        from app.db import SessionLocal
        from app.services.ai_service import AIService

        db = SessionLocal()
        try:
            service = AIService(db)
            config = service.get_config()
            return jsonify({'data': config})
        finally:
            db.close()

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/ai/config', methods=['PUT'])
@admin_required()
def update_ai_config():
    """Update AI service configuration.

    Request Body:
        provider: AI provider (glm, openai, anthropic)
        api_key: API key for the provider
        model: Model to use
        enabled: Whether AI analysis is enabled

    Returns:
        JSON response confirming update
    """
    try:
        from app.db import SessionLocal
        from app.services.ai_service import AIService

        data = request.get_json()
        if not data:
            return jsonify({'error': 'No configuration provided'}), 400

        db = SessionLocal()
        try:
            service = AIService(db)

            # Get current config and update with new values
            current = service._load_config()
            if 'provider' in data:
                current['provider'] = data['provider']
            if 'api_key' in data and data['api_key']:  # Only update if provided
                provider = current.get('provider', 'glm')
                current.setdefault('api_keys', {})[provider] = data['api_key']
            if 'model' in data:
                current['model'] = data['model']
            if 'api_url' in data:
                current['api_url'] = data['api_url']
            if 'enabled' in data:
                current['enabled'] = data['enabled']

            service.save_config(current)
            return jsonify({'data': {'message': 'AI configuration updated successfully'}})

        finally:
            db.close()

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/ai/test', methods=['POST'])
@admin_required()
def test_ai_connection():
    """Test AI API connection.

    Returns:
        JSON response with test results
    """
    try:
        from app.db import SessionLocal
        from app.services.ai_service import AIService

        db = SessionLocal()
        try:
            service = AIService(db)
            result = service.test_connection()
            return jsonify({'data': result})
        finally:
            db.close()

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# Filtering Rules Endpoints
# ============================================================================

@admin_bp.route('/filter-rules', methods=['GET'])
@admin_required()
def get_filter_rules():
    """Get all filtering rules.

    Returns:
        JSON response with filter rules
    """
    try:
        import copy
        from datetime import UTC, datetime

        from app.db import SessionLocal
        from app.models import SystemSettings

        db = SessionLocal()
        try:
            settings = db.query(SystemSettings).filter(
                SystemSettings.key == 'filter_rules'
            ).first()

            default_rules = {
                'exclude_keywords': [
                    'hiring', 'job', 'salary', 'interview', 'resume',
                    'who is hiring', 'freelancer', 'remote job',
                ],
                'signal_phrases': [
                    {'phrase': 'i wish', 'category': 'feature_request'},
                    {'phrase': 'looking for a tool', 'category': 'feature_request'},
                    {'phrase': 'does anyone know', 'category': 'feature_request'},
                    {'phrase': 'no way to', 'category': 'integration_gap'},
                    {'phrase': 'ended up building', 'category': 'workaround'},
                    {'phrase': 'wrote a script', 'category': 'workaround'},
                    {'phrase': 'someone should build', 'category': 'idea'},
                    {'phrase': "why doesn't", 'category': 'idea'},
                    {'phrase': "i'd pay for", 'category': 'willingness_to_pay'},
                    {'phrase': 'shut up and take my money', 'category': 'willingness_to_pay'},
                    {'phrase': 'missing feature', 'category': 'feature_request'},
                    {'phrase': 'integrate with', 'category': 'integration_gap'},
                    {'phrase': 'no integration', 'category': 'integration_gap'},
                    {'phrase': 'manually every', 'category': 'pain_point'},
                    {'phrase': 'hours every week', 'category': 'pain_point'},
                    {'phrase': 'any alternative', 'category': 'feature_request'},
                    {'phrase': 'is there a', 'category': 'feature_request'},
                    {'phrase': 'switched from', 'category': 'pain_point'},
                    {'phrase': 'frustrated with', 'category': 'pain_point'},
                    {'phrase': 'hate that', 'category': 'pain_point'},
                ],
                'require_keywords': [],
                'min_upvotes': 5,
                'min_comments': 2,
                'exclude_categories': ['political', 'hardware', 'career'],
                'custom_rules': [],
            }

            if settings and settings.value:
                # Deep copy to avoid mutating the SQLAlchemy-tracked object
                rules = copy.deepcopy(settings.value)
                # Seed signal_phrases with defaults if missing (first-time migration)
                if 'signal_phrases' not in rules:
                    rules['signal_phrases'] = default_rules['signal_phrases']
                    # Persist the migration so add/remove work correctly
                    settings.value = rules
                    settings.updated_at = datetime.now(UTC)
                    db.commit()
            else:
                rules = default_rules

            return jsonify({'data': rules})

        finally:
            db.close()

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/filter-rules', methods=['PUT'])
@admin_required()
def update_filter_rules():
    """Update filtering rules.

    Request Body:
        exclude_keywords: List of keywords to exclude
        require_keywords: List of keywords to require
        min_upvotes: Minimum upvotes required
        min_comments: Minimum comments required
        exclude_categories: Categories to exclude
        custom_rules: User-defined rules

    Returns:
        JSON response confirming update
    """
    try:
        from app.db import SessionLocal
        from app.models import SystemSettings
        from datetime import UTC, datetime

        data = request.get_json()
        if not data:
            return jsonify({'error': 'No rules provided'}), 400

        db = SessionLocal()
        try:
            settings = db.query(SystemSettings).filter(
                SystemSettings.key == 'filter_rules'
            ).first()

            if settings:
                settings.value = data
                settings.updated_at = datetime.now(UTC)
            else:
                settings = SystemSettings(
                    key='filter_rules',
                    value=data
                )
                db.add(settings)

            db.commit()
            return jsonify({'data': {'message': 'Filter rules updated successfully'}})

        finally:
            db.close()

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/filter-rules/add-exclusion', methods=['POST'])
@admin_required()
def add_exclusion_rule():
    """Quick add an exclusion keyword or pattern.

    Request Body:
        keyword: Keyword or pattern to exclude
        reason: Why this should be excluded (optional)

    Returns:
        JSON response confirming addition
    """
    try:
        import copy
        from datetime import UTC, datetime

        from app.db import SessionLocal
        from app.models import SystemSettings

        data = request.get_json()
        keyword = data.get('keyword', '').strip().lower()
        reason = data.get('reason', '')

        if not keyword:
            return jsonify({'error': 'Keyword is required'}), 400

        db = SessionLocal()
        try:
            settings = db.query(SystemSettings).filter(
                SystemSettings.key == 'filter_rules'
            ).first()

            if settings:
                # Deep copy to avoid SQLAlchemy reference identity issue
                rules = copy.deepcopy(settings.value)
            else:
                rules = {
                    'exclude_keywords': [],
                    'signal_phrases': [],
                    'require_keywords': [],
                    'min_upvotes': 5,
                    'min_comments': 2,
                    'exclude_categories': [],
                    'custom_rules': [],
                }

            # Add to exclude_keywords if not already there
            if keyword not in rules.get('exclude_keywords', []):
                rules.setdefault('exclude_keywords', []).append(keyword)

            # Also add to custom_rules with reason
            rules.setdefault('custom_rules', []).append({
                'type': 'exclude_keyword',
                'value': keyword,
                'reason': reason,
                'added_at': datetime.now(UTC).isoformat(),
            })

            if settings:
                settings.value = rules
                settings.updated_at = datetime.now(UTC)
            else:
                settings = SystemSettings(key='filter_rules', value=rules)
                db.add(settings)

            db.commit()
            return jsonify({'data': {'message': f'Added exclusion: {keyword}'}})

        finally:
            db.close()

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/filter-rules/add-signal', methods=['POST'])
@admin_required()
def add_signal_phrase():
    """Add a signal phrase (positive keyword/phrase to look for).

    Signal phrases indicate market opportunity signals: feature requests,
    workarounds, integration gaps, willingness to pay, etc.

    Request Body:
        phrase: Signal phrase to add
        category: Category hint (optional) — e.g. 'pain_point', 'feature_request',
                  'workaround', 'integration_gap', 'willingness_to_pay', 'idea'

    Returns:
        JSON response confirming addition
    """
    try:
        import copy
        from datetime import UTC, datetime

        from app.db import SessionLocal
        from app.models import SystemSettings

        data = request.get_json()
        phrase = data.get('phrase', '').strip().lower()
        category = data.get('category', '').strip()

        if not phrase:
            return jsonify({'error': 'Phrase is required'}), 400

        db = SessionLocal()
        try:
            settings = db.query(SystemSettings).filter(
                SystemSettings.key == 'filter_rules'
            ).first()

            if settings:
                # Deep copy to break SQLAlchemy reference identity
                rules = copy.deepcopy(settings.value)
            else:
                rules = {
                    'exclude_keywords': [],
                    'signal_phrases': [],
                    'min_upvotes': 5,
                    'min_comments': 2,
                    'exclude_categories': [],
                    'custom_rules': [],
                }

            # Ensure signal_phrases list exists (migration for existing rules)
            rules.setdefault('signal_phrases', [])

            # Check for duplicates
            existing_phrases = [
                sp['phrase'] if isinstance(sp, dict) else sp
                for sp in rules['signal_phrases']
            ]
            if phrase in existing_phrases:
                return jsonify({'error': f'Signal phrase already exists: {phrase}'}), 409

            rules['signal_phrases'].append({
                'phrase': phrase,
                'category': category,
                'added_at': datetime.now(UTC).isoformat(),
            })

            if settings:
                settings.value = rules
                settings.updated_at = datetime.now(UTC)
            else:
                settings = SystemSettings(key='filter_rules', value=rules)
                db.add(settings)

            db.commit()
            return jsonify({'data': {'message': f'Added signal phrase: {phrase}'}})

        finally:
            db.close()

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/filter-rules/remove-signal', methods=['POST'])
@admin_required()
def remove_signal_phrase():
    """Remove a signal phrase.

    Request Body:
        phrase: Signal phrase to remove

    Returns:
        JSON response confirming removal
    """
    try:
        import copy
        from datetime import UTC, datetime

        from app.db import SessionLocal
        from app.models import SystemSettings

        data = request.get_json()
        phrase = data.get('phrase', '').strip().lower()

        if not phrase:
            return jsonify({'error': 'Phrase is required'}), 400

        db = SessionLocal()
        try:
            settings = db.query(SystemSettings).filter(
                SystemSettings.key == 'filter_rules'
            ).first()

            if not settings:
                return jsonify({'error': 'No filter rules configured'}), 404

            # Deep copy to break SQLAlchemy reference identity
            rules = copy.deepcopy(settings.value)
            signals = rules.get('signal_phrases', [])

            # Remove matching phrase (handle both dict and string entries)
            rules['signal_phrases'] = [
                sp for sp in signals
                if (sp['phrase'] if isinstance(sp, dict) else sp) != phrase
            ]

            settings.value = rules
            settings.updated_at = datetime.now(UTC)
            db.commit()

            return jsonify({'data': {'message': f'Removed signal phrase: {phrase}'}})

        finally:
            db.close()

    except Exception as e:
        return jsonify({'error': str(e)}), 500
