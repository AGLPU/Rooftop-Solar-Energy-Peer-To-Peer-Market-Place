"""Remove original_energy_kwh - use blockchain snapshot instead

Revision ID: 0010
Revises: 0009
Create Date: 2026-07-19

Rationale: Immutable listing data is now stored on blockchain as a snapshot.
The original_energy_kwh field is no longer needed in the database since:
1. Blockchain stores the complete immutable snapshot (price, title, location, etc.)
2. Energy_kwh is legitimately dynamic (changes with purchases)
3. Validation compares against blockchain snapshot instead of DB

This simplifies the model and aligns with blockchain-as-source-of-truth architecture.
"""

from alembic import op
import sqlalchemy as sa


revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("listings", "original_energy_kwh", schema="public")


def downgrade() -> None:
    op.add_column(
        "listings",
        sa.Column("original_energy_kwh", sa.Integer(), nullable=False),
        schema="public"
    )
