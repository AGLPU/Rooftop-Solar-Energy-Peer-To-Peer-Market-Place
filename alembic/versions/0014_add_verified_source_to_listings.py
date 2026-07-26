"""Add verified energy source fields to listings table

Revision ID: 0014
Revises: 0013
Create Date: 2026-07-26

Purpose:
  Listings now require a certified meter/IoT reading ID and its timestamp.
  A seller may list the same source device multiple times (different readings),
  but cannot list the same (source_id, source_timestamp) pair twice — that would
  be selling the same energy reading twice.

Adds:
  - source_id        VARCHAR(100)  — certified meter/IoT reading ID
  - source_timestamp TIMESTAMP     — when the certified reading was taken
  - UNIQUE constraint on (seller_id, source_id, source_timestamp)
"""

from alembic import op
import sqlalchemy as sa


revision = "0014"
down_revision = "0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "listings",
        sa.Column("source_id", sa.String(100), nullable=True),
        schema="public"
    )
    op.add_column(
        "listings",
        sa.Column("source_timestamp", sa.DateTime, nullable=True),
        schema="public"
    )
    # Unique on (seller, source_id, source_timestamp):
    # same meter can have many readings, but each reading can only be listed once
    op.create_unique_constraint(
        "uq_listings_seller_source_ts",
        "listings",
        ["seller_id", "source_id", "source_timestamp"],
        schema="public"
    )


def downgrade() -> None:
    op.drop_constraint("uq_listings_seller_source_ts", "listings", schema="public")
    op.drop_column("listings", "source_timestamp", schema="public")
    op.drop_column("listings", "source_id", schema="public")
