"""create listings table

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-13
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "listings",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("seller_id", UUID(as_uuid=True), sa.ForeignKey("public.users.id"), nullable=False),
        sa.Column("energy_kwh", sa.Integer, nullable=False),
        sa.Column("price_per_kwh", sa.Numeric(10, 6), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.String(1000), nullable=True),
        sa.Column("location", sa.String(200), nullable=True),
        sa.Column(
            "status",
            sa.Enum("active", "sold", "expired", "cancelled", name="listingstatus"),
            nullable=False,
            server_default="active",
        ),
        sa.Column("blockchain_tx_hash", sa.String(66), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=True),
        sa.Column("expires_at", sa.DateTime, nullable=True),
    )
    op.create_index("ix_listings_seller_id", "listings", ["seller_id"])
    op.create_index("ix_listings_status", "listings", ["status"])


def downgrade() -> None:
    op.drop_index("ix_listings_status", table_name="listings")
    op.drop_index("ix_listings_seller_id", table_name="listings")
    op.drop_table("listings")
    op.execute("DROP TYPE IF EXISTS listingstatus")

