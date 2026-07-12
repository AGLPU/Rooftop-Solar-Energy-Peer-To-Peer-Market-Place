"""create purchases table

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-13
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "purchases",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("buyer_id", UUID(as_uuid=True), sa.ForeignKey("public.users.id"), nullable=False),
        sa.Column("seller_id", UUID(as_uuid=True), sa.ForeignKey("public.users.id"), nullable=False),
        sa.Column("listing_id", UUID(as_uuid=True), sa.ForeignKey("public.listings.id"), nullable=False),
        sa.Column("energy_kwh", sa.Integer, nullable=False),
        sa.Column("price_per_kwh", sa.Numeric(10, 6), nullable=False),
        sa.Column("total_price", sa.Numeric(12, 6), nullable=False),
        sa.Column(
            "status",
            sa.Enum("pending", "completed", "failed", "refunded", "consumed", name="purchasestatus"),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("blockchain_tx_hash", sa.String(66), nullable=True),
        sa.Column("consume_tx_hash", sa.String(66), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime, nullable=True),
        sa.Column("consumed_at", sa.DateTime, nullable=True),
    )
    op.create_index("ix_purchases_buyer_id", "purchases", ["buyer_id"])
    op.create_index("ix_purchases_seller_id", "purchases", ["seller_id"])
    op.create_index("ix_purchases_listing_id", "purchases", ["listing_id"])
    op.create_index("ix_purchases_status", "purchases", ["status"])


def downgrade() -> None:
    op.drop_index("ix_purchases_status", table_name="purchases")
    op.drop_index("ix_purchases_listing_id", table_name="purchases")
    op.drop_index("ix_purchases_seller_id", table_name="purchases")
    op.drop_index("ix_purchases_buyer_id", table_name="purchases")
    op.drop_table("purchases")
    op.execute("DROP TYPE IF EXISTS purchasestatus")

