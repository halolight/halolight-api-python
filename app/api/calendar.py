"""Calendar event management routes matching API spec."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_active_user
from app.core.database import get_db
from app.models import CalendarEvent, EventAttendee, User
from app.models.base import generate_cuid
from app.schemas.user import UserBasicResponse

router = APIRouter(prefix="/calendar", tags=["Calendar"])


# ============== Schemas ==============
class EventCreate(BaseModel):
    title: str
    description: str | None = None
    startTime: datetime
    endTime: datetime
    location: str | None = None
    isAllDay: bool = False
    color: str | None = None


class EventUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    startTime: datetime | None = None
    endTime: datetime | None = None
    location: str | None = None
    isAllDay: bool | None = None
    color: str | None = None


class EventReschedule(BaseModel):
    startTime: datetime
    endTime: datetime


class AddAttendee(BaseModel):
    userId: str
    status: str = "PENDING"  # PENDING, ACCEPTED, DECLINED, TENTATIVE


class AttendeeResponse(BaseModel):
    id: str
    user: UserBasicResponse
    status: str

    model_config = {"from_attributes": True}


class EventResponse(BaseModel):
    id: str
    title: str
    description: str | None = None
    startTime: datetime
    endTime: datetime
    location: str | None = None
    isAllDay: bool = False
    color: str | None = None
    organizer: UserBasicResponse
    attendees: list[AttendeeResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EventListResponse(BaseModel):
    data: list[EventResponse]


class BatchDeleteRequest(BaseModel):
    ids: list[str]


class BatchDeleteResponse(BaseModel):
    message: str
    deleted_count: int


# ============== Helper ==============
def _build_event_response(event: CalendarEvent) -> EventResponse:
    attendees = []
    if event.attendees:
        for att in event.attendees:
            attendees.append(
                AttendeeResponse(
                    id=att.id,
                    user=UserBasicResponse(
                        id=att.user.id,
                        email=att.user.email,
                        name=att.user.name,
                        avatar=att.user.avatar,
                    ),
                    status=att.status,
                )
            )

    return EventResponse(
        id=event.id,
        title=event.title,
        description=event.description,
        startTime=event.start_time,
        endTime=event.end_time,
        location=event.location,
        isAllDay=event.is_all_day,
        color=event.color,
        organizer=UserBasicResponse(
            id=event.organizer.id,
            email=event.organizer.email,
            name=event.organizer.name,
            avatar=event.organizer.avatar,
        ),
        attendees=attendees,
        created_at=event.created_at,
        updated_at=event.updated_at,
    )


# ============== Routes ==============
@router.get("/events", response_model=EventListResponse)
async def list_events(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    start: datetime | None = None,
    end: datetime | None = None,
) -> EventListResponse:
    """Get calendar events with optional date range filter."""
    query = db.query(CalendarEvent).filter(CalendarEvent.organizer_id == current_user.id)
    query = query.options(
        joinedload(CalendarEvent.organizer),
        joinedload(CalendarEvent.attendees).joinedload(EventAttendee.user),
    )

    if start:
        query = query.filter(CalendarEvent.start_time >= start)
    if end:
        query = query.filter(CalendarEvent.end_time <= end)

    events = query.order_by(CalendarEvent.start_time).all()

    return EventListResponse(data=[_build_event_response(e) for e in events])


@router.get("/events/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> EventResponse:
    """Get event by ID."""
    event = (
        db.query(CalendarEvent)
        .filter(CalendarEvent.id == event_id, CalendarEvent.organizer_id == current_user.id)
        .options(
            joinedload(CalendarEvent.organizer),
            joinedload(CalendarEvent.attendees).joinedload(EventAttendee.user),
        )
        .first()
    )

    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    return _build_event_response(event)


@router.post("/events", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(
    event_data: EventCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> EventResponse:
    """Create a new calendar event."""
    event = CalendarEvent(
        id=generate_cuid(),
        title=event_data.title,
        description=event_data.description,
        start_time=event_data.startTime,
        end_time=event_data.endTime,
        location=event_data.location,
        is_all_day=event_data.isAllDay,
        color=event_data.color,
        organizer_id=current_user.id,
    )

    db.add(event)
    db.commit()

    event = (
        db.query(CalendarEvent)
        .filter(CalendarEvent.id == event.id)
        .options(
            joinedload(CalendarEvent.organizer),
            joinedload(CalendarEvent.attendees).joinedload(EventAttendee.user),
        )
        .first()
    )
    return _build_event_response(event)


@router.put("/events/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: str,
    event_data: EventUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> EventResponse:
    """Update event information."""
    event = (
        db.query(CalendarEvent)
        .filter(CalendarEvent.id == event_id, CalendarEvent.organizer_id == current_user.id)
        .first()
    )

    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    update_dict = event_data.model_dump(exclude_unset=True)
    field_mapping = {
        "startTime": "start_time",
        "endTime": "end_time",
        "isAllDay": "is_all_day",
    }

    for key, value in update_dict.items():
        if value is not None:
            db_field = field_mapping.get(key, key)
            setattr(event, db_field, value)

    db.commit()

    event = (
        db.query(CalendarEvent)
        .filter(CalendarEvent.id == event.id)
        .options(
            joinedload(CalendarEvent.organizer),
            joinedload(CalendarEvent.attendees).joinedload(EventAttendee.user),
        )
        .first()
    )
    return _build_event_response(event)


@router.patch("/events/{event_id}/reschedule", response_model=EventResponse)
async def reschedule_event(
    event_id: str,
    reschedule_data: EventReschedule,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> EventResponse:
    """Reschedule event time."""
    event = (
        db.query(CalendarEvent)
        .filter(CalendarEvent.id == event_id, CalendarEvent.organizer_id == current_user.id)
        .first()
    )

    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    event.start_time = reschedule_data.startTime
    event.end_time = reschedule_data.endTime
    db.commit()

    event = (
        db.query(CalendarEvent)
        .filter(CalendarEvent.id == event.id)
        .options(
            joinedload(CalendarEvent.organizer),
            joinedload(CalendarEvent.attendees).joinedload(EventAttendee.user),
        )
        .first()
    )
    return _build_event_response(event)


@router.post("/events/{event_id}/attendees", response_model=EventResponse)
async def add_attendee(
    event_id: str,
    attendee_data: AddAttendee,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> EventResponse:
    """Add attendee to event."""
    event = (
        db.query(CalendarEvent)
        .filter(CalendarEvent.id == event_id, CalendarEvent.organizer_id == current_user.id)
        .first()
    )

    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    # Check if user exists
    user = db.query(User).filter(User.id == attendee_data.userId).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Check if already attendee
    existing = (
        db.query(EventAttendee)
        .filter(EventAttendee.event_id == event_id, EventAttendee.user_id == attendee_data.userId)
        .first()
    )

    if existing:
        existing.status = attendee_data.status
    else:
        attendee = EventAttendee(
            id=generate_cuid(),
            event_id=event_id,
            user_id=attendee_data.userId,
            status=attendee_data.status,
        )
        db.add(attendee)

    db.commit()

    event = (
        db.query(CalendarEvent)
        .filter(CalendarEvent.id == event.id)
        .options(
            joinedload(CalendarEvent.organizer),
            joinedload(CalendarEvent.attendees).joinedload(EventAttendee.user),
        )
        .first()
    )
    return _build_event_response(event)


@router.delete("/events/{event_id}/attendees/{attendee_id}")
async def remove_attendee(
    event_id: str,
    attendee_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> dict[str, str]:
    """Remove attendee from event."""
    event = (
        db.query(CalendarEvent)
        .filter(CalendarEvent.id == event_id, CalendarEvent.organizer_id == current_user.id)
        .first()
    )

    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    attendee = (
        db.query(EventAttendee)
        .filter(EventAttendee.id == attendee_id, EventAttendee.event_id == event_id)
        .first()
    )

    if not attendee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attendee not found")

    db.delete(attendee)
    db.commit()

    return {"message": "Attendee removed successfully"}


@router.post("/events/batch-delete", response_model=BatchDeleteResponse)
async def batch_delete_events(
    delete_data: BatchDeleteRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> BatchDeleteResponse:
    """Batch delete events."""
    deleted = (
        db.query(CalendarEvent)
        .filter(
            CalendarEvent.id.in_(delete_data.ids),
            CalendarEvent.organizer_id == current_user.id,
        )
        .delete(synchronize_session=False)
    )
    db.commit()

    return BatchDeleteResponse(
        message=f"Successfully deleted {deleted} events",
        deleted_count=deleted,
    )


@router.delete("/events/{event_id}")
async def delete_event(
    event_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> dict[str, str]:
    """Delete event."""
    event = (
        db.query(CalendarEvent)
        .filter(CalendarEvent.id == event_id, CalendarEvent.organizer_id == current_user.id)
        .first()
    )

    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    db.delete(event)
    db.commit()

    return {"message": "Event successfully deleted", "id": event_id}
