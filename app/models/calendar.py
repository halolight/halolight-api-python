"""Calendar event models matching Prisma schema."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, generate_cuid
from app.models.enums import AttendeeStatus

if TYPE_CHECKING:
    from app.models.user import User


# PostgreSQL enum type - must match Prisma's created enum
attendee_status_enum = ENUM(
    "PENDING",
    "ACCEPTED",
    "DECLINED",
    name="AttendeeStatus",
    create_type=False,  # Prisma already created it
)


class CalendarEvent(Base):
    """Calendar event model - matches Prisma calendar_events table."""

    __tablename__ = "calendar_events"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_cuid)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    type: Mapped[str] = mapped_column(String, nullable=False)  # meeting, task, reminder, holiday
    color: Mapped[str | None] = mapped_column(String, nullable=True)
    all_day: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    location: Mapped[str | None] = mapped_column(String, nullable=True)
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
        "User", back_populates="owned_events", foreign_keys=[owner_id]
    )
    attendees: Mapped[list[EventAttendee]] = relationship(
        "EventAttendee", back_populates="event", cascade="all, delete-orphan"
    )
    reminders: Mapped[list[EventReminder]] = relationship(
        "EventReminder", back_populates="event", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_calendar_events_owner_id", "owner_id"),
        Index("idx_calendar_events_start_at_end_at", "start_at", "end_at"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<CalendarEvent(id={self.id}, title={self.title})>"


class EventAttendee(Base):
    """Event attendee junction table - matches Prisma event_attendees table."""

    __tablename__ = "event_attendees"

    event_id: Mapped[str] = mapped_column(
        ForeignKey("calendar_events.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    status: Mapped[str] = mapped_column(
        attendee_status_enum,
        nullable=False,
        server_default=AttendeeStatus.PENDING.value,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    event: Mapped[CalendarEvent] = relationship("CalendarEvent", back_populates="attendees")
    user: Mapped[User] = relationship("User", back_populates="event_attendances")

    def __repr__(self) -> str:
        """String representation."""
        return f"<EventAttendee(event_id={self.event_id}, user_id={self.user_id})>"


class EventReminder(Base):
    """Event reminder model - matches Prisma event_reminders table."""

    __tablename__ = "event_reminders"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_cuid)
    event_id: Mapped[str] = mapped_column(
        ForeignKey("calendar_events.id", ondelete="CASCADE"), nullable=False
    )
    remind_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    event: Mapped[CalendarEvent] = relationship("CalendarEvent", back_populates="reminders")

    def __repr__(self) -> str:
        """String representation."""
        return f"<EventReminder(id={self.id}, event_id={self.event_id})>"
