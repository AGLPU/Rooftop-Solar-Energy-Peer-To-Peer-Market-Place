"""add original_energy_kwh to listings table

Revision ID: 0009
Revises: 0008
Create Date: 2026-07-19

"""

from alembic import op
import sqlalchemy as sa


revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "listings",
        sa.Column("original_energy_kwh", sa.Integer(), nullable=True),
        schema="public"
    )
    
    # Backfill existing listings: original_energy_kwh = energy_kwh (as-is)
    op.execute(
        "UPDATE public.listings SET original_energy_kwh = energy_kwh WHERE original_energy_kwh IS NULL"
    )
    
    # Now make it non-nullable
    op.alter_column(
        "listings",
        "original_energy_kwh",
        existing_type=sa.Integer(),
        nullable=False,
        schema="public"
    )


def downgrade() -> None:
    op.drop_column("listings", "original_energy_kwh", schema="public")
