"""Profile models for farmers, buyers, and FPOs."""
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime,
    ForeignKey, JSON, Index,
)
from app.core.database import Base


class FarmerProfile(Base):
    """Extended profile for farmer users."""
    __tablename__ = "farmer_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    farm_address = Column(Text, nullable=True)
    village = Column(String(255), nullable=True)
    taluka = Column(String(255), nullable=True)
    district = Column(String(255), nullable=True)
    state = Column(String(100), default="Maharashtra", nullable=False)
    pincode = Column(String(10), nullable=True)
    land_area_acres = Column(String(50), nullable=True)
    primary_crops = Column(JSON, nullable=True)  # List of crop names
    farming_type = Column(String(100), nullable=True)  # organic, conventional, etc.
    bank_account_verified = Column(Boolean, default=False)
    id_verified = Column(Boolean, default=False)
    fpo_id = Column(Integer, ForeignKey("fpo_profiles.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("ix_farmer_district", "district"),
        Index("ix_farmer_state", "state"),
    )


class BuyerProfile(Base):
    """Extended profile for buyer users."""
    __tablename__ = "buyer_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    business_name = Column(String(500), nullable=True)
    business_type = Column(String(100), nullable=True)  # retailer, wholesaler, processor, hotel, mess, institutional
    gst_number = Column(String(20), nullable=True)
    business_address = Column(Text, nullable=True)
    city = Column(String(255), nullable=True)
    district = Column(String(255), nullable=True)
    state = Column(String(100), default="Maharashtra", nullable=False)
    pincode = Column(String(10), nullable=True)
    preferred_crops = Column(JSON, nullable=True)
    avg_monthly_volume = Column(String(100), nullable=True)
    business_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("ix_buyer_district", "district"),
        Index("ix_buyer_business_type", "business_type"),
    )


class FPOProfile(Base):
    """FPO (Farmer Producer Organization) profile."""
    __tablename__ = "fpo_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    org_name = Column(String(500), nullable=False)
    registration_number = Column(String(100), nullable=True)
    org_type = Column(String(100), nullable=True)
    address = Column(Text, nullable=True)
    district = Column(String(255), nullable=True)
    state = Column(String(100), default="Maharashtra", nullable=False)
    pincode = Column(String(10), nullable=True)
    member_count = Column(Integer, default=0)
    primary_commodities = Column(JSON, nullable=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc), nullable=False)



class TraderProfile(Base):
    """Extended profile for trader users (formerly buyers)."""
    __tablename__ = "trader_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    business_name = Column(String(500), nullable=True)
    business_type = Column(String(100), nullable=True)  # retailer, wholesaler, processor, etc.
    gst_number = Column(String(20), nullable=True)
    business_address = Column(Text, nullable=True)
    city = Column(String(255), nullable=True)
    district = Column(String(255), nullable=True)
    state = Column(String(100), default="Maharashtra", nullable=False)
    pincode = Column(String(10), nullable=True)
    preferred_crops = Column(JSON, nullable=True)
    avg_monthly_volume = Column(String(100), nullable=True)
    business_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc), nullable=False)

class FPOMembership(Base):
    """Membership linking farmers with FPO organizations."""
    __tablename__ = "fpo_memberships"

    id = Column(Integer, primary_key=True, autoincrement=True)

    fpo_id = Column(
        Integer,
        ForeignKey("fpo_profiles.id", ondelete="CASCADE"),
        nullable=False
    )

    farmer_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    role = Column(String(50), nullable=True)
    can_list_crops = Column(Boolean, nullable=True)
    can_negotiate = Column(Boolean, nullable=True)
    can_approve_deals = Column(Boolean, nullable=True)

    joined_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    is_active = Column(Boolean, nullable=True)

    __table_args__ = (
        Index(
            "ix_fpo_membership_unique",
            "fpo_id",
            "farmer_user_id",
            unique=True
        ),
    )
