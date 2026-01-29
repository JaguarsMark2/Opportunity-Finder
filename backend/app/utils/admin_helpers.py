"""Admin authentication and authorization helpers."""

import os
from functools import wraps

from flask import jsonify
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from sqlalchemy.exc import SQLAlchemyError

from app.db import get_db

# DEV MODE: Bypass auth checks for development
DEV_MODE = os.getenv('DEV_MODE', 'true').lower() == 'true'
DEV_ADMIN_ID = "1de75072-3eb7-4bdd-a0a0-ff2016b9960b"


def admin_required():
    """Decorator that requires admin role for endpoint access.

    Returns:
        Decorator function that checks if user has admin role.

    Raises:
        401: If no valid token provided
        403: If user is not an admin
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            # DEV MODE: Bypass JWT verification
            if DEV_MODE:
                user_id = DEV_ADMIN_ID
            else:
                # Verify JWT token first
                verify_jwt_in_request()

                # Get user ID from token
                user_id = get_jwt_identity()
                if not user_id:
                    return jsonify({'error': 'Invalid token'}), 401

            # Check if user has admin role
            db = next(get_db())
            try:
                from app.models.user import User, UserRole

                user = db.query(User).filter(User.id == user_id).first()
                if not user or user.role != UserRole.ADMIN:
                    return jsonify({'error': 'Admin access required'}), 403

            except SQLAlchemyError as e:
                return jsonify({'error': f'Database error: {str(e)}'}), 500

            return fn(*args, **kwargs)
        return wrapper
    return decorator


def validate_admin_access(user_id: str) -> tuple[bool, str | None]:
    """Validate that a user has admin access.

    Args:
        user_id: The user ID to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    db = next(get_db())
    try:
        from app.models.user import User, UserRole

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False, 'User not found'
        if user.role != UserRole.ADMIN:
            return False, 'Admin access required'

        return True, None

    except SQLAlchemyError as e:
        return False, f'Database error: {str(e)}'
