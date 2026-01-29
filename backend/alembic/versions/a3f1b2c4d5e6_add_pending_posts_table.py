"""Add pending_posts table for consensus-based clustering

Revision ID: a3f1b2c4d5e6
Revises: c70a8bb38236
Create Date: 2026-01-29 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a3f1b2c4d5e6'
down_revision: Union[str, None] = 'c70a8bb38236'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create pending_posts table."""
    op.create_table(
        'pending_posts',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('url', sa.String(1000), nullable=False, unique=True),
        sa.Column('source_type', sa.String(50), nullable=False),
        sa.Column('pain_point', sa.Text(), nullable=True),
        sa.Column('opportunity_name', sa.String(200), nullable=True),
        sa.Column('category', sa.String(100), nullable=True),
        sa.Column('ai_analysis', sa.JSON(), nullable=True),
        sa.Column('engagement_metrics', sa.JSON(), nullable=True),
        sa.Column('scan_id', sa.String(36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('now()')),
    )
    op.create_index('ix_pending_posts_url', 'pending_posts', ['url'])
    op.create_index('ix_pending_posts_scan_id', 'pending_posts', ['scan_id'])
    op.create_index('ix_pending_posts_created_at', 'pending_posts', ['created_at'])


def downgrade() -> None:
    """Drop pending_posts table."""
    op.drop_index('ix_pending_posts_created_at', table_name='pending_posts')
    op.drop_index('ix_pending_posts_scan_id', table_name='pending_posts')
    op.drop_index('ix_pending_posts_url', table_name='pending_posts')
    op.drop_table('pending_posts')
