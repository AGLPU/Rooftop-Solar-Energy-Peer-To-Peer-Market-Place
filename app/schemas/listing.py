from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from uuid import UUID
from decimal import Decimal
from typing import Optional


# ─── Request Schemas ─────────────────────────────────────────

class ListingCreateRequest(BaseModel):
    """Request to create a new energy listing"""
    energy_kwh: int = Field(..., gt=0, description="Amount of energy in kWh")
    price_per_kwh: Decimal = Field(..., gt=0, description="Price per kWh in ETH")
    title: str = Field(..., min_length=5, max_length=200, description="Listing title")
    description: Optional[str] = Field(None, max_length=1000, description="Listing description")
    location: Optional[str] = Field(None, max_length=200, description="Energy production location")
    expires_at: Optional[datetime] = Field(None, description="When listing expires")


class ListingUpdateRequest(BaseModel):
    """Request to update an existing listing"""
    price_per_kwh: Optional[Decimal] = Field(None, gt=0, description="New price per kWh")
    title: Optional[str] = Field(None, min_length=5, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    location: Optional[str] = Field(None, max_length=200)
    expires_at: Optional[datetime] = None


# ─── Response Schemas ────────────────────────────────────────

class ListingResponse(BaseModel):
    """Response for a single listing"""
    id: UUID
    seller_id: UUID
    energy_kwh: int
    price_per_kwh: Decimal
    title: str
    description: Optional[str]
    location: Optional[str]
    status: str
    blockchain_tx_hash: Optional[str]
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime]

    # Computed fields
    total_price: float
    is_available: bool

    model_config = ConfigDict(from_attributes=True)


class ListingWithSellerResponse(BaseModel):
    """Response with seller information"""
    id: UUID
    seller_id: UUID
    seller_name: str = Field(..., description="Seller's full name")
    seller_wallet: Optional[str] = Field(None, description="Seller's wallet address")
    energy_kwh: int
    price_per_kwh: Decimal
    title: str
    description: Optional[str]
    location: Optional[str]
    status: str
    blockchain_tx_hash: Optional[str]
    created_at: datetime
    expires_at: Optional[datetime]
    total_price: float
    is_available: bool

    model_config = ConfigDict(from_attributes=True)


class MessageResponse(BaseModel):
    """Generic message response"""
    message: str

