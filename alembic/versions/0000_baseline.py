"""baseline — represents schema applied before version control

Revision ID: fc205d912b87
Revises:
Create Date: 2026-07-31
"""
from alembic import op

revision = "fc205d912b87"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass  # schema already exists in DB


def downgrade() -> None:
    pass
