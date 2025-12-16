"""File and Folder models matching Prisma schema."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Index, Integer, String, func
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, generate_cuid
from app.models.enums import SharePermission

if TYPE_CHECKING:
    from app.models.team import Team
    from app.models.user import User


# PostgreSQL enum type - must match Prisma's created enum
share_permission_enum = ENUM(
    "VIEW",
    "READ",
    "DOWNLOAD",
    "EDIT",
    "COMMENT",
    name="SharePermission",
    create_type=False,  # Prisma already created it
)


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
    shares: Mapped[list[FileShare]] = relationship(
        "FileShare", back_populates="file", cascade="all, delete-orphan"
    )
    access_logs: Mapped[list[FileAccessLog]] = relationship(
        "FileAccessLog", back_populates="file", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_files_owner_id", "owner_id"),
        Index("idx_files_folder_id", "folder_id"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<File(id={self.id}, name={self.name})>"


class FileShare(Base):
    """File share model - tracks file sharing with users/teams."""

    __tablename__ = "file_shares"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_cuid)
    file_id: Mapped[str] = mapped_column(ForeignKey("files.id", ondelete="CASCADE"), nullable=False)
    shared_with_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    team_id: Mapped[str | None] = mapped_column(ForeignKey("teams.id"), nullable=True)
    permission: Mapped[str] = mapped_column(
        share_permission_enum,
        nullable=False,
        server_default=SharePermission.VIEW.value,
    )
    share_token: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    access_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    max_access_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_revoked: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    file: Mapped[File] = relationship("File", back_populates="shares")
    shared_with: Mapped[User | None] = relationship(
        "User", back_populates="shared_files", foreign_keys=[shared_with_id]
    )
    team: Mapped[Team | None] = relationship(
        "Team", back_populates="file_shares", foreign_keys=[team_id]
    )

    __table_args__ = (
        Index("idx_file_shares_file_id", "file_id"),
        Index("idx_file_shares_shared_with_id", "shared_with_id"),
        Index("idx_file_shares_share_token", "share_token"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<FileShare(id={self.id}, file_id={self.file_id}, permission={self.permission})>"


class FileAccessLog(Base):
    """File access log - tracks who accessed shared files and when."""

    __tablename__ = "file_access_logs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_cuid)
    file_id: Mapped[str] = mapped_column(ForeignKey("files.id", ondelete="CASCADE"), nullable=False)
    share_id: Mapped[str | None] = mapped_column(
        ForeignKey("file_shares.id", ondelete="SET NULL"), nullable=True
    )
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String, nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String, nullable=True)
    action: Mapped[str] = mapped_column(String, nullable=False)  # view, download, edit
    accessed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    file: Mapped[File] = relationship("File", back_populates="access_logs")
    user: Mapped[User | None] = relationship("User", foreign_keys=[user_id])

    __table_args__ = (
        Index("idx_file_access_logs_file_id", "file_id"),
        Index("idx_file_access_logs_user_id", "user_id"),
        Index("idx_file_access_logs_accessed_at", "accessed_at"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<FileAccessLog(id={self.id}, file_id={self.file_id}, action={self.action})>"
