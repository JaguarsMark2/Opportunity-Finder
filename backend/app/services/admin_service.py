"""Admin service for administrative operations."""

from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy.exc import SQLAlchemyError

from app.db import get_db
from app.models.email_log import EmailLog
from app.models.opportunity import Opportunity
from app.models.scan import Scan
from app.models.subscription_tier import SubscriptionTier
from app.models.user import User
from app.models.user_opportunity import UserOpportunity

# ============================================================================
# Pricing Tier Management
# ============================================================================

def create_pricing_tier(data: dict[str, Any]) -> tuple[SubscriptionTier | None, str | None]:
    """Create a new pricing tier.

    Args:
        data: Pricing tier data from request

    Returns:
        Tuple of (tier, error_message)
    """
    db = next(get_db())

    try:
        # Check if slug already exists
        existing = db.query(SubscriptionTier).filter(
            SubscriptionTier.slug == data['slug']
        ).first()
        if existing:
            return None, f"Pricing tier with slug '{data['slug']}' already exists"

        # Create new tier
        tier = SubscriptionTier(
            name=data['name'],
            slug=data['slug'],
            description=data['description'],
            price=data['price'],
            yearly_price=data.get('yearly_price'),
            currency=data.get('currency', 'USD'),
            stripe_price_id=data.get('stripe_price_id'),
            stripe_yearly_price_id=data.get('stripe_yearly_price_id'),
            opportunities_limit=data.get('opportunities_limit'),
            scan_frequency=data.get('scan_frequency', 'daily'),
            email_alerts_enabled=data.get('email_alerts_enabled', True),
            email_frequency=data.get('email_frequency', 'daily'),
            features=data.get('features', []),
            is_active=data.get('is_active', True),
            display_order=data.get('display_order', 0),
        )

        db.add(tier)
        db.commit()
        db.refresh(tier)

        return tier, None

    except SQLAlchemyError as e:
        db.rollback()
        return None, f"Database error: {str(e)}"
    except Exception as e:
        db.rollback()
        return None, f"Error creating pricing tier: {str(e)}"


def update_pricing_tier(tier_id: str, data: dict[str, Any]) -> tuple[SubscriptionTier | None, str | None]:
    """Update an existing pricing tier.

    Args:
        tier_id: ID of tier to update
        data: Update data

    Returns:
        Tuple of (tier, error_message)
    """
    db = next(get_db())

    try:
        tier = db.query(SubscriptionTier).filter(SubscriptionTier.id == tier_id).first()
        if not tier:
            return None, "Pricing tier not found"

        # Check slug uniqueness if updating slug
        if 'slug' in data and data['slug'] != tier.slug:
            existing = db.query(SubscriptionTier).filter(
                SubscriptionTier.slug == data['slug']
            ).first()
            if existing:
                return None, f"Pricing tier with slug '{data['slug']}' already exists"

        # Update fields
        for field in [
            'name', 'description', 'price', 'yearly_price', 'currency',
            'stripe_price_id', 'stripe_yearly_price_id', 'opportunities_limit',
            'scan_frequency', 'email_alerts_enabled', 'email_frequency',
            'features', 'is_active', 'display_order'
        ]:
            if field in data:
                setattr(tier, field, data[field])

        tier.updated_at = datetime.now(UTC)

        db.commit()
        db.refresh(tier)

        return tier, None

    except SQLAlchemyError as e:
        db.rollback()
        return None, f"Database error: {str(e)}"
    except Exception as e:
        db.rollback()
        return None, f"Error updating pricing tier: {str(e)}"


def delete_pricing_tier(tier_id: str) -> tuple[bool, str | None]:
    """Delete a pricing tier.

    Args:
        tier_id: ID of tier to delete

    Returns:
        Tuple of (success, error_message)
    """
    db = next(get_db())

    try:
        tier = db.query(SubscriptionTier).filter(SubscriptionTier.id == tier_id).first()
        if not tier:
            return False, "Pricing tier not found"

        # Check if any users are on this tier
        user_count = db.query(User).filter(User.subscription_tier_id == tier_id).count()
        if user_count > 0:
            return False, f"Cannot delete tier with {user_count} active users. Disable it instead."

        db.delete(tier)
        db.commit()

        return True, None

    except SQLAlchemyError as e:
        db.rollback()
        return False, f"Database error: {str(e)}"
    except Exception as e:
        db.rollback()
        return False, f"Error deleting pricing tier: {str(e)}"


def list_pricing_tiers(include_inactive: bool = False) -> tuple[list[SubscriptionTier], str | None]:
    """List all pricing tiers.

    Args:
        include_inactive: Whether to include inactive tiers

    Returns:
        Tuple of (tiers, error_message)
    """
    db = next(get_db())

    try:
        query = db.query(SubscriptionTier)
        if not include_inactive:
            query = query.filter(SubscriptionTier.is_active is True)

        tiers = query.order_by(SubscriptionTier.display_order).all()

        # Add user count for each tier
        for tier in tiers:
            tier.user_count = db.query(User).filter(User.subscription_tier_id == tier.id).count()

        return tiers, None

    except SQLAlchemyError as e:
        return [], f"Database error: {str(e)}"


# ============================================================================
# User Management
# ============================================================================

def list_users(
    search: str | None = None,
    role: str | None = None,
    subscription_status: str | None = None,
    subscription_tier_id: str | None = None,
    is_email_verified: bool | None = None,
    limit: int = 50,
    cursor: str | None = None
) -> tuple[list[User], str | None, str | None]:
    """List users with filters.

    Returns:
        Tuple of (users, next_cursor, error_message)
    """
    db = next(get_db())

    try:
        query = db.query(User)

        # Apply filters
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(User.email.ilike(search_pattern))

        if role:
            query = query.filter(User.role == role)

        if subscription_status:
            query = query.filter(User.subscription_status == subscription_status)

        if subscription_tier_id:
            query = query.filter(User.subscription_tier_id == subscription_tier_id)

        if is_email_verified is not None:
            query = query.filter(User.email_verified == is_email_verified)

        # Apply cursor pagination
        if cursor:
            query = query.filter(User.created_at < cursor)

        # Order and limit
        query = query.order_by(User.created_at.desc()).limit(limit + 1)

        users = query.all()

        # Determine next cursor
        next_cursor = None
        if len(users) > limit:
            users = users[:limit]
            next_cursor = users[-1].created_at.isoformat()

        # Add additional fields
        for user in users:
            tier = db.query(SubscriptionTier).filter(SubscriptionTier.id == user.subscription_tier_id).first()
            user.tier_name = tier.name if tier else None

            user.opportunity_count = db.query(UserOpportunity).filter(
                UserOpportunity.user_id == user.id,
                UserOpportunity.status.in_(['researching', 'building'])
            ).count()

            user.saved_opportunity_count = db.query(UserOpportunity).filter(
                UserOpportunity.user_id == user.id,
                UserOpportunity.is_saved is True
            ).count()

        return users, next_cursor, None

    except SQLAlchemyError as e:
        return [], None, f"Database error: {str(e)}"


def get_user_details(user_id: str) -> tuple[dict[str, Any] | None, str | None]:
    """Get detailed user information for admin.

    Returns:
        Tuple of (user_data, error_message)
    """
    db = next(get_db())

    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None, "User not found"

        # Get tier info
        tier = db.query(SubscriptionTier).filter(SubscriptionTier.id == user.subscription_tier_id).first()

        # Get opportunity stats
        total_viewed = db.query(UserOpportunity).filter(UserOpportunity.user_id == user_id).count()
        saved_count = db.query(UserOpportunity).filter(
            UserOpportunity.user_id == user_id,
            UserOpportunity.is_saved is True
        ).count()
        researching_count = db.query(UserOpportunity).filter(
            UserOpportunity.user_id == user_id,
            UserOpportunity.status == 'researching'
        ).count()
        building_count = db.query(UserOpportunity).filter(
            UserOpportunity.user_id == user_id,
            UserOpportunity.status == 'building'
        ).count()

        return {
            'id': user.id,
            'email': user.email,
            'role': user.role,
            'subscription_status': user.subscription_status,
            'subscription_tier_id': user.subscription_tier_id,
            'tier_name': tier.name if tier else None,
            'email_verified': user.email_verified,
            'created_at': user.created_at.isoformat(),
            'last_login': user.last_login.isoformat() if user.last_login else None,
            'stats': {
                'total_viewed': total_viewed,
                'saved_count': saved_count,
                'researching_count': researching_count,
                'building_count': building_count,
            }
        }, None

    except SQLAlchemyError as e:
        return None, f"Database error: {str(e)}"


def update_user(user_id: str, data: dict[str, Any]) -> tuple[bool, str | None]:
    """Update user as admin.

    Returns:
        Tuple of (success, error_message)
    """
    db = next(get_db())

    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False, "User not found"

        # Update allowed fields
        for field in ['role', 'subscription_status', 'subscription_tier_id', 'email_verified']:
            if field in data:
                setattr(user, field, data[field])

        user.updated_at = datetime.now(UTC)

        db.commit()

        return True, None

    except SQLAlchemyError as e:
        db.rollback()
        return False, f"Database error: {str(e)}"


# ============================================================================
# Analytics
# ============================================================================

def get_analytics(time_range: str = '30d') -> tuple[dict[str, Any] | None, str | None]:
    """Get analytics data for admin dashboard.

    Args:
        time_range: Time range for data ('24h', '7d', '30d', '90d', 'all')

    Returns:
        Tuple of (analytics_data, error_message)
    """
    db = next(get_db())

    try:
        # Calculate time cutoff
        now = datetime.now(UTC)
        if time_range == '24h':
            cutoff = now - timedelta(hours=24)
        elif time_range == '7d':
            cutoff = now - timedelta(days=7)
        elif time_range == '30d':
            cutoff = now - timedelta(days=30)
        elif time_range == '90d':
            cutoff = now - timedelta(days=90)
        else:
            cutoff = None

        # User metrics
        total_users = db.query(User).count()
        new_users = db.query(User).filter(User.created_at >= cutoff).count() if cutoff else 0
        active_users = db.query(User).filter(User.subscription_status == 'active').count()
        trial_users = db.query(User).filter(User.subscription_status == 'free').count()
        admin_users = db.query(User).filter(User.role == 'admin').count()

        # Revenue metrics (simplified - assumes price per tier)
        active_tiers = db.query(
            User.subscription_tier_id,
            SubscriptionTier.price
        ).join(SubscriptionTier, User.subscription_tier_id == SubscriptionTier.id).filter(
            User.subscription_status == 'active'
        ).all()

        monthly_recurring_revenue = sum(tier.price or 0 for user_id, tier in active_tiers)

        # Opportunity metrics
        total_opportunities = db.query(Opportunity).count()
        new_opportunities = db.query(Opportunity).filter(Opportunity.created_at >= cutoff).count() if cutoff else 0
        validated_opportunities = db.query(Opportunity).filter(Opportunity.is_validated is True).count()
        high_score_count = db.query(Opportunity).filter(Opportunity.score >= 70).count()

        # Scan metrics
        total_scans = db.query(Scan).count()
        recent_scans = db.query(Scan).filter(Scan.created_at >= cutoff).count() if cutoff else 0
        successful_scans = db.query(Scan).filter(Scan.status == 'completed').count()

        # Email metrics
        total_emails = db.query(EmailLog).count()
        recent_emails = db.query(EmailLog).filter(EmailLog.sent_at >= cutoff).count() if cutoff else 0
        successful_emails = db.query(EmailLog).filter(EmailLog.status == 'sent').count()

        # Get daily signups (simplified)
        days = 30 if time_range in ['30d', '90d', 'all'] else (7 if time_range == '7d' else 1)
        daily_signups = []
        for i in range(days):
            day_start = now - timedelta(days=i)
            day_end = day_start + timedelta(days=1)
            count = db.query(User).filter(
                User.created_at >= day_start,
                User.created_at < day_end
            ).count()
            daily_signups.append({
                'date': day_start.strftime('%Y-%m-%d'),
                'count': count
            })

        return {
            'users': {
                'total': total_users,
                'new': new_users,
                'active': active_users,
                'free': trial_users,
                'admins': admin_users,
                'daily_signups': list(reversed(daily_signups)),
            },
            'revenue': {
                'mrr': round(monthly_recurring_revenue, 2),
                'active_subscribers': active_users,
            },
            'opportunities': {
                'total': total_opportunities,
                'new': new_opportunities,
                'validated': validated_opportunities,
                'high_score': high_score_count,
            },
            'scans': {
                'total': total_scans,
                'recent': recent_scans,
                'successful': successful_scans,
                'success_rate': round(successful_scans / total_scans * 100, 1) if total_scans > 0 else 0,
            },
            'emails': {
                'total': total_emails,
                'recent': recent_emails,
                'successful': successful_emails,
                'success_rate': round(successful_emails / total_emails * 100, 1) if total_emails > 0 else 0,
            },
        }, None

    except SQLAlchemyError as e:
        return None, f"Database error: {str(e)}"
