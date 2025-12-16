"""Activity log model matching Prisma schema."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, generate_cuid

if TYPE_CHECKING:
    from app.models.user import User


class ActivityLog(Base):
    """Activity log model - matches Prisma activity_logs table."""

    __tablename__ = "activity_logs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_cuid)
    actor_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    action: Mapped[str] = mapped_column(
        String, nullable=False
    )  # e.g., "document.create", "user.update"
    target_type: Mapped[str] = mapped_column(String, nullable=False)  # document, file, user, etc.
    target_id: Mapped[str] = mapped_column(String, nullable=False)
    extra_data: Mapped[dict | None] = mapped_column(
        "metadata", JSONB, nullable=True
    )  # Column name is 'metadata' in DB, but attribute is 'extra_data' to avoid SQLAlchemy reserved word
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    actor: Mapped[User] = relationship("User", back_populates="activities")

    __table_args__ = (
        Index("idx_activity_logs_actor_id", "actor_id"),
        Index("idx_activity_logs_target_type_target_id", "target_type", "target_id"),
        Index("idx_activity_logs_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<ActivityLog(id={self.id}, action={self.action})>"
