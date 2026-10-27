"""Transaction and delivery tracking models."""
import enum
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Text, Numeric, DateTime,
    ForeignKey, Enum, Index,
)
from app.core.database import Base


class TransactionStatus(str, enum.Enum):
    """Transaction status."""
    CREATED = "created"
    IN_PROGRESS = "in_progress"
    DELIVERED = "delivered"
    COMPLETED = "completed"
    DISPUTED = "disputed"
    CANCELLED = "cancelled"


class DeliveryStatus(str, enum.Enum):
    """Delivery status."""
    PENDING = "pending"
    PICKUP_SCHEDULED = "pickup_scheduled"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    CONFIRMED = "confirmed"
    FAILED = "failed"


class Transaction(Base):
    """A recorded transaction from a confirmed agreement."""
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    agreement_id = Column(Integer, ForeignKey("agreements.id"), nullable=False, unique=True)
    seller_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    buyer_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # From agreement
    crop_name = Column(String(255), nullable=False)
    quantity = Column(Numeric(12, 2), nullable=False)
    unit = Column(String(20), nullable=False)
    rate = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), default="INR")
    total_value = Column(Numeric(14, 2), nullable=False)

    # Payment status
    payment_status = Column(String(50), default="pending")
    payment_method = Column(String(50), nullable=True)
    payment_reference = Column(String(255), nullable=True)

    # Status
    status = Column(Enum(TransactionStatus), default=TransactionStatus.CREATED, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_txn_seller", "seller_id"),
        Index("ix_txn_buyer", "buyer_id"),
        Index("ix_txn_status", "status"),
    )


class Delivery(Base):
    """Delivery tracking for a transaction."""
    __tablename__ = "deliveries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False)

    # Pickup
    pickup_location = Column(Text, nullable=True)
    pickup_date = Column(DateTime(timezone=True), nullable=True)
    pickup_contact = Column(String(255), nullable=True)

    # Delivery
    delivery_location = Column(Text, nullable=True)
    expected_delivery_date = Column(DateTime(timezone=True), nullable=True)
    actual_delivery_date = Column(DateTime(timezone=True), nullable=True)
    delivery_contact = Column(String(255), nullable=True)

    # Logistics
    transporter_name = Column(String(255), nullable=True)
    vehicle_number = Column(String(50), nullable=True)
    tracking_reference = Column(String(255), nullable=True)

    # Weight verification
    dispatched_quantity = Column(Numeric(12, 2), nullable=True)
    received_quantity = Column(Numeric(12, 2), nullable=True)
    unit = Column(String(20), nullable=True)

    # Status
    status = Column(Enum(DeliveryStatus), default=DeliveryStatus.PENDING, nullable=False)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("ix_delivery_txn", "transaction_id"),
        Index("ix_delivery_status", "status"),
    )
