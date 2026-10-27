"""Pydantic schemas for offers."""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field


class OfferCreate(BaseModel):
    """Schema for creating an offer."""
    listing_id: int
    offered_price: Decimal = Field(..., gt=0, max_digits=12, decimal_places=2)
    quantity: Decimal = Field(..., gt=0, max_digits=12, decimal_places=2)
    unit: str = Field(..., pattern="^(kg|quintal|ton|piece|dozen|bag)$")
    currency: str = Field(default="INR", pattern="^INR$")
    delivery_terms: Optional[str] = None
    payment_terms: Optional[str] = None
    notes: Optional[str] = None
    expires_at: Optional[datetime] = None
    idempotency_key: Optional[str] = Field(None, max_length=100)


class OfferUpdate(BaseModel):
    """Schema for updating/countering an offer."""
    offered_price: Optional[Decimal] = Field(None, gt=0, max_digits=12, decimal_places=2)
    quantity: Optional[Decimal] = Field(None, gt=0, max_digits=12, decimal_places=2)
    delivery_terms: Optional[str] = None
    payment_terms: Optional[str] = None
    notes: Optional[str] = None


class OfferResponse(BaseModel):
    """Schema for offer response."""
    id: int
    listing_id: int
    buyer_id: int
    seller_id: int
    offered_price: Decimal
    currency: str
    quantity: Decimal
    unit: str
    delivery_terms: Optional[str] = None
    payment_terms: Optional[str] = None
    notes: Optional[str] = None
    expires_at: Optional[datetime] = None
    parent_offer_id: Optional[int] = None
    status: str
    version: int
    created_at: datetime
    updated_at: datetime
    responded_at: Optional[datetime] = None

    # Joined fields
    buyer_name: Optional[str] = None
    seller_name: Optional[str] = None
    listing_crop_name: Optional[str] = None

    model_config = {"from_attributes": True}


class OfferAction(BaseModel):
    """Schema for accepting/rejecting an offer."""
    action: str = Field(..., pattern="^(accept|reject|withdraw)$")
    notes: Optional[str] = None


class CounterOffer(BaseModel):
    """Schema for making a counter-offer."""
    offered_price: Decimal = Field(..., gt=0, max_digits=12, decimal_places=2)
    quantity: Optional[Decimal] = Field(None, gt=0, max_digits=12, decimal_places=2)
    delivery_terms: Optional[str] = None
    payment_terms: Optional[str] = None
    notes: Optional[str] = None
    expires_at: Optional[datetime] = None


class PaginatedOffers(BaseModel):
    """Paginated offer response."""
    items: List[OfferResponse]
    total: int
    page: int
    page_size: int
