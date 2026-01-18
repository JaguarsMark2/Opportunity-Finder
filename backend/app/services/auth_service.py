"""Authentication service for user management."""

import uuid
import os

from sqlalchemy.orm import Session

from app.models import SubscriptionTier, User
from app.redis_client import redis_client
from app.services.email_service import EmailService
from app.utils.auth_helpers import (
    generate_reset_token,
    generate_verification_token,
    hash_password,
    verify_password,
)
from config import settings


class AuthService:
    """Service for authentication operations."""

    def __init__(self, db: Session):
        """Initialize auth service with database session.

        Args:
            db: Database session
        """
        self.db = db
        self.email_service = EmailService()

    def register_user(self, email: str, password: str) -> dict:
        """Register a new user.

        Args:
            email: User email
            password: Plain text password

        Returns:
            Dict with success status and message

        Raises:
            ValueError: If email already exists
        """
        # Check if user exists
        existing = self.db.query(User).filter(User.email == email).first()
        if existing:
            raise ValueError("Email already registered")

        # Create user
        user = User(
            id=str(uuid.uuid4()),
            email=email.lower(),
            password_hash=hash_password(password),
            role='user',
            subscription_status='free',
            email_verified=True
        )

        # Assign free tier (assuming id=1 is free tier)
        free_tier = self.db.query(SubscriptionTier).filter(
            SubscriptionTier.price == 0
        ).first()
        if free_tier:
            user.subscription_tier_id = free_tier.id

        self.db.add(user)
        self.db.commit()

        # Send verification email
        token = generate_verification_token(email)
        verification_url = f"{settings.FRONTEND_URL}/verify-email/{token}"
        self.email_service.send_verification_email(email, verification_url)

        return {
            'success': True,
            'message': 'Registration successful. Please check your email to verify your account.',
            'user_id': user.id
        }

    def login_user(self, email: str, password: str) -> dict:
        """Authenticate user and return tokens.

        Args:
            email: User email
            password: Plain text password

        Returns:
            Dict with access and refresh tokens

        Raises:
            ValueError: If credentials invalid or email not verified
        """
        user = self.db.query(User).filter(User.email == email.lower()).first()

        if not user or not verify_password(password, user.password_hash):
            raise ValueError("Invalid email or password")

        if not user.email_verified:
            raise ValueError("Please verify your email before logging in")

        # Generate tokens (Flask-JWT-Extended handles this)
        # Store refresh token in Redis for revocation
        from flask_jwt_extended import create_access_token, create_refresh_token

        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)

        # Store refresh token in Redis
        refresh_key = f"refresh_token:{user.id}:{refresh_token[:20]}"
        redis_client.setex(
            refresh_key,
            settings.JWT_REFRESH_TOKEN_EXPIRES,
            refresh_token
        )

        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': {
                'id': user.id,
                'email': user.email,
                'role': user.role.value if hasattr(user.role, 'value') else user.role,
                'subscription_status': user.subscription_status.value if hasattr(user.subscription_status, 'value') else user.subscription_status
            }
        }

    def verify_email(self, token: str) -> bool:
        """Verify email using token.

        Args:
            token: Verification token

        Returns:
            True if verification successful

        Raises:
            ValueError: If token invalid
        """
        import jwt
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            if payload.get('type') != 'email_verification':
                raise ValueError("Invalid token type")

            user = self.db.query(User).filter(
                User.email == payload['email'].lower()
            ).first()

            if not user:
                raise ValueError("User not found")

            if user.email_verified:
                return True  # Already verified

            user.email_verified = True
            self.db.commit()

            # Send welcome email
            self.email_service.send_welcome_email(user.email)

            return True

        except jwt.ExpiredSignatureError:
            raise ValueError("Verification link has expired")
        except jwt.InvalidTokenError:
            raise ValueError("Invalid verification link")

    def request_password_reset(self, email: str) -> bool:
        """Request password reset.

        Args:
            email: User email

        Returns:
            True if reset email sent
        """
        user = self.db.query(User).filter(User.email == email.lower()).first()
        if not user:
            # Don't reveal if email exists
            return True

        token = generate_reset_token(email)
        reset_url = f"{settings.FRONTEND_URL}/reset-password/{token}"
        self.email_service.send_password_reset_email(email, reset_url)

        return True

    def reset_password(self, token: str, new_password: str) -> bool:
        """Reset password using token.

        Args:
            token: Reset token
            new_password: New password

        Returns:
            True if password reset successful

        Raises:
            ValueError: If token invalid
        """
        import jwt
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            if payload.get('type') != 'password_reset':
                raise ValueError("Invalid token type")

            user = self.db.query(User).filter(
                User.email == payload['email'].lower()
            ).first()

            if not user:
                raise ValueError("User not found")

            user.password_hash = hash_password(new_password)
            self.db.commit()

            return True

        except jwt.ExpiredSignatureError:
            raise ValueError("Reset link has expired")
        except jwt.InvalidTokenError:
            raise ValueError("Invalid reset link")

    def logout_user(self, user_id: str, refresh_token: str) -> bool:
        """Logout user by invalidating refresh token.

        Args:
            user_id: User ID
            refresh_token: Refresh token to invalidate

        Returns:
            True if logout successful
        """
        # Remove from Redis
        refresh_key = f"refresh_token:{user_id}:{refresh_token[:20]}"
        redis_client.delete(refresh_key)

        # Add to blacklist (optional, for access tokens)
        return True

    def revoke_all_tokens(self, user_id: str) -> bool:
        """Revoke all refresh tokens for a user (admin function).

        Args:
            user_id: User ID

        Returns:
            True if all tokens revoked
        """
        pattern = f"refresh_token:{user_id}:*"
        keys = redis_client.keys(pattern)
        if keys:
            redis_client.delete(*keys)
        return True
