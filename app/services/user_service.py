"""User service for business logic."""
import secrets
from math import ceil

from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserUpdate


class UserService:
    """User service for managing user operations."""

    def __init__(self, db: Session) -> None:
        """Initialize user service.

        Args:
            db: Database session
        """
        self.db = db

    def get_by_id(self, user_id: str) -> User | None:
        """Get user by ID.

        Args:
            user_id: User ID

        Returns:
            User or None if not found
        """
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_email(self, email: str) -> User | None:
        """Get user by email.

        Args:
            email: User email

        Returns:
            User or None if not found
        """
        return self.db.query(User).filter(User.email == email).first()

    def get_all(
        self, skip: int = 0, limit: int = 10
    ) -> tuple[list[User], int]:
        """Get all users with pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            Tuple of (list of users, total count)
        """
        query = self.db.query(User)
        total = query.count()
        users = query.offset(skip).limit(limit).all()
        return users, total

    def create(self, user_data: UserCreate, role: UserRole = UserRole.USER) -> User:
        """Create a new user.

        Args:
            user_data: User creation data
            role: User role (default: USER)

        Returns:
            Created user

        Raises:
            ValueError: If user with email already exists
        """
        # Check if user exists
        existing_user = self.get_by_email(user_data.email)
        if existing_user:
            raise ValueError("User with this email already exists")

        # Generate unique ID (using secrets for cryptographically strong random)
        user_id = f"user_{secrets.token_urlsafe(16)}"

        # Hash password
        hashed_password = hash_password(user_data.password)

        # Create user
        user = User(
            id=user_id,
            email=user_data.email,
            name=user_data.name,
            password=hashed_password,
            role=role,
            status="active",
        )

        self.db.add(user)
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
        if "password" in update_dict:
            update_dict["password"] = hash_password(update_dict["password"])

        for key, value in update_dict.items():
            setattr(user, key, value)

        self.db.commit()
        self.db.refresh(user)

        return user

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

    def verify_password(self, user: User, password: str) -> bool:
        """Verify user password.

        Args:
            user: User object
            password: Plain text password

        Returns:
            True if password is correct, False otherwise
        """
        return verify_password(password, user.password)

    def calculate_pagination(
        self, total: int, page: int, page_size: int
    ) -> dict[str, int]:
        """Calculate pagination metadata.

        Args:
            total: Total number of records
            page: Current page number (1-indexed)
            page_size: Number of records per page

        Returns:
            Dictionary with pagination metadata
        """
        total_pages = ceil(total / page_size) if page_size > 0 else 0
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }
