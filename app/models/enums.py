"""Enum types matching Prisma schema."""

import enum


class UserStatus(str, enum.Enum):
    """User account status."""

    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"


class SharePermission(str, enum.Enum):
    """Document share permission level."""

    READ = "READ"
    EDIT = "EDIT"
    COMMENT = "COMMENT"


class AttendeeStatus(str, enum.Enum):
    """Calendar event attendee response status."""

    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    DECLINED = "DECLINED"
