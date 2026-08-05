"""add user auth columns and itineraries table

Revision ID: b2c3d4e5f6a1
Revises: a1b2c3d4e5f6
Create Date: 2025-01-01
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "b2c3d4e5f6a1"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Add auth columns to users ─────────────────────────────────────────────
    op.add_column("users", sa.Column("email", sa.String(255), nullable=True))
    op.add_column("users", sa.Column("hashed_password", sa.String(255), nullable=True))
    op.add_column("users", sa.Column("display_name", sa.String(128), nullable=True))
    op.add_column("users", sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"))
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # ── Create itineraries table ───────────────────────────────────────────────
    op.create_table(
        "itineraries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("destination", sa.String(255), nullable=False),
        sa.Column("budget_level", sa.String(32), nullable=False),
        sa.Column("duration_days", sa.Integer(), nullable=False),
        sa.Column("plan", postgresql.JSONB(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_itineraries_user_id", "itineraries", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_itineraries_user_id", "itineraries")
    op.drop_table("itineraries")
    op.drop_index("ix_users_email", "users")
    op.drop_column("users", "is_active")
    op.drop_column("users", "display_name")
    op.drop_column("users", "hashed_password")
    op.drop_column("users", "email")
