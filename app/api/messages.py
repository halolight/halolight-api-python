"""Message and conversation management routes matching API spec."""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_active_user
from app.core.database import get_db
from app.models import Conversation, ConversationParticipant, Message, User
from app.models.base import generate_cuid
from app.schemas.user import UserBasicResponse

router = APIRouter(prefix="/messages", tags=["Messages"])


# ============== Schemas ==============
class MessageCreate(BaseModel):
    content: str
    conversationId: str | None = None
    recipientId: str | None = None  # For new conversations


class MessageResponse(BaseModel):
    id: str
    content: str
    sender: UserBasicResponse
    isRead: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationResponse(BaseModel):
    id: str
    participants: list[UserBasicResponse] = Field(default_factory=list)
    lastMessage: MessageResponse | None = None
    unreadCount: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ConversationListResponse(BaseModel):
    data: list[ConversationResponse]


class MessageListResponse(BaseModel):
    data: list[MessageResponse]


# ============== Helper ==============
def _build_message_response(message: Message) -> MessageResponse:
    return MessageResponse(
        id=message.id,
        content=message.content,
        sender=UserBasicResponse(
            id=message.sender.id,
            email=message.sender.email,
            name=message.sender.name,
            avatar=message.sender.avatar,
        ),
        isRead=message.is_read,
        created_at=message.created_at,
    )


def _build_conversation_response(
    conversation: Conversation, current_user_id: str, db: Session
) -> ConversationResponse:
    participants = []
    for p in conversation.participants:
        participants.append(
            UserBasicResponse(
                id=p.user.id,
                email=p.user.email,
                name=p.user.name,
                avatar=p.user.avatar,
            )
        )

    # Get last message
    last_message = (
        db.query(Message)
        .filter(Message.conversation_id == conversation.id)
        .options(joinedload(Message.sender))
        .order_by(Message.created_at.desc())
        .first()
    )

    # Get unread count
    unread_count = (
        db.query(Message)
        .filter(
            Message.conversation_id == conversation.id,
            Message.sender_id != current_user_id,
            Message.is_read.is_(False),
        )
        .count()
    )

    return ConversationResponse(
        id=conversation.id,
        participants=participants,
        lastMessage=_build_message_response(last_message) if last_message else None,
        unreadCount=unread_count,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
    )


# ============== Routes ==============
@router.get("/conversations", response_model=ConversationListResponse)
async def list_conversations(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> ConversationListResponse:
    """Get all conversations for current user."""
    conversations = (
        db.query(Conversation)
        .join(ConversationParticipant)
        .filter(ConversationParticipant.user_id == current_user.id)
        .options(joinedload(Conversation.participants).joinedload(ConversationParticipant.user))
        .order_by(Conversation.updated_at.desc())
        .all()
    )

    return ConversationListResponse(
        data=[_build_conversation_response(c, current_user.id, db) for c in conversations]
    )


@router.get("/conversations/{conversation_id}", response_model=MessageListResponse)
async def get_conversation_messages(
    conversation_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    limit: int = Query(50, ge=1, le=100),
) -> MessageListResponse:
    """Get messages in a conversation."""
    # Verify user is participant
    participant = (
        db.query(ConversationParticipant)
        .filter(
            ConversationParticipant.conversation_id == conversation_id,
            ConversationParticipant.user_id == current_user.id,
        )
        .first()
    )

    if not participant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .options(joinedload(Message.sender))
        .order_by(Message.created_at.desc())
        .limit(limit)
        .all()
    )

    return MessageListResponse(data=[_build_message_response(m) for m in reversed(messages)])


@router.post("/send", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    message_data: MessageCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> MessageResponse:
    """Send a message."""
    conversation_id = message_data.conversationId

    # Create new conversation if needed
    if not conversation_id and message_data.recipientId:
        # Check if conversation already exists between users
        existing = (
            db.query(Conversation)
            .join(ConversationParticipant)
            .filter(ConversationParticipant.user_id == current_user.id)
            .filter(
                Conversation.id.in_(
                    db.query(ConversationParticipant.conversation_id).filter(
                        ConversationParticipant.user_id == message_data.recipientId
                    )
                )
            )
            .first()
        )

        if existing:
            conversation_id = existing.id
        else:
            # Create new conversation
            conversation = Conversation(id=generate_cuid())
            db.add(conversation)
            db.flush()

            # Add participants
            db.add(
                ConversationParticipant(conversation_id=conversation.id, user_id=current_user.id)
            )
            db.add(
                ConversationParticipant(
                    conversation_id=conversation.id, user_id=message_data.recipientId
                )
            )
            conversation_id = conversation.id

    if not conversation_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either conversationId or recipientId is required",
        )

    # Verify user is participant
    participant = (
        db.query(ConversationParticipant)
        .filter(
            ConversationParticipant.conversation_id == conversation_id,
            ConversationParticipant.user_id == current_user.id,
        )
        .first()
    )

    if not participant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not a participant in this conversation"
        )

    # Create message
    message = Message(
        id=generate_cuid(),
        conversation_id=conversation_id,
        sender_id=current_user.id,
        content=message_data.content,
    )

    db.add(message)

    # Update conversation timestamp
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if conversation:
        from datetime import datetime

        conversation.updated_at = datetime.now(UTC)

    db.commit()

    message = (
        db.query(Message)
        .filter(Message.id == message.id)
        .options(joinedload(Message.sender))
        .first()
    )
    return _build_message_response(message)


@router.put("/conversations/{conversation_id}/read")
async def mark_conversation_read(
    conversation_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> dict[str, str]:
    """Mark all messages in conversation as read."""
    # Verify user is participant
    participant = (
        db.query(ConversationParticipant)
        .filter(
            ConversationParticipant.conversation_id == conversation_id,
            ConversationParticipant.user_id == current_user.id,
        )
        .first()
    )

    if not participant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    # Mark messages as read
    db.query(Message).filter(
        Message.conversation_id == conversation_id,
        Message.sender_id != current_user.id,
        Message.is_read.is_(False),
    ).update({"is_read": True}, synchronize_session=False)
    db.commit()

    return {"message": "Messages marked as read"}


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> dict[str, str]:
    """Delete conversation (removes user from participants)."""
    participant = (
        db.query(ConversationParticipant)
        .filter(
            ConversationParticipant.conversation_id == conversation_id,
            ConversationParticipant.user_id == current_user.id,
        )
        .first()
    )

    if not participant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    db.delete(participant)
    db.commit()

    return {"message": "Conversation deleted successfully", "id": conversation_id}
