"""Admin authentication and authorization helpers."""

from functools import wraps

from flask import jsonify
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from sqlalchemy.exc import SQLAlchemyError

from app.db import get_db


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
            # Verify JWT token first
            verify_jwt_in_request()

            # Get user ID from token
            user_id = get_jwt_identity()
            if not user_id:
                return jsonify({'error': 'Invalid token'}), 401

            # Check if user has admin role
            db = next(get_db())
            try:
                from app.models.user import User

                user = db.query(User).filter(User.id == user_id).first()
                if not user or user.role != 'admin':
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
        from app.models.user import User

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False, 'User not found'
        if user.role != 'admin':
            return False, 'Admin access required'

        return True, None

    except SQLAlchemyError as e:
        return False, f'Database error: {str(e)}'
