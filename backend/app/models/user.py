import os
import sys
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import enum

from app.db import Base


class UserRole(str, enum.Enum):
    """User roles."""
    USER = "user"
    ADMIN = "admin"


class SubscriptionStatus(str, enum.Enum):
    """Subscription statuses."""
    FREE = "free"
    ACTIVE = "active"
    CANCELLED = "cancelled"
    PAST_DUE = "past_due"


class User(Base):
    """User model representing application users."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)  # UUID stored as string
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    role: Mapped[UserRole] = mapped_column(SQLEnum(UserRole), default=UserRole.USER, nullable=False)
    subscription_tier_id: Mapped[int | None] = mapped_column(ForeignKey("subscription_tiers.id"), nullable=True)
    subscription_status: Mapped[SubscriptionStatus] = mapped_column(
        SQLEnum(SubscriptionStatus), default=SubscriptionStatus.FREE, nullable=False, index=True
    )
    stripe_customer_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    stripe_subscription_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)

    # Relationships
    # subscription_tier: Mapped["SubscriptionTier"] = relationship(back_populates="users")
    # user_opportunities: Mapped[list["UserOpportunity"]] = relationship(back_populates="user", cascade="all, delete-orphan")
