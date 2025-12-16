"""User management routes matching API spec."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user
from app.core.database import get_db
from app.models import User
from app.schemas.user import (
    BatchDeleteRequest,
    BatchDeleteResponse,
    PaginationMeta,
    UserCreate,
    UserDetailResponse,
    UserListResponse,
    UserResponse,
    UserStatusUpdate,
    UserUpdate,
)
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=UserListResponse)
async def list_users(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    search: str | None = Query(None, description="Search keyword (name, username, email)"),
    status: str | None = Query(
        None, description="Filter by status (ACTIVE/INACTIVE/SUSPENDED/all)"
    ),
    role: str | None = Query(None, description="Filter by role name (or 'all')"),
) -> UserListResponse:
    """Get user list with pagination, search, and filtering.

    Args:
        db: Database session
        current_user: Current authenticated user
        page: Page number (1-indexed)
        limit: Number of users per page
        search: Search keyword for name, username, or email
        status: Filter by user status
        role: Filter by role name

    Returns:
        Paginated list of users
    """
    user_service = UserService(db)

    # Get users with filtering
    users, total = user_service.get_all(
        page=page,
        limit=limit,
        search=search,
        status=status,
        role=role,
    )

    # Calculate pagination metadata
    pagination = user_service.calculate_pagination(total, page, limit)

    return UserListResponse(
        data=[UserResponse.model_validate(user) for user in users],
        meta=PaginationMeta(
            total=pagination["total"],
            page=pagination["page"],
            limit=pagination["limit"],
            totalPages=pagination["totalPages"],
        ),
    )


@router.get("/{user_id}", response_model=UserDetailResponse)
async def get_user(
    user_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> UserDetailResponse:
    """Get user by ID with roles and teams.

    Args:
        user_id: User ID
        db: Database session
        current_user: Current authenticated user

    Returns:
        User data with roles and teams

    Raises:
        HTTPException: If user not found
    """
    user_service = UserService(db)
    user = user_service.get_by_id(user_id, with_roles=True)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Build response with roles
    from app.schemas.user import RoleBasic, TeamBasic

    roles = [RoleBasic(id=ur.role.id, name=ur.role.name, label=ur.role.label) for ur in user.roles]

    teams = [
        TeamBasic(
            id=tm.team.id,
            name=tm.team.name,
            role=tm.role.name if tm.role else None,
        )
        for tm in user.teams
    ]

    return UserDetailResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        name=user.name,
        avatar=user.avatar,
        phone=user.phone,
        status=user.status,
        department=user.department,
        position=user.position,
        created_at=user.created_at,
        updated_at=user.updated_at,
        roles=roles,
        teams=teams,
    )


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> UserResponse:
    """Create a new user.

    Args:
        user_data: User creation data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Created user

    Raises:
        HTTPException: If user with email already exists
    """
    user_service = UserService(db)

    try:
        user = user_service.create(user_data)
        return UserResponse.model_validate(user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        ) from e


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> UserResponse:
    """Update user information.

    Args:
        user_id: User ID
        user_data: User update data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Updated user

    Raises:
        HTTPException: If user not found
    """
    user_service = UserService(db)
    user = user_service.update(user_id, user_data)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return UserResponse.model_validate(user)


@router.patch("/{user_id}/status", response_model=UserResponse)
async def update_user_status(
    user_id: str,
    status_data: UserStatusUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> UserResponse:
    """Update user status (ACTIVE/INACTIVE/SUSPENDED).

    Args:
        user_id: User ID
        status_data: New status
        db: Database session
        current_user: Current authenticated user

    Returns:
        Updated user

    Raises:
        HTTPException: If user not found or trying to modify own status
    """
    # Prevent self-status change
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change your own status",
        )

    user_service = UserService(db)
    user = user_service.update_status(user_id, status_data.status)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return UserResponse.model_validate(user)


@router.post("/batch-delete", response_model=BatchDeleteResponse)
async def batch_delete_users(
    request: BatchDeleteRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> BatchDeleteResponse:
    """Delete multiple users.

    Args:
        request: List of user IDs to delete
        db: Database session
        current_user: Current authenticated user

    Returns:
        Number of users deleted

    Raises:
        HTTPException: If trying to delete own account
    """
    # Prevent self-deletion
    if current_user.id in request.ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account",
        )

    user_service = UserService(db)
    deleted_count = user_service.batch_delete(request.ids)

    return BatchDeleteResponse(
        message=f"Successfully deleted {deleted_count} users",
        deleted_count=deleted_count,
    )


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> dict[str, str]:
    """Delete user.

    Args:
        user_id: User ID
        db: Database session
        current_user: Current authenticated user

    Returns:
        Success message

    Raises:
        HTTPException: If user not found or trying to delete self
    """
    # Prevent self-deletion
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account",
        )

    user_service = UserService(db)
    deleted = user_service.delete(user_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return {"message": "User successfully deleted", "id": user_id}
