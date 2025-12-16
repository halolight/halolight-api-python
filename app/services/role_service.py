"""Role and Permission services for business logic."""

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models import Permission, Role, RolePermission, UserRole
from app.models.base import generate_cuid
from app.schemas.role import PermissionCreate, RoleCreate, RoleUpdate


class PermissionService:
    """Permission service for managing permission operations."""

    def __init__(self, db: Session) -> None:
        """Initialize permission service.

        Args:
            db: Database session
        """
        self.db = db

    def get_by_id(self, permission_id: str) -> Permission | None:
        """Get permission by ID.

        Args:
            permission_id: Permission ID

        Returns:
            Permission or None if not found
        """
        return self.db.query(Permission).filter(Permission.id == permission_id).first()

    def get_by_action(self, action: str) -> Permission | None:
        """Get permission by action name.

        Args:
            action: Permission action (e.g., users:read)

        Returns:
            Permission or None if not found
        """
        return self.db.query(Permission).filter(Permission.action == action).first()

    def get_all(self) -> list[Permission]:
        """Get all permissions.

        Returns:
            List of all permissions
        """
        return self.db.query(Permission).order_by(Permission.action).all()

    def create(self, permission_data: PermissionCreate) -> Permission:
        """Create a new permission.

        Args:
            permission_data: Permission creation data

        Returns:
            Created permission

        Raises:
            ValueError: If permission with action already exists
        """
        existing = self.get_by_action(permission_data.name)
        if existing:
            raise ValueError(f"Permission '{permission_data.name}' already exists")

        permission = Permission(
            id=generate_cuid(),
            action=permission_data.name,
            description=permission_data.description,
        )

        self.db.add(permission)
        self.db.commit()
        self.db.refresh(permission)

        return permission

    def delete(self, permission_id: str) -> bool:
        """Delete permission.

        Args:
            permission_id: Permission ID

        Returns:
            True if deleted, False if not found
        """
        permission = self.get_by_id(permission_id)
        if not permission:
            return False

        self.db.delete(permission)
        self.db.commit()

        return True


class RoleService:
    """Role service for managing role operations."""

    def __init__(self, db: Session) -> None:
        """Initialize role service.

        Args:
            db: Database session
        """
        self.db = db

    def get_by_id(self, role_id: str, with_permissions: bool = False) -> Role | None:
        """Get role by ID.

        Args:
            role_id: Role ID
            with_permissions: Whether to eager load permissions

        Returns:
            Role or None if not found
        """
        query = self.db.query(Role).filter(Role.id == role_id)
        if with_permissions:
            query = query.options(
                joinedload(Role.permissions).joinedload(RolePermission.permission)
            )
        return query.first()

    def get_by_name(self, name: str) -> Role | None:
        """Get role by name.

        Args:
            name: Role name

        Returns:
            Role or None if not found
        """
        return self.db.query(Role).filter(Role.name == name).first()

    def get_all(self, with_permissions: bool = True) -> list[Role]:
        """Get all roles.

        Args:
            with_permissions: Whether to eager load permissions

        Returns:
            List of all roles
        """
        query = self.db.query(Role)
        if with_permissions:
            query = query.options(
                joinedload(Role.permissions).joinedload(RolePermission.permission)
            )
        return query.order_by(Role.name).all()

    def get_user_count(self, role_id: str) -> int:
        """Get count of users with this role.

        Args:
            role_id: Role ID

        Returns:
            Number of users with this role
        """
        return (
            self.db.query(func.count(UserRole.user_id)).filter(UserRole.role_id == role_id).scalar()
            or 0
        )

    def create(self, role_data: RoleCreate) -> Role:
        """Create a new role.

        Args:
            role_data: Role creation data

        Returns:
            Created role

        Raises:
            ValueError: If role with name already exists
        """
        existing = self.get_by_name(role_data.name)
        if existing:
            raise ValueError(f"Role '{role_data.name}' already exists")

        role = Role(
            id=generate_cuid(),
            name=role_data.name,
            label=role_data.name,  # Default label to name
            description=role_data.description,
        )

        self.db.add(role)
        self.db.commit()
        self.db.refresh(role)

        return role

    def update(self, role_id: str, role_data: RoleUpdate) -> Role | None:
        """Update role.

        Args:
            role_id: Role ID
            role_data: Role update data

        Returns:
            Updated role or None if not found
        """
        role = self.get_by_id(role_id)
        if not role:
            return None

        update_dict = role_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            if value is not None:
                setattr(role, key, value)

        self.db.commit()
        self.db.refresh(role)

        return role

    def delete(self, role_id: str) -> bool:
        """Delete role.

        Args:
            role_id: Role ID

        Returns:
            True if deleted, False if not found
        """
        role = self.get_by_id(role_id)
        if not role:
            return False

        self.db.delete(role)
        self.db.commit()

        return True

    def assign_permissions(self, role_id: str, permission_ids: list[str]) -> Role | None:
        """Assign permissions to a role (replaces existing).

        Args:
            role_id: Role ID
            permission_ids: List of permission IDs to assign

        Returns:
            Updated role with permissions or None if role not found
        """
        role = self.get_by_id(role_id, with_permissions=True)
        if not role:
            return None

        # Remove existing role permissions
        self.db.query(RolePermission).filter(RolePermission.role_id == role_id).delete(
            synchronize_session=False
        )

        # Add new permissions
        for perm_id in permission_ids:
            role_permission = RolePermission(role_id=role_id, permission_id=perm_id)
            self.db.add(role_permission)

        self.db.commit()

        # Refresh to get updated permissions
        return self.get_by_id(role_id, with_permissions=True)

    def get_role_permissions(self, role_id: str) -> list[Permission]:
        """Get all permissions for a role.

        Args:
            role_id: Role ID

        Returns:
            List of permissions
        """
        role = self.get_by_id(role_id, with_permissions=True)
        if not role:
            return []

        return [rp.permission for rp in role.permissions]
