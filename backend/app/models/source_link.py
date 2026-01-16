import os
import sys
from datetime import UTC, datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db import Base


class SourceLink(Base):
    """Source link model representing URLs where opportunities were found."""

    __tablename__ = "source_links"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    opportunity_id: Mapped[str] = mapped_column(ForeignKey("opportunities.id", ondelete="CASCADE"), nullable=False, index=True)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # 'reddit', 'indie_hackers', etc.
    url: Mapped[str] = mapped_column(String(1000), nullable=False)
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    engagement_metrics: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # JSONB
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
