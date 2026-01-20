"""Authentication API routes."""

from json import JSONDecodeError

from marshmallow import ValidationError

from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required

from app.db import SessionLocal
from app.schemas.auth import (
    LoginSchema,
    RegisterSchema,
    ResetPasswordRequestSchema,
    ResetPasswordSchema,
)
from app.services.auth_service import AuthService
from app.utils.rate_limit import rate_limit

auth_bp = Blueprint('auth', __name__, url_prefix='/api/v1/auth')


@auth_bp.route('/register', methods=['POST'])
@rate_limit(limit=50, period=3600)  # 5 registrations per hour
def register():
    """Register a new user."""
    try:
        schema = RegisterSchema()
        data = schema.load(request.json)

        db = SessionLocal()
        service = AuthService(db)

        result = service.register_user(data['email'], data['password'])
        db.close()

        return jsonify(result), 201

    except ValidationError as e:
        return jsonify({'error': 'Validation failed', 'details': e.messages}), 400
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception:
        return jsonify({'error': 'Registration failed'}), 500


@auth_bp.route('/login', methods=['POST'])
@rate_limit(limit=50, period=300)  # 50 login attempts per 5 minutes (dev/QA)
def login():
    """Authenticate user."""
    try:
        schema = LoginSchema()
        data = schema.load(request.json)

        db = SessionLocal()
        service = AuthService(db)

        result = service.login_user(data['email'], data['password'])
        db.close()

        return jsonify(result), 200

    except JSONDecodeError:
        return jsonify({'error': 'Invalid JSON'}), 400
    except ValidationError as e:
        return jsonify({'error': 'Validation failed', 'details': e.messages}), 400
    except ValueError as e:
        return jsonify({'error': str(e)}), 401
    except Exception:
        return jsonify({'error': 'Login failed'}), 500


@auth_bp.route('/verify-email/<token>', methods=['GET'])
def verify_email(token):
    """Verify email address."""
    try:
        db = SessionLocal()
        service = AuthService(db)

        service.verify_email(token)
        db.close()

        return jsonify({
            'message': 'Email verified successfully. You can now login.'
        }), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception:
        return jsonify({'error': 'Verification failed'}), 500


@auth_bp.route('/forgot-password', methods=['POST'])
@rate_limit(limit=3, period=3600)  # 3 reset requests per hour
def forgot_password():
    """Request password reset."""
    try:
        schema = ResetPasswordRequestSchema()
        data = schema.load(request.json)

        db = SessionLocal()
        service = AuthService(db)

        # Always return success to prevent email enumeration
        service.request_password_reset(data['email'])
        db.close()

        return jsonify({
            'message': 'If an account exists with this email, a password reset link has been sent.'
        }), 200

    except Exception:
        return jsonify({'error': 'Request failed'}), 500


@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    """Reset password with token."""
    try:
        schema = ResetPasswordSchema()
        data = schema.load(request.json)

        db = SessionLocal()
        service = AuthService(db)

        service.reset_password(data['token'], data['new_password'])
        db.close()

        return jsonify({'message': 'Password reset successfully'}), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception:
        return jsonify({'error': 'Reset failed'}), 500


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token."""
    try:
        current_user_id = get_jwt_identity()

        # Verify refresh token is still in Redis
        auth_header = request.headers.get('Authorization')
        refresh_token = auth_header.split()[1] if auth_header else None

        if refresh_token:
            from app.redis_client import redis_client
            refresh_key = f"refresh_token:{current_user_id}:{refresh_token[:20]}"
            if not redis_client.exists(refresh_key):
                return jsonify({'error': 'Invalid refresh token'}), 401

        new_token = create_access_token(identity=current_user_id)

        return jsonify({'access_token': new_token}), 200

    except Exception:
        return jsonify({'error': 'Token refresh failed'}), 500


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Logout user and invalidate refresh token."""
    try:
        user_id = get_jwt_identity()

        # Get refresh token from request body
        refresh_token = request.json.get('refresh_token')
        if not refresh_token:
            return jsonify({'error': 'Refresh token required'}), 400

        db = SessionLocal()
        service = AuthService(db)

        service.logout_user(user_id, refresh_token)
        db.close()

        return jsonify({'message': 'Logged out successfully'}), 200

    except Exception:
        return jsonify({'error': 'Logout failed'}), 500


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current authenticated user."""
    try:
        user_id = get_jwt_identity()
        db = SessionLocal()
        from app.models import User

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            db.close()
            return jsonify({'error': 'User not found'}), 404

        result = {
            'id': user.id,
            'email': user.email,
            'role': user.role.value if hasattr(user.role, 'value') else user.role,
            'subscription_status': user.subscription_status.value if hasattr(user.subscription_status, 'value') else user.subscription_status,
            'email_verified': user.email_verified
        }
        db.close()

        return jsonify(result), 200

    except Exception:
        return jsonify({'error': 'Failed to get user'}), 500
