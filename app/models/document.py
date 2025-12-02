"""Document models matching Prisma schema."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, generate_cuid
from app.models.enums import SharePermission

if TYPE_CHECKING:
    from app.models.team import Team
    from app.models.user import User


# PostgreSQL enum type - must match Prisma's created enum
share_permission_enum = ENUM(
    "READ",
    "EDIT",
    "COMMENT",
    name="SharePermission",
    create_type=False,  # Prisma already created it
)


class Document(Base):
    """Document model - matches Prisma documents table."""

    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_cuid)
    title: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    folder: Mapped[str | None] = mapped_column(String, nullable=True)
    type: Mapped[str] = mapped_column(String, nullable=False)  # pdf, doc, image, etc.
    size: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default="0")
    views: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    owner_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    team_id: Mapped[str | None] = mapped_column(ForeignKey("teams.id"), nullable=True)
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
    owner: Mapped[User] = relationship("User", back_populates="documents", foreign_keys=[owner_id])
    team: Mapped[Team | None] = relationship("Team", back_populates="documents")
    shares: Mapped[list[DocumentShare]] = relationship(
        "DocumentShare", back_populates="document", cascade="all, delete-orphan"
    )
    tags: Mapped[list[DocumentTag]] = relationship(
        "DocumentTag", back_populates="document", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_documents_owner_id", "owner_id"),
        Index("idx_documents_team_id", "team_id"),
        Index("idx_documents_folder", "folder"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Document(id={self.id}, title={self.title})>"


class DocumentShare(Base):
    """Document share model - matches Prisma document_shares table."""

    __tablename__ = "document_shares"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_cuid)
    document_id: Mapped[str] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    shared_with_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    team_id: Mapped[str | None] = mapped_column(ForeignKey("teams.id"), nullable=True)
    permission: Mapped[str] = mapped_column(
        share_permission_enum,
        nullable=False,
        server_default=SharePermission.READ.value,
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    document: Mapped[Document] = relationship("Document", back_populates="shares")
    shared_with: Mapped[User | None] = relationship(
        "User", back_populates="shared_documents", foreign_keys=[shared_with_id]
    )
    team: Mapped[Team | None] = relationship(
        "Team", back_populates="shares", foreign_keys=[team_id]
    )

    __table_args__ = (
        Index("idx_document_shares_document_id", "document_id"),
        Index("idx_document_shares_shared_with_id", "shared_with_id"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<DocumentShare(id={self.id}, document_id={self.document_id})>"


class Tag(Base):
    """Tag model - matches Prisma tags table."""

    __tablename__ = "tags"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_cuid)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    documents: Mapped[list[DocumentTag]] = relationship(
        "DocumentTag", back_populates="tag", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Tag(id={self.id}, name={self.name})>"


class DocumentTag(Base):
    """Document-Tag junction table - matches Prisma document_tags table."""

    __tablename__ = "document_tags"

    document_id: Mapped[str] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), primary_key=True
    )
    tag_id: Mapped[str] = mapped_column(ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)

    # Relationships
    document: Mapped[Document] = relationship("Document", back_populates="tags")
    tag: Mapped[Tag] = relationship("Tag", back_populates="documents")

    def __repr__(self) -> str:
        """String representation."""
        return f"<DocumentTag(document_id={self.document_id}, tag_id={self.tag_id})>"
