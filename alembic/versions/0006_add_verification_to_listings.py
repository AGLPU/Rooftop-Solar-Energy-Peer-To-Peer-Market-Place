"""add verification fields to listings table

Revision ID: 0006
Revises: 0005
Create Date: 2026-07-16
"""

from alembic import op
import sqlalchemy as sa


revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "listings",
        sa.Column("verified", sa.Boolean(), nullable=False, server_default="false"),
        schema="public"
    )
    op.add_column(
        "listings",
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        schema="public"
    )


def downgrade() -> None:
    op.drop_column("listings", "verified_at", schema="public")
    op.drop_column("listings", "verified", schema="public")
