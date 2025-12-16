"""API dependencies for authentication and authorization."""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models import User, UserStatus
from app.services.user_service import UserService

# Security scheme for JWT bearer token
security = HTTPBearer()


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """Get current authenticated user from JWT token.

    Args:
        credentials: HTTP bearer token credentials
        db: Database session

    Returns:
        Current authenticated user

    Raises:
        HTTPException: If token is invalid or user not found
    """
    token = credentials.credentials
    payload = decode_access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id: str | None = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_service = UserService(db)
    user = user_service.get_by_id(user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Get current active user.

    Args:
        current_user: Current authenticated user

    Returns:
        Current active user

    Raises:
        HTTPException: If user is inactive or suspended
    """
    if current_user.status != UserStatus.ACTIVE.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is not active",
        )
    return current_user


def check_permission(required_permission: str):
    """Create a dependency that checks if user has a specific permission.

    Supports wildcard matching:
    - "*" matches everything
    - "users:*" matches all user permissions
    - "users:read" matches exact permission

    Args:
        required_permission: Required permission string (e.g., "users:read")

    Returns:
        Dependency function that checks permission
    """

    def permission_checker(
        current_user: Annotated[User, Depends(get_current_active_user)],
        db: Annotated[Session, Depends(get_db)],
    ) -> User:
        """Check if user has the required permission.

        Args:
            current_user: Current authenticated user
            db: Database session

        Returns:
            Current user if permission check passes

        Raises:
            HTTPException: If user doesn't have required permission
        """
        user_service = UserService(db)
        user = user_service.get_by_id(current_user.id, with_roles=True)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        # Collect all permissions from user's roles
        user_permissions: set[str] = set()
        for user_role in user.roles:
            role = user_role.role
            for role_permission in role.permissions:
                user_permissions.add(role_permission.permission.action)

        # Check if user has the required permission
        if has_permission(user_permissions, required_permission):
            return current_user

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission denied: requires '{required_permission}'",
        )

    return permission_checker


def has_permission(user_permissions: set[str], required: str) -> bool:
    """Check if user has the required permission using wildcard matching.

    Args:
        user_permissions: Set of user's permission strings
        required: Required permission string

    Returns:
        True if user has permission, False otherwise
    """
    # Exact match
    if required in user_permissions:
        return True

    # Check for full wildcard
    if "*" in user_permissions:
        return True

    # Check for resource wildcard (e.g., "users:*" for "users:read")
    if ":" in required:
        resource, _ = required.split(":", 1)
        if f"{resource}:*" in user_permissions:
            return True

    return False


# Common permission dependencies
RequireUsersRead = Depends(check_permission("users:read"))
RequireUsersCreate = Depends(check_permission("users:create"))
RequireUsersUpdate = Depends(check_permission("users:update"))
RequireUsersDelete = Depends(check_permission("users:delete"))
RequireAdmin = Depends(check_permission("*"))
