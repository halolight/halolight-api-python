"""Document management routes matching API spec."""

import math
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user
from app.core.database import get_db
from app.models import User
from app.schemas.document import (
    BatchDeleteRequest,
    BatchDeleteResponse,
    DocumentCreate,
    DocumentListResponse,
    DocumentMove,
    DocumentRename,
    DocumentResponse,
    DocumentShare,
    DocumentTagsUpdate,
    DocumentUnshare,
    DocumentUpdate,
)
from app.schemas.user import PaginationMeta, UserBasicResponse
from app.services.document_service import DocumentService

router = APIRouter(prefix="/documents", tags=["Documents"])


def _build_document_response(document) -> DocumentResponse:
    """Build document response from model."""
    tags = [dt.tag.name for dt in document.tags] if document.tags else []
    return DocumentResponse(
        id=document.id,
        title=document.title,
        content=document.content,
        folderId=document.folder,
        tags=tags,
        author=UserBasicResponse(
            id=document.owner.id,
            email=document.owner.email,
            name=document.owner.name,
            avatar=document.owner.avatar,
        ),
        created_at=document.created_at,
        updated_at=document.updated_at,
    )


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    folderId: str | None = None,
    tags: str | None = None,
    search: str | None = None,
) -> DocumentListResponse:
    """Get paginated document list.

    Args:
        db: Database session
        current_user: Current authenticated user
        page: Page number
        limit: Items per page
        folderId: Filter by folder ID
        tags: Filter by tags (comma-separated)
        search: Search in title

    Returns:
        Paginated document list
    """
    document_service = DocumentService(db)

    tag_list = tags.split(",") if tags else None

    documents, total = document_service.get_list(
        user_id=current_user.id,
        page=page,
        limit=limit,
        folder_id=folderId,
        tags=tag_list,
        search=search,
    )

    return DocumentListResponse(
        data=[_build_document_response(doc) for doc in documents],
        meta=PaginationMeta(
            total=total,
            page=page,
            limit=limit,
            totalPages=math.ceil(total / limit) if total > 0 else 1,
        ),
    )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> DocumentResponse:
    """Get document by ID.

    Args:
        document_id: Document ID
        db: Database session
        current_user: Current authenticated user

    Returns:
        Document data

    Raises:
        HTTPException: If document not found or access denied
    """
    document_service = DocumentService(db)

    if not document_service.can_access(document_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    document = document_service.get_by_id(document_id)
    return _build_document_response(document)


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_document(
    document_data: DocumentCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> DocumentResponse:
    """Create a new document.

    Args:
        document_data: Document creation data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Created document
    """
    document_service = DocumentService(db)
    document = document_service.create(document_data, current_user.id)

    return _build_document_response(document)


@router.put("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: str,
    document_data: DocumentUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> DocumentResponse:
    """Update document content.

    Args:
        document_id: Document ID
        document_data: Document update data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Updated document

    Raises:
        HTTPException: If document not found or not owner
    """
    document_service = DocumentService(db)

    if not document_service.is_owner(document_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only document owner can update",
        )

    document = document_service.update(document_id, document_data)

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    return _build_document_response(document)


@router.patch("/{document_id}/rename", response_model=DocumentResponse)
async def rename_document(
    document_id: str,
    rename_data: DocumentRename,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> DocumentResponse:
    """Rename document.

    Args:
        document_id: Document ID
        rename_data: New title
        db: Database session
        current_user: Current authenticated user

    Returns:
        Updated document

    Raises:
        HTTPException: If document not found or not owner
    """
    document_service = DocumentService(db)

    if not document_service.is_owner(document_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only document owner can rename",
        )

    document = document_service.rename(document_id, rename_data.title)

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    return _build_document_response(document)


@router.post("/{document_id}/move", response_model=DocumentResponse)
async def move_document(
    document_id: str,
    move_data: DocumentMove,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> DocumentResponse:
    """Move document to folder.

    Args:
        document_id: Document ID
        move_data: Target folder ID
        db: Database session
        current_user: Current authenticated user

    Returns:
        Updated document

    Raises:
        HTTPException: If document not found or not owner
    """
    document_service = DocumentService(db)

    if not document_service.is_owner(document_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only document owner can move",
        )

    document = document_service.move(document_id, move_data.folderId)

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    return _build_document_response(document)


@router.post("/{document_id}/tags", response_model=DocumentResponse)
async def update_document_tags(
    document_id: str,
    tags_data: DocumentTagsUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> DocumentResponse:
    """Update document tags.

    Args:
        document_id: Document ID
        tags_data: New tags
        db: Database session
        current_user: Current authenticated user

    Returns:
        Updated document

    Raises:
        HTTPException: If document not found or not owner
    """
    document_service = DocumentService(db)

    if not document_service.is_owner(document_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only document owner can update tags",
        )

    document = document_service.update_tags(document_id, tags_data.tags)

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    return _build_document_response(document)


@router.post("/{document_id}/share")
async def share_document(
    document_id: str,
    share_data: DocumentShare,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> dict[str, str]:
    """Share document with user or team.

    Args:
        document_id: Document ID
        share_data: Share data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Success message

    Raises:
        HTTPException: If document not found or not owner
    """
    document_service = DocumentService(db)

    if not document_service.is_owner(document_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only document owner can share",
        )

    share = document_service.share(
        document_id,
        user_id=share_data.userId,
        team_id=share_data.teamId,
        permission=share_data.permission,
    )

    if not share:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    return {"message": "Document shared successfully"}


@router.post("/{document_id}/unshare")
async def unshare_document(
    document_id: str,
    unshare_data: DocumentUnshare,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> dict[str, str]:
    """Remove share from document.

    Args:
        document_id: Document ID
        unshare_data: Unshare data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Success message

    Raises:
        HTTPException: If document not found or not owner
    """
    document_service = DocumentService(db)

    if not document_service.is_owner(document_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only document owner can unshare",
        )

    unshared = document_service.unshare(
        document_id,
        user_id=unshare_data.userId,
        team_id=unshare_data.teamId,
    )

    if not unshared:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Share not found",
        )

    return {"message": "Document unshared successfully"}


@router.post("/batch-delete", response_model=BatchDeleteResponse)
async def batch_delete_documents(
    delete_data: BatchDeleteRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> BatchDeleteResponse:
    """Batch delete documents.

    Args:
        delete_data: Document IDs to delete
        db: Database session
        current_user: Current authenticated user

    Returns:
        Delete result
    """
    document_service = DocumentService(db)
    deleted_count = document_service.batch_delete(delete_data.ids, current_user.id)

    return BatchDeleteResponse(
        message=f"Successfully deleted {deleted_count} documents",
        deleted_count=deleted_count,
    )


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> dict[str, str]:
    """Delete document.

    Args:
        document_id: Document ID
        db: Database session
        current_user: Current authenticated user

    Returns:
        Success message

    Raises:
        HTTPException: If document not found or not owner
    """
    document_service = DocumentService(db)

    if not document_service.is_owner(document_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only document owner can delete",
        )

    deleted = document_service.delete(document_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    return {"message": "Document successfully deleted", "id": document_id}
