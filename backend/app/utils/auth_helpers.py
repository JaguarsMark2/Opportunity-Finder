"""Authentication helper functions and decorators."""

from datetime import UTC, datetime, timedelta
from functools import wraps

import jwt
from flask import jsonify
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

from config import settings


def hash_password(password: str) -> str:
    """Hash password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        Hashed password
    """
    import bcrypt
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash.

    Args:
        password: Plain text password
        hashed: Hashed password

    Returns:
        True if password matches
    """
    import bcrypt
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


def generate_verification_token(email: str) -> str:
    """Generate email verification token.

    Args:
        email: User email

    Returns:
        JWT token for email verification
    """
    return jwt.encode(
        {
            'email': email,
            'type': 'email_verification',
            'exp': datetime.now(UTC) + timedelta(hours=24)
        },
        settings.SECRET_KEY,
        algorithm='HS256'
    )


def generate_reset_token(email: str) -> str:
    """Generate password reset token.

    Args:
        email: User email

    Returns:
        JWT token for password reset
    """
    return jwt.encode(
        {
            'email': email,
            'type': 'password_reset',
            'exp': datetime.now(UTC) + timedelta(hours=1)
        },
        settings.SECRET_KEY,
        algorithm='HS256'
    )


def admin_required(f):
    """Decorator requiring admin role.

    Args:
        f: Function to decorate

    Returns:
        Decorated function
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        verify_jwt_in_request()
        from app.db import SessionLocal
        from app.models import User

        user_id = get_jwt_identity()
        db = SessionLocal()
        user = db.query(User).filter(User.id == user_id).first()
        db.close()

        if not user or user.role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403

        return f(*args, **kwargs)
    return decorated_function


def get_current_user_id() -> str | None:
    """Get current user ID from JWT.

    Returns:
        User ID or None if not authenticated
    """
    try:
        verify_jwt_in_request(optional=True)
        return get_jwt_identity()  # type: ignore[no-any-return]
    except Exception:
        return None
