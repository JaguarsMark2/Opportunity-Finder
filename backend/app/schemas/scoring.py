"""Scoring request/response schemas."""

from marshmallow import Schema, ValidationError, fields, validate, validates


class UpdateWeightsSchema(Schema):
    """Schema for updating scoring weights."""
    demand_frequency = fields.Float(required=True, validate=validate.Range(min=0, max=1))
    revenue_proof = fields.Float(required=True, validate=validate.Range(min=0, max=1))
    competition = fields.Float(required=True, validate=validate.Range(min=0, max=1))
    build_complexity = fields.Float(required=True, validate=validate.Range(min=0, max=1))

    @validates('demand_frequency')
    @validates('revenue_proof')
    @validates('competition')
    @validates('build_complexity')
    def validate_weight_range(self, value):
        """Validate weight is non-negative."""
        if value < 0:
            raise ValidationError("Weight must be non-negative")


class UpdateThresholdsSchema(Schema):
    """Schema for updating validation thresholds."""
    min_revenue_mrr = fields.Integer(required=True, validate=validate.Range(min=0))
    min_mentions = fields.Integer(required=True, validate=validate.Range(min=0))
    min_competitors = fields.Integer(required=True, validate=validate.Range(min=0))


class ScoreBreakdownSchema(Schema):
    """Schema for score breakdown."""
    demand_score = fields.Integer()
    revenue_score = fields.Integer()
    competition_score = fields.Integer()
    complexity_score = fields.Integer()


class ScoringResultSchema(Schema):
    """Schema for scoring result."""
    score = fields.Integer()
    breakdown = fields.Nested(ScoreBreakdownSchema)
    is_validated = fields.Boolean()
    recommendation = fields.String()


class ScoringConfigSchema(Schema):
    """Schema for scoring configuration."""
    weights = fields.Dict(keys=fields.Str(), values=fields.Float())
    thresholds = fields.Dict(keys=fields.Str(), values=fields.Integer())
