"""Offer and offer event models for the negotiation system."""
import enum
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Text, Numeric, DateTime,
    ForeignKey, Enum, Index, CheckConstraint,
)
from app.core.database import Base


class OfferStatus(str, enum.Enum):
    """Status of an offer."""
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    COUNTERED = "countered"
    WITHDRAWN = "withdrawn"
    EXPIRED = "expired"


class OfferEventType(str, enum.Enum):
    """Types of offer events for audit trail."""
    CREATED = "created"
    UPDATED = "updated"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    COUNTERED = "countered"
    WITHDRAWN = "withdrawn"
    EXPIRED = "expired"


class Offer(Base):
    """An offer on a crop listing."""
    __tablename__ = "offers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    listing_id = Column(Integer, ForeignKey("crop_listings.id", ondelete="CASCADE"), nullable=False)
    buyer_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    seller_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Offer details
    offered_price = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), default="INR", nullable=False)
    quantity = Column(Numeric(12, 2), nullable=False)
    unit = Column(String(20), nullable=False)

    # Terms
    delivery_terms = Column(Text, nullable=True)
    payment_terms = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    # Counter offer reference
    parent_offer_id = Column(Integer, ForeignKey("offers.id"), nullable=True)

    # Status
    status = Column(Enum(OfferStatus), default=OfferStatus.PENDING, nullable=False)
    version = Column(Integer, default=1, nullable=False)

    # Idempotency
    idempotency_key = Column(String(100), unique=True, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    responded_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint("offered_price > 0", name="ck_offer_positive_price"),
        CheckConstraint("quantity > 0", name="ck_offer_positive_quantity"),
        Index("ix_offer_listing", "listing_id"),
        Index("ix_offer_buyer", "buyer_id"),
        Index("ix_offer_seller", "seller_id"),
        Index("ix_offer_status", "status"),
        Index("ix_offer_listing_status", "listing_id", "status"),
    )


class OfferEvent(Base):
    """Audit trail of offer changes."""
    __tablename__ = "offer_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    offer_id = Column(Integer, ForeignKey("offers.id", ondelete="CASCADE"), nullable=False)
    event_type = Column(Enum(OfferEventType), nullable=False)
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    old_status = Column(String(20), nullable=True)
    new_status = Column(String(20), nullable=True)
    old_price = Column(Numeric(12, 2), nullable=True)
    new_price = Column(Numeric(12, 2), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("ix_offer_event_offer", "offer_id"),
    )
