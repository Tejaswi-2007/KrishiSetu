'''Auction and Bid models.'''

from datetime import datetime, timezone
from decimal import Decimal

import enum
from sqlalchemy import (
    Column, Integer, String, DateTime, Numeric, ForeignKey, Enum, CheckConstraint, Index, Text
)
from sqlalchemy.orm import relationship

from app.core.database import Base
from .listing import NegotiabilityType

class AuctionStatus(str, enum.Enum):
    """Lifecycle of an auction."""
    SCHEDULED = "scheduled"
    LIVE = "live"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class Auction(Base):
    __tablename__ = "auctions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    seller_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    # Reference to a CropListing (could be None if created directly)
    listing_id = Column(Integer, ForeignKey("crop_listings.id", ondelete="SET NULL"), nullable=True)

    # Core details (duplicate some fields for convenience)
    crop_name = Column(String(255), nullable=False)
    crop_variety = Column(String(255), nullable=True)
    category = Column(String(100), nullable=True)
    quantity = Column(Numeric(12, 2), nullable=False)
    unit = Column(String(20), nullable=False)
    starting_price = Column(Numeric(12, 2), nullable=False)
    expected_price = Column(Numeric(12, 2), nullable=True)  # seller's expectation
    location = Column(String(500), nullable=True)

    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)

    status = Column(Enum(AuctionStatus), default=AuctionStatus.SCHEDULED, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    bids = relationship("Bid", back_populates="auction", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_auction_positive_quantity"),
        CheckConstraint("starting_price > 0", name="ck_auction_positive_start_price"),
        Index("ix_auction_status", "status"),
        Index("ix_auction_seller", "seller_id"),
    )

class Bid(Base):
    __tablename__ = "bids"

    id = Column(Integer, primary_key=True, autoincrement=True)
    auction_id = Column(Integer, ForeignKey("auctions.id", ondelete="CASCADE"), nullable=False, index=True)
    bidder_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    amount = Column(Numeric(12, 2), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    auction = relationship("Auction", back_populates="bids")

    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_bid_positive_amount"),
        Index("ix_bid_auction_bidder", "auction_id", "bidder_id"),
    )
