"""Team schemas for request/response validation."""

from datetime import datetime

from pydantic import BaseModel, Field


# ============== Owner/Member schemas ==============
class OwnerBasic(BaseModel):
    """Basic owner information."""

    id: str
    name: str

    model_config = {"from_attributes": True}


class MemberBasic(BaseModel):
    """Basic member information."""

    id: str
    name: str
    email: str
    avatar: str | None = None
    role: str | None = None  # Role in the team

    model_config = {"from_attributes": True}


# ============== Team schemas ==============
class TeamCreate(BaseModel):
    """Schema for creating a team."""

    name: str
    description: str | None = None


class TeamUpdate(BaseModel):
    """Schema for updating a team."""

    name: str | None = None
    description: str | None = None
    avatar: str | None = None


class TeamResponse(BaseModel):
    """Schema for team response."""

    id: str
    name: str
    description: str | None = None
    avatar: str | None = None
    owner: OwnerBasic
    memberCount: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}


class TeamDetailResponse(TeamResponse):
    """Team response with members."""

    members: list[MemberBasic] = Field(default_factory=list)


class TeamListResponse(BaseModel):
    """Schema for team list response."""

    data: list[TeamResponse]


# ============== Member management schemas ==============
class AddMemberRequest(BaseModel):
    """Schema for adding a member to a team."""

    userId: str
    roleId: str | None = None  # Optional role in the team


class RemoveMemberResponse(BaseModel):
    """Schema for remove member response."""

    message: str
    teamId: str
    userId: str
