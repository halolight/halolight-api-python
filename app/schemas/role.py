"""Role and Permission schemas for request/response validation."""

from datetime import datetime

from pydantic import BaseModel, Field


# ============== Permission schemas ==============
class PermissionBase(BaseModel):
    """Base permission schema."""

    action: str = Field(..., alias="name", description="Permission action (e.g., users:read)")
    description: str | None = None


class PermissionCreate(BaseModel):
    """Schema for creating a permission."""

    name: str = Field(..., description="Permission name (e.g., users:read)")
    description: str | None = None


class PermissionResponse(BaseModel):
    """Schema for permission response."""

    id: str
    name: str  # Maps to action field
    description: str | None = None

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_model(cls, obj):
        """Convert from ORM model where field is 'action' to response with 'name'."""
        return cls(id=obj.id, name=obj.action, description=obj.description)


class PermissionListResponse(BaseModel):
    """Schema for permission list response."""

    data: list[PermissionResponse]


# ============== Role schemas ==============
class RoleBase(BaseModel):
    """Base role schema."""

    name: str
    label: str | None = None
    description: str | None = None


class RoleCreate(BaseModel):
    """Schema for creating a role."""

    name: str
    description: str | None = None


class RoleUpdate(BaseModel):
    """Schema for updating a role."""

    name: str | None = None
    label: str | None = None
    description: str | None = None


class RolePermissionAssign(BaseModel):
    """Schema for assigning permissions to a role."""

    permissionIds: list[str]


class RoleResponse(BaseModel):
    """Schema for role response."""

    id: str
    name: str
    label: str | None = None
    description: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class RoleWithPermissionsResponse(RoleResponse):
    """Role response with permissions and user count."""

    permissions: list[PermissionResponse] = Field(default_factory=list)
    userCount: int = 0


class RoleListResponse(BaseModel):
    """Schema for role list response."""

    data: list[RoleWithPermissionsResponse]
