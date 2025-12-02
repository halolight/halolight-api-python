"""User schemas for request/response validation."""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.models.enums import UserStatus


# ============== Role schemas (simplified for user response) ==============
class RoleBasic(BaseModel):
    """Basic role information for embedding in user responses."""

    id: str
    name: str
    label: str

    model_config = {"from_attributes": True}


class PermissionBasic(BaseModel):
    """Basic permission information."""

    id: str
    action: str
    description: str | None = None

    model_config = {"from_attributes": True}


class RoleWithPermissions(RoleBasic):
    """Role with permissions for detailed user responses."""

    permissions: list[str] = Field(default_factory=list)  # List of action strings


# ============== Team schemas (simplified for user response) ==============
class TeamBasic(BaseModel):
    """Basic team information for embedding in user responses."""

    id: str
    name: str
    role: str | None = None  # User's role in the team

    model_config = {"from_attributes": True}


# ============== Pagination ==============
class PaginationMeta(BaseModel):
    """Pagination metadata matching API spec."""

    total: int
    page: int
    limit: int
    totalPages: int


# ============== User schemas ==============
class UserBase(BaseModel):
    """Base user schema with common attributes."""

    email: EmailStr
    name: str


class UserCreate(UserBase):
    """Schema for creating a user."""

    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")
    phone: str | None = None
    username: str | None = None  # Will be auto-generated from email if not provided
    avatar: str | None = None
    status: UserStatus = UserStatus.ACTIVE


class UserUpdate(BaseModel):
    """Schema for updating a user."""

    email: EmailStr | None = None
    name: str | None = None
    password: str | None = Field(None, min_length=8)
    phone: str | None = None
    avatar: str | None = None
    status: UserStatus | None = None
    department: str | None = None
    position: str | None = None
    bio: str | None = None


class UserStatusUpdate(BaseModel):
    """Schema for updating user status only."""

    status: UserStatus


# User response schemas
class UserBasicResponse(BaseModel):
    """Basic user response (for embedding in other responses)."""

    id: str
    email: str
    name: str
    avatar: str | None = None

    model_config = {"from_attributes": True}


class UserResponse(UserBasicResponse):
    """Schema for user response (without password)."""

    username: str
    phone: str | None = None
    status: str
    department: str | None = None
    position: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserDetailResponse(UserResponse):
    """Detailed user response with roles and teams."""

    roles: list[RoleBasic] = Field(default_factory=list)
    teams: list[TeamBasic] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    """Schema for paginated user list response."""

    data: list[UserResponse]
    meta: PaginationMeta


# ============== Authentication schemas ==============
class LoginRequest(BaseModel):
    """Schema for login request."""

    email: EmailStr
    password: str = Field(..., min_length=1)


class RegisterRequest(BaseModel):
    """Schema for registration request."""

    email: EmailStr
    name: str
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")
    phone: str | None = None


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request."""

    refreshToken: str


class ForgotPasswordRequest(BaseModel):
    """Schema for forgot password request."""

    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Schema for reset password request."""

    token: str
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")


class AuthUserResponse(BaseModel):
    """User information in auth response."""

    id: str
    email: str
    name: str
    avatar: str | None = None
    phone: str | None = None
    status: str

    model_config = {"from_attributes": True}


class AuthResponse(BaseModel):
    """Schema for authentication response (login/register)."""

    accessToken: str
    refreshToken: str
    user: AuthUserResponse


class TokenRefreshResponse(BaseModel):
    """Schema for token refresh response."""

    accessToken: str
    refreshToken: str


class LogoutResponse(BaseModel):
    """Schema for logout response."""

    message: str = "Successfully logged out"


class MeResponse(BaseModel):
    """Schema for /auth/me response with full user details."""

    id: str
    email: str
    name: str
    avatar: str | None = None
    phone: str | None = None
    status: str
    roles: list[RoleWithPermissions] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TokenPayload(BaseModel):
    """Schema for JWT token payload."""

    sub: str  # User ID
    email: str
    type: str = "access"  # "access" or "refresh"
    exp: datetime | None = None
    iat: datetime | None = None


# ============== Batch operations ==============
class BatchDeleteRequest(BaseModel):
    """Schema for batch delete request."""

    ids: list[str]


class BatchDeleteResponse(BaseModel):
    """Schema for batch delete response."""

    message: str
    deleted_count: int
