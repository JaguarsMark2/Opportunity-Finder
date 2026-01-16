import os
import sys
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db import Base


class UserOpportunity(Base):
    """User-opportunity junction model for user tracking."""

    __tablename__ = "user_opportunities"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    opportunity_id: Mapped[str] = mapped_column(ForeignKey("opportunities.id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), default="new", nullable=False)  # 'new', 'researching', 'building', 'rejected'
    user_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    saved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)

    @property
    def notes(self) -> str | None:
        """Alias for user_notes property for backward compatibility."""
        return self.user_notes

    @notes.setter
    def notes(self, value: str | None) -> None:
        """Setter for notes alias."""
        self.user_notes = value

    @property
    def is_saved(self) -> bool:
        """Alias for saved property for backward compatibility."""
        return self.saved

    @is_saved.setter
    def is_saved(self, value: bool) -> None:
        """Setter for is_saved alias."""
        self.saved = value
