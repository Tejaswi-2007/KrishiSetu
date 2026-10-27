"""Deal rooms API endpoints."""
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, List

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.deal_room import DealRoom, DealRoomParticipant, ChatMessage, DealRoomStatus, ParticipantRole
from app.models.listing import CropListing
from app.models.offer import Offer
from app.core.config import get_settings

router = APIRouter()
settings = get_settings()


class DealRoomCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    listing_id: Optional[int] = None
    offer_id: Optional[int] = None
    scheduled_at: Optional[datetime] = None
    participant_ids: List[int] = []
    video_enabled: bool = True


class DealRoomResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    listing_id: Optional[int] = None
    offer_id: Optional[int] = None
    created_by: int
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    jitsi_room_name: Optional[str] = None
    video_enabled: bool
    status: str
    notes: Optional[str] = None
    outcome: Optional[str] = None
    created_at: datetime
    participants: list = []
    jitsi_domain: str = ""

    model_config = {"from_attributes": True}


class MessageResponse(BaseModel):
    id: int
    room_id: int
    sender_id: Optional[int] = None
    sender_name: Optional[str] = None
    content: str
    message_type: str
    created_at: datetime


@router.post("", response_model=DealRoomResponse, status_code=status.HTTP_201_CREATED)
def create_deal_room(
    data: DealRoomCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new deal room."""
    jitsi_room = f"digimandi-{uuid.uuid4().hex[:12]}"

    room = DealRoom(
        title=data.title,
        description=data.description,
        listing_id=data.listing_id,
        offer_id=data.offer_id,
        created_by=current_user.id,
        scheduled_at=data.scheduled_at,
        jitsi_room_name=jitsi_room,
        video_enabled=data.video_enabled,
        status=DealRoomStatus.SCHEDULED if data.scheduled_at else DealRoomStatus.ACTIVE,
    )
    db.add(room)
    db.flush()

    # Add creator as host
    db.add(DealRoomParticipant(room_id=room.id, user_id=current_user.id, role=ParticipantRole.HOST))

    # Add other participants
    for pid in data.participant_ids:
        if pid != current_user.id:
            user = db.query(User).filter(User.id == pid).first()
            if user:
                db.add(DealRoomParticipant(room_id=room.id, user_id=pid, role=ParticipantRole.PARTICIPANT))

    db.commit()
    db.refresh(room)

    return _room_to_response(room, db)


@router.get("", response_model=List[DealRoomResponse])
def list_deal_rooms(
    status_filter: str = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List deal rooms the current user participates in."""
    participant_rooms = db.query(DealRoomParticipant.room_id).filter(
        DealRoomParticipant.user_id == current_user.id
    ).subquery()

    query = db.query(DealRoom).filter(DealRoom.id.in_(participant_rooms))
    if status_filter:
        query = query.filter(DealRoom.status == DealRoomStatus(status_filter))

    rooms = query.order_by(DealRoom.created_at.desc()).all()
    return [_room_to_response(r, db) for r in rooms]


@router.get("/{room_id}", response_model=DealRoomResponse)
def get_deal_room(
    room_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get deal room details. Only participants can view."""
    room = db.query(DealRoom).filter(DealRoom.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Deal room not found")

    participant = db.query(DealRoomParticipant).filter(
        DealRoomParticipant.room_id == room_id,
        DealRoomParticipant.user_id == current_user.id,
    ).first()
    if not participant and current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Not a participant in this deal room")

    return _room_to_response(room, db)


@router.post("/{room_id}/messages", response_model=MessageResponse)
def send_message(
    room_id: int,
    content: str = Query(..., min_length=1),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Send a chat message in a deal room."""
    # Verify participation
    participant = db.query(DealRoomParticipant).filter(
        DealRoomParticipant.room_id == room_id,
        DealRoomParticipant.user_id == current_user.id,
    ).first()
    if not participant:
        raise HTTPException(status_code=403, detail="Not a participant")

    msg = ChatMessage(
        room_id=room_id,
        sender_id=current_user.id,
        content=content,
        message_type="text",
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)

    return MessageResponse(
        id=msg.id, room_id=msg.room_id, sender_id=msg.sender_id,
        sender_name=current_user.full_name, content=msg.content,
        message_type=msg.message_type, created_at=msg.created_at,
    )


@router.get("/{room_id}/messages", response_model=List[MessageResponse])
def get_messages(
    room_id: int,
    before_id: int = Query(None),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get chat messages for a deal room."""
    participant = db.query(DealRoomParticipant).filter(
        DealRoomParticipant.room_id == room_id,
        DealRoomParticipant.user_id == current_user.id,
    ).first()
    if not participant:
        raise HTTPException(status_code=403, detail="Not a participant")

    query = db.query(ChatMessage).filter(
        ChatMessage.room_id == room_id,
        ChatMessage.is_deleted == False,
    )
    if before_id:
        query = query.filter(ChatMessage.id < before_id)

    messages = query.order_by(ChatMessage.created_at.desc()).limit(limit).all()
    messages.reverse()

    # Get sender names
    sender_ids = {m.sender_id for m in messages if m.sender_id}
    senders = {u.id: u.full_name for u in db.query(User).filter(User.id.in_(sender_ids)).all()} if sender_ids else {}

    return [
        MessageResponse(
            id=m.id, room_id=m.room_id, sender_id=m.sender_id,
            sender_name=senders.get(m.sender_id), content=m.content,
            message_type=m.message_type, created_at=m.created_at,
        )
        for m in messages
    ]


@router.post("/{room_id}/status")
def update_room_status(
    room_id: int,
    new_status: str = Query(..., pattern="^(active|paused|completed|cancelled)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update deal room status. Only host can update."""
    room = db.query(DealRoom).filter(DealRoom.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Deal room not found")

    participant = db.query(DealRoomParticipant).filter(
        DealRoomParticipant.room_id == room_id,
        DealRoomParticipant.user_id == current_user.id,
        DealRoomParticipant.role == ParticipantRole.HOST,
    ).first()
    if not participant and current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Only the host can update room status")

    now = datetime.now(timezone.utc)
    room.status = DealRoomStatus(new_status)
    if new_status == "active" and not room.started_at:
        room.started_at = now
    elif new_status in ("completed", "cancelled"):
        room.ended_at = now

    db.commit()
    return {"detail": f"Room status updated to {new_status}"}


def _room_to_response(room: DealRoom, db: Session) -> DealRoomResponse:
    """Convert room model to response."""
    participants = db.query(DealRoomParticipant).filter(DealRoomParticipant.room_id == room.id).all()
    user_ids = [p.user_id for p in participants]
    users = {u.id: u for u in db.query(User).filter(User.id.in_(user_ids)).all()} if user_ids else {}

    return DealRoomResponse(
        id=room.id, title=room.title, description=room.description,
        listing_id=room.listing_id, offer_id=room.offer_id,
        created_by=room.created_by, scheduled_at=room.scheduled_at,
        started_at=room.started_at, ended_at=room.ended_at,
        jitsi_room_name=room.jitsi_room_name, video_enabled=room.video_enabled,
        status=room.status.value, notes=room.notes, outcome=room.outcome,
        created_at=room.created_at, jitsi_domain=settings.JITSI_DOMAIN,
        participants=[
            {"user_id": p.user_id, "role": p.role.value,
             "name": users[p.user_id].full_name if p.user_id in users else None,
             "is_online": p.is_online}
            for p in participants
        ],
    )
