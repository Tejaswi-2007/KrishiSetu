"""User model and role enumeration."""
import enum
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Boolean, Enum, DateTime, Text,
    Index,
)
from app.core.database import Base


class UserRole(str, enum.Enum):
    """User roles in the application."""
    FARMER = "farmer"
    BUYER = "buyer"
    FPO_ADMIN = "fpo_admin"
    ADMIN = "admin"


class User(Base):
    """Core user account model."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(15), unique=True, nullable=True, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.FARMER)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    language_pref = Column(String(5), default="en", nullable=False)
    avatar_url = Column(String(500), nullable=True)
    last_login = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("ix_users_role", "role"),
        Index("ix_users_active_role", "is_active", "role"),
    )
