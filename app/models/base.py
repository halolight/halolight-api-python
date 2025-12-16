"""Base model and utilities."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass


def generate_cuid() -> str:
    """Generate a cuid-like identifier.

    Format matches Prisma's cuid() output: starts with 'c' followed by
    25 alphanumeric characters (lowercase).

    Returns:
        A cuid-style string identifier.
    """
    # Generate a UUID and convert to a cuid-like format
    # cuid format: c + 25 chars (lowercase alphanumeric)
    uid = uuid.uuid4().hex + uuid.uuid4().hex[:7]  # 32 + 7 = 39 chars
    return f"c{uid[:24]}"  # c + 24 chars = 25 total
