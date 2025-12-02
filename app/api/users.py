"""User routes."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, require_admin
from app.core.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserListResponse, UserResponse, UserUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> UserResponse:
    """Get current user profile.

    Args:
        current_user: Current authenticated user

    Returns:
        Current user profile
    """
    return UserResponse.model_validate(current_user)


@router.get("", response_model=UserListResponse)
async def list_users(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_admin)],
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Page size"),
) -> UserListResponse:
    """List all users with pagination (admin only).

    Args:
        db: Database session
        _: Current admin user (for authorization)
        page: Page number (1-indexed)
        page_size: Number of users per page

    Returns:
        Paginated list of users
    """
    user_service = UserService(db)

    # Calculate skip
    skip = (page - 1) * page_size

    # Get users
    users, total = user_service.get_all(skip=skip, limit=page_size)

    # Calculate pagination metadata
    pagination = user_service.calculate_pagination(total, page, page_size)

    return UserListResponse(
        users=[UserResponse.model_validate(user) for user in users],
        total=pagination["total"],
        page=pagination["page"],
        page_size=pagination["page_size"],
        total_pages=pagination["total_pages"],
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_admin)],
) -> UserResponse:
    """Get user by ID (admin only).

    Args:
        user_id: User ID
        db: Database session
        _: Current admin user (for authorization)

    Returns:
        User data

    Raises:
        HTTPException: If user not found
    """
    user_service = UserService(db)
    user = user_service.get_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return UserResponse.model_validate(user)


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_admin)],
) -> UserResponse:
    """Create a new user (admin only).

    Args:
        user_data: User creation data
        db: Database session
        _: Current admin user (for authorization)

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
    _: Annotated[User, Depends(require_admin)],
) -> UserResponse:
    """Update user (admin only).

    Args:
        user_id: User ID
        user_data: User update data
        db: Database session
        _: Current admin user (for authorization)

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


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_admin)],
) -> None:
    """Delete user (admin only).

    Args:
        user_id: User ID
        db: Database session
        current_user: Current admin user

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
