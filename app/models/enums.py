"""Enum types matching Prisma schema."""

import enum


class UserStatus(str, enum.Enum):
    """User account status."""

    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"


class SharePermission(str, enum.Enum):
    """Document/File share permission level."""

    VIEW = "VIEW"  # View only (alias for READ)
    READ = "READ"  # Read access
    DOWNLOAD = "DOWNLOAD"  # Can download
    EDIT = "EDIT"  # Can edit
    COMMENT = "COMMENT"  # Can comment


class AttendeeStatus(str, enum.Enum):
    """Calendar event attendee response status."""

    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    DECLINED = "DECLINED"
