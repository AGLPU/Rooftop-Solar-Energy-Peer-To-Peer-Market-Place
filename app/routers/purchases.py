from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.database import get_db, get_read_db
from app.models.user import User
from app.schemas.purchase import (
    PurchaseCreateRequest,
    PurchaseResponse
)
from app.services.purchase_service import PurchaseService, get_purchase_service
from app.utils.auth import get_current_active_user

router = APIRouter(prefix="/purchases", tags=["Purchases"])


# ─── Create Purchase ─────────────────────────────────────────────────────────

@router.post(
    "/",
    response_model=PurchaseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Purchase energy",
    description="Buy energy from a listing"
)
def create_purchase(
    payload: PurchaseCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    svc: PurchaseService = Depends(get_purchase_service)
):
    return svc.create_purchase(db, payload, current_user)


# ─── Get Single Purchase ─────────────────────────────────────────────────────

@router.get(
    "/{purchase_id}",
    response_model=PurchaseResponse,
    summary="Get purchase by ID",
    description="Get details of a specific purchase"
)
def get_purchase(
    purchase_id: UUID,
    db: Session = Depends(get_read_db),
    current_user: User = Depends(get_current_active_user),
    svc: PurchaseService = Depends(get_purchase_service)
):
    return svc.get_purchase(db, purchase_id, current_user)


# ─── Get My Purchases ────────────────────────────────────────────────────────

@router.get(
    "/my-purchases",
    response_model=List[PurchaseResponse],
    summary="Get my purchases",
    description="Get all purchases made by the current user"
)
def get_my_purchases(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_read_db),
    current_user: User = Depends(get_current_active_user),
    svc: PurchaseService = Depends(get_purchase_service)
):
    return svc.get_user_purchases(db, current_user.id, skip=skip, limit=limit)


# ─── Get My Sales ───────────────────────────────────────────────────────���────

@router.get(
    "/my-sales",
    response_model=List[PurchaseResponse],
    summary="Get my sales",
    description="Get all sales made by the current user (as seller)"
)
def get_my_sales(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_read_db),
    current_user: User = Depends(get_current_active_user),
    svc: PurchaseService = Depends(get_purchase_service)
):
    return svc.get_user_sales(db, current_user.id, skip=skip, limit=limit)

