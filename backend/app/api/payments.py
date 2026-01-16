"""Payment API endpoints for Stripe integration."""

import stripe
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.services.stripe_service import (
    cancel_subscription as cancel_user_subscription,
)
from app.services.stripe_service import (
    construct_webhook_event,
    create_checkout_session,
    create_customer_portal_session,
    handle_webhook_event,
)

# Create blueprint
payments_bp = Blueprint('payments', __name__, url_prefix='/api/v1/payments')


# ============================================================================
# Checkout Endpoints
# ============================================================================

@payments_bp.route('/create-checkout', methods=['POST'])
@jwt_required()
def create_checkout():
    """Create a Stripe checkout session for subscription.

    Request Body:
        {
            "tier_id": "string",
            "success_url": "string",  // optional, defaults to frontend URL
            "cancel_url": "string"   // optional, defaults to frontend URL
        }

    Returns:
        {
            "data": {
                "checkout_url": "string",
                "session_id": "string"
            }
        }
    """
    try:
        data = request.get_json()
        tier_id = data.get('tier_id')

        if not tier_id:
            return jsonify({'error': 'tier_id is required'}), 400

        user_id = get_jwt_identity()

        # Get URLs from request or use defaults
        success_url = data.get(
            'success_url',
            request.headers.get('Origin', 'http://localhost:5173') + '/billing?success=true'
        )
        cancel_url = data.get(
            'cancel_url',
            request.headers.get('Origin', 'http://localhost:5173') + '/billing?canceled=true'
        )

        # Create checkout session
        session_data, error = create_checkout_session(user_id, tier_id, success_url, cancel_url)
        if error:
            return jsonify({'error': error}), 400

        return jsonify({'data': session_data})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# Customer Portal Endpoints
# ============================================================================

@payments_bp.route('/customer-portal', methods=['POST'])
@jwt_required()
def customer_portal():
    """Create a Stripe customer portal session.

    Request Body:
        {
            "return_url": "string"  // optional, defaults to frontend URL
        }

    Returns:
        {
            "data": {
                "portal_url": "string"
            }
        }
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json() or {}

        return_url = data.get(
            'return_url',
            request.headers.get('Origin', 'http://localhost:5173') + '/billing'
        )

        portal_url, error = create_customer_portal_session(user_id, return_url)
        if error:
            return jsonify({'error': error}), 400

        return jsonify({'data': {'portal_url': portal_url}})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# Subscription Management Endpoints
# ============================================================================

@payments_bp.route('/subscription', methods=['GET'])
@jwt_required()
def get_subscription():
    """Get current user's subscription details.

    Returns:
        {
            "data": {
                "subscription_status": "string",
                "tier_id": "string",
                "tier_name": "string",
                "stripe_subscription_id": "string",
                "cancel_at_period_end": boolean
            }
        }
    """
    try:
        from app.db import get_db
        from app.models.subscription_tier import SubscriptionTier
        from app.models.user import User

        user_id = get_jwt_identity()
        db = next(get_db())

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Get tier details
        tier = None
        if user.subscription_tier_id:
            tier = db.query(SubscriptionTier).filter(
                SubscriptionTier.id == user.subscription_tier_id
            ).first()

        # Get subscription details from Stripe if exists
        cancel_at_period_end = False
        if user.stripe_subscription_id:
            try:
                subscription = stripe.Subscription.retrieve(user.stripe_subscription_id)
                cancel_at_period_end = subscription.get('cancel_at_period_end', False)
            except stripe.error.StripeError:
                pass

        return jsonify({
            'data': {
                'subscription_status': user.subscription_status,
                'tier_id': user.subscription_tier_id,
                'tier_name': tier.name if tier else None,
                'tier_slug': tier.slug if tier else 'free',
                'tier_price': tier.price if tier else 0,
                'stripe_subscription_id': user.stripe_subscription_id,
                'cancel_at_period_end': cancel_at_period_end,
            }
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@payments_bp.route('/subscription/cancel', methods=['POST'])
@jwt_required()
def cancel_subscription():
    """Cancel subscription at period end.

    Returns:
        {
            "data": {
                "message": "Subscription will be canceled at period end"
            }
        }
    """
    try:
        user_id = get_jwt_identity()

        success, error = cancel_user_subscription(user_id)
        if error:
            return jsonify({'error': error}), 400

        return jsonify({
            'data': {
                'message': 'Subscription will be canceled at period end'
            }
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# Webhook Endpoint
# ============================================================================

@payments_bp.route('/webhook', methods=['POST'])
def webhook():
    """Handle Stripe webhook events.

    This endpoint receives webhook events from Stripe for:
    - checkout.session.completed
    - customer.subscription.updated
    - customer.subscription.deleted
    - invoice.paid
    - invoice.payment_failed

    The webhook signature is verified for security.
    """
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')

    if not sig_header:
        return jsonify({'error': 'No Stripe-Signature header found'}), 400

    # Construct and verify event
    event, error = construct_webhook_event(payload, sig_header)
    if error:
        return jsonify({'error': error}), 400

    # Handle the event
    success, error = handle_webhook_event(event)
    if error:
        # Log error but return 200 to Stripe (don't retry on errors we understand)
        print(f"Webhook handling error: {error}")
        return jsonify({'error': error}), 200

    return jsonify({'received': True}), 200


# ============================================================================
# Pricing/Tier Info for Frontend
# ============================================================================

@payments_bp.route('/pricing', methods=['GET'])
def get_pricing():
    """Get available pricing tiers for checkout.

    Returns:
        {
            "data": {
                "items": [
                    {
                        "id": "string",
                        "name": "string",
                        "slug": "string",
                        "description": "string",
                        "price": number,
                        "yearly_price": number,
                        "currency": "string",
                        "features": ["string"],
                        "is_active": boolean
                    }
                ]
            }
        }
    """
    try:
        from app.db import get_db
        from app.models.subscription_tier import SubscriptionTier

        db = next(get_db())

        tiers = db.query(SubscriptionTier).filter(
            SubscriptionTier.is_active is True
        ).order_by(SubscriptionTier.display_order).all()

        items = []
        for tier in tiers:
            items.append({
                'id': tier.id,
                'name': tier.name,
                'slug': tier.slug,
                'description': tier.description,
                'price': tier.price,
                'yearly_price': tier.yearly_price,
                'currency': tier.currency,
                'features': tier.features or [],
                'is_active': tier.is_active,
                'display_order': tier.display_order,
            })

        return jsonify({'data': {'items': items}})

    except Exception as e:
        return jsonify({'error': str(e)}), 500
