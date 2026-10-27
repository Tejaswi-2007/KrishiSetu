"""Deal room models for negotiation workspaces."""
import enum
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime,
    ForeignKey, Enum, Index,
)
from app.core.database import Base


class DealRoomStatus(str, enum.Enum):
    """Deal room lifecycle status."""
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ParticipantRole(str, enum.Enum):
    """Role of a participant in a deal room."""
    HOST = "host"
    PARTICIPANT = "participant"
    OBSERVER = "observer"


class DealRoom(Base):
    """A negotiation workspace."""
    __tablename__ = "deal_rooms"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)

    # Links to listing/offer
    listing_id = Column(Integer, ForeignKey("crop_listings.id"), nullable=True)
    offer_id = Column(Integer, ForeignKey("offers.id"), nullable=True)

    # Creator
    created_by = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Schedule
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)

    # Video conferencing
    jitsi_room_name = Column(String(255), nullable=True)
    video_enabled = Column(Boolean, default=True)

    # Status
    status = Column(Enum(DealRoomStatus), default=DealRoomStatus.SCHEDULED, nullable=False)

    # Notes
    notes = Column(Text, nullable=True)
    outcome = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("ix_deal_room_status", "status"),
        Index("ix_deal_room_creator", "created_by"),
    )


class DealRoomParticipant(Base):
    """Participants in a deal room."""
    __tablename__ = "deal_room_participants"

    id = Column(Integer, primary_key=True, autoincrement=True)
    room_id = Column(Integer, ForeignKey("deal_rooms.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(Enum(ParticipantRole), default=ParticipantRole.PARTICIPANT)
    joined_at = Column(DateTime(timezone=True), nullable=True)
    left_at = Column(DateTime(timezone=True), nullable=True)
    is_online = Column(Boolean, default=False)
    invited_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_drp_room_user", "room_id", "user_id", unique=True),
    )


class ChatMessage(Base):
    """Persistent chat messages in a deal room."""
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    room_id = Column(Integer, ForeignKey("deal_rooms.id", ondelete="CASCADE"), nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    content = Column(Text, nullable=False)
    message_type = Column(String(50), default="text")  # text, system, offer_update, file
    metadata_json = Column(Text, nullable=True)  # additional structured data
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("ix_chat_room_created", "room_id", "created_at"),
    )
