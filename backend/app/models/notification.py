"""Notification model."""
import enum
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime,
    ForeignKey, Enum, Index,
)
from app.core.database import Base


class NotificationType(str, enum.Enum):
    """Types of notifications."""
    NEW_OFFER = "new_offer"
    OFFER_ACCEPTED = "offer_accepted"
    OFFER_REJECTED = "offer_rejected"
    COUNTER_OFFER = "counter_offer"
    DEAL_ROOM_INVITE = "deal_room_invite"
    DEAL_ROOM_REMINDER = "deal_room_reminder"
    AGREEMENT_REVIEW = "agreement_review"
    AGREEMENT_CONFIRMED = "agreement_confirmed"
    DELIVERY_UPDATE = "delivery_update"
    SUPPORT_UPDATE = "support_update"
    SYSTEM = "system"
    LISTING_EXPIRED = "listing_expired"
    PRICE_ALERT = "price_alert"


class Notification(Base):
    """In-app notification record."""
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    type = Column(Enum(NotificationType), nullable=False)
    title = Column(String(500), nullable=False)
    message = Column(Text, nullable=True)
    link = Column(String(500), nullable=True)  # route to navigate to
    is_read = Column(Boolean, default=False, nullable=False)
    metadata_json = Column(Text, nullable=True)

    # Related entity references
    related_id = Column(Integer, nullable=True)
    related_type = Column(String(50), nullable=True)  # offer, listing, deal_room, agreement, etc.

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    read_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_notif_user_unread", "user_id", "is_read"),
        Index("ix_notif_user_created", "user_id", "created_at"),
    )
