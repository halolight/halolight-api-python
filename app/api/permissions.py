"""Permission management routes matching API spec."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user
from app.core.database import get_db
from app.models import User
from app.schemas.role import (
    PermissionCreate,
    PermissionListResponse,
    PermissionResponse,
)
from app.services.role_service import PermissionService

router = APIRouter(prefix="/permissions", tags=["Permissions"])


@router.get("", response_model=PermissionListResponse)
async def list_permissions(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> PermissionListResponse:
    """Get all permissions.

    Args:
        db: Database session
        current_user: Current authenticated user

    Returns:
        List of all permissions
    """
    permission_service = PermissionService(db)
    permissions = permission_service.get_all()

    return PermissionListResponse(data=[PermissionResponse.from_orm_model(p) for p in permissions])


@router.get("/{permission_id}", response_model=PermissionResponse)
async def get_permission(
    permission_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> PermissionResponse:
    """Get permission by ID.

    Args:
        permission_id: Permission ID
        db: Database session
        current_user: Current authenticated user

    Returns:
        Permission data

    Raises:
        HTTPException: If permission not found
    """
    permission_service = PermissionService(db)
    permission = permission_service.get_by_id(permission_id)

    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found",
        )

    return PermissionResponse.from_orm_model(permission)


@router.post("", response_model=PermissionResponse, status_code=status.HTTP_201_CREATED)
async def create_permission(
    permission_data: PermissionCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> PermissionResponse:
    """Create a new permission.

    Args:
        permission_data: Permission creation data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Created permission

    Raises:
        HTTPException: If permission with action already exists
    """
    permission_service = PermissionService(db)

    try:
        permission = permission_service.create(permission_data)
        return PermissionResponse.from_orm_model(permission)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        ) from e


@router.delete("/{permission_id}")
async def delete_permission(
    permission_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> dict[str, str]:
    """Delete permission.

    Args:
        permission_id: Permission ID
        db: Database session
        current_user: Current authenticated user

    Returns:
        Success message

    Raises:
        HTTPException: If permission not found
    """
    permission_service = PermissionService(db)
    deleted = permission_service.delete(permission_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found",
        )

    return {"message": "Permission successfully deleted", "id": permission_id}
