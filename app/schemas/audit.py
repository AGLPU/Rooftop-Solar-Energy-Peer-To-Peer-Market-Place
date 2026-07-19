from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime


def get_etherscan_link(tx_hash: str, network: Optional[str] = None) -> Optional[str]:
    """Generate Etherscan link for a transaction hash based on network"""
    if not tx_hash:
        return None
    
    # Map network names to Etherscan URLs
    network_map = {
        "sepolia": "https://sepolia.etherscan.io/tx/",
        "testnet": "https://sepolia.etherscan.io/tx/",
        "mainnet": "https://etherscan.io/tx/",
        "ethereum": "https://etherscan.io/tx/",
    }
    
    # Default to Sepolia (testnet)
    base_url = network_map.get(network.lower() if network else "sepolia", "https://sepolia.etherscan.io/tx/")
    return f"{base_url}{tx_hash}"


class AuditLogResponse(BaseModel):
    """Response model for a single audit log entry"""
    id: UUID
    event_type: str
    listing_id: UUID
    purchase_id: Optional[UUID] = None
    initiated_by: Optional[UUID] = None
    initiated_by_username: Optional[str] = None
    energy_kwh: Optional[int] = None
    blockchain_tx_hash: Optional[str] = None
    etherscan_link: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime

    class Config:
        from_attributes = True

    @classmethod
    def from_orm_with_user(cls, audit_log, db=None):
        """Custom constructor to include username and etherscan link"""
        from app.config import get_settings
        
        initiated_by_username = None
        if audit_log.initiated_by_user:
            initiated_by_username = audit_log.initiated_by_user.username
        
        details = audit_log.get_details_dict() if audit_log.details else None
        
        # Generate Etherscan link if transaction hash exists
        etherscan_link = None
        if audit_log.blockchain_tx_hash:
            settings = get_settings()
            etherscan_link = get_etherscan_link(audit_log.blockchain_tx_hash, settings.blockchain_network)
        
        return cls(
            id=audit_log.id,
            event_type=audit_log.event_type,
            listing_id=audit_log.listing_id,
            purchase_id=audit_log.purchase_id,
            initiated_by=audit_log.initiated_by,
            initiated_by_username=initiated_by_username,
            energy_kwh=audit_log.energy_kwh,
            blockchain_tx_hash=audit_log.blockchain_tx_hash,
            etherscan_link=etherscan_link,
            details=details,
            timestamp=audit_log.timestamp
        )


class ListingAuditHistoryResponse(BaseModel):
    """Response for listing audit history endpoint"""
    listing_id: UUID
    listing_title: str
    listing_energy_kwh: int
    seller_id: UUID
    seller_username: str
    total_events: int
    events: List[AuditLogResponse]


class PurchaseAuditHistoryResponse(BaseModel):
    """Response for purchase audit history endpoint"""
    purchase_id: UUID
    listing_id: UUID
    buyer_id: UUID
    buyer_username: str
    seller_id: UUID
    seller_username: str
    energy_kwh: int
    total_events: int
    events: List[AuditLogResponse]


class ListingTraceResponse(BaseModel):
    """Detailed trace of a listing's journey through the marketplace"""
    listing_id: UUID
    listing_title: str
    seller_username: str
    energy_kwh: int
    total_events: int
    event_timeline: List[AuditLogResponse]
    summary: Dict[str, Any]  # Summary statistics


class TokenTraceResponse(BaseModel):
    """Complete trace of a token from creation to consumption"""
    token_identifier: str  # "EC-{energy_kwh}-{seller_uuid}"
    listing_id: UUID
    seller_username: str
    energy_kwh: int
    current_status: str  # CREATED, VERIFIED, PURCHASED, CONSUMED, TAMPERED, etc.
    journey: List[Dict[str, Any]]  # Simplified journey steps
    total_events: int
