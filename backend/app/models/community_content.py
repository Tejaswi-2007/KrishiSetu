"""Database-backed farmer communities, posts, and source-linked public resources."""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index, UniqueConstraint
from app.core.database import Base

class CommunityGroup(Base):
    __tablename__ = "community_groups"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(180), nullable=False)
    kind = Column(String(20), nullable=False, index=True)  # crop | region
    crop = Column(String(80), nullable=True, index=True)
    state = Column(String(120), nullable=True, index=True)
    district = Column(String(120), nullable=True, index=True)
    taluka = Column(String(120), nullable=True, index=True)
    village = Column(String(120), nullable=True, index=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    __table_args__ = (UniqueConstraint("kind", "name", "crop", "state", "district", "taluka", "village", name="uq_community_group_identity"),)

class CommunityMembership(Base):
    __tablename__ = "community_memberships"
    id = Column(Integer, primary_key=True, autoincrement=True)
    community_id = Column(Integer, ForeignKey("community_groups.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    joined_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    __table_args__ = (UniqueConstraint("community_id", "user_id", name="uq_community_member"),)

class CommunityPost(Base):
    __tablename__ = "community_posts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    author_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    community_id = Column(Integer, ForeignKey("community_groups.id", ondelete="SET NULL"), nullable=True, index=True)
    body = Column(Text, nullable=False)
    category = Column(String(80), nullable=False, default="General")
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class PublicResource(Base):
    __tablename__ = "public_resources"
    id = Column(Integer, primary_key=True, autoincrement=True)
    kind = Column(String(20), nullable=False, index=True)  # scheme | news
    title = Column(String(300), nullable=False)
    summary = Column(Text, nullable=False)
    documents = Column(Text, nullable=True)
    source_name = Column(String(200), nullable=False)
    source_url = Column(String(1000), nullable=False)
    published_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    __table_args__ = (Index("ix_public_resources_kind_date", "kind", "published_at"),)
