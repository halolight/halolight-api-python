"""User schemas for request/response validation."""
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.models.user import UserRole


# Base schema with common attributes
class UserBase(BaseModel):
    """Base user schema."""

    email: EmailStr
    name: str | None = None


# Schema for user creation
class UserCreate(UserBase):
    """Schema for creating a user."""

    password: str = Field(..., min_length=6, description="Password must be at least 6 characters")


# Schema for user update
class UserUpdate(BaseModel):
    """Schema for updating a user."""

    email: EmailStr | None = None
    name: str | None = None
    password: str | None = Field(None, min_length=6)
    role: UserRole | None = None
    avatar: str | None = None
    status: str | None = None


# Schema for user response (without password)
class UserResponse(UserBase):
    """Schema for user response."""

    id: str
    role: UserRole
    avatar: str | None = None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# Schema for user list response with pagination
class UserListResponse(BaseModel):
    """Schema for paginated user list response."""

    users: list[UserResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# Authentication schemas
class LoginRequest(BaseModel):
    """Schema for login request."""

    email: EmailStr
    password: str = Field(..., min_length=1)


class RegisterRequest(UserCreate):
    """Schema for registration request (same as UserCreate)."""

    pass


class AuthResponse(BaseModel):
    """Schema for authentication response."""

    token: str
    user: UserResponse


class TokenPayload(BaseModel):
    """Schema for JWT token payload."""

    sub: str  # User ID
    email: str
    role: UserRole
    exp: datetime | None = None
    iat: datetime | None = None
