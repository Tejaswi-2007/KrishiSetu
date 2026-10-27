"""Market price models for agricultural price intelligence."""
import enum
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Text, Numeric, DateTime, Date,
    Boolean, Enum, Index, UniqueConstraint, ForeignKey,
)
from app.core.database import Base


class PriceType(str, enum.Enum):
    """Type of price record."""
    MINIMUM = "minimum"
    MAXIMUM = "maximum"
    MODAL = "modal"
    AVERAGE = "average"


class DataFreshness(str, enum.Enum):
    """Data freshness status."""
    CURRENT = "current"
    STALE = "stale"
    UNAVAILABLE = "unavailable"


class PriceSource(Base):
    """Registry of market price data sources."""
    __tablename__ = "price_sources"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True)
    source_type = Column(String(100), nullable=False)  # api, scrape, manual, dataset
    base_url = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    last_sync_at = Column(DateTime(timezone=True), nullable=True)
    last_sync_status = Column(String(50), nullable=True)  # success, partial, failed
    last_sync_error = Column(Text, nullable=True)
    sync_frequency_hours = Column(Integer, default=24)
    record_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc), nullable=False)


class MarketPrice(Base):
    """Market-reported price record."""
    __tablename__ = "market_prices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_id = Column(Integer, ForeignKey("price_sources.id"), nullable=False)

    # Crop info
    crop_name = Column(String(255), nullable=False)
    variety = Column(String(255), nullable=True)

    # Market info
    market_name = Column(String(255), nullable=False)
    district = Column(String(255), nullable=True)
    state = Column(String(100), default="Maharashtra")

    # Price data
    min_price = Column(Numeric(12, 2), nullable=True)
    max_price = Column(Numeric(12, 2), nullable=True)
    modal_price = Column(Numeric(12, 2), nullable=True)
    price_unit = Column(String(20), default="quintal", nullable=False)
    currency = Column(String(3), default="INR", nullable=False)

    # Dates
    reporting_date = Column(Date, nullable=False)
    arrival_quantity = Column(Numeric(12, 2), nullable=True)
    arrival_unit = Column(String(20), nullable=True)

    # Provenance
    source_record_id = Column(String(255), nullable=True)
    retrieval_timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    is_validated = Column(Boolean, default=False)
    freshness = Column(Enum(DataFreshness), default=DataFreshness.CURRENT)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("ix_mp_crop_market_date", "crop_name", "market_name", "reporting_date"),
        Index("ix_mp_crop_district", "crop_name", "district"),
        Index("ix_mp_reporting_date", "reporting_date"),
        UniqueConstraint(
            "source_id", "crop_name", "variety", "market_name", "reporting_date",
            name="uq_price_source_crop_market_date"
        ),
    )
