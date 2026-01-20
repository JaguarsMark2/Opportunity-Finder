"""Opportunity request/response schemas."""

from marshmallow import Schema, fields, validate


class OpportunityListSchema(Schema):
    """Schema for opportunity list request parameters."""
    min_score = fields.Integer(required=False, validate=validate.Range(min=0, max=100))
    max_score = fields.Integer(required=False, validate=validate.Range(min=0, max=100))
    is_validated = fields.Boolean(required=False)
    sort = fields.String(
        required=False,
        validate=validate.OneOf(['score', 'revenue', 'mentions', 'created_at', '-score', '-revenue', '-mentions', '-created_at'])
    )
    search = fields.String(required=False)
    time_range = fields.String(
        required=False,
        validate=validate.OneOf(['day', 'week', 'month', 'year', 'all'])
    )
    limit = fields.Integer(required=False, validate=validate.Range(min=1, max=100))
    cursor = fields.String(required=False)


class OpportunityUpdateSchema(Schema):
    """Schema for updating user-specific opportunity data."""
    status = fields.String(
        required=False,
        validate=validate.OneOf(['new', 'investigating', 'interested', 'dismissed'])
    )
    notes = fields.String(required=False, validate=validate.Length(max=5000))
    is_saved = fields.Boolean(required=False)


class OpportunityResponseSchema(Schema):
    """Schema for opportunity response."""
    id = fields.String()
    title = fields.String()
    description = fields.String()
    problem = fields.String(allow_none=True)
    solution = fields.String(allow_none=True)
    target_market = fields.String(allow_none=True)
    pricing_model = fields.String(allow_none=True)

    # Scores
    score = fields.Integer(allow_none=True)
    problem_score = fields.Integer(allow_none=True)
    feasibility_score = fields.Integer(allow_none=True)
    why_now_score = fields.Integer(allow_none=True)

    # Validation
    is_validated = fields.Boolean()
    revenue_proof = fields.String(allow_none=True)
    competitor_count = fields.Integer()
    mention_count = fields.Integer()

    # Market data
    keyword_volume = fields.String(allow_none=True)
    growth_rate = fields.String(allow_none=True)
    competition_level = fields.String(allow_none=True)

    # Meta
    source_types = fields.List(fields.String())
    cluster_id = fields.String(allow_none=True)
    created_at = fields.DateTime()
    updated_at = fields.DateTime()

    # User-specific data
    user_status = fields.String(allow_none=True)
    user_notes = fields.String(allow_none=True)
    is_saved = fields.Boolean()


class OpportunityDetailSchema(OpportunityResponseSchema):
    """Schema for opportunity detail with competitors."""
    competitors = fields.List(fields.Dict())
    source_links = fields.List(fields.Dict())


class StatsResponseSchema(Schema):
    """Schema for statistics response."""
    total_opportunities = fields.Integer()
    validated_count = fields.Integer()
    avg_score = fields.Float()
    score_distribution = fields.Dict()
    top_sources = fields.List(fields.Dict())
    recent_count = fields.Integer()


class UserProfileSchema(Schema):
    """Schema for user profile."""
    id = fields.String()
    email = fields.Email()
    role = fields.String()
    subscription_status = fields.String()
    subscription_tier_id = fields.String(allow_none=True)
    email_verified = fields.Boolean()
    created_at = fields.DateTime()


class UserProfileUpdateSchema(Schema):
    """Schema for updating user profile."""
    # Add fields that users can update
    # (Currently minimal, can be extended)
    pass


class PaginationMetaSchema(Schema):
    """Schema for pagination metadata."""
    next_cursor = fields.String(allow_none=True)
    has_more = fields.Boolean()
    total_count = fields.Integer()
