import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User, UserRole, UserStatus
from app.schemas.user import (
    ChangePasswordRequest,
    UserRegisterRequest,
    UserUpdateRequest,
)
from app.utils.auth import create_access_token, create_refresh_token
from app.utils.hashing import hash_password, verify_password
from app.config import get_settings

settings = get_settings()


class UserService:
    """
    All business logic for user management.
    No HTTP concerns here — only database + domain rules.
    """

    # ─── Register ────────────────────────────────────────────────────────────

    def register(self, db: Session, req: UserRegisterRequest) -> User:
        # 1. uniqueness checks
        if db.query(User).filter(User.email == req.email).first():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Email '{req.email}' is already registered",
            )
        if db.query(User).filter(User.username == req.username).first():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Username '{req.username}' is already taken",
            )
        if req.wallet_address and db.query(User).filter(User.wallet_address == req.wallet_address).first():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Wallet address already linked to another account",
            )

        # 2. create model
        user = User(
            email=req.email,
            username=req.username,
            hashed_password=hash_password(req.password),
            full_name=req.full_name,
            phone_number=req.phone_number,
            address=req.address,
            city=req.city,
            country=req.country or "Canada",
            role=req.role,
            status=UserStatus.ACTIVE,
            wallet_address=req.wallet_address,
            is_verified=False,
            is_active=True,
        )

        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    # ─── Login ───────────────────────────────────────────────────────────────

    def login(self, db: Session, email: str, password: str) -> dict:
        user = db.query(User).filter(User.email == email).first()

        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is inactive. Please contact support.",
            )
        if user.status == UserStatus.BANNED:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account has been banned.",
            )

        # update last_login_at
        user.last_login_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(user)

        access_token  = create_access_token(str(user.id), user.role.value)
        refresh_token = create_refresh_token(str(user.id))

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in": settings.access_token_expire_minutes * 60,
            "user": user,
        }

    # ─── Logout ──────────────────────────────────────────────────────────────

    def logout(self, db: Session, user: User) -> None:
        """
        Handle user logout.
        Updates last_logout_at timestamp and can be extended for token blacklisting.
        """
        user.last_logout_at = datetime.now(timezone.utc)
        db.commit()

    # ─── Get user ────────────────────────────────────────────────────────────

    def get_by_id(self, db: Session, user_id: uuid.UUID) -> User:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return user

    def get_all(self, db: Session, skip: int = 0, limit: int = 20) -> list[User]:
        return db.query(User).offset(skip).limit(limit).all()

    # ─── Update ──────────────────────────────────────────────────────────────

    def update(self, db: Session, user_id: uuid.UUID, req: UserUpdateRequest, current_user: User) -> User:
        user = self.get_by_id(db, user_id)

        # only self or admin can update
        if current_user.id != user.id and current_user.role != UserRole.ADMIN:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorised")

        # wallet uniqueness check
        if req.wallet_address and req.wallet_address != user.wallet_address:
            conflict = db.query(User).filter(User.wallet_address == req.wallet_address).first()
            if conflict:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Wallet address already linked to another account",
                )

        update_data = req.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)

        db.commit()
        db.refresh(user)
        return user

    # ─── Change password ─────────────────────────────────────────────────────

    def change_password(self, db: Session, user_id: uuid.UUID, req: ChangePasswordRequest, current_user: User) -> User:
        user = self.get_by_id(db, user_id)

        if current_user.id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorised")

        if not verify_password(req.current_password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")

        user.hashed_password = hash_password(req.new_password)
        db.commit()
        db.refresh(user)
        return user

    # ─── Deactivate / Delete ──────────────────────────────────────────────────

    def deactivate(self, db: Session, user_id: uuid.UUID, current_user: User) -> User:
        user = self.get_by_id(db, user_id)

        if current_user.id != user.id and current_user.role != UserRole.ADMIN:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorised")

        user.is_active = False
        user.status = UserStatus.INACTIVE
        db.commit()
        db.refresh(user)
        return user

    def hard_delete(self, db: Session, user_id: uuid.UUID) -> None:
        """Admin-only hard delete."""
        user = self.get_by_id(db, user_id)
        db.delete(user)
        db.commit()


# singleton — injected via Depends
user_service = UserService()


def get_user_service() -> UserService:
    return user_service

