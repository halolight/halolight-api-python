"""Conversation and Message models matching Prisma schema."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, generate_cuid

if TYPE_CHECKING:
    from app.models.user import User


class Conversation(Base):
    """Conversation model - matches Prisma conversations table."""

    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_cuid)
    name: Mapped[str | None] = mapped_column(String, nullable=True)
    is_group: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    avatar: Mapped[str | None] = mapped_column(String, nullable=True)
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
    participants: Mapped[list[ConversationParticipant]] = relationship(
        "ConversationParticipant",
        back_populates="conversation",
        cascade="all, delete-orphan",
    )
    messages: Mapped[list[Message]] = relationship(
        "Message", back_populates="conversation", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Conversation(id={self.id}, name={self.name})>"


class ConversationParticipant(Base):
    """Conversation participant junction table - matches Prisma conversation_participants table."""

    __tablename__ = "conversation_participants"

    conversation_id: Mapped[str] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    role: Mapped[str | None] = mapped_column(
        String, nullable=True, server_default="member"
    )  # owner, admin, member
    unread_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    last_read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    conversation: Mapped[Conversation] = relationship("Conversation", back_populates="participants")
    user: Mapped[User] = relationship("User", back_populates="conversations")

    def __repr__(self) -> str:
        """String representation."""
        return f"<ConversationParticipant(conversation_id={self.conversation_id}, user_id={self.user_id})>"


class Message(Base):
    """Message model - matches Prisma messages table."""

    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_cuid)
    conversation_id: Mapped[str] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
    )
    sender_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    type: Mapped[str] = mapped_column(
        String, nullable=False, server_default="text"
    )  # text, image, file
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    conversation: Mapped[Conversation] = relationship("Conversation", back_populates="messages")
    sender: Mapped[User] = relationship("User", back_populates="messages", foreign_keys=[sender_id])

    __table_args__ = (
        Index("idx_messages_conversation_id", "conversation_id"),
        Index("idx_messages_sender_id", "sender_id"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Message(id={self.id}, type={self.type})>"
