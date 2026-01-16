import os
import sys
from datetime import UTC, datetime

from sqlalchemy import JSON, Boolean, DateTime, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db import Base


class SubscriptionTier(Base):
    """Subscription tier model for pricing plans."""

    __tablename__ = "subscription_tiers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    interval: Mapped[str] = mapped_column(String(20), nullable=False)  # 'month' or 'year'
    features: Mapped[dict] = mapped_column(JSON, nullable=False)  # JSONB
    sources_allowed: Mapped[int] = mapped_column(Integer, nullable=False)
    scans_per_month: Mapped[int] = mapped_column(Integer, nullable=False)
    export_limit: Mapped[int] = mapped_column(Integer, nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)

    @property
    def is_active(self) -> bool:
        """Alias for enabled property for backward compatibility."""
        return self.enabled
