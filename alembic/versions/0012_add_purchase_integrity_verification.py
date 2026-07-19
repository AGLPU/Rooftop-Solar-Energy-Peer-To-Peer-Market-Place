"""Add purchase integrity verification - purchase_hash and is_tampered columns

Revision ID: 0012
Revises: 0011
Create Date: 2026-07-20

Purpose: Add purchase data integrity verification using immutable hashes stored on blockchain

The problem we're solving:
  1. Purchase record: energy_kwh=50, price=$100, buyer_id=X
  2. Attacker modifies DB: energy_kwh=100 (falsely increases purchase)
  3. Buyer sees 100 kWh but wallet only has 50 kWh
  
Solution:
  1. Calculate SHA256 hash of purchase data (energy_kwh + price + buyer_id + etc.)
  2. Store this hash immutably on blockchain during purchase
  3. On retrieval/consumption: recalculate hash and verify against blockchain
  4. If mismatch → is_tampered=true → block consumption
  
Fields added:
  - purchase_hash: SHA256 hash of purchase data (stored on blockchain)
  - is_tampered: boolean flag set to true if hash verification fails
"""

from alembic import op
import sqlalchemy as sa


revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add purchase_hash column - stores SHA256 hash from blockchain
    op.add_column(
        "purchases",
        sa.Column("purchase_hash", sa.String(64), nullable=True),
        schema="public"
    )
    
    # Add is_tampered column - false by default, set to true if hash doesn't match
    op.add_column(
        "purchases",
        sa.Column("is_tampered", sa.Boolean(), nullable=False, server_default="false"),
        schema="public"
    )
    
    # Create index on is_tampered for quick filtering
    op.create_index(
        "ix_purchases_is_tampered",
        "purchases",
        ["is_tampered"],
        schema="public"
    )


def downgrade() -> None:
    op.drop_index("ix_purchases_is_tampered", table_name="purchases", schema="public")
    op.drop_column("purchases", "is_tampered", schema="public")
    op.drop_column("purchases", "purchase_hash", schema="public")
