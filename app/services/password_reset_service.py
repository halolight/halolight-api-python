"""Service for password reset flow."""

from __future__ import annotations

import hashlib
import logging
import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import update
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.models import PasswordResetToken, User
from app.models.base import generate_cuid

logger = logging.getLogger(__name__)


class PasswordResetError(Exception):
    """Base exception for password reset errors."""

    pass


class InvalidTokenError(PasswordResetError):
    """Raised when the reset token is invalid."""

    pass


class ExpiredTokenError(PasswordResetError):
    """Raised when the reset token has expired."""

    pass


class UsedTokenError(PasswordResetError):
    """Raised when the reset token has already been used."""

    pass


class PasswordResetService:
    """Handle password reset token creation and consumption."""

    def __init__(self, db: Session) -> None:
        """Initialize the service with a database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def _hash_token(self, token: str) -> str:
        """Hash the token using SHA-256.

        Args:
            token: Raw token string

        Returns:
            Hexadecimal hash of the token
        """
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def create_token(self, user: User) -> str:
        """Create a reset token, store hash, and return raw token.

        This method invalidates any previous tokens for the user before
        creating a new one.

        Args:
            user: User to create token for

        Returns:
            Raw token string (to be sent via email)
        """
        # Generate a secure random token
        raw_token = secrets.token_urlsafe(32)
        token_hash = self._hash_token(raw_token)
        expires_at = datetime.now(UTC) + timedelta(
            minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES
        )

        try:
            # Invalidate previous tokens for this user
            self.db.query(PasswordResetToken).filter(PasswordResetToken.user_id == user.id).delete()

            # Create new token record
            record = PasswordResetToken(
                id=generate_cuid(),
                user_id=user.id,
                token_hash=token_hash,
                expires_at=expires_at,
            )
            self.db.add(record)
            self.db.commit()

            logger.info("Created password reset token for user %s", user.id)
            return raw_token
        except Exception:
            self.db.rollback()
            raise

    def reset_password(self, token: str, new_password: str) -> User:
        """Validate token and update the user's password atomically.

        Uses atomic update to ensure the token can only be used once,
        even under concurrent requests.

        Args:
            token: Raw token string
            new_password: New password to set

        Returns:
            User whose password was reset

        Raises:
            InvalidTokenError: If token is invalid
            UsedTokenError: If token has been used
            ExpiredTokenError: If token has expired
            ValueError: If user not found
        """
        token_hash = self._hash_token(token)
        now = datetime.now(UTC)

        try:
            # Atomic update: mark token as used only if not already used and not expired
            # This prevents race conditions where two concurrent requests both pass validation
            result = self.db.execute(
                update(PasswordResetToken)
                .where(PasswordResetToken.token_hash == token_hash)
                .where(PasswordResetToken.used_at.is_(None))
                .where(PasswordResetToken.expires_at > now)
                .values(used_at=now)
                .returning(PasswordResetToken.user_id)
            )
            row = result.fetchone()

            if not row:
                # Token not found, already used, or expired - need to determine which
                record = (
                    self.db.query(PasswordResetToken)
                    .filter(PasswordResetToken.token_hash == token_hash)
                    .first()
                )

                if not record:
                    logger.warning("Invalid password reset token attempted")
                    raise InvalidTokenError("Invalid reset token")

                if record.is_used():
                    logger.warning(
                        "Used password reset token attempted for user %s", record.user_id
                    )
                    raise UsedTokenError("Reset token has already been used")

                if record.is_expired(now):
                    logger.warning(
                        "Expired password reset token attempted for user %s", record.user_id
                    )
                    raise ExpiredTokenError("Reset token has expired")

                # Should not reach here, but handle gracefully
                raise InvalidTokenError("Invalid reset token")

            user_id = row[0]

            # Get user and update password
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                self.db.rollback()
                raise ValueError("User not found for token")

            # Update password
            user.password = hash_password(new_password)
            self.db.commit()

            logger.info("Password reset completed for user %s", user.id)
            return user

        except (InvalidTokenError, UsedTokenError, ExpiredTokenError, ValueError):
            self.db.rollback()
            raise
        except Exception:
            self.db.rollback()
            raise

    def verify_token(self, token: str) -> User:
        """Verify a reset token and return the associated user.

        Note: This does NOT consume the token, use reset_password for that.

        Args:
            token: Raw token string

        Returns:
            User associated with the token

        Raises:
            InvalidTokenError: If token is invalid
            UsedTokenError: If token has been used
            ExpiredTokenError: If token has expired
            ValueError: If user not found
        """
        token_hash = self._hash_token(token)
        record = (
            self.db.query(PasswordResetToken)
            .filter(PasswordResetToken.token_hash == token_hash)
            .first()
        )

        if not record:
            raise InvalidTokenError("Invalid reset token")

        if record.is_used():
            raise UsedTokenError("Reset token has already been used")

        now = datetime.now(UTC)
        if record.is_expired(now):
            raise ExpiredTokenError("Reset token has expired")

        user = self.db.query(User).filter(User.id == record.user_id).first()
        if not user:
            raise ValueError("User not found for token")

        return user

    def cleanup_expired_tokens(self) -> int:
        """Remove all expired tokens from the database.

        Returns:
            Number of tokens deleted
        """
        now = datetime.now(UTC)
        try:
            count = (
                self.db.query(PasswordResetToken)
                .filter(PasswordResetToken.expires_at < now)
                .delete()
            )
            self.db.commit()
            logger.info("Cleaned up %d expired password reset tokens", count)
            return count
        except Exception:
            self.db.rollback()
            raise
