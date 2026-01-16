import os
import sys
from datetime import UTC, datetime

from sqlalchemy import JSON, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db import Base


class Scan(Base):
    """Scan model representing data collection runs."""

    __tablename__ = "scans"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)  # 'pending', 'running', 'completed', 'failed'
    progress: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    opportunities_found: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sources_processed: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # JSONB
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
