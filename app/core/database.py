"""Database connection and session management."""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from .config import settings

# Create database engine
engine = create_engine(
    str(settings.DATABASE_URL),
    echo=settings.DATABASE_ECHO,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Import Base from models for backward compatibility
from app.models.base import Base  # noqa: E402, F401


def get_db() -> Generator[Session, None, None]:
    """Get database session.

    Yields:
        Database session

    This is a dependency that can be injected into FastAPI routes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
