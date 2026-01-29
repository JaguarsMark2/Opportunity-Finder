"""PendingPost model for holding AI-analyzed posts before consensus is reached.

Posts are stored here temporarily until the clustering pipeline finds
2+ posts describing the same problem, at which point they get promoted
to an Opportunity with SourceLinks.
"""

import os
import sys
from datetime import UTC, datetime

from sqlalchemy import JSON, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db import Base


class PendingPost(Base):
    """Temporary storage for AI-analyzed posts awaiting consensus.

    Posts sit here until the clustering pipeline determines that multiple
    posts describe the same problem. Only then do they get promoted to
    Opportunities with SourceLinks.
    """

    __tablename__ = "pending_posts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    url: Mapped[str] = mapped_column(String(1000), nullable=False, unique=True, index=True)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)

    # AI analysis results
    pain_point: Mapped[str | None] = mapped_column(Text, nullable=True)
    opportunity_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ai_analysis: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Engagement data from source
    engagement_metrics: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Tracking
    scan_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
        index=True,
    )
