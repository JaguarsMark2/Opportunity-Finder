import os
import sys
from datetime import UTC, datetime

from sqlalchemy import ARRAY, JSON, Boolean, CheckConstraint, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db import Base


class Opportunity(Base):
    """Opportunity model representing validated business opportunities."""

    __tablename__ = "opportunities"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)  # UUID
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    problem: Mapped[str | None] = mapped_column(Text, nullable=True)
    solution: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_market: Mapped[str | None] = mapped_column(Text, nullable=True)
    pricing_model: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Scoring fields
    score: Mapped[int | None] = mapped_column(Integer, CheckConstraint("score >= 0 AND score <= 100"), nullable=True)
    problem_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    feasibility_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    why_now_score: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Validation fields
    is_validated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    revenue_proof: Mapped[str | None] = mapped_column(Text, nullable=True)
    competitor_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    mention_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Market data
    keyword_volume: Mapped[str | None] = mapped_column(String(50), nullable=True)
    growth_rate: Mapped[str | None] = mapped_column(String(50), nullable=True)
    competition_level: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Source tracking
    sources: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # JSONB
    source_types: Mapped[list[str] | None] = mapped_column(ARRAY(String(50)), nullable=True)

    # Meta
    cluster_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)

    __table_args__ = (
        CheckConstraint("score >= 0 AND score <= 100", name="check_score_range"),
    )
