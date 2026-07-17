from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from uuid import UUID
from datetime import datetime, timezone
from typing import List, Optional

from app.models.listing import Listing, ListingStatus, EnergySource
from app.models.user import User, UserRole
from app.schemas.listing import ListingCreateRequest, ListingUpdateRequest
from app.services.blockchain_service import get_blockchain_service


class ListingService:
    """Service for energy listing operations"""

    def _check_listing_integrity(self, db: Session, listing: Listing) -> bool:
        """
        Verify listing hasn't been tampered with by comparing DB hash to blockchain hash.
        Returns True if intact, False if tampered.
        Updates is_tampered flag if tampering is detected.
        """
        # Only check verified listings with blockchain records
        if not listing.verified or not listing.blockchain_tx_hash:
            return True

        blockchain = get_blockchain_service()
        if not blockchain.is_available():
            return True  # Can't verify if blockchain unavailable

        try:
            # Get listing record from blockchain
            on_chain_listing = blockchain.get_listing_record(str(listing.id))
            if not on_chain_listing:
                return True  # Listing not on chain, can't verify
            
            # Compute current hash from DB state
            current_hash = blockchain.compute_listing_hash(listing)
            on_chain_hash = on_chain_listing.get("listing_hash")
            
            if current_hash != on_chain_hash:
                # Tampering detected - update listing
                listing.is_tampered = True
                listing.tampered_at = datetime.now(timezone.utc)
                listing.tampered_reason = (
                    f"HASH MISMATCH DETECTED: Listing fields were modified after creation. "
                    f"On-chain hash: {on_chain_hash[:16]}... | Current DB hash: {current_hash[:16]}... "
                    f"Modified fields may include: energy_kwh, price_per_kwh, title, description, location, status"
                )
                db.commit()
                return False
            
            # Listing is intact
            if listing.is_tampered:
                # Clear tampering flag if it was previously set but now passes verification
                listing.is_tampered = False
                listing.tampered_at = None
                listing.tampered_reason = None
                db.commit()
            
            return True
        except Exception as e:
            # If verification fails, log but don't fail the query
            return True

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
        # Auto-generate title if not provided: "EC-{energy_kwh}-{first_block_of_seller_uuid}"
        title = payload.title
        if not title:
            seller_uuid_block = str(seller.id).split('-')[0]  # Get first block of UUID (first 8 chars)
            title = f"EC-{payload.energy_kwh}-{seller_uuid_block}"
        
        listing = Listing(
            seller_id=seller.id,
            energy_kwh=payload.energy_kwh,
            price_per_kwh=payload.price_per_kwh,
            energy_source=payload.energy_source,
            title=title,
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
            listing.verified = True  # Auto-verify on successful blockchain mint
            listing.verified_at = datetime.utcnow()
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
        seller_id: Optional[UUID] = None,
        energy_source: Optional[EnergySource] = None,
        current_user: Optional[User] = None
    ) -> List[Listing]:
        """
        Get all listings with filters and real-time integrity verification.
        - Buyers: only see verified + non-tampered listings (checked on-the-fly)
        - Sellers: see their own (verified + unverified) + others' verified
        - Admins: see all listings
        """
        query = db.query(Listing)

        if status:
            query = query.filter(Listing.status == status)
        if seller_id:
            query = query.filter(Listing.seller_id == seller_id)
        if energy_source:
            query = query.filter(Listing.energy_source == energy_source)

        # Visibility logic: buyers only see verified, sellers/admins see all
        if current_user and current_user.role == UserRole.BUYER:
            query = query.filter(Listing.verified == True)
        elif current_user and current_user.role == UserRole.SELLER:
            # Sellers see verified listings OR their own listings (verified + unverified)
            query = query.filter(
                (Listing.verified == True) | (Listing.seller_id == current_user.id)
            )
        # ADMIN sees all listings (no filter)

        query = query.order_by(Listing.created_at.desc())
        listings = query.offset(skip).limit(limit).all()

        # Real-time integrity check for each listing
        filtered_listings = []
        for listing in listings:
            self._check_listing_integrity(db, listing)
            
            # After integrity check, apply visibility filter
            if current_user and current_user.role == UserRole.BUYER:
                # Buyers can't see tampered listings
                if not listing.is_tampered:
                    filtered_listings.append(listing)
            else:
                # Sellers and admins can see all (including tampered)
                filtered_listings.append(listing)

        return filtered_listings

    def get_active_listings(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 20,
        energy_source: Optional[EnergySource] = None,
        current_user: Optional[User] = None
    ) -> List[Listing]:
        """
        Get only active, available listings with real-time integrity verification.
        - Buyers: only see verified + non-tampered listings (checked on-the-fly)
        - Sellers: see their own (verified + unverified) + others' verified
        - Admins: see all listings
        """
        query = db.query(Listing)\
            .filter(Listing.status == ListingStatus.ACTIVE)\
            .filter(
                (Listing.expires_at.is_(None)) |
                (Listing.expires_at > datetime.utcnow())
            )
        if energy_source:
            query = query.filter(Listing.energy_source == energy_source)

        # Visibility logic: buyers only see verified, sellers/admins see all
        if current_user and current_user.role == UserRole.BUYER:
            query = query.filter(Listing.verified == True)
        elif current_user and current_user.role == UserRole.SELLER:
            # Sellers see verified listings OR their own listings (verified + unverified)
            query = query.filter(
                (Listing.verified == True) | (Listing.seller_id == current_user.id)
            )
        # ADMIN sees all listings (no filter)

        listings = query.order_by(Listing.created_at.desc()).offset(skip).limit(limit).all()

        # Real-time integrity check for each listing
        filtered_listings = []
        for listing in listings:
            self._check_listing_integrity(db, listing)
            
            # After integrity check, apply visibility filter
            if current_user and current_user.role == UserRole.BUYER:
                # Buyers can't see tampered listings
                if not listing.is_tampered:
                    filtered_listings.append(listing)
            else:
                # Sellers and admins can see all (including tampered)
                filtered_listings.append(listing)

        return filtered_listings

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

        # ── Block changes to blockchain-immutable fields ───────────────────
        # These fields are recorded on-chain at mint time.
        # Changing them in DB would cause a TAMPERED status on verify.
        blockchain = get_blockchain_service()
        if listing.blockchain_tx_hash and blockchain.is_available():
            if payload.price_per_kwh is not None and payload.price_per_kwh != listing.price_per_kwh:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="price_per_kwh cannot be changed after listing is recorded on blockchain. Cancel and create a new listing."
                )
            if hasattr(payload, 'energy_kwh') and payload.energy_kwh is not None and payload.energy_kwh != listing.energy_kwh:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="energy_kwh cannot be changed after listing is recorded on blockchain. Cancel and create a new listing."
                )
            if payload.location is not None and payload.location != listing.location:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="location cannot be changed after listing is recorded on blockchain. Cancel and create a new listing."
                )
            if hasattr(payload, 'energy_source') and payload.energy_source is not None and payload.energy_source != listing.energy_source:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="energy_source cannot be changed after listing is recorded on blockchain. Cancel and create a new listing."
                )
            if payload.expires_at is not None and listing.expires_at is not None:
                if payload.expires_at < listing.expires_at:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="expires_at cannot be reduced after listing is recorded on blockchain. You can only extend the expiry date."
                    )
                if payload.expires_at != listing.expires_at:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="expires_at is recorded on blockchain and cannot be changed. Cancel and create a new listing with a different expiry."
                    )

        # Update allowed fields only
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

