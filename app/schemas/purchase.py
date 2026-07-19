from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from uuid import UUID
from decimal import Decimal
from typing import Optional


class PurchaseCreateRequest(BaseModel):
    """Request to purchase energy from a listing"""
    listing_id: UUID = Field(..., description="ID of the listing to purchase from")
    energy_kwh: int = Field(..., gt=0, description="Amount of energy to purchase in kWh")


class PurchaseResponse(BaseModel):
    """Response for a purchase transaction"""
    id: UUID
    buyer_id: UUID
    seller_id: UUID
    listing_id: UUID
    energy_kwh: int
    price_per_kwh: Decimal
    total_price: Decimal
    status: str
    blockchain_tx_hash: Optional[str] = None   # tx hash when tokens were transferred (purchase)
    consume_tx_hash: Optional[str] = None      # tx hash when tokens were burned (consumed)
    purchase_hash: Optional[str] = None        # SHA256 hash of purchase data for integrity verification
    is_tampered: bool = False                  # True if purchase data was modified after creation
    created_at: datetime
    completed_at: Optional[datetime] = None
    consumed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

    @property
    def can_consume(self) -> bool:
        """Buyer can consume energy only if purchase is completed and not tampered"""
        return self.status == "COMPLETED" and not self.is_tampered

