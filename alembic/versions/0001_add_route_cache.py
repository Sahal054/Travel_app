"""add route_cache table

Revision ID: a1b2c3d4e5f6
Revises:
Create Date: 2026-07-31
"""
from alembic import op
import sqlalchemy as sa

revision = "a1b2c3d4e5f6"
down_revision = "fc205d912b87"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "route_cache",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("route_hash", sa.String(64), nullable=False),
        sa.Column("encoded_polyline", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_route_cache_route_hash", "route_cache", ["route_hash"], unique=True
    )


def downgrade() -> None:
    op.drop_index("ix_route_cache_route_hash", table_name="route_cache")
    op.drop_table("route_cache")
