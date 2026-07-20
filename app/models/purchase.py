from sqlalchemy import Column, String, Integer, Numeric, DateTime, ForeignKey, Enum as SQLEnum, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from uuid import uuid4
import enum

from app.database import Base
from app.config import get_settings

settings = get_settings()


class PurchaseStatus(str, enum.Enum):
    """Status of energy purchase"""
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"
    CONSUMED = "CONSUMED"  # Buyer has burned the SEC tokens — energy actually used


class Purchase(Base):
    """
    Energy Purchase Model
    Represents a transaction where buyer purchases energy from seller
    """
    __tablename__ = "purchases"
    __table_args__ = {"schema": settings.database_schema}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Buyer and Seller
    buyer_id = Column(UUID(as_uuid=True), ForeignKey(f"{settings.database_schema}.users.id"), nullable=False)
    seller_id = Column(UUID(as_uuid=True), ForeignKey(f"{settings.database_schema}.users.id"), nullable=False)
    listing_id = Column(UUID(as_uuid=True), ForeignKey(f"{settings.database_schema}.listings.id"), nullable=False)

    # Purchase details
    energy_kwh = Column(Integer, nullable=False)  # Amount purchased
    price_per_kwh = Column(Numeric(10, 6), nullable=False)  # Price at time of purchase
    total_price = Column(Numeric(12, 6), nullable=False)  # Total cost in ETH

    # Status
    status = Column(SQLEnum(PurchaseStatus, values_callable=lambda x: [e.value for e in x]), default=PurchaseStatus.PENDING, nullable=False)

    # Blockchain
    blockchain_tx_hash = Column(String(66), nullable=True)  # Ethereum transaction hash (purchase)
    consume_tx_hash = Column(String(66), nullable=True)      # Ethereum transaction hash (burn)
    payment_tx_hash = Column(String(66), nullable=True)      # Ethereum transaction hash (payment transfer)
    purchase_hash = Column(String(64), nullable=True)        # SHA256 hash of purchase data (immutable proof)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)   # When purchase completed
    consumed_at = Column(DateTime, nullable=True)    # When energy was consumed (tokens burned)
    is_tampered = Column(Boolean, default=False, nullable=False)

    # Relationships
    buyer = relationship("User", foreign_keys=[buyer_id], back_populates="purchases")
    seller = relationship("User", foreign_keys=[seller_id], back_populates="sales")
    listing = relationship("Listing", back_populates="purchases")

    def __repr__(self):
        return f"<Purchase {self.id}: {self.energy_kwh} kWh for {self.total_price} ETH>"

