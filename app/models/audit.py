from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Enum as SQLEnum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from uuid import uuid4
import enum
import json

from app.database import Base
from app.config import get_settings

settings = get_settings()


class AuditEventType(str, enum.Enum):
    """Types of events that can be audited"""
    LISTING_CREATED = "LISTING_CREATED"           # New listing created
    LISTING_VERIFIED = "LISTING_VERIFIED"         # Listing verified on blockchain
    LISTING_TAMPERED = "LISTING_TAMPERED"         # Tampering detected
    LISTING_EXPIRED = "LISTING_EXPIRED"           # Listing expired
    LISTING_CANCELLED = "LISTING_CANCELLED"       # Seller cancelled listing
    
    PURCHASE_CREATED = "PURCHASE_CREATED"         # Purchase initiated
    PURCHASE_COMPLETED = "PURCHASE_COMPLETED"     # Tokens transferred to buyer
    PURCHASE_CONSUMED = "PURCHASE_CONSUMED"       # Energy consumed (tokens burned)
    PURCHASE_REFUNDED = "PURCHASE_REFUNDED"       # Refund issued
    PURCHASE_FAILED = "PURCHASE_FAILED"           # Purchase failed
    
    VERIFICATION_REQUESTED = "VERIFICATION_REQUESTED"  # Buyer/Admin requested verify
    BLOCKCHAIN_TX_MINTED = "BLOCKCHAIN_TX_MINTED"      # Tokens minted on-chain


class AuditLog(Base):
    """
    Audit Log Model
    Tracks all significant events related to energy credits/tokens
    Enables tracing the complete lifecycle of energy credits
    """
    __tablename__ = "audit_logs"
    __table_args__ = {"schema": settings.database_schema}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # What happened
    event_type = Column(
        SQLEnum(AuditEventType, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True
    )

    # Which energy credit (listing)
    listing_id = Column(UUID(as_uuid=True), ForeignKey(f"{settings.database_schema}.listings.id"), nullable=False, index=True)

    # Which purchase (if applicable)
    purchase_id = Column(UUID(as_uuid=True), ForeignKey(f"{settings.database_schema}.purchases.id"), nullable=True, index=True)

    # Who initiated the event
    initiated_by = Column(UUID(as_uuid=True), ForeignKey(f"{settings.database_schema}.users.id"), nullable=True)

    # Energy amount involved (kWh)
    energy_kwh = Column(Integer, nullable=True)

    # Blockchain transaction hash
    blockchain_tx_hash = Column(String(66), nullable=True)

    # Event details (JSON for flexibility)
    details = Column(Text, nullable=True)  # JSON string with event-specific details

    # Timestamp when event occurred
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    listing = relationship("Listing", backref="audit_logs")
    purchase = relationship("Purchase", backref="audit_logs")
    initiated_by_user = relationship("User", foreign_keys=[initiated_by], backref="audit_logs")

    def __repr__(self):
        return f"<AuditLog {self.id}: {self.event_type} on listing {self.listing_id}>"

    def get_details_dict(self):
        """Parse JSON details into dict"""
        if self.details:
            try:
                return json.loads(self.details)
            except json.JSONDecodeError:
                return {}
        return {}
