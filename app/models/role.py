"""Role and Permission models matching Prisma schema."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, generate_cuid

if TYPE_CHECKING:
    from app.models.team import TeamMember
    from app.models.user import User


class Role(Base):
    """Role model - matches Prisma roles table."""

    __tablename__ = "roles"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_cuid)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    label: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
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
    permissions: Mapped[list[RolePermission]] = relationship(
        "RolePermission", back_populates="role", cascade="all, delete-orphan"
    )
    users: Mapped[list[UserRole]] = relationship(
        "UserRole", back_populates="role", cascade="all, delete-orphan"
    )
    team_members: Mapped[list[TeamMember]] = relationship("TeamMember", back_populates="role")

    def __repr__(self) -> str:
        """String representation."""
        return f"<Role(id={self.id}, name={self.name})>"


class Permission(Base):
    """Permission model - matches Prisma permissions table."""

    __tablename__ = "permissions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_cuid)
    action: Mapped[str] = mapped_column(
        String, unique=True, nullable=False
    )  # e.g., "users:view", "documents:*", "*"
    resource: Mapped[str] = mapped_column(String, nullable=False)  # users, documents, etc.
    description: Mapped[str | None] = mapped_column(String, nullable=True)
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
    roles: Mapped[list[RolePermission]] = relationship(
        "RolePermission", back_populates="permission", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("idx_permissions_action", "action"),)

    def __repr__(self) -> str:
        """String representation."""
        return f"<Permission(id={self.id}, action={self.action})>"


class RolePermission(Base):
    """Role-Permission junction table - matches Prisma role_permissions table."""

    __tablename__ = "role_permissions"

    role_id: Mapped[str] = mapped_column(
        ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True
    )
    permission_id: Mapped[str] = mapped_column(
        ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True
    )

    # Relationships
    role: Mapped[Role] = relationship("Role", back_populates="permissions")
    permission: Mapped[Permission] = relationship("Permission", back_populates="roles")

    def __repr__(self) -> str:
        """String representation."""
        return f"<RolePermission(role_id={self.role_id}, permission_id={self.permission_id})>"


class UserRole(Base):
    """User-Role junction table - matches Prisma user_roles table."""

    __tablename__ = "user_roles"

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    role_id: Mapped[str] = mapped_column(
        ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True
    )

    # Relationships
    user: Mapped[User] = relationship("User", back_populates="roles")
    role: Mapped[Role] = relationship("Role", back_populates="users")

    def __repr__(self) -> str:
        """String representation."""
        return f"<UserRole(user_id={self.user_id}, role_id={self.role_id})>"
