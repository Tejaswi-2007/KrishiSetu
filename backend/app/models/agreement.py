"""Agreement and confirmation models."""
import enum
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Text, Numeric, DateTime,
    ForeignKey, Enum, Index,
)
from app.core.database import Base


class AgreementStatus(str, enum.Enum):
    """Status of an agreement."""
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    CONFIRMED = "confirmed"
    DISPUTED = "disputed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class Agreement(Base):
    """A structured agreement between buyer and seller."""
    __tablename__ = "agreements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    deal_room_id = Column(Integer, ForeignKey("deal_rooms.id"), nullable=True)
    offer_id = Column(Integer, ForeignKey("offers.id"), nullable=True)
    listing_id = Column(Integer, ForeignKey("crop_listings.id"), nullable=True)

    # Parties
    seller_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    buyer_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Agreed terms
    crop_name = Column(String(255), nullable=False)
    crop_variety = Column(String(255), nullable=True)
    agreed_quantity = Column(Numeric(12, 2), nullable=False)
    unit = Column(String(20), nullable=False)
    agreed_rate = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), default="INR")
    quality_requirements = Column(Text, nullable=True)

    # Delivery
    delivery_location = Column(Text, nullable=True)
    delivery_date = Column(DateTime(timezone=True), nullable=True)
    delivery_window_start = Column(DateTime(timezone=True), nullable=True)
    delivery_window_end = Column(DateTime(timezone=True), nullable=True)

    # Payment
    payment_terms = Column(Text, nullable=True)
    total_value = Column(Numeric(14, 2), nullable=True)

    # Fees and costs
    commission_rate = Column(Numeric(5, 2), nullable=True)
    transportation_cost = Column(Numeric(12, 2), nullable=True)
    loading_cost = Column(Numeric(12, 2), nullable=True)
    packaging_cost = Column(Numeric(12, 2), nullable=True)
    other_costs = Column(Numeric(12, 2), nullable=True)
    other_costs_description = Column(Text, nullable=True)

    # Cancellation / dispute
    cancellation_terms = Column(Text, nullable=True)
    dispute_terms = Column(Text, nullable=True)

    # Status
    status = Column(Enum(AgreementStatus), default=AgreementStatus.DRAFT, nullable=False)
    version = Column(Integer, default=1)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    confirmed_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_agreement_seller", "seller_id"),
        Index("ix_agreement_buyer", "buyer_id"),
        Index("ix_agreement_status", "status"),
    )


class AgreementConfirmation(Base):
    """Record of explicit confirmation by a party."""
    __tablename__ = "agreement_confirmations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    agreement_id = Column(Integer, ForeignKey("agreements.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    confirmed = Column(String(10), nullable=False)  # "yes" or "no"
    agreement_version = Column(Integer, nullable=False)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    notes = Column(Text, nullable=True)
    confirmed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("ix_ac_agreement_user", "agreement_id", "user_id"),
    )
