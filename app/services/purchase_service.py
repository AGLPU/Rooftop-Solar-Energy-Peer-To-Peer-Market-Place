from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from uuid import UUID
from datetime import datetime, timezone
from decimal import Decimal
from typing import List
import json

from app.models.purchase import Purchase, PurchaseStatus
from app.models.listing import Listing, ListingStatus
from app.models.user import User, UserRole
from app.schemas.purchase import PurchaseCreateRequest
from app.services.blockchain_service import get_blockchain_service
from app.services.audit_service import AuditService
from app.models.audit import AuditEventType


class PurchaseService:
    """Service for energy purchase operations"""

    def create_purchase(
        self,
        db: Session,
        payload: PurchaseCreateRequest,
        buyer: User
    ) -> Purchase:
        """Create a new energy purchase"""

        # Verify buyer role — Admin is READ-ONLY and cannot purchase energy
        if buyer.role != UserRole.BUYER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only buyers can purchase energy"
            )

        # Verify buyer has wallet address
        if not buyer.wallet_address:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Buyer must have a wallet address to purchase energy"
            )

        # Get listing
        listing = db.query(Listing).filter(Listing.id == payload.listing_id).first()
        if not listing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Listing not found"
            )

        # Verify listing is available
        if not listing.is_available:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Listing is not available for purchase"
            )

        # Verify listing is not tampered
        if listing.is_tampered:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"This listing has been flagged as tampered and is no longer available for purchase. Reason: {listing.tampered_reason}"
            )

        # Verify buyer is not the seller
        if listing.seller_id == buyer.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot purchase your own listing"
            )

        # Verify sufficient energy available
        if payload.energy_kwh > listing.energy_kwh:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient energy available. Only {listing.energy_kwh} kWh remaining"
            )

        # Calculate total price
        total_price = Decimal(payload.energy_kwh) * listing.price_per_kwh

        # Create purchase
        purchase = Purchase(
            buyer_id=buyer.id,
            seller_id=listing.seller_id,
            listing_id=listing.id,
            energy_kwh=payload.energy_kwh,
            price_per_kwh=listing.price_per_kwh,
            total_price=total_price,
            status=PurchaseStatus.PENDING
        )

        db.add(purchase)

        # Update listing
        listing.energy_kwh -= payload.energy_kwh
        if listing.energy_kwh == 0:
            listing.status = ListingStatus.SOLD

        listing.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(purchase)

        # ── Audit: Log purchase creation ──────────────────────────────────────
        AuditService.log_event(
            db=db,
            event_type=AuditEventType.PURCHASE_CREATED,
            listing_id=listing.id,
            purchase_id=purchase.id,
            energy_kwh=purchase.energy_kwh,
            initiated_by=buyer,
            details={
                "buyer_id": str(purchase.buyer_id),
                "seller_id": str(purchase.seller_id),
                "total_price": str(purchase.total_price)
            }
        )

        # ── Blockchain: Transfer SEC tokens seller → buyer ─────────────────
        # Backend (Account #0 / contract owner) calls recordPurchase().
        # This moves SEC tokens from the seller's wallet to the buyer's wallet.
        # Admin does NOT do this — it is triggered automatically when a purchase happens.
        # This is a WRITE operation: costs gas, signed by contract owner's private key.
        seller = db.query(User).filter(User.id == listing.seller_id).first()
        if seller and seller.wallet_address and buyer.wallet_address:
            blockchain = get_blockchain_service()
            tx_hash = blockchain.record_purchase(
                seller_address=seller.wallet_address,
                buyer_address=buyer.wallet_address,
                energy_kwh=payload.energy_kwh,
                price_eth=total_price
            )
            if tx_hash:
                purchase.blockchain_tx_hash = tx_hash
                purchase.status = PurchaseStatus.COMPLETED
                purchase.completed_at = datetime.utcnow()
                db.commit()
                db.refresh(purchase)
                
                # ── Audit: Log purchase completion ───────────────────────────
                AuditService.log_event(
                    db=db,
                    event_type=AuditEventType.PURCHASE_COMPLETED,
                    listing_id=listing.id,
                    purchase_id=purchase.id,
                    energy_kwh=purchase.energy_kwh,
                    blockchain_tx_hash=tx_hash,
                    initiated_by=None,  # System/blockchain triggered
                    details={"status": "COMPLETED"}
                )

        return purchase

    def get_purchase(self, db: Session, purchase_id: UUID, user: User) -> Purchase:
        """Get a single purchase by ID"""
        purchase = db.query(Purchase).filter(Purchase.id == purchase_id).first()

        if not purchase:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Purchase not found"
            )

        # Verify user is buyer, seller, or admin
        if user.role != UserRole.ADMIN:
            if purchase.buyer_id != user.id and purchase.seller_id != user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only view your own purchases"
                )

        return purchase

    def get_user_purchases(
        self,
        db: Session,
        user_id: UUID,
        skip: int = 0,
        limit: int = 20
    ) -> List[Purchase]:
        """Get all purchases for a user (as buyer)"""
        return db.query(Purchase)\
            .filter(Purchase.buyer_id == user_id)\
            .order_by(Purchase.created_at.desc())\
            .offset(skip)\
            .limit(limit)\
            .all()

    def get_user_sales(
        self,
        db: Session,
        user_id: UUID,
        skip: int = 0,
        limit: int = 20
    ) -> List[Purchase]:
        """Get all sales for a user (as seller)"""
        return db.query(Purchase)\
            .filter(Purchase.seller_id == user_id)\
            .order_by(Purchase.created_at.desc())\
            .offset(skip)\
            .limit(limit)\
            .all()

    def complete_purchase(
        self,
        db: Session,
        purchase_id: UUID,
        blockchain_tx_hash: str
    ) -> Purchase:
        """Mark purchase as completed with blockchain transaction"""
        purchase = db.query(Purchase).filter(Purchase.id == purchase_id).first()

        if not purchase:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Purchase not found"
            )

        if purchase.status != PurchaseStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot complete purchase with status: {purchase.status}"
            )

        purchase.status = PurchaseStatus.COMPLETED
        purchase.blockchain_tx_hash = blockchain_tx_hash
        purchase.completed_at = datetime.utcnow()

        db.commit()
        db.refresh(purchase)

        return purchase

    def fail_purchase(
        self,
        db: Session,
        purchase_id: UUID,
        reason: str = None
    ) -> Purchase:
        """Mark purchase as failed"""
        purchase = db.query(Purchase).filter(Purchase.id == purchase_id).first()

        if not purchase:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Purchase not found"
            )

        if purchase.status != PurchaseStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot fail purchase with status: {purchase.status}"
            )

        purchase.status = PurchaseStatus.FAILED

        # Return energy to listing
        listing = db.query(Listing).filter(Listing.id == purchase.listing_id).first()
        if listing:
            listing.energy_kwh += purchase.energy_kwh
            if listing.status == ListingStatus.SOLD:
                listing.status = ListingStatus.ACTIVE
            listing.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(purchase)

        return purchase


    def consume_purchase(
        self,
        db: Session,
        purchase_id: UUID,
        buyer: User
    ) -> Purchase:
        """
        Buyer marks energy as consumed → SEC tokens are burned on blockchain.

        Only the buyer who owns the purchase can consume it.
        Purchase must be in COMPLETED status before it can be consumed.
        """
        purchase = db.query(Purchase).filter(Purchase.id == purchase_id).first()

        if not purchase:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Purchase not found"
            )

        # Only the buyer themselves can consume
        if purchase.buyer_id != buyer.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the buyer of this purchase can consume the energy"
            )

        # Must be completed before consuming
        if purchase.status != PurchaseStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot consume energy for purchase with status: {purchase.status}. Must be COMPLETED first."
            )

        if not buyer.wallet_address:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Buyer must have a wallet address to consume energy"
            )

        # ── Blockchain: Burn SEC tokens from buyer's wallet ────────────────
        # Backend (Account #0) calls consumeEnergyFor(buyer, kwh)
        # This DESTROYS the tokens — permanent proof that energy was actually used
        blockchain = get_blockchain_service()
        tx_hash = blockchain.consume_energy_for(
            buyer_address=buyer.wallet_address,
            energy_kwh=purchase.energy_kwh
        )

        if tx_hash:
            purchase.consume_tx_hash = tx_hash

        purchase.status = PurchaseStatus.CONSUMED
        purchase.consumed_at = datetime.utcnow()

        db.commit()
        db.refresh(purchase)

        # ── Audit: Log energy consumption ────────────────────────────────────
        AuditService.log_event(
            db=db,
            event_type=AuditEventType.PURCHASE_CONSUMED,
            listing_id=purchase.listing_id,
            purchase_id=purchase.id,
            energy_kwh=purchase.energy_kwh,
            blockchain_tx_hash=purchase.consume_tx_hash,
            initiated_by=buyer,
            details={"consumed_at": str(datetime.now(timezone.utc))}
        )

        return purchase


def get_purchase_service() -> PurchaseService:
    """Dependency to get purchase service"""
    return PurchaseService()

