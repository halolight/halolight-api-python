"""Authentication routes."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import create_access_token
from app.schemas.user import AuthResponse, LoginRequest, RegisterRequest, UserResponse
from app.services.user_service import UserService

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
        Authentication response with token and user data

    Raises:
        HTTPException: If user with email already exists
    """
    user_service = UserService(db)

    try:
        # Create user
        user = user_service.create(user_data)

        # Create access token
        token = create_access_token(
            data={
                "sub": user.id,
                "email": user.email,
                "role": user.role.value,
            }
        )

        # Return response
        return AuthResponse(
            token=token,
            user=UserResponse.model_validate(user),
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
        Authentication response with token and user data

    Raises:
        HTTPException: If credentials are invalid
    """
    user_service = UserService(db)

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

    # Create access token
    token = create_access_token(
        data={
            "sub": user.id,
            "email": user.email,
            "role": user.role.value,
        }
    )

    # Return response
    return AuthResponse(
        token=token,
        user=UserResponse.model_validate(user),
    )


@router.post("/logout")
async def logout() -> dict[str, str]:
    """Logout user (placeholder).

    Note: With JWT, logout is typically handled client-side by removing the token.
    For server-side logout, you would need to implement token blacklisting with Redis or a database.

    Returns:
        Success message
    """
    return {"message": "Logout successful"}
