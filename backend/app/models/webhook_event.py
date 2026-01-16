import os
import sys
from datetime import UTC, datetime

from sqlalchemy import JSON, Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db import Base


class WebhookEvent(Base):
    """Webhook event model for Stripe webhook idempotency."""

    __tablename__ = "webhook_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    stripe_event_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)  # JSONB
    processed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)

    @property
    def event_id(self) -> str:
        """Alias for stripe_event_id property for backward compatibility."""
        return self.stripe_event_id
