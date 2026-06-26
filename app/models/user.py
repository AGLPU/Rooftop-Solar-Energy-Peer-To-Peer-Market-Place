import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean, Column, DateTime, Enum, String, Text, func
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base
from app.config import get_settings

settings = get_settings()


class UserRole(str, enum.Enum):
    BUYER  = "BUYER"    # purchases solar energy credits
    SELLER = "SELLER"   # lists rooftop solar energy
    ADMIN  = "ADMIN"    # platform admin


class UserStatus(str, enum.Enum):
    ACTIVE   = "ACTIVE"
    INACTIVE = "INACTIVE"
    BANNED   = "BANNED"


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": settings.database_schema}

    # ─── Identity ───────────────────────────────────────────
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)

    # ─── Profile ─────────────────────────────────────────────
    full_name = Column(String(255), nullable=False)
    phone_number = Column(String(20), nullable=True)
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True, default="Canada")

    # ─── Marketplace ─────────────────────────────────────────
    role = Column(Enum(UserRole), nullable=False, default=UserRole.BUYER)
    status = Column(Enum(UserStatus), nullable=False, default=UserStatus.ACTIVE)

    # ─── Blockchain (Ethereum) ───────────────────────────────
    wallet_address = Column(String(42), nullable=True, unique=True)  # 0x + 40 hex chars

    # ─── Auth ────────────────────────────────────────────────
    is_verified = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # ─── Audit ───────────────────────────────────────────────
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    last_login_at = Column(DateTime(timezone=True), nullable=True)

    # ─── Relationships ───────────────────────────────────────
    listings = relationship("Listing", back_populates="seller", foreign_keys="Listing.seller_id")
    purchases = relationship("Purchase", back_populates="buyer", foreign_keys="Purchase.buyer_id")
    sales = relationship("Purchase", back_populates="seller", foreign_keys="Purchase.seller_id")

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email} role={self.role}>"

