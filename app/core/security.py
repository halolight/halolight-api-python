"""Security utilities for password hashing and JWT token handling."""

from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from .config import settings

# Password hashing context - matches NestJS/Java implementations (bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Token types
TOKEN_TYPE_ACCESS = "access"
TOKEN_TYPE_REFRESH = "refresh"


def hash_password(password: str) -> str:
    """Hash a password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        Hashed password
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash.

    Args:
        plain_password: Plain text password
        hashed_password: Hashed password from database

    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token.

    Args:
        data: Data to encode in the token (e.g., user_id, email)
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update(
        {
            "exp": expire,
            "iat": datetime.now(UTC),
            "type": TOKEN_TYPE_ACCESS,
        }
    )

    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )

    return encoded_jwt


def create_refresh_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """Create a JWT refresh token.

    Args:
        data: Data to encode in the token (e.g., user_id)
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT refresh token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode.update(
        {
            "exp": expire,
            "iat": datetime.now(UTC),
            "type": TOKEN_TYPE_REFRESH,
        }
    )

    # Use refresh secret if configured, otherwise fall back to main secret
    secret_key = settings.JWT_REFRESH_SECRET_KEY or settings.JWT_SECRET_KEY

    encoded_jwt = jwt.encode(
        to_encode,
        secret_key,
        algorithm=settings.JWT_ALGORITHM,
    )

    return encoded_jwt


def decode_access_token(token: str) -> dict[str, Any] | None:
    """Decode and verify a JWT access token.

    Args:
        token: JWT token string

    Returns:
        Decoded token payload or None if invalid
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        # Verify it's an access token
        if payload.get("type") != TOKEN_TYPE_ACCESS:
            return None
        return payload
    except JWTError:
        return None


def decode_refresh_token(token: str) -> dict[str, Any] | None:
    """Decode and verify a JWT refresh token.

    Args:
        token: JWT refresh token string

    Returns:
        Decoded token payload or None if invalid
    """
    try:
        # Use refresh secret if configured, otherwise fall back to main secret
        secret_key = settings.JWT_REFRESH_SECRET_KEY or settings.JWT_SECRET_KEY

        payload = jwt.decode(
            token,
            secret_key,
            algorithms=[settings.JWT_ALGORITHM],
        )
        # Verify it's a refresh token
        if payload.get("type") != TOKEN_TYPE_REFRESH:
            return None
        return payload
    except JWTError:
        return None


def generate_tokens(user_id: str, email: str) -> tuple[str, str, datetime]:
    """Generate access and refresh token pair.

    Args:
        user_id: User ID to encode
        email: User email to encode in access token

    Returns:
        Tuple of (access_token, refresh_token, refresh_expires_at)
    """
    # Access token includes more user info
    access_token = create_access_token({"sub": user_id, "email": email})

    # Refresh token only includes user ID
    refresh_token = create_refresh_token({"sub": user_id})

    # Calculate refresh token expiration for storage
    refresh_expires_at = datetime.now(UTC) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)

    return access_token, refresh_token, refresh_expires_at
