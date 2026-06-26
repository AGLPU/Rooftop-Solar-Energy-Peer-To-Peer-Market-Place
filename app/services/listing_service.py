from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from uuid import UUID
from datetime import datetime
from typing import List, Optional

from app.models.listing import Listing, ListingStatus
from app.models.user import User, UserRole
from app.schemas.listing import ListingCreateRequest, ListingUpdateRequest


class ListingService:
    """Service for energy listing operations"""

    def create_listing(
        self,
        db: Session,
        payload: ListingCreateRequest,
        seller: User
    ) -> Listing:
        """Create a new energy listing"""

        # Verify seller role
        if seller.role not in [UserRole.SELLER, UserRole.ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only sellers can create listings"
            )

        # Verify seller has wallet address
        if not seller.wallet_address:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Seller must have a wallet address to create listings"
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

