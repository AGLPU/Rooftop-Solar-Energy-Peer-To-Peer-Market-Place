from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

from app.database import get_db
from app.models.user import User, UserRole
from app.models.listing import Listing
from app.models.purchase import Purchase
from app.services.audit_service import AuditService
from app.schemas.audit import (
    AuditLogResponse,
    ListingAuditHistoryResponse,
    PurchaseAuditHistoryResponse,
    ListingTraceResponse
)
from app.utils.auth import get_current_active_user

router = APIRouter(prefix="/api/v1/audit", tags=["audit"])


@router.get(
    "/listing/{listing_id}",
    response_model=ListingAuditHistoryResponse,
    summary="Get audit history for a listing",
    description=(
        "Retrieve the complete audit trail for an energy listing.\n\n"
        "Shows all events including:\n"
        "- When listing was created\n"
        "- When it was verified on blockchain\n"
        "- Any tampering detected\n"
        "- All purchases made\n"
        "- Energy consumed/burned\n\n"
        "Useful for tracking the complete lifecycle of energy credits."
    )
)
def get_listing_audit_history(
    listing_id: UUID,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get audit history for a specific listing"""
    
    # Fetch listing
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found"
        )
    
    # ── ACCESS CONTROL ────────────────────────────────────────────────────
    if current_user.role == UserRole.ADMIN:
        # Admin can view all listings' audit
        pass
    elif current_user.role == UserRole.SELLER:
        # Sellers can only view their own listings' audit
        if listing.seller_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view audit history for your own listings"
            )
    elif current_user.role == UserRole.BUYER:
        # Buyers can only view audit if they purchased from this listing
        has_purchase = db.query(Purchase).filter(
            Purchase.listing_id == listing_id,
            Purchase.buyer_id == current_user.id
        ).first()
        if not has_purchase:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view audit history for listings you have purchased from"
            )
    
    # Get audit logs
    audit_logs = AuditService.get_listing_history(db, listing_id, skip, limit)
    
    # Convert to response models
    events = [AuditLogResponse.from_orm_with_user(log) for log in audit_logs]
    
    return ListingAuditHistoryResponse(
        listing_id=listing.id,
        listing_title=listing.title,
        listing_energy_kwh=listing.energy_kwh,
        seller_id=listing.seller_id,
        seller_username=listing.seller.username,
        total_events=len(audit_logs),
        events=events
    )


@router.get(
    "/purchase/{purchase_id}",
    response_model=PurchaseAuditHistoryResponse,
    summary="Get audit history for a purchase",
    description=(
        "Retrieve the audit trail for a specific energy purchase/transaction.\n\n"
        "Shows:\n"
        "- When purchase was created\n"
        "- When tokens were transferred\n"
        "- When energy was consumed (tokens burned)\n"
        "- All blockchain transactions involved\n\n"
        "Useful for verifying token transfers and energy consumption."
    )
)
def get_purchase_audit_history(
    purchase_id: UUID,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get audit history for a specific purchase"""
    
    # Fetch purchase
    purchase = db.query(Purchase).filter(Purchase.id == purchase_id).first()
    if not purchase:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase not found"
        )
    
    # ── ACCESS CONTROL ────────────────────────────────────────────────────
    if current_user.role == UserRole.ADMIN:
        # Admin can view all purchases' audit
        pass
    elif current_user.role == UserRole.SELLER:
        # Sellers can only view purchases where they are the seller
        if purchase.seller_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view audit history for your own sales"
            )
    elif current_user.role == UserRole.BUYER:
        # Buyers can only view purchases where they are the buyer
        if purchase.buyer_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view audit history for your own purchases"
            )
    
    # Get audit logs
    audit_logs = AuditService.get_purchase_history(db, purchase_id, skip, limit)
    
    # Convert to response models
    events = [AuditLogResponse.from_orm_with_user(log) for log in audit_logs]
    
    return PurchaseAuditHistoryResponse(
        purchase_id=purchase.id,
        listing_id=purchase.listing_id,
        buyer_id=purchase.buyer_id,
        buyer_username=purchase.buyer.username,
        seller_id=purchase.seller_id,
        seller_username=purchase.seller.username,
        energy_kwh=purchase.energy_kwh,
        total_events=len(audit_logs),
        events=events
    )


@router.get(
    "/listing/{listing_id}/trace",
    response_model=ListingTraceResponse,
    summary="Get detailed trace of a listing's journey",
    description=(
        "Get a simplified, human-readable trace of a listing's complete journey:\n\n"
        "- Creation and verification\n"
        "- Tamper detection events\n"
        "- All purchases made from this listing\n"
        "- Energy consumption events\n\n"
        "Includes summary statistics (total purchases, energy sold, etc.)"
    )
)
def get_listing_trace(
    listing_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get detailed trace of a listing's journey"""
    
    # Fetch listing
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found"
        )
    
    # ── ACCESS CONTROL ────────────────────────────────────────────────────
    if current_user.role == UserRole.ADMIN:
        # Admin can view all listings' trace
        pass
    elif current_user.role == UserRole.SELLER:
        # Sellers can only view their own listings' trace
        if listing.seller_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view trace for your own listings"
            )
    elif current_user.role == UserRole.BUYER:
        # Buyers can only view trace if they purchased from this listing
        has_purchase = db.query(Purchase).filter(
            Purchase.listing_id == listing_id,
            Purchase.buyer_id == current_user.id
        ).first()
        if not has_purchase:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view trace for listings you have purchased from"
            )
    
    # Get all audit logs for this listing
    audit_logs = AuditService.get_listing_history(db, listing_id, skip=0, limit=1000)
    
    # Convert to response models
    events = [AuditLogResponse.from_orm_with_user(log) for log in audit_logs]
    
    # Build summary
    summary = {
        "total_energy_kwh": listing.energy_kwh,
        "created_at": listing.created_at,
        "verified": listing.verified,
        "is_tampered": listing.is_tampered,
        "status": listing.status,
        "total_purchases": len([e for e in events if "PURCHASE" in e.event_type]),
        "total_consumed": len([e for e in events if e.event_type == "PURCHASE_CONSUMED"]),
        "tamper_events": len([e for e in events if e.event_type == "LISTING_TAMPERED"]),
    }
    
    return ListingTraceResponse(
        listing_id=listing.id,
        listing_title=listing.title,
        seller_username=listing.seller.username,
        energy_kwh=listing.energy_kwh,
        total_events=len(audit_logs),
        event_timeline=events,
        summary=summary
    )


@router.get(
    "/blockchain-tx/{tx_hash}",
    response_model=List[AuditLogResponse],
    summary="Trace a blockchain transaction",
    description=(
        "Find all audit events related to a specific blockchain transaction hash.\n\n"
        "Useful for:\n"
        "- Verifying token mint transactions\n"
        "- Tracking token transfers\n"
        "- Tracing energy consumption (burn) transactions"
    )
)
def trace_blockchain_transaction(
    tx_hash: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Trace a blockchain transaction across audit logs"""
    
    audit_logs = AuditService.get_blockchain_hash_history(db, tx_hash)
    
    if not audit_logs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No audit events found for transaction {tx_hash}"
        )
    
    # ── ACCESS CONTROL ────────────────────────────────────────────────────
    if current_user.role != UserRole.ADMIN:
        # Non-admin users can only trace transactions they're involved in
        user_involved = False
        
        for audit_log in audit_logs:
            # Check if user initiated this event
            if audit_log.initiated_by == current_user.id:
                user_involved = True
                break
            
            # Check if user is seller of the listing
            if audit_log.listing.seller_id == current_user.id:
                user_involved = True
                break
            
            # Check if user is buyer/seller of the purchase
            if audit_log.purchase:
                if audit_log.purchase.buyer_id == current_user.id or audit_log.purchase.seller_id == current_user.id:
                    user_involved = True
                    break
        
        if not user_involved:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only trace transactions you are involved in"
            )
    
    return [AuditLogResponse.from_orm_with_user(log) for log in audit_logs]
