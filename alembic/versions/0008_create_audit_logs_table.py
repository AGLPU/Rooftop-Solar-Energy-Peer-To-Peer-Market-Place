"""create audit_logs table

Revision ID: 0008
Revises: 0007
Create Date: 2026-07-19

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("listing_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("purchase_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("initiated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("energy_kwh", sa.Integer(), nullable=True),
        sa.Column("blockchain_tx_hash", sa.String(66), nullable=True),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["listing_id"], ["public.listings.id"], ),
        sa.ForeignKeyConstraint(["purchase_id"], ["public.purchases.id"], ),
        sa.ForeignKeyConstraint(["initiated_by"], ["public.users.id"], ),
        sa.PrimaryKeyConstraint("id"),
        schema="public"
    )
    op.create_index(
        op.f("ix_public_audit_logs_event_type"),
        "audit_logs",
        ["event_type"],
        unique=False,
        schema="public"
    )
    op.create_index(
        op.f("ix_public_audit_logs_listing_id"),
        "audit_logs",
        ["listing_id"],
        unique=False,
        schema="public"
    )
    op.create_index(
        op.f("ix_public_audit_logs_purchase_id"),
        "audit_logs",
        ["purchase_id"],
        unique=False,
        schema="public"
    )
    op.create_index(
        op.f("ix_public_audit_logs_timestamp"),
        "audit_logs",
        ["timestamp"],
        unique=False,
        schema="public"
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_public_audit_logs_timestamp"), table_name="audit_logs", schema="public")
    op.drop_index(op.f("ix_public_audit_logs_purchase_id"), table_name="audit_logs", schema="public")
    op.drop_index(op.f("ix_public_audit_logs_listing_id"), table_name="audit_logs", schema="public")
    op.drop_index(op.f("ix_public_audit_logs_event_type"), table_name="audit_logs", schema="public")
    op.drop_table("audit_logs", schema="public")
