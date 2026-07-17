from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.database import get_db, get_read_db
from app.models.user import User
from app.models.listing import ListingStatus, EnergySource
from app.schemas.listing import (
    ListingCreateRequest,
    ListingUpdateRequest,
    ListingResponse,
    ListingWithSellerResponse,
    MessageResponse
)
from app.services.listing_service import ListingService, get_listing_service
from app.utils.auth import get_current_active_user, require_admin

router = APIRouter(prefix="/listings", tags=["Listings"])


# ─── Create Listing ──────────────────────────────────────────────────────────

@router.post(
    "/",
    response_model=ListingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new energy listing",
    description=(
        "Create a solar energy listing for sale.\n\n"
        "- **Seller**: creates listing for themselves. Do NOT pass `seller_id`.\n"
        "- **Admin (on behalf of seller)**: pass `seller_id` (the seller's user ID) to create for that seller.\n"
        "- **Admin (for themselves)**: leave `seller_id` empty — listing will be created under the admin's own account."
    )
)
def create_listing(
    payload: ListingCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    svc: ListingService = Depends(get_listing_service)
):
    return svc.create_listing(db, payload, current_user)


# ─── Get All Listings ────────────────────────────────────────────────────────

@router.get(
    "/",
    response_model=List[ListingResponse],
    summary="Get all listings",
    description="Get all energy listings with optional filters. Buyers only see verified listings."
)
def list_listings(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[ListingStatus] = Query(None, description="Filter by status"),
    seller_id: Optional[UUID] = Query(None, description="Filter by seller"),
    energy_source: Optional[EnergySource] = Query(None, description="Filter by energy source (SOLAR, WIND, HYDRO, BIOMASS, GEOTHERMAL, TIDAL, OTHER)"),
    db: Session = Depends(get_read_db),
    svc: ListingService = Depends(get_listing_service),
    current_user: Optional[User] = Depends(get_current_active_user)
):
    return svc.get_all_listings(db, skip=skip, limit=limit, status=status, seller_id=seller_id, energy_source=energy_source, current_user=current_user)


# ─── Get Active Listings ─────────────────────────────────────────────────────

@router.get(
    "/active",
    response_model=List[ListingResponse],
    summary="Get active listings",
    description="Get only active and available energy listings. Buyers only see verified listings."
)
def get_active_listings(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    energy_source: Optional[EnergySource] = Query(None, description="Filter by energy source (SOLAR, WIND, HYDRO, BIOMASS, GEOTHERMAL, TIDAL, OTHER)"),
    db: Session = Depends(get_read_db),
    svc: ListingService = Depends(get_listing_service),
    current_user: Optional[User] = Depends(get_current_active_user)
):
    return svc.get_active_listings(db, skip=skip, limit=limit, energy_source=energy_source, current_user=current_user)


# ─── Get My Listings ─────────────────────────────────────────────────────────

@router.get(
    "/my-listings",
    response_model=List[ListingResponse],
    summary="Get my listings",
    description="Get all listings created by the current user"
)
def get_my_listings(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_read_db),
    current_user: User = Depends(get_current_active_user),
    svc: ListingService = Depends(get_listing_service)
):
    return svc.get_all_listings(db, skip=skip, limit=limit, seller_id=current_user.id, current_user=current_user)


# ─── Get Single Listing ──────────────────────────────────────────────────────

@router.get(
    "/{listing_id}",
    response_model=ListingResponse,
    summary="Get listing by ID",
    description="Get detailed information about a specific listing"
)
def get_listing(
    listing_id: UUID,
    db: Session = Depends(get_read_db),
    svc: ListingService = Depends(get_listing_service)
):
    return svc.get_listing(db, listing_id)


# ─── Update Listing ──────────────────────────────────────────────────────────

@router.patch(
    "/{listing_id}",
    response_model=ListingResponse,
    summary="Update a listing",
    description="Update listing details (owner only)"
)
def update_listing(
    listing_id: UUID,
    payload: ListingUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    svc: ListingService = Depends(get_listing_service)
):
    return svc.update_listing(db, listing_id, payload, current_user)


# ─── Cancel Listing ──────────────────────────────────────────────────────────

@router.post(
    "/{listing_id}/cancel",
    response_model=ListingResponse,
    summary="Cancel a listing",
    description="Cancel an active listing (owner only)"
)
def cancel_listing(
    listing_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    svc: ListingService = Depends(get_listing_service)
):
    return svc.cancel_listing(db, listing_id, current_user)


# ─── Delete Listing ──────────────────────────────────────────────────────────

@router.delete(
    "/{listing_id}",
    response_model=MessageResponse,
    summary="Delete a listing",
    description="Delete a listing (only if no purchases)"
)
def delete_listing(
    listing_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    svc: ListingService = Depends(get_listing_service)
):
    svc.delete_listing(db, listing_id, current_user)
    return MessageResponse(message="Listing deleted successfully")

