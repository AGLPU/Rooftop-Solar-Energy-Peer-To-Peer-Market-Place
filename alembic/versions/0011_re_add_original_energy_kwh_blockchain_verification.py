"""Re-add original_energy_kwh - store on blockchain for verification

Revision ID: 0011
Revises: 0010
Create Date: 2026-07-19

Reason: CRITICAL - Energy tampering detection requires tracking original energy on blockchain.

The problem we're solving:
  1. Listing: 100 kWh created, stored on blockchain
  2. Buyer purchases 50 kWh
  3. DB updates: energy_kwh = 50 (correct)
  4. Attacker/bug changes DB: energy_kwh = 100 (restored!)
  
  Without original_energy_kwh on blockchain:
    → We can't verify if energy_kwh was tampered with
    → Blockchain snapshot only has immutable fields (price, title, etc.)
    → No record of what ORIGINAL energy was
    → Cannot compute: remaining = original - purchases
    → TAMPERING UNDETECTED!

Solution:
  Store original_energy_kwh on blockchain at creation (immutable).
  On verification:
    - Compute: sum_of_purchases = all completed purchases
    - Verify: energy_kwh == original_energy_kwh - sum_of_purchases
    - If mismatch → TAMPERING DETECTED

This is stored on blockchain, not just in DB, so it's tamper-proof.
"""

from alembic import op
import sqlalchemy as sa


revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "listings",
        sa.Column("original_energy_kwh", sa.Integer(), nullable=True),
        schema="public"
    )
    
    # Backfill: original = current (as-is at this point in time)
    op.execute(
        "UPDATE public.listings SET original_energy_kwh = energy_kwh WHERE original_energy_kwh IS NULL"
    )
    
    # Make non-nullable
    op.alter_column(
        "listings",
        "original_energy_kwh",
        existing_type=sa.Integer(),
        nullable=False,
        schema="public"
    )


def downgrade() -> None:
    op.drop_column("listings", "original_energy_kwh", schema="public")
