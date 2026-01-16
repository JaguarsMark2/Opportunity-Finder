import os
import sys
from datetime import UTC, datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db import Base


class Competitor(Base):
    """Competitor model representing existing solutions in the market."""

    __tablename__ = "competitors"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    opportunity_id: Mapped[str] = mapped_column(ForeignKey("opportunities.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    revenue_est: Mapped[str | None] = mapped_column(String(100), nullable=True)
    pricing: Mapped[str | None] = mapped_column(String(100), nullable=True)
    features: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # JSONB
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
