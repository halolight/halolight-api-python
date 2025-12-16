"""Password reset token model."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, generate_cuid

if TYPE_CHECKING:
    from app.models.user import User


class PasswordResetToken(Base):
    """Store password reset tokens with expiry and usage tracking."""

    __tablename__ = "password_reset_tokens"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_cuid)
    user_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="password_reset_tokens")

    __table_args__ = (
        Index("idx_password_reset_tokens_user_id", "user_id"),
        Index("idx_password_reset_tokens_token_hash", "token_hash"),
    )

    def is_expired(self, now: datetime) -> bool:
        """Return True if the token is expired."""
        # Ensure both datetimes are comparable (handle timezone awareness)
        if now.tzinfo is None and self.expires_at.tzinfo is not None:
            now = now.replace(tzinfo=UTC)
        elif now.tzinfo is not None and self.expires_at.tzinfo is None:
            expires_at = self.expires_at.replace(tzinfo=UTC)
            return now >= expires_at
        return now >= self.expires_at

    def is_used(self) -> bool:
        """Return True if the token has been used."""
        return self.used_at is not None

    def __repr__(self) -> str:
        """String representation."""
        return f"<PasswordResetToken(id={self.id}, user_id={self.user_id}, used={self.is_used()})>"
