"""Database models package."""

from app.models.activity import ActivityLog
from app.models.base import Base, generate_cuid
from app.models.calendar import CalendarEvent, EventAttendee, EventReminder
from app.models.conversation import Conversation, ConversationParticipant, Message
from app.models.document import Document, DocumentShare, DocumentTag, Tag
from app.models.enums import AttendeeStatus, SharePermission, UserStatus
from app.models.file import File, FileAccessLog, FileShare, Folder
from app.models.notification import Notification
from app.models.password_reset_token import PasswordResetToken
from app.models.refresh_token import RefreshToken
from app.models.role import Permission, Role, RolePermission, UserRole
from app.models.team import Team, TeamMember
from app.models.user import User

__all__ = [
    # Base
    "Base",
    "generate_cuid",
    # Enums
    "UserStatus",
    "SharePermission",
    "AttendeeStatus",
    # User & Auth
    "User",
    "RefreshToken",
    "PasswordResetToken",
    # Role & Permission
    "Role",
    "Permission",
    "RolePermission",
    "UserRole",
    # Team
    "Team",
    "TeamMember",
    # Document
    "Document",
    "DocumentShare",
    "Tag",
    "DocumentTag",
    # File & Folder
    "File",
    "Folder",
    "FileShare",
    "FileAccessLog",
    # Calendar
    "CalendarEvent",
    "EventAttendee",
    "EventReminder",
    # Conversation & Message
    "Conversation",
    "ConversationParticipant",
    "Message",
    # Notification
    "Notification",
    # Activity
    "ActivityLog",
]
