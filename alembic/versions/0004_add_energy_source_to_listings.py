"""add energy_source to listings

Revision ID: 0004
Revises: 0003
Create Date: 2026-07-13
"""

from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create the enum type
    op.execute("CREATE TYPE energysource AS ENUM ('SOLAR', 'WIND', 'HYDRO', 'BIOMASS', 'GEOTHERMAL', 'TIDAL', 'OTHER')")

    # Add column with default SOLAR for existing rows
    op.add_column(
        "listings",
        sa.Column(
            "energy_source",
            sa.Enum("SOLAR", "WIND", "HYDRO", "BIOMASS", "GEOTHERMAL", "TIDAL", "OTHER", name="energysource"),
            nullable=False,
            server_default="SOLAR"
        )
    )

    # Create index for filtering by energy source
    op.create_index("ix_listings_energy_source", "listings", ["energy_source"])


def downgrade() -> None:
    op.drop_index("ix_listings_energy_source", table_name="listings")
    op.drop_column("listings", "energy_source")
    op.execute("DROP TYPE IF EXISTS energysource")

