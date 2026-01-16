"""Authentication request/response schemas."""

from marshmallow import Schema, ValidationError, fields, validate, validates


class RegisterSchema(Schema):
    """Schema for user registration."""
    email = fields.Email(required=True)
    password = fields.Str(
        required=True,
        validate=validate.Length(min=8, max=128),
        error_messages={'required': 'Password is required'}
    )

    @validates('password')
    def validate_password_strength(self, value):
        """Validate password strength."""
        if not any(c.isupper() for c in value):
            raise ValidationError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in value):
            raise ValidationError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in value):
            raise ValidationError('Password must contain at least one digit')


class LoginSchema(Schema):
    """Schema for user login."""
    email = fields.Email(required=True)
    password = fields.Str(required=True)


class ResetPasswordRequestSchema(Schema):
    """Schema for password reset request."""
    email = fields.Email(required=True)


class ResetPasswordSchema(Schema):
    """Schema for password reset."""
    token = fields.Str(required=True)
    new_password = fields.Str(
        required=True,
        validate=validate.Length(min=8, max=128)
    )


class RefreshTokenSchema(Schema):
    """Schema for token refresh."""
    refresh_token = fields.Str(required=True)


class UserResponseSchema(Schema):
    """Schema for user response."""
    id = fields.Str()
    email = fields.Email()
    role = fields.Str()
    subscription_status = fields.Str()


class AuthResponseSchema(Schema):
    """Schema for auth response with tokens."""
    access_token = fields.Str()
    refresh_token = fields.Str()
    user = fields.Nested(UserResponseSchema)
