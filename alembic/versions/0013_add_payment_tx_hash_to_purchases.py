"""Add payment_tx_hash to purchases table for payment tracking

Revision ID: 0013
Revises: 0012
Create Date: 2026-07-20

Purpose: Track ETH payment transfers from buyer to seller on blockchain

This migration adds:
  - payment_tx_hash: Ethereum transaction hash of the payment transfer (ETH from buyer to seller)

This allows complete traceability of both energy token transfers and actual payments.
"""

from alembic import op
import sqlalchemy as sa


revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add payment_tx_hash column - stores Ethereum transaction hash of payment transfer
    op.add_column(
        "purchases",
        sa.Column("payment_tx_hash", sa.String(66), nullable=True),
        schema="public"
    )
    
    # Create index on payment_tx_hash for quick lookup
    op.create_index(
        "ix_purchases_payment_tx_hash",
        "purchases",
        ["payment_tx_hash"],
        schema="public"
    )


def downgrade() -> None:
    op.drop_index("ix_purchases_payment_tx_hash", table_name="purchases", schema="public")
    op.drop_column("purchases", "payment_tx_hash", schema="public")
