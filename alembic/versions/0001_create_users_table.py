"""create users table

Revision ID: 0001
Revises:
Create Date: 2026-06-22
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
import uuid

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("username", sa.String(100), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        # profile
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("phone_number", sa.String(20), nullable=True),
        sa.Column("address", sa.Text, nullable=True),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("country", sa.String(100), nullable=True, server_default="Canada"),
        # marketplace
        sa.Column(
            "role",
            sa.Enum("BUYER", "SELLER", "ADMIN", name="userrole"),
            nullable=False,
            server_default="BUYER",
        ),
        sa.Column(
            "status",
            sa.Enum("ACTIVE", "INACTIVE", "BANNED", name="userstatus"),
            nullable=False,
            server_default="ACTIVE",
        ),
        # blockchain
        sa.Column("wallet_address", sa.String(42), nullable=True, unique=True),
        # auth
        sa.Column("is_verified", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        # audit
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_username", "users", ["username"])


def downgrade() -> None:
    op.drop_index("ix_users_username", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
    op.execute("DROP TYPE IF EXISTS userrole")
    op.execute("DROP TYPE IF EXISTS userstatus")

