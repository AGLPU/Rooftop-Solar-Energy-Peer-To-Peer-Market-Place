"""add tampering detection to listings table

Revision ID: 0007
Revises: 0006
Create Date: 2026-07-16
"""

from alembic import op
import sqlalchemy as sa


revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "listings",
        sa.Column("is_tampered", sa.Boolean(), nullable=False, server_default="false"),
        schema="public"
    )
    op.add_column(
        "listings",
        sa.Column("tampered_at", sa.DateTime(timezone=True), nullable=True),
        schema="public"
    )
    op.add_column(
        "listings",
        sa.Column("tampered_reason", sa.String(500), nullable=True),
        schema="public"
    )


def downgrade() -> None:
    op.drop_column("listings", "tampered_reason", schema="public")
    op.drop_column("listings", "tampered_at", schema="public")
    op.drop_column("listings", "is_tampered", schema="public")
