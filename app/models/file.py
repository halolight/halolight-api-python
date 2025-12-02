"""File and Folder models matching Prisma schema."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, generate_cuid

if TYPE_CHECKING:
    from app.models.team import Team
    from app.models.user import User


class Folder(Base):
    """Folder model - matches Prisma folders table."""

    __tablename__ = "folders"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_cuid)
    name: Mapped[str] = mapped_column(String, nullable=False)
    path: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    parent_id: Mapped[str | None] = mapped_column(ForeignKey("folders.id"), nullable=True)
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
    owner: Mapped[User] = relationship("User", back_populates="folders", foreign_keys=[owner_id])
    team: Mapped[Team | None] = relationship("Team", back_populates="folders")
    parent: Mapped[Folder | None] = relationship(
        "Folder",
        back_populates="children",
        remote_side="Folder.id",
        foreign_keys=[parent_id],
    )
    children: Mapped[list[Folder]] = relationship(
        "Folder", back_populates="parent", cascade="all, delete-orphan"
    )
    files: Mapped[list[File]] = relationship(
        "File", back_populates="folder", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_folders_path", "path"),
        Index("idx_folders_owner_id", "owner_id"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Folder(id={self.id}, name={self.name}, path={self.path})>"


class File(Base):
    """File model - matches Prisma files table."""

    __tablename__ = "files"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_cuid)
    name: Mapped[str] = mapped_column(String, nullable=False)
    path: Mapped[str] = mapped_column(String, nullable=False)
    mime_type: Mapped[str] = mapped_column(String, nullable=False)
    size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    thumbnail: Mapped[str | None] = mapped_column(String, nullable=True)
    folder_id: Mapped[str | None] = mapped_column(ForeignKey("folders.id"), nullable=True)
    owner_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    team_id: Mapped[str | None] = mapped_column(ForeignKey("teams.id"), nullable=True)
    is_favorite: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
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
    owner: Mapped[User] = relationship("User", back_populates="files", foreign_keys=[owner_id])
    team: Mapped[Team | None] = relationship("Team", back_populates="files")
    folder: Mapped[Folder | None] = relationship("Folder", back_populates="files")

    __table_args__ = (
        Index("idx_files_owner_id", "owner_id"),
        Index("idx_files_folder_id", "folder_id"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<File(id={self.id}, name={self.name})>"
