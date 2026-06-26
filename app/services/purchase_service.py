from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from typing import List

from app.models.purchase import Purchase, PurchaseStatus
from app.models.listing import Listing, ListingStatus
from app.models.user import User, UserRole
from app.schemas.purchase import PurchaseCreateRequest


class PurchaseService:
    """Service for energy purchase operations"""

    def create_purchase(
        self,
        db: Session,
        payload: PurchaseCreateRequest,
        buyer: User
    ) -> Purchase:
        """Create a new energy purchase"""

        # Verify buyer role
        if buyer.role not in [UserRole.BUYER, UserRole.ADMIN]:
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


def get_purchase_service() -> PurchaseService:
    """Dependency to get purchase service"""
    return PurchaseService()

