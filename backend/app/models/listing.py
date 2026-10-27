"""Crop catalogue and listing models."""
import enum
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, Numeric,
    ForeignKey, Enum, Index, CheckConstraint,
)
from app.core.database import Base


class ListingStatus(str, enum.Enum):
    """Lifecycle status of a crop listing."""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    SOLD = "sold"
    EXPIRED = "expired"
    CLOSED = "closed"


class NegotiabilityType(str, enum.Enum):
    """Whether the price is negotiable."""
    FIXED = "fixed"
    NEGOTIABLE = "negotiable"
    AUCTION = "auction"


class DeliveryPreference(str, enum.Enum):
    """Pickup or delivery preference."""
    PICKUP = "pickup"
    DELIVERY = "delivery"
    BOTH = "both"


class CropCatalogue(Base):
    """Master catalogue of crops and varieties."""
    __tablename__ = "crop_catalogue"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name_en = Column(String(255), nullable=False)
    name_mr = Column(String(255), nullable=True)
    category = Column(String(100), nullable=True)  # grains, vegetables, fruits, spices, oilseeds, pulses, etc.
    variety = Column(String(255), nullable=True)
    unit_options = Column(String(500), default="kg,quintal,ton")  # comma-separated valid units
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("ix_crop_name_en", "name_en"),
        Index("ix_crop_category", "category"),
    )


class CropListing(Base):
    """A farmer's crop listing on the marketplace."""
    __tablename__ = "crop_listings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    seller_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    crop_id = Column(Integer, ForeignKey("crop_catalogue.id"), nullable=True)

    # Crop details
    crop_name = Column(String(255), nullable=False)
    crop_variety = Column(String(255), nullable=True)
    category = Column(String(100), nullable=True)
    grade = Column(String(100), nullable=True)
    quality_description = Column(Text, nullable=True)

    # Quantity and pricing
    quantity = Column(Numeric(12, 2), nullable=False)
    unit = Column(String(20), nullable=False)  # kg, quintal, ton
    asking_price = Column(Numeric(12, 2), nullable=False)
    price_currency = Column(String(3), default="INR", nullable=False)
    negotiability = Column(Enum(NegotiabilityType), default=NegotiabilityType.NEGOTIABLE)

    # Availability
    available_from = Column(DateTime(timezone=True), nullable=True)
    harvest_date = Column(DateTime(timezone=True), nullable=True)
    expiry_date = Column(DateTime(timezone=True), nullable=True)

    # Location
    location = Column(String(500), nullable=True)
    village = Column(String(255), nullable=True)
    taluka = Column(String(255), nullable=True)
    district = Column(String(255), nullable=True)
    state = Column(String(100), default="Maharashtra")
    pincode = Column(String(10), nullable=True)

    # Delivery
    delivery_preference = Column(Enum(DeliveryPreference), default=DeliveryPreference.BOTH)
    delivery_notes = Column(Text, nullable=True)

    # Images and docs
    images = Column(Text, nullable=True)  # JSON array of image URLs
    quality_docs = Column(Text, nullable=True)  # JSON array of doc URLs

    # Status
    status = Column(Enum(ListingStatus), default=ListingStatus.DRAFT, nullable=False)
    view_count = Column(Integer, default=0)
    offer_count = Column(Integer, default=0)
    quantity_remaining = Column(Numeric(12, 2), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    published_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_listing_positive_quantity"),
        CheckConstraint("asking_price > 0", name="ck_listing_positive_price"),
        Index("ix_listing_status", "status"),
        Index("ix_listing_crop_name", "crop_name"),
        Index("ix_listing_district", "district"),
        Index("ix_listing_active_crop", "status", "crop_name"),
        Index("ix_listing_seller_status", "seller_id", "status"),
    )
