from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from uuid import UUID
from datetime import datetime
from typing import List, Optional

from app.models.listing import Listing, ListingStatus
from app.models.user import User, UserRole
from app.schemas.listing import ListingCreateRequest, ListingUpdateRequest
from app.services.blockchain_service import get_blockchain_service


class ListingService:
    """Service for energy listing operations"""

    def create_listing(
        self,
        db: Session,
        payload: ListingCreateRequest,
        current_user: User
    ) -> Listing:
        """Create a new energy listing.

        - SELLER: creates a listing for themselves.
        - ADMIN: must supply payload.seller_id to create on behalf of that seller.
        """

        # ── Determine the actual seller ────────────────────────────────────
        if current_user.role == UserRole.ADMIN:
            if payload.seller_id:
                # Admin creating ON BEHALF of a specific seller
                seller = db.query(User).filter(User.id == payload.seller_id).first()
                if not seller:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Seller not found"
                    )
                if seller.role != UserRole.SELLER:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Target user is not a seller"
                    )
            else:
                # Admin creating FOR THEMSELVES (no seller_id provided)
                seller = current_user
        elif current_user.role == UserRole.SELLER:
            # Seller always creates for themselves
            seller = current_user
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only sellers or admins can create listings"
            )

        # Verify seller has wallet address
        if not seller.wallet_address:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Seller '{seller.username}' must have a wallet address to create listings"
            )

        # Create listing
        listing = Listing(
            seller_id=seller.id,
            energy_kwh=payload.energy_kwh,
            price_per_kwh=payload.price_per_kwh,
            title=payload.title,
            description=payload.description,
            location=payload.location,
            expires_at=payload.expires_at,
            status=ListingStatus.ACTIVE
        )

        db.add(listing)
        db.commit()
        db.refresh(listing)

        # ── Blockchain: Mint SEC tokens to seller ──────────────────────────
        blockchain = get_blockchain_service()
        listing_hash = blockchain.compute_listing_hash(listing)
        tx_hash = blockchain.mint_energy(
            seller_address=seller.wallet_address,
            energy_kwh=listing.energy_kwh,
            price_per_kwh=listing.price_per_kwh,
            listing_id=str(listing.id),
            listing_hash=listing_hash
        )
        if tx_hash:
            listing.blockchain_tx_hash = tx_hash
            db.commit()
            db.refresh(listing)

        return listing

    def get_listing(self, db: Session, listing_id: UUID) -> Listing:
        """Get a single listing by ID"""
        listing = db.query(Listing).filter(Listing.id == listing_id).first()

        if not listing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Listing not found"
            )

        return listing

    def get_all_listings(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 20,
        status: Optional[ListingStatus] = None,
        seller_id: Optional[UUID] = None
    ) -> List[Listing]:
        """Get all listings with filters"""
        query = db.query(Listing)

        if status:
            query = query.filter(Listing.status == status)

        if seller_id:
            query = query.filter(Listing.seller_id == seller_id)

        # Order by most recent first
        query = query.order_by(Listing.created_at.desc())

        return query.offset(skip).limit(limit).all()

    def get_active_listings(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 20
    ) -> List[Listing]:
        """Get only active, available listings"""
        return db.query(Listing)\
            .filter(Listing.status == ListingStatus.ACTIVE)\
            .filter(
                (Listing.expires_at.is_(None)) |
                (Listing.expires_at > datetime.utcnow())
            )\
            .order_by(Listing.created_at.desc())\
            .offset(skip)\
            .limit(limit)\
            .all()

    def update_listing(
        self,
        db: Session,
        listing_id: UUID,
        payload: ListingUpdateRequest,
        current_user: User
    ) -> Listing:
        """Update a listing"""
        listing = self.get_listing(db, listing_id)

        # Verify ownership
        if listing.seller_id != current_user.id and current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own listings"
            )

        # Update fields if provided
        if payload.price_per_kwh is not None:
            listing.price_per_kwh = payload.price_per_kwh
        if payload.title is not None:
            listing.title = payload.title
        if payload.description is not None:
            listing.description = payload.description
        if payload.location is not None:
            listing.location = payload.location
        if payload.expires_at is not None:
            listing.expires_at = payload.expires_at

        listing.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(listing)

        return listing

    def cancel_listing(
        self,
        db: Session,
        listing_id: UUID,
        current_user: User
    ) -> Listing:
        """Cancel a listing"""
        listing = self.get_listing(db, listing_id)

        # Verify ownership
        if listing.seller_id != current_user.id and current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only cancel your own listings"
            )

        # Check if already cancelled or sold
        if listing.status != ListingStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel listing with status: {listing.status}"
            )

        listing.status = ListingStatus.CANCELLED
        listing.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(listing)

        return listing

    def delete_listing(
        self,
        db: Session,
        listing_id: UUID,
        current_user: User
    ) -> None:
        """Delete a listing (admin only or if no purchases)"""
        listing = self.get_listing(db, listing_id)

        # Only admin or owner can delete
        if listing.seller_id != current_user.id and current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own listings"
            )

        # Check if listing has purchases
        if listing.purchases:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete listing with existing purchases"
            )

        db.delete(listing)
        db.commit()


def get_listing_service() -> ListingService:
    """Dependency to get listing service"""
    return ListingService()

