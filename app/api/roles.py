"""Role management routes matching API spec."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user
from app.core.database import get_db
from app.models import User
from app.schemas.role import (
    PermissionResponse,
    RoleCreate,
    RoleListResponse,
    RolePermissionAssign,
    RoleUpdate,
    RoleWithPermissionsResponse,
)
from app.services.role_service import RoleService

router = APIRouter(prefix="/roles", tags=["Roles"])


@router.get("", response_model=RoleListResponse)
async def list_roles(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> RoleListResponse:
    """Get all roles with permissions and user count.

    Args:
        db: Database session
        current_user: Current authenticated user

    Returns:
        List of all roles
    """
    role_service = RoleService(db)
    roles = role_service.get_all(with_permissions=True)

    role_responses = []
    for role in roles:
        permissions = [PermissionResponse.from_orm_model(rp.permission) for rp in role.permissions]
        user_count = role_service.get_user_count(role.id)
        role_responses.append(
            RoleWithPermissionsResponse(
                id=role.id,
                name=role.name,
                label=role.label,
                description=role.description,
                created_at=role.created_at,
                permissions=permissions,
                userCount=user_count,
            )
        )

    return RoleListResponse(data=role_responses)


@router.get("/{role_id}", response_model=RoleWithPermissionsResponse)
async def get_role(
    role_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> RoleWithPermissionsResponse:
    """Get role by ID with permissions.

    Args:
        role_id: Role ID
        db: Database session
        current_user: Current authenticated user

    Returns:
        Role data with permissions

    Raises:
        HTTPException: If role not found
    """
    role_service = RoleService(db)
    role = role_service.get_by_id(role_id, with_permissions=True)

    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )

    permissions = [PermissionResponse.from_orm_model(rp.permission) for rp in role.permissions]
    user_count = role_service.get_user_count(role.id)

    return RoleWithPermissionsResponse(
        id=role.id,
        name=role.name,
        label=role.label,
        description=role.description,
        created_at=role.created_at,
        permissions=permissions,
        userCount=user_count,
    )


@router.post("", response_model=RoleWithPermissionsResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    role_data: RoleCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> RoleWithPermissionsResponse:
    """Create a new role.

    Args:
        role_data: Role creation data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Created role

    Raises:
        HTTPException: If role with name already exists
    """
    role_service = RoleService(db)

    try:
        role = role_service.create(role_data)
        return RoleWithPermissionsResponse(
            id=role.id,
            name=role.name,
            label=role.label,
            description=role.description,
            created_at=role.created_at,
            permissions=[],
            userCount=0,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        ) from e


@router.patch("/{role_id}", response_model=RoleWithPermissionsResponse)
async def update_role(
    role_id: str,
    role_data: RoleUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> RoleWithPermissionsResponse:
    """Update role information.

    Args:
        role_id: Role ID
        role_data: Role update data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Updated role

    Raises:
        HTTPException: If role not found
    """
    role_service = RoleService(db)
    role = role_service.update(role_id, role_data)

    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )

    # Reload with permissions
    role = role_service.get_by_id(role_id, with_permissions=True)
    permissions = [PermissionResponse.from_orm_model(rp.permission) for rp in role.permissions]
    user_count = role_service.get_user_count(role.id)

    return RoleWithPermissionsResponse(
        id=role.id,
        name=role.name,
        label=role.label,
        description=role.description,
        created_at=role.created_at,
        permissions=permissions,
        userCount=user_count,
    )


@router.post("/{role_id}/permissions", response_model=RoleWithPermissionsResponse)
async def assign_permissions(
    role_id: str,
    permission_data: RolePermissionAssign,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> RoleWithPermissionsResponse:
    """Assign permissions to a role.

    Args:
        role_id: Role ID
        permission_data: Permission IDs to assign
        db: Database session
        current_user: Current authenticated user

    Returns:
        Updated role with permissions

    Raises:
        HTTPException: If role not found
    """
    role_service = RoleService(db)
    role = role_service.assign_permissions(role_id, permission_data.permissionIds)

    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )

    permissions = [PermissionResponse.from_orm_model(rp.permission) for rp in role.permissions]
    user_count = role_service.get_user_count(role.id)

    return RoleWithPermissionsResponse(
        id=role.id,
        name=role.name,
        label=role.label,
        description=role.description,
        created_at=role.created_at,
        permissions=permissions,
        userCount=user_count,
    )


@router.delete("/{role_id}")
async def delete_role(
    role_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> dict[str, str]:
    """Delete role.

    Args:
        role_id: Role ID
        db: Database session
        current_user: Current authenticated user

    Returns:
        Success message

    Raises:
        HTTPException: If role not found
    """
    role_service = RoleService(db)
    deleted = role_service.delete(role_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )

    return {"message": "Role successfully deleted", "id": role_id}
