from sqlalchemy import Column, String, Integer, Numeric, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from uuid import uuid4
import enum

from app.database import Base
from app.config import get_settings

settings = get_settings()


class ListingStatus(str, enum.Enum):
    """Status of energy listing"""
    ACTIVE = "active"
    SOLD = "sold"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class Listing(Base):
    """
    Energy Listing Model
    Represents solar energy available for sale
    """
    __tablename__ = "listings"
    __table_args__ = {"schema": settings.database_schema}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Seller information
    seller_id = Column(UUID(as_uuid=True), ForeignKey(f"{settings.database_schema}.users.id"), nullable=False)

    # Energy details
    energy_kwh = Column(Integer, nullable=False)  # Amount of energy in kWh
    price_per_kwh = Column(Numeric(10, 6), nullable=False)  # Price per kWh in ETH

    # Listing details
    title = Column(String(200), nullable=False)
    description = Column(String(1000), nullable=True)
    location = Column(String(200), nullable=True)  # City, region

    # Status
    status = Column(SQLEnum(ListingStatus, values_callable=lambda x: [e.value for e in x]), default=ListingStatus.ACTIVE, nullable=False)

    # Blockchain
    blockchain_tx_hash = Column(String(66), nullable=True)  # Ethereum tx hash (0x + 64 chars)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)  # When listing expires

    # Relationships
    seller = relationship("User", back_populates="listings", foreign_keys=[seller_id])
    purchases = relationship("Purchase", back_populates="listing", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Listing {self.id}: {self.energy_kwh} kWh @ {self.price_per_kwh} ETH/kWh>"

    @property
    def total_price(self) -> float:
        """Calculate total price for entire listing"""
        return float(self.energy_kwh * self.price_per_kwh)

    @property
    def is_available(self) -> bool:
        """Check if listing is available for purchase"""
        if self.status != ListingStatus.ACTIVE:
            return False
        if self.expires_at and self.expires_at < datetime.utcnow():
            return False
        return True

