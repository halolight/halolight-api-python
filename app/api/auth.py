"""Authentication routes matching API spec."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user
from app.core.database import get_db
from app.core.security import (
    decode_refresh_token,
    generate_tokens,
)
from app.models import User, UserStatus
from app.schemas.user import (
    AuthResponse,
    AuthUserResponse,
    ForgotPasswordRequest,
    LoginRequest,
    LogoutResponse,
    MeResponse,
    RefreshTokenRequest,
    RegisterRequest,
    ResetPasswordRequest,
    RoleWithPermissions,
    TokenRefreshResponse,
)
from app.services.user_service import RefreshTokenService, UserService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: RegisterRequest,
    db: Annotated[Session, Depends(get_db)],
) -> AuthResponse:
    """Register a new user.

    Args:
        user_data: User registration data
        db: Database session

    Returns:
        Authentication response with tokens and user data

    Raises:
        HTTPException: If user with email already exists
    """
    user_service = UserService(db)
    refresh_token_service = RefreshTokenService(db)

    try:
        # Create user
        user = user_service.create(user_data)

        # Generate tokens
        access_token, refresh_token, expires_at = generate_tokens(user.id, user.email)

        # Store refresh token
        refresh_token_service.create(user.id, refresh_token, expires_at)

        # Return response
        return AuthResponse(
            accessToken=access_token,
            refreshToken=refresh_token,
            user=AuthUserResponse(
                id=user.id,
                email=user.email,
                name=user.name,
                avatar=user.avatar,
                phone=user.phone,
                status=user.status,
            ),
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        ) from e


@router.post("/login", response_model=AuthResponse)
async def login(
    credentials: LoginRequest,
    db: Annotated[Session, Depends(get_db)],
) -> AuthResponse:
    """Login user.

    Args:
        credentials: Login credentials
        db: Database session

    Returns:
        Authentication response with tokens and user data

    Raises:
        HTTPException: If credentials are invalid or user is not active
    """
    user_service = UserService(db)
    refresh_token_service = RefreshTokenService(db)

    # Find user by email
    user = user_service.get_by_email(credentials.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    # Verify password
    if not user_service.verify_password(user, credentials.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    # Check if user is active
    if user.status != UserStatus.ACTIVE.value:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is not active",
        )

    # Generate tokens
    access_token, refresh_token, expires_at = generate_tokens(user.id, user.email)

    # Store refresh token
    refresh_token_service.create(user.id, refresh_token, expires_at)

    # Update last login
    user_service.update_last_login(user.id)

    # Return response
    return AuthResponse(
        accessToken=access_token,
        refreshToken=refresh_token,
        user=AuthUserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            avatar=user.avatar,
            phone=user.phone,
            status=user.status,
        ),
    )


@router.post("/refresh", response_model=TokenRefreshResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    db: Annotated[Session, Depends(get_db)],
) -> TokenRefreshResponse:
    """Refresh access token using refresh token.

    Args:
        request: Refresh token request
        db: Database session

    Returns:
        New token pair

    Raises:
        HTTPException: If refresh token is invalid or expired
    """
    user_service = UserService(db)
    refresh_token_service = RefreshTokenService(db)

    # Decode refresh token
    payload = decode_refresh_token(request.refreshToken)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    # Check if refresh token exists in database
    stored_token = refresh_token_service.get_by_token(request.refreshToken)
    if not stored_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked",
        )

    # Check if token is still valid
    if not refresh_token_service.is_valid(stored_token):
        refresh_token_service.delete(request.refreshToken)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired",
        )

    # Get user
    user = user_service.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    # Check if user is still active
    if user.status != UserStatus.ACTIVE.value:
        refresh_token_service.delete(request.refreshToken)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is not active",
        )

    # Generate new tokens
    new_access_token, new_refresh_token, expires_at = generate_tokens(user.id, user.email)

    # Rotate refresh token (delete old, create new)
    refresh_token_service.rotate(request.refreshToken, user.id, new_refresh_token, expires_at)

    return TokenRefreshResponse(
        accessToken=new_access_token,
        refreshToken=new_refresh_token,
    )


@router.get("/me", response_model=MeResponse)
async def get_current_user_info(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> MeResponse:
    """Get current authenticated user information.

    Args:
        current_user: Current authenticated user
        db: Database session

    Returns:
        User information with roles and permissions
    """
    user_service = UserService(db)

    # Get user with roles loaded
    user = user_service.get_by_id(current_user.id, with_roles=True)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Build roles with permissions
    roles_with_permissions: list[RoleWithPermissions] = []
    for user_role in user.roles:
        role = user_role.role
        permissions = [rp.permission.action for rp in role.permissions]
        roles_with_permissions.append(
            RoleWithPermissions(
                id=role.id,
                name=role.name,
                label=role.label,
                permissions=permissions,
            )
        )

    return MeResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        avatar=user.avatar,
        phone=user.phone,
        status=user.status,
        roles=roles_with_permissions,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@router.post("/logout", response_model=LogoutResponse)
async def logout(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> LogoutResponse:
    """Logout user by invalidating all refresh tokens.

    Args:
        current_user: Current authenticated user
        db: Database session

    Returns:
        Success message
    """
    refresh_token_service = RefreshTokenService(db)

    # Delete all refresh tokens for the user
    refresh_token_service.delete_all_for_user(current_user.id)

    return LogoutResponse(message="Successfully logged out")


@router.post("/forgot-password")
async def forgot_password(
    request: ForgotPasswordRequest,
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, str]:
    """Request password reset email.

    Note: This is a placeholder. In production, this would send an email
    with a password reset link.

    Args:
        request: Forgot password request with email
        db: Database session

    Returns:
        Success message (always returns success for security)
    """
    user_service = UserService(db)

    # Check if user exists (but don't reveal this to the client)
    user = user_service.get_by_email(request.email)

    if user:
        # TODO: Generate password reset token and send email
        # For now, just log (in production, send email)
        pass

    # Always return success to prevent email enumeration
    return {"message": "If the email exists, a password reset link has been sent"}


@router.post("/reset-password")
async def reset_password(
    request: ResetPasswordRequest,
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, str]:
    """Reset password using reset token.

    Note: This is a placeholder. In production, this would verify the reset token
    and update the password.

    Args:
        request: Reset password request with token and new password
        db: Database session

    Returns:
        Success message

    Raises:
        HTTPException: If token is invalid
    """
    # TODO: Implement password reset token verification
    # For now, return an error since we haven't implemented the token system
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Password reset functionality is not yet implemented",
    )
