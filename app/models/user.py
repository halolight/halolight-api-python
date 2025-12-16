"""User model matching Prisma schema."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, Index, String, func
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, generate_cuid
from app.models.enums import UserStatus

if TYPE_CHECKING:
    from app.models.activity import ActivityLog
    from app.models.calendar import CalendarEvent, EventAttendee
    from app.models.conversation import ConversationParticipant, Message
    from app.models.document import Document, DocumentShare
    from app.models.file import File, FileShare, Folder
    from app.models.notification import Notification
    from app.models.password_reset_token import PasswordResetToken
    from app.models.refresh_token import RefreshToken
    from app.models.role import UserRole
    from app.models.team import Team, TeamMember

# PostgreSQL enum type - must match Prisma's created enum
user_status_enum = ENUM(
    "ACTIVE",
    "INACTIVE",
    "SUSPENDED",
    name="UserStatus",
    create_type=False,  # Prisma already created it
)


class User(Base):
    """User model - matches Prisma users table."""

    __tablename__ = "users"

    # Primary key
    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_cuid)

    # Required fields
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)

    # Optional fields
    phone: Mapped[str | None] = mapped_column(String, unique=True, nullable=True)
    avatar: Mapped[str | None] = mapped_column(String, nullable=True)
    department: Mapped[str | None] = mapped_column(String, nullable=True)
    position: Mapped[str | None] = mapped_column(String, nullable=True)
    bio: Mapped[str | None] = mapped_column(String, nullable=True)

    # Status with enum
    status: Mapped[str] = mapped_column(
        user_status_enum,
        nullable=False,
        server_default=UserStatus.ACTIVE.value,
    )

    # Quota tracking
    quota_used: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default="0")

    # Timestamps
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    roles: Mapped[list[UserRole]] = relationship(
        "UserRole", back_populates="user", cascade="all, delete-orphan"
    )
    teams: Mapped[list[TeamMember]] = relationship(
        "TeamMember", back_populates="user", cascade="all, delete-orphan"
    )
    owned_teams: Mapped[list[Team]] = relationship(
        "Team",
        back_populates="owner",
        cascade="all, delete-orphan",
        foreign_keys="Team.owner_id",
    )
    documents: Mapped[list[Document]] = relationship(
        "Document",
        back_populates="owner",
        cascade="all, delete-orphan",
        foreign_keys="Document.owner_id",
    )
    shared_documents: Mapped[list[DocumentShare]] = relationship(
        "DocumentShare",
        back_populates="shared_with",
        foreign_keys="DocumentShare.shared_with_id",
    )
    shared_files: Mapped[list["FileShare"]] = relationship(
        "FileShare",
        back_populates="shared_with",
        foreign_keys="FileShare.shared_with_id",
    )
    files: Mapped[list[File]] = relationship(
        "File",
        back_populates="owner",
        cascade="all, delete-orphan",
        foreign_keys="File.owner_id",
    )
    folders: Mapped[list[Folder]] = relationship(
        "Folder",
        back_populates="owner",
        cascade="all, delete-orphan",
        foreign_keys="Folder.owner_id",
    )
    owned_events: Mapped[list[CalendarEvent]] = relationship(
        "CalendarEvent",
        back_populates="owner",
        cascade="all, delete-orphan",
        foreign_keys="CalendarEvent.owner_id",
    )
    event_attendances: Mapped[list[EventAttendee]] = relationship(
        "EventAttendee", back_populates="user", cascade="all, delete-orphan"
    )
    notifications: Mapped[list[Notification]] = relationship(
        "Notification", back_populates="user", cascade="all, delete-orphan"
    )
    conversations: Mapped[list[ConversationParticipant]] = relationship(
        "ConversationParticipant", back_populates="user", cascade="all, delete-orphan"
    )
    messages: Mapped[list[Message]] = relationship(
        "Message",
        back_populates="sender",
        cascade="all, delete-orphan",
        foreign_keys="Message.sender_id",
    )
    activities: Mapped[list[ActivityLog]] = relationship(
        "ActivityLog", back_populates="actor", cascade="all, delete-orphan"
    )
    refresh_tokens: Mapped[list[RefreshToken]] = relationship(
        "RefreshToken", back_populates="user", cascade="all, delete-orphan"
    )
    password_reset_tokens: Mapped[list["PasswordResetToken"]] = relationship(
        "PasswordResetToken", back_populates="user", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_users_email", "email"),
        Index("idx_users_username", "username"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<User(id={self.id}, email={self.email}, status={self.status})>"
