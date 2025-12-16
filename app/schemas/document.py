"""Document schemas for request/response validation."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.user import PaginationMeta, UserBasicResponse


# ============== Document schemas ==============
class DocumentCreate(BaseModel):
    """Schema for creating a document."""

    title: str
    content: str
    folderId: str | None = None
    tags: list[str] = Field(default_factory=list)


class DocumentUpdate(BaseModel):
    """Schema for updating a document."""

    title: str | None = None
    content: str | None = None


class DocumentRename(BaseModel):
    """Schema for renaming a document."""

    title: str


class DocumentMove(BaseModel):
    """Schema for moving a document."""

    folderId: str | None = None


class DocumentTagsUpdate(BaseModel):
    """Schema for updating document tags."""

    tags: list[str]


class DocumentShare(BaseModel):
    """Schema for sharing a document."""

    userId: str | None = None
    teamId: str | None = None
    permission: str = "READ"  # READ, EDIT, COMMENT


class DocumentUnshare(BaseModel):
    """Schema for unsharing a document."""

    userId: str | None = None
    teamId: str | None = None


class DocumentResponse(BaseModel):
    """Schema for document response."""

    id: str
    title: str
    content: str
    folderId: str | None = None
    tags: list[str] = Field(default_factory=list)
    author: UserBasicResponse
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DocumentListResponse(BaseModel):
    """Schema for paginated document list response."""

    data: list[DocumentResponse]
    meta: PaginationMeta


class BatchDeleteRequest(BaseModel):
    """Schema for batch delete request."""

    ids: list[str]


class BatchDeleteResponse(BaseModel):
    """Schema for batch delete response."""

    message: str
    deleted_count: int
