import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db, get_read_db
from app.models.user import User
from app.schemas.user import (
    ChangePasswordRequest,
    MessageResponse,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
    UserUpdateRequest,
)
from app.services.user_service import UserService, get_user_service
from app.utils.auth import get_current_active_user, require_admin

router = APIRouter(prefix="/users", tags=["Users"])


# ─── Register ────────────────────────────────────────────────────────────────

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description=(
        "Creates a new buyer, seller, or admin account. "
        "Optionally link an Ethereum wallet address for P2P energy trading."
    ),
)
def register(
    payload: UserRegisterRequest,
    db: Session = Depends(get_db),
    svc: UserService = Depends(get_user_service),
):
    return svc.register(db, payload)


# ─── Login ───────────────────────────────────────────────────────────────────

@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login and receive JWT tokens",
)
def login(
    payload: UserLoginRequest,
    db: Session = Depends(get_db),
    svc: UserService = Depends(get_user_service),
):
    result = svc.login(db, payload.email, payload.password)
    return TokenResponse(
        access_token=result["access_token"],
        refresh_token=result["refresh_token"],
        expires_in=result["expires_in"],
        user=UserResponse.model_validate(result["user"]),
    )

@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Logout and invalidate JWT tokens",
)
def logout(
    payload: UserLoginRequest,
    db: Session = Depends(get_db),
    svc: UserService = Depends(get_user_service),
):
    svc.logout(db, payload.email)
    return MessageResponse(message="Logged out successfully")


# ─── Current user (me) ───────────────────────────────────────────────────────

@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get the currently authenticated user",
)
def get_me(current_user: User = Depends(get_current_active_user)):
    return current_user


# ─── Get all users (admin) ───────────────────────────────────────────────────

@router.get(
    "/",
    response_model=list[UserResponse],
    summary="List all users — Admin only",
)
def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_read_db),  # Use read replica for better performance
    _: User = Depends(require_admin),
    svc: UserService = Depends(get_user_service),
):
    return svc.get_all(db, skip=skip, limit=limit)


# ─── Get user by ID ───────────────────────────────────────────────────────────

@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get user by ID",
)
def get_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_read_db),  # Use read replica for better performance
    current_user: User = Depends(get_current_active_user),
    svc: UserService = Depends(get_user_service),
):
    return svc.get_by_id(db, user_id)


# ─── Update user ──────────────────────────────────────────────────────────────

@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update profile fields",
)
def update_user(
    user_id: uuid.UUID,
    payload: UserUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    svc: UserService = Depends(get_user_service),
):
    return svc.update(db, user_id, payload, current_user)


# ─── Change password ──────────────────────────────────────────────────────────

@router.post(
    "/{user_id}/change-password",
    response_model=MessageResponse,
    summary="Change password",
)
def change_password(
    user_id: uuid.UUID,
    payload: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    svc: UserService = Depends(get_user_service),
):
    svc.change_password(db, user_id, payload, current_user)
    return MessageResponse(message="Password updated successfully")


# ─── Deactivate (soft-delete) ────────────────────────────────────────────────

@router.post(
    "/{user_id}/deactivate",
    response_model=UserResponse,
    summary="Deactivate a user account",
)
def deactivate_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    svc: UserService = Depends(get_user_service),
):
    return svc.deactivate(db, user_id, current_user)


# ─── Hard delete (admin only) ────────────────────────────────────────────────

@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Permanently delete a user — Admin only",
)
def delete_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
    svc: UserService = Depends(get_user_service),
):
    svc.hard_delete(db, user_id)

