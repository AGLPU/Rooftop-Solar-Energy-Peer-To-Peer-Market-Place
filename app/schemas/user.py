import re
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

from app.models.user import UserRole, UserStatus

# ─── Wallet address validator ────────────────────────────────────────────────
_ETH_ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")


# ════════════════════════════════════════════════════════════════════════════
# REQUEST schemas
# ════════════════════════════════════════════════════════════════════════════

class UserRegisterRequest(BaseModel):
    """Payload for POST /users/register"""

    email: EmailStr = Field(..., examples=["alice@solar.io"])
    username: str = Field(..., min_length=3, max_length=50, examples=["alice_solar"])
    password: str = Field(..., min_length=8, max_length=128, examples=["Str0ng!Pass"])
    confirm_password: str = Field(..., examples=["Str0ng!Pass"])
    full_name: str = Field(..., min_length=2, max_length=255, examples=["Alice Dupont"])
    phone_number: Optional[str] = Field(None, max_length=20, examples=["+1-514-555-0100"])
    address: Optional[str] = Field(None, examples=["123 Solar St"])
    city: Optional[str] = Field(None, max_length=100, examples=["Montreal"])
    country: Optional[str] = Field("Canada", max_length=100)
    role: UserRole = Field(UserRole.BUYER, examples=["SELLER"])
    wallet_address: Optional[str] = Field(None, examples=["0xAbCd...1234"])

    @field_validator("username")
    @classmethod
    def username_alphanumeric(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z0-9_]+$", v):
            raise ValueError("Username may only contain letters, digits and underscores")
        return v.lower()

    @field_validator("wallet_address")
    @classmethod
    def validate_wallet(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not _ETH_ADDRESS_RE.match(v):
            raise ValueError("wallet_address must be a valid Ethereum address (0x + 40 hex chars)")
        return v

    @model_validator(mode="after")
    def passwords_match(self) -> "UserRegisterRequest":
        if self.password != self.confirm_password:
            raise ValueError("password and confirm_password do not match")
        return self


class UserLoginRequest(BaseModel):
    """Payload for POST /users/login"""

    email: EmailStr = Field(..., examples=["alice@solar.io"])
    password: str = Field(..., examples=["Str0ng!Pass"])


class UserUpdateRequest(BaseModel):
    """Payload for PATCH /users/{id}  — all fields optional"""

    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    phone_number: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    wallet_address: Optional[str] = None

    @field_validator("wallet_address")
    @classmethod
    def validate_wallet(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not _ETH_ADDRESS_RE.match(v):
            raise ValueError("wallet_address must be a valid Ethereum address")
        return v


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)
    confirm_new_password: str

    @model_validator(mode="after")
    def passwords_match(self) -> "ChangePasswordRequest":
        if self.new_password != self.confirm_new_password:
            raise ValueError("new_password and confirm_new_password do not match")
        return self


# ════════════════════════════════════════════════════════════════════════════
# RESPONSE schemas
# ════════════════════════════════════════════════════════════════════════════

class UserResponse(BaseModel):
    """Returned for single-user endpoints"""

    id: uuid.UUID
    email: EmailStr
    username: str
    full_name: str
    phone_number: Optional[str]
    address: Optional[str]
    city: Optional[str]
    country: Optional[str]
    role: UserRole
    status: UserStatus
    wallet_address: Optional[str]
    is_verified: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime]

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """Returned on successful login"""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int          # seconds
    user: UserResponse


class MessageResponse(BaseModel):
    message: str

