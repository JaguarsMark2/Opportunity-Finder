"""Admin request/response schemas."""

from marshmallow import Schema, fields, validate, validates

# ============================================================================
# Pricing Tier Schemas
# ============================================================================

class PricingTierCreateSchema(Schema):
    """Schema for creating a pricing tier."""
    name = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=100),
        metadata={'description': 'Tier name (e.g., "Pro", "Enterprise")'}
    )
    slug = fields.Str(
        required=True,
        validate=[validate.Length(min=1, max=50), validate.Regexp('^[a-z0-9-]+$', error='Slug must contain only lowercase letters, numbers, and hyphens')],
        metadata={'description': 'URL-friendly slug (e.g., "pro", "enterprise")'}
    )
    description = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=500),
        metadata={'description': 'Tier description'}
    )
    price = fields.Float(
        required=True,
        validate=validate.Range(min=0),
        metadata={'description': 'Monthly price in USD'}
    )
    yearly_price = fields.Float(
        validate=validate.Range(min=0),
        missing=None,
        metadata={'description': 'Yearly price in USD (optional)'}
    )
    currency = fields.Str(
        missing='USD',
        validate=validate.OneOf(['USD', 'EUR', 'GBP']),
        metadata={'description': 'Currency code'}
    )
    stripe_price_id = fields.Str(
        missing=None,
        validate=validate.Length(max=100),
        metadata={'description': 'Stripe price ID for billing'}
    )
    stripe_yearly_price_id = fields.Str(
        missing=None,
        validate=validate.Length(max=100),
        metadata={'description': 'Stripe yearly price ID'}
    )
    opportunities_limit = fields.Int(
        validate=validate.Range(min=0),
        missing=None,
        metadata={'description': 'Max opportunities per billing cycle (null=unlimited)'}
    )
    scan_frequency = fields.Str(
        missing='daily',
        validate=validate.OneOf(['realtime', 'hourly', 'daily', 'weekly']),
        metadata={'description': 'How often to run scans'}
    )
    email_alerts_enabled = fields.Bool(
        missing=True,
        metadata={'description': 'Whether email alerts are enabled'}
    )
    email_frequency = fields.Str(
        missing='daily',
        validate=validate.OneOf(['immediate', 'daily', 'weekly']),
        metadata={'description': 'How often to send email alerts'}
    )
    features = fields.List(
        fields.Str(),
        missing=[],
        metadata={'description': 'List of features included in this tier'}
    )
    is_active = fields.Bool(
        missing=True,
        metadata={'description': 'Whether this tier is currently available'}
    )
    display_order = fields.Int(
        missing=0,
        metadata={'description': 'Display order for pricing page'}
    )

    @validates('slug')
    def validate_slug_unique(self, value):
        """Validate that slug is unique (will be checked in service layer)."""
        return value


class PricingTierUpdateSchema(Schema):
    """Schema for updating a pricing tier."""
    name = fields.Str(validate=validate.Length(min=1, max=100))
    description = fields.Str(validate=validate.Length(min=1, max=500))
    price = fields.Float(validate=validate.Range(min=0))
    yearly_price = fields.Float(validate=validate.Range(min=0))
    currency = fields.Str(validate=validate.OneOf(['USD', 'EUR', 'GBP']))
    stripe_price_id = fields.Str(validate=validate.Length(max=100))
    stripe_yearly_price_id = fields.Str(validate=validate.Length(max=100))
    opportunities_limit = fields.Int(validate=validate.Range(min=0))
    scan_frequency = fields.Str(validate=validate.OneOf(['realtime', 'hourly', 'daily', 'weekly']))
    email_alerts_enabled = fields.Bool()
    email_frequency = fields.Str(validate=validate.OneOf(['immediate', 'daily', 'weekly']))
    features = fields.List(fields.Str())
    is_active = fields.Bool()
    display_order = fields.Int()


class PricingTierResponseSchema(Schema):
    """Schema for pricing tier response."""
    id = fields.Str()
    name = fields.Str()
    slug = fields.Str()
    description = fields.Str()
    price = fields.Float()
    yearly_price = fields.Float(allow_none=True)
    currency = fields.Str()
    stripe_price_id = fields.Str(allow_none=True)
    stripe_yearly_price_id = fields.Str(allow_none=True)
    opportunities_limit = fields.Int(allow_none=True)
    scan_frequency = fields.Str()
    email_alerts_enabled = fields.Bool()
    email_frequency = fields.Str()
    features = fields.List(fields.Str())
    is_active = fields.Bool()
    display_order = fields.Int()
    user_count = fields.Int(dump_only=True, metadata={'description': 'Number of users on this tier'})
    created_at = fields.DateTime()
    updated_at = fields.DateTime()


# ============================================================================
# User Management Schemas
# ============================================================================

class UserListQuerySchema(Schema):
    """Schema for user list query parameters."""
    search = fields.Str(
        missing=None,
        metadata={'description': 'Search by email or name'}
    )
    role = fields.Str(
        missing=None,
        validate=validate.OneOf(['user', 'admin']),
        metadata={'description': 'Filter by role'}
    )
    subscription_status = fields.Str(
        missing=None,
        validate=validate.OneOf(['active', 'trialing', 'past_due', 'canceled', 'incomplete', 'incomplete_expired']),
        metadata={'description': 'Filter by subscription status'}
    )
    subscription_tier_id = fields.Str(missing=None)
    is_email_verified = fields.Bool(missing=None)
    limit = fields.Int(missing=50, validate=validate.Range(min=1, max=100))
    cursor = fields.Str(missing=None)


class UserUpdateSchema(Schema):
    """Schema for updating user as admin."""
    role = fields.Str(
        validate=validate.OneOf(['user', 'admin']),
        metadata={'description': 'User role'}
    )
    subscription_status = fields.Str(
        validate=validate.OneOf(['active', 'trialing', 'past_due', 'canceled', 'incomplete', 'incomplete_expired']),
        metadata={'description': 'Subscription status'}
    )
    subscription_tier_id = fields.Str(allow_none=True)
    email_verified = fields.Bool()


class UserAdminResponseSchema(Schema):
    """Schema for user details in admin panel."""
    id = fields.Str()
    email = fields.Str()
    role = fields.Str()
    subscription_status = fields.Str()
    subscription_tier_id = fields.Str(allow_none=True)
    tier_name = fields.Str(allow_none=True, dump_only=True)
    email_verified = fields.Bool()
    created_at = fields.DateTime()
    last_login = fields.DateTime(allow_none=True, dump_only=True)
    opportunity_count = fields.Int(dump_only=True)
    saved_opportunity_count = fields.Int(dump_only=True)


# ============================================================================
# Data Source Configuration Schemas
# ============================================================================

class DataSourceConfigSchema(Schema):
    """Schema for data source configuration."""
    source_type = fields.Str(
        required=True,
        validate=validate.OneOf(['reddit', 'indie_hackers', 'product_hunt', 'hacker_news', 'google_trends', 'microns']),
        metadata={'description': 'Type of data source'}
    )
    is_enabled = fields.Bool(
        required=True,
        metadata={'description': 'Whether this source is active'}
    )
    config = fields.Dict(
        required=True,
        metadata={'description': 'Source-specific configuration (API keys, etc.)'}
    )


class DataSourceTestSchema(Schema):
    """Schema for testing data source connection."""
    source_type = fields.Str(
        required=True,
        validate=validate.OneOf(['reddit', 'indie_hackers', 'product_hunt', 'hacker_news', 'google_trends', 'microns'])
    )


# ============================================================================
# Scoring Configuration Schemas
# ============================================================================

class ScoringWeightsUpdateSchema(Schema):
    """Schema for updating scoring weights."""
    demand_weight = fields.Float(validate=validate.Range(min=0, max=1))
    competition_weight = fields.Float(validate=validate.Range(min=0, max=1))
    engagement_weight = fields.Float(validate=validate.Range(min=0, max=1))
    validation_weight = fields.Float(validate=validate.Range(min=0, max=1))
    recency_weight = fields.Float(validate=validate.Range(min=0, max=1))


class ScoringThresholdsUpdateSchema(Schema):
    """Schema for updating scoring thresholds."""
    high_score_threshold = fields.Float(validate=validate.Range(min=0, max=100))
    medium_score_threshold = fields.Float(validate=validate.Range(min=0, max=100))
    validation_threshold = fields.Float(validate=validate.Range(min=0, max=100))
    min_competitors = fields.Int(validate=validate.Range(min=0))
    max_competitors = fields.Int(validate=validate.Range(min=0))


class ScoringConfigResponseSchema(Schema):
    """Schema for scoring configuration response."""
    weights = fields.Dict()
    thresholds = fields.Dict()
    enabled_criteria = fields.Dict()
    last_updated = fields.DateTime()
    updated_by = fields.Str()


# ============================================================================
# Scan Settings Schemas
# ============================================================================

class ScanScheduleSchema(Schema):
    """Schema for scan schedule configuration."""
    source_type = fields.Str(
        required=True,
        validate=validate.OneOf(['reddit', 'indie_hackers', 'product_hunt', 'hacker_news', 'google_trends', 'microns', 'all'])
    )
    frequency = fields.Str(
        required=True,
        validate=validate.OneOf(['realtime', 'hourly', 'daily', 'weekly', 'manual']),
        metadata={'description': 'How often to scan this source'}
    )
    cron_schedule = fields.Str(
        allow_none=True,
        metadata={'description': 'Cron expression for custom scheduling'}
    )
    is_enabled = fields.Bool(
        required=True,
        metadata={'description': 'Whether this scan schedule is active'}
    )


class ManualScanSchema(Schema):
    """Schema for triggering manual scan."""
    sources = fields.List(
        fields.Str(validate=validate.OneOf(['reddit', 'indie_hackers', 'product_hunt', 'hacker_news', 'google_trends', 'microns'])),
        missing=['all'],
        metadata={'description': 'List of sources to scan (empty = all enabled sources)'}
    )


# ============================================================================
# Email Settings Schemas
# ============================================================================

class EmailTemplateSchema(Schema):
    """Schema for email template configuration."""
    template_type = fields.Str(
        required=True,
        validate=validate.OneOf(['daily_digest', 'weekly_digest', 'opportunity_alert', 'trial_ending', 'payment_failed', 'welcome']),
        metadata={'description': 'Type of email template'}
    )
    subject = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=200),
        metadata={'description': 'Email subject line'}
    )
    body_template = fields.Str(
        required=True,
        metadata={'description': 'Email body (can include Jinja2 variables)'}
    )
    is_enabled = fields.Bool(
        required=True,
        metadata={'description': 'Whether this template is active'}
    )


class EmailFrequencyByTierSchema(Schema):
    """Schema for setting email frequency per tier."""
    tier_id = fields.Str(required=True)
    frequency = fields.Str(
        required=True,
        validate=validate.OneOf(['immediate', 'daily', 'weekly', 'none']),
        metadata={'description': 'Email frequency for this tier'}
    )


# ============================================================================
# Analytics Schemas
# ============================================================================

class AnalyticsQuerySchema(Schema):
    """Schema for analytics query parameters."""
    time_range = fields.Str(
        missing='30d',
        validate=validate.OneOf(['24h', '7d', '30d', '90d', 'all']),
        metadata={'description': 'Time range for analytics'}
    )


class AnalyticsResponseSchema(Schema):
    """Schema for analytics response."""
    users = fields.Dict(dump_only=True)
    revenue = fields.Dict(dump_only=True)
    opportunities = fields.Dict(dump_only=True)
    scans = fields.Dict(dump_only=True)
    emails = fields.Dict(dump_only=True)
