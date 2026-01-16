"""Stripe service for payment processing.

Handles checkout sessions, webhooks, customer portal, and subscription management.
"""

import os
from datetime import UTC, datetime
from typing import Any

import stripe

from app.db import get_db
from app.models.subscription_tier import SubscriptionTier
from app.models.user import User
from app.models.webhook_event import WebhookEvent

# Initialize Stripe with API key from environment
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')
STRIPE_PRICE_ID_MAP = {
    'starter': os.getenv('STRIPE_STARTER_PRICE_ID'),
    'pro': os.getenv('STRIPE_PRO_PRICE_ID'),
    'enterprise': os.getenv('STRIPE_ENTERPRISE_PRICE_ID'),
}


class StripeServiceError(Exception):
    """Custom exception for Stripe service errors."""
    pass


def get_or_create_stripe_customer(user_id: str) -> tuple[str | None, str | None]:
    """Get existing Stripe customer or create a new one.

    Args:
        user_id: User ID in our system

    Returns:
        Tuple of (customer_id, error_message)
    """
    db = next(get_db())

    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None, "User not found"

        # Return existing customer ID if already set
        if user.stripe_customer_id:
            return user.stripe_customer_id, None

        # Create new Stripe customer
        customer = stripe.Customer.create(
            email=user.email,
            metadata={
                'user_id': user_id,
            }
        )

        # Save customer ID to user
        user.stripe_customer_id = customer.id
        db.commit()

        return customer.id, None

    except stripe.StripeError as e:
        return None, f"Stripe error: {str(e)}"
    except Exception as e:
        return None, f"Error creating customer: {str(e)}"


def create_checkout_session(
    user_id: str,
    tier_id: str,
    success_url: str,
    cancel_url: str
) -> tuple[dict[str, Any] | None, str | None]:
    """Create a Stripe checkout session for subscription.

    Args:
        user_id: User ID
        tier_id: Subscription tier ID
        success_url: URL to redirect after successful payment
        cancel_url: URL to redirect if payment is cancelled

    Returns:
        Tuple of (session_data, error_message)
        session_data contains { 'checkout_url': str, 'session_id': str }
    """
    db = next(get_db())

    try:
        # Get tier
        tier = db.query(SubscriptionTier).filter(SubscriptionTier.id == tier_id).first()
        if not tier:
            return None, "Subscription tier not found"

        # Get or create Stripe customer
        customer_id, error = get_or_create_stripe_customer(user_id)
        if error:
            return None, error

        # customer_id should not be None if there's no error
        assert customer_id is not None

        # Use Stripe price ID from tier or fallback to env var
        price_id = tier.stripe_price_id
        if not price_id and tier.slug in STRIPE_PRICE_ID_MAP:
            price_id = STRIPE_PRICE_ID_MAP[tier.slug]

        if not price_id:
            return None, "No Stripe price ID configured for this tier"

        # Create checkout session
        session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=['card'],
            line_items=[
                {
                    'price': price_id,
                    'quantity': 1,
                }
            ],
            mode='subscription',
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                'user_id': user_id,
                'tier_id': tier_id,
            },
            subscription_data={
                'metadata': {
                    'user_id': user_id,
                    'tier_id': tier_id,
                }
            },
            allow_promotion_codes=True,
        )

        return {
            'checkout_url': session.url,
            'session_id': session.id,
        }, None

    except stripe.StripeError as e:
        return None, f"Stripe error: {str(e)}"
    except Exception as e:
        return None, f"Error creating checkout session: {str(e)}"


def create_customer_portal_session(
    user_id: str,
    return_url: str
) -> tuple[str | None, str | None]:
    """Create a Stripe customer portal session.

    Args:
        user_id: User ID
        return_url: URL to redirect after portal session

    Returns:
        Tuple of (portal_url, error_message)
    """
    db = next(get_db())

    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None, "User not found"

        if not user.stripe_customer_id:
            return None, "No Stripe customer found for user"

        # Create portal session
        session = stripe.billing_portal.Session.create(
            customer=user.stripe_customer_id,
            return_url=return_url,
        )

        return session.url, None

    except stripe.StripeError as e:
        return None, f"Stripe error: {str(e)}"
    except Exception as e:
        return None, f"Error creating portal session: {str(e)}"


def construct_webhook_event(payload: bytes, sig_header: str) -> tuple[stripe.Event | None, str | None]:
    """Construct webhook event from payload and signature.

    Args:
        payload: Raw request body
        sig_header: Stripe-Signature header

    Returns:
        Tuple of (event, error_message)
    """
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
        return event, None
    except ValueError:
        return None, "Invalid payload"
    except stripe.SignatureVerificationError:
        return None, "Invalid signature"


def is_webhook_processed(event_id: str) -> bool:
    """Check if webhook event has already been processed.

    Args:
        event_id: Stripe event ID

    Returns:
        True if already processed
    """
    db = next(get_db())
    existing = db.query(WebhookEvent).filter(WebhookEvent.event_id == event_id).first()
    return existing is not None


def mark_webhook_processed(event_id: str, event_type: str) -> None:
    """Mark a webhook event as processed.

    Args:
        event_id: Stripe event ID
        event_type: Event type (e.g., 'checkout.session.completed')
    """
    db = next(get_db())
    webhook_event = WebhookEvent(
        event_id=event_id,
        event_type=event_type,
        processed_at=datetime.now(UTC)
    )
    db.add(webhook_event)
    db.commit()


def handle_checkout_session_completed(event: stripe.Event) -> tuple[bool, str | None]:
    """Handle checkout.session.completed webhook event.

    Args:
        event: Stripe event object

    Returns:
        Tuple of (success, error_message)
    """
    try:
        session = event['data']['object']
        metadata = session.get('metadata', {})

        user_id = metadata.get('user_id')
        tier_id = metadata.get('tier_id')

        if not user_id or not tier_id:
            return False, "Missing user_id or tier_id in session metadata"

        # Check if already processed
        if is_webhook_processed(event['id']):
            return True, None  # Already processed, skip

        db = next(get_db())
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False, "User not found"

        # Get subscription details
        subscription_id = session.get('subscription')
        if subscription_id:
            # Fetch subscription to get current period end
            stripe.Subscription.retrieve(subscription_id)
            user.stripe_subscription_id = subscription_id
            user.subscription_status = 'active'
        else:
            user.subscription_status = 'active'

        # Update tier
        user.subscription_tier_id = tier_id
        user.updated_at = datetime.now(UTC)

        db.commit()

        # Mark as processed
        mark_webhook_processed(event['id'], event['type'])

        return True, None

    except Exception as e:
        return False, f"Error handling checkout completed: {str(e)}"


def handle_subscription_updated(event: stripe.Event) -> tuple[bool, str | None]:
    """Handle customer.subscription.updated webhook event.

    Args:
        event: Stripe event object

    Returns:
        Tuple of (success, error_message)
    """
    try:
        subscription = event['data']['object']
        customer_id = subscription.get('customer')

        # Check if already processed
        if is_webhook_processed(event['id']):
            return True, None

        db = next(get_db())
        user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
        if not user:
            return False, "User not found"

        # Update subscription status
        status_map = {
            'active': 'active',
            'past_due': 'past_due',
            'canceled': 'canceled',
            'unpaid': 'past_due',
            'trialing': 'trialing',
            'incomplete': 'incomplete',
            'incomplete_expired': 'incomplete_expired',
        }

        user.subscription_status = status_map.get(
            subscription.get('status'),
            'incomplete'
        )

        # Update subscription ID
        user.stripe_subscription_id = subscription.get('id')

        db.commit()

        # Mark as processed
        mark_webhook_processed(event['id'], event['type'])

        return True, None

    except Exception as e:
        return False, f"Error handling subscription updated: {str(e)}"


def handle_subscription_deleted(event: stripe.Event) -> tuple[bool, str | None]:
    """Handle customer.subscription.deleted webhook event.

    Args:
        event: Stripe event object

    Returns:
        Tuple of (success, error_message)
    """
    try:
        subscription = event['data']['object']
        customer_id = subscription.get('customer')

        # Check if already processed
        if is_webhook_processed(event['id']):
            return True, None

        db = next(get_db())
        user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
        if not user:
            return False, "User not found"

        # Downgrade to free tier
        free_tier = db.query(SubscriptionTier).filter(SubscriptionTier.slug == 'free').first()

        user.subscription_status = 'canceled'
        user.subscription_tier_id = free_tier.id if free_tier else None
        user.stripe_subscription_id = None
        user.updated_at = datetime.now(UTC)

        db.commit()

        # Mark as processed
        mark_webhook_processed(event['id'], event['type'])

        return True, None

    except Exception as e:
        return False, f"Error handling subscription deleted: {str(e)}"


def handle_invoice_paid(event: stripe.Event) -> tuple[bool, str | None]:
    """Handle invoice.paid webhook event.

    Args:
        event: Stripe event object

    Returns:
        Tuple of (success, error_message)
    """
    try:
        invoice = event['data']['object']
        customer_id = invoice.get('customer')

        # Check if already processed
        if is_webhook_processed(event['id']):
            return True, None

        db = next(get_db())
        user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
        if not user:
            # User might have been deleted, ignore
            return True, None

        # Update status to active (payment successful)
        user.subscription_status = 'active'
        db.commit()

        # Mark as processed
        mark_webhook_processed(event['id'], event['type'])

        return True, None

    except Exception as e:
        return False, f"Error handling invoice paid: {str(e)}"


def handle_invoice_payment_failed(event: stripe.Event) -> tuple[bool, str | None]:
    """Handle invoice.payment_failed webhook event.

    Args:
        event: Stripe event object

    Returns:
        Tuple of (success, error_message)
    """
    try:
        invoice = event['data']['object']
        customer_id = invoice.get('customer')

        # Check if already processed
        if is_webhook_processed(event['id']):
            return True, None

        db = next(get_db())
        user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
        if not user:
            return True, None

        # Update status to past_due
        user.subscription_status = 'past_due'
        db.commit()

        # Mark as processed
        mark_webhook_processed(event['id'], event['type'])

        return True, None

    except Exception as e:
        return False, f"Error handling invoice payment failed: {str(e)}"


# Webhook event handler mapping
WEBHOOK_HANDLERS = {
    'checkout.session.completed': handle_checkout_session_completed,
    'customer.subscription.updated': handle_subscription_updated,
    'customer.subscription.deleted': handle_subscription_deleted,
    'invoice.paid': handle_invoice_paid,
    'invoice.payment_failed': handle_invoice_payment_failed,
}


def handle_webhook_event(event: stripe.Event) -> tuple[bool, str | None]:
    """Route webhook event to appropriate handler.

    Args:
        event: Stripe event object

    Returns:
        Tuple of (success, error_message)
    """
    event_type = event['type']

    handler = WEBHOOK_HANDLERS.get(event_type)
    if not handler:
        # Unknown event type, but don't fail
        return True, None

    return handler(event)


def cancel_subscription(user_id: str) -> tuple[bool, str | None]:
    """Cancel a user's subscription at period end.

    Args:
        user_id: User ID

    Returns:
        Tuple of (success, error_message)
    """
    db = next(get_db())

    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False, "User not found"

        if not user.stripe_subscription_id:
            return False, "No active subscription found"

        # Cancel subscription at period end
        stripe.Subscription.modify(
            user.stripe_subscription_id,
            cancel_at_period_end=True
        )

        return True, None

    except stripe.StripeError as e:
        return False, f"Stripe error: {str(e)}"
    except Exception as e:
        return False, f"Error canceling subscription: {str(e)}"
