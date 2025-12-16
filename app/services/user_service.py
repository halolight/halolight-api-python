"""User service for business logic."""

from datetime import UTC, datetime
from math import ceil

from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.core.security import hash_password, verify_password
from app.models import RefreshToken, Role, RolePermission, User, UserRole, UserStatus
from app.models.base import generate_cuid
from app.schemas.user import RegisterRequest, UserCreate, UserUpdate


class UserService:
    """User service for managing user operations."""

    def __init__(self, db: Session) -> None:
        """Initialize user service.

        Args:
            db: Database session
        """
        self.db = db

    def get_by_id(self, user_id: str, with_roles: bool = False) -> User | None:
        """Get user by ID.

        Args:
            user_id: User ID
            with_roles: Whether to eager load roles

        Returns:
            User or None if not found
        """
        query = self.db.query(User).filter(User.id == user_id)
        if with_roles:
            query = query.options(
                joinedload(User.roles)
                .joinedload(UserRole.role)
                .joinedload(Role.permissions)
                .joinedload(RolePermission.permission)
            )
        return query.first()

    def get_by_email(self, email: str) -> User | None:
        """Get user by email.

        Args:
            email: User email

        Returns:
            User or None if not found
        """
        return self.db.query(User).filter(User.email == email).first()

    def get_by_username(self, username: str) -> User | None:
        """Get user by username.

        Args:
            username: Username

        Returns:
            User or None if not found
        """
        return self.db.query(User).filter(User.username == username).first()

    def get_all(
        self,
        page: int = 1,
        limit: int = 10,
        search: str | None = None,
        status: str | None = None,
        role: str | None = None,
    ) -> tuple[list[User], int]:
        """Get all users with pagination and filtering.

        Args:
            page: Page number (1-indexed)
            limit: Number of records per page
            search: Search keyword for name, username, or email
            status: Filter by status (ACTIVE, INACTIVE, SUSPENDED, or 'all')
            role: Filter by role name (or 'all')

        Returns:
            Tuple of (list of users, total count)
        """
        query = self.db.query(User)

        # Search filter
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    User.name.ilike(search_pattern),
                    User.username.ilike(search_pattern),
                    User.email.ilike(search_pattern),
                )
            )

        # Status filter
        if status and status.lower() != "all":
            query = query.filter(User.status == status.upper())

        # Role filter (requires join)
        if role and role.lower() != "all":
            query = query.join(User.roles).join(UserRole.role).filter(Role.name == role)

        # Get total count before pagination
        total = query.count()

        # Apply pagination
        skip = (page - 1) * limit
        users = query.offset(skip).limit(limit).all()

        return users, total

    def create(
        self,
        user_data: UserCreate | RegisterRequest,
        default_role_id: str | None = None,
    ) -> User:
        """Create a new user.

        Args:
            user_data: User creation data
            default_role_id: Default role ID to assign

        Returns:
            Created user

        Raises:
            ValueError: If user with email/username already exists
        """
        # Check if email exists
        existing_user = self.get_by_email(user_data.email)
        if existing_user:
            raise ValueError("User with this email already exists")

        # Generate username from email if not provided
        username = getattr(user_data, "username", None)
        if not username:
            # Extract username from email (before @)
            username = user_data.email.split("@")[0]
            # Ensure uniqueness by appending random suffix if needed
            base_username = username
            counter = 1
            while self.get_by_username(username):
                username = f"{base_username}{counter}"
                counter += 1

        # Check if username exists
        if self.get_by_username(username):
            raise ValueError("User with this username already exists")

        # Generate cuid
        user_id = generate_cuid()

        # Hash password
        hashed_password = hash_password(user_data.password)

        # Create user
        user = User(
            id=user_id,
            email=user_data.email,
            username=username,
            name=user_data.name,
            password=hashed_password,
            phone=getattr(user_data, "phone", None),
            avatar=getattr(user_data, "avatar", None),
            status=getattr(user_data, "status", UserStatus.ACTIVE),
        )

        self.db.add(user)
        self.db.flush()  # Flush to get the ID before adding role

        # Assign default role if provided
        if default_role_id:
            user_role = UserRole(user_id=user.id, role_id=default_role_id)
            self.db.add(user_role)

        self.db.commit()
        self.db.refresh(user)

        return user

    def update(self, user_id: str, user_data: UserUpdate) -> User | None:
        """Update user.

        Args:
            user_id: User ID
            user_data: User update data

        Returns:
            Updated user or None if not found
        """
        user = self.get_by_id(user_id)
        if not user:
            return None

        # Update fields
        update_dict = user_data.model_dump(exclude_unset=True)

        # Hash password if provided
        if "password" in update_dict and update_dict["password"]:
            update_dict["password"] = hash_password(update_dict["password"])

        for key, value in update_dict.items():
            if value is not None:
                setattr(user, key, value)

        self.db.commit()
        self.db.refresh(user)

        return user

    def update_status(self, user_id: str, status: UserStatus) -> User | None:
        """Update user status.

        Args:
            user_id: User ID
            status: New status

        Returns:
            Updated user or None if not found
        """
        user = self.get_by_id(user_id)
        if not user:
            return None

        user.status = status
        self.db.commit()
        self.db.refresh(user)

        return user

    def update_last_login(self, user_id: str) -> None:
        """Update user's last login timestamp.

        Args:
            user_id: User ID
        """
        user = self.get_by_id(user_id)
        if user:
            user.last_login_at = datetime.now(UTC)
            self.db.commit()

    def delete(self, user_id: str) -> bool:
        """Delete user.

        Args:
            user_id: User ID

        Returns:
            True if deleted, False if not found
        """
        user = self.get_by_id(user_id)
        if not user:
            return False

        self.db.delete(user)
        self.db.commit()

        return True

    def batch_delete(self, user_ids: list[str]) -> int:
        """Delete multiple users.

        Args:
            user_ids: List of user IDs to delete

        Returns:
            Number of users deleted
        """
        deleted_count = (
            self.db.query(User).filter(User.id.in_(user_ids)).delete(synchronize_session=False)
        )
        self.db.commit()
        return deleted_count

    def verify_password(self, user: User, password: str) -> bool:
        """Verify user password.

        Args:
            user: User object
            password: Plain text password

        Returns:
            True if password is correct, False otherwise
        """
        return verify_password(password, user.password)

    def calculate_pagination(self, total: int, page: int, limit: int) -> dict[str, int]:
        """Calculate pagination metadata.

        Args:
            total: Total number of records
            page: Current page number (1-indexed)
            limit: Number of records per page

        Returns:
            Dictionary with pagination metadata
        """
        total_pages = ceil(total / limit) if limit > 0 else 0
        return {
            "total": total,
            "page": page,
            "limit": limit,
            "totalPages": total_pages,
        }


class RefreshTokenService:
    """Service for managing refresh tokens."""

    def __init__(self, db: Session) -> None:
        """Initialize refresh token service.

        Args:
            db: Database session
        """
        self.db = db

    def create(self, user_id: str, token: str, expires_at: datetime) -> RefreshToken:
        """Create a new refresh token.

        Args:
            user_id: User ID
            token: Refresh token string
            expires_at: Token expiration datetime

        Returns:
            Created refresh token
        """
        refresh_token = RefreshToken(
            id=generate_cuid(),
            user_id=user_id,
            token=token,
            expires_at=expires_at,
        )

        self.db.add(refresh_token)
        self.db.commit()
        self.db.refresh(refresh_token)

        return refresh_token

    def get_by_token(self, token: str) -> RefreshToken | None:
        """Get refresh token by token string.

        Args:
            token: Refresh token string

        Returns:
            RefreshToken or None if not found
        """
        return self.db.query(RefreshToken).filter(RefreshToken.token == token).first()

    def delete(self, token: str) -> bool:
        """Delete refresh token.

        Args:
            token: Refresh token string

        Returns:
            True if deleted, False if not found
        """
        refresh_token = self.get_by_token(token)
        if not refresh_token:
            return False

        self.db.delete(refresh_token)
        self.db.commit()

        return True

    def delete_all_for_user(self, user_id: str) -> int:
        """Delete all refresh tokens for a user.

        Args:
            user_id: User ID

        Returns:
            Number of tokens deleted
        """
        deleted_count = (
            self.db.query(RefreshToken)
            .filter(RefreshToken.user_id == user_id)
            .delete(synchronize_session=False)
        )
        self.db.commit()
        return deleted_count

    def is_valid(self, refresh_token: RefreshToken) -> bool:
        """Check if refresh token is valid (not expired).

        Args:
            refresh_token: RefreshToken object

        Returns:
            True if valid, False otherwise
        """
        return refresh_token.expires_at > datetime.now(UTC)

    def rotate(
        self, old_token: str, user_id: str, new_token: str, expires_at: datetime
    ) -> RefreshToken | None:
        """Rotate refresh token (delete old, create new).

        Args:
            old_token: Old refresh token string
            user_id: User ID
            new_token: New refresh token string
            expires_at: New token expiration datetime

        Returns:
            New RefreshToken or None if old token not found
        """
        # Delete old token
        if not self.delete(old_token):
            return None

        # Create new token
        return self.create(user_id, new_token, expires_at)
