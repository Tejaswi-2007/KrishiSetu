"""Document model for file uploads."""
import enum
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, BigInteger,
    ForeignKey, Enum, Index,
)
from app.core.database import Base


class DocumentType(str, enum.Enum):
    """Types of documents."""
    CROP_IMAGE = "crop_image"
    QUALITY_CERTIFICATE = "quality_certificate"
    AGREEMENT_DOC = "agreement_doc"
    PROFILE_AVATAR = "profile_avatar"
    IDENTITY_DOC = "identity_doc"
    CHAT_ATTACHMENT = "chat_attachment"
    OTHER = "other"


class Document(Base):
    """Uploaded document record."""
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    uploader_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    filename = Column(String(500), nullable=False)
    original_filename = Column(String(500), nullable=False)
    storage_key = Column(String(500), unique=True, nullable=False)
    content_type = Column(String(100), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    doc_type = Column(Enum(DocumentType), default=DocumentType.OTHER)

    # Access control
    is_private = Column(Boolean, default=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Related entity
    related_id = Column(Integer, nullable=True)
    related_type = Column(String(50), nullable=True)  # listing, deal_room, agreement, profile

    # Metadata
    description = Column(Text, nullable=True)
    checksum = Column(String(64), nullable=True)  # SHA-256
    scan_status = Column(String(20), default="pending")  # pending, clean, infected, error

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_doc_uploader", "uploader_id"),
        Index("ix_doc_related", "related_type", "related_id"),
        Index("ix_doc_storage_key", "storage_key"),
    )
