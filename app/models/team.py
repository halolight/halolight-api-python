"""Team models matching Prisma schema."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, generate_cuid

if TYPE_CHECKING:
    from app.models.document import Document, DocumentShare
    from app.models.file import File, Folder
    from app.models.role import Role
    from app.models.user import User


class Team(Base):
    """Team model - matches Prisma teams table."""

    __tablename__ = "teams"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_cuid)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    avatar: Mapped[str | None] = mapped_column(String, nullable=True)
    owner_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
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
    owner: Mapped[User] = relationship(
        "User", back_populates="owned_teams", foreign_keys=[owner_id]
    )
    members: Mapped[list[TeamMember]] = relationship(
        "TeamMember", back_populates="team", cascade="all, delete-orphan"
    )
    documents: Mapped[list[Document]] = relationship("Document", back_populates="team")
    files: Mapped[list[File]] = relationship("File", back_populates="team")
    folders: Mapped[list[Folder]] = relationship("Folder", back_populates="team")
    shares: Mapped[list[DocumentShare]] = relationship(
        "DocumentShare", back_populates="team", foreign_keys="DocumentShare.team_id"
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Team(id={self.id}, name={self.name})>"


class TeamMember(Base):
    """Team member junction table - matches Prisma team_members table."""

    __tablename__ = "team_members"

    team_id: Mapped[str] = mapped_column(
        ForeignKey("teams.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    role_id: Mapped[str | None] = mapped_column(ForeignKey("roles.id"), nullable=True)
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    team: Mapped[Team] = relationship("Team", back_populates="members")
    user: Mapped[User] = relationship("User", back_populates="teams")
    role: Mapped[Role | None] = relationship("Role", back_populates="team_members")

    def __repr__(self) -> str:
        """String representation."""
        return f"<TeamMember(team_id={self.team_id}, user_id={self.user_id})>"
