from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from uuid import UUID
from decimal import Decimal
from typing import Optional
from app.models.listing import EnergySource


class ListingCreateRequest(BaseModel):
    """Request to create a new energy listing"""
    energy_kwh: int = Field(..., gt=0, description="Amount of energy in kWh")
    price_per_kwh: Decimal = Field(..., gt=0, description="Price per kWh in ETH")
    energy_source: EnergySource = Field(EnergySource.SOLAR, description="Type of renewable energy source")
    title: Optional[str] = Field(None, min_length=5, max_length=200, description="Listing title (auto-generated if not provided)")
    description: Optional[str] = Field(None, max_length=1000, description="Listing description")
    location: Optional[str] = Field(None, max_length=200, description="Energy production location")
    expires_at: Optional[datetime] = Field(None, description="When listing expires")
    seller_id: Optional[UUID] = Field(None, description="[Admin only] Target seller's user ID")


class ListingUpdateRequest(BaseModel):
    """Request to update an existing listing"""
    price_per_kwh: Optional[Decimal] = Field(None, gt=0, description="New price per kWh")
    title: Optional[str] = Field(None, min_length=5, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    location: Optional[str] = Field(None, max_length=200)
    expires_at: Optional[datetime] = None


class ListingResponse(BaseModel):
    """Response for a single listing"""
    id: UUID
    seller_id: UUID
    energy_kwh: int
    price_per_kwh: Decimal
    energy_source: EnergySource
    title: str
    description: Optional[str]
    location: Optional[str]
    status: str
    blockchain_tx_hash: Optional[str]
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime]
    total_price: float
    is_available: bool

    model_config = ConfigDict(from_attributes=True)


class SellerInfo(BaseModel):
    """Seller information for listings"""
    id: UUID
    username: str
    email: str
    role: str


class ListingWithSellerResponse(BaseModel):
    """Response for listing with seller details"""
    id: UUID
    seller_id: UUID
    seller: SellerInfo
    energy_kwh: int
    price_per_kwh: Decimal
    energy_source: EnergySource
    title: str
    description: Optional[str]
    location: Optional[str]
    status: str
    blockchain_tx_hash: Optional[str]
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime]
    total_price: float
    is_available: bool

    model_config = ConfigDict(from_attributes=True)


class ListingListResponse(BaseModel):
    """Response for a list of listings with pagination"""
    listings: list[ListingResponse]
    total: int
    page: int
    page_size: int
    has_more: bool

    model_config = ConfigDict(from_attributes=True)


class MessageResponse(BaseModel):
    """Generic message response"""
    message: str

