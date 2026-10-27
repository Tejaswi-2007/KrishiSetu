"""Pydantic schemas for crop listings."""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


class ListingCreate(BaseModel):
    """Schema for creating a crop listing."""
    crop_name: str = Field(..., min_length=1, max_length=255)
    crop_variety: Optional[str] = Field(None, max_length=255)
    category: Optional[str] = Field(None, max_length=100)
    crop_id: Optional[int] = None
    grade: Optional[str] = Field(None, max_length=100)
    quality_description: Optional[str] = None
    quantity: Decimal = Field(..., gt=0, max_digits=12, decimal_places=2)
    unit: str = Field(..., pattern="^(kg|quintal|ton|piece|dozen|bag)$")
    asking_price: Decimal = Field(..., gt=0, max_digits=12, decimal_places=2)
    price_currency: str = Field(default="INR", pattern="^INR$")
    negotiability: str = Field(default="negotiable", pattern="^(fixed|negotiable|auction)$")
    available_from: Optional[datetime] = None
    harvest_date: Optional[datetime] = None
    location: Optional[str] = Field(None, max_length=500)
    village: Optional[str] = Field(None, max_length=255)
    taluka: Optional[str] = Field(None, max_length=255)
    district: Optional[str] = Field(None, max_length=255)
    state: str = Field(default="Maharashtra", max_length=100)
    pincode: Optional[str] = Field(None, pattern=r"^\d{6}$")
    delivery_preference: str = Field(default="both", pattern="^(pickup|delivery|both)$")
    delivery_notes: Optional[str] = None


class ListingUpdate(BaseModel):
    """Schema for updating a crop listing."""
    crop_variety: Optional[str] = Field(None, max_length=255)
    grade: Optional[str] = Field(None, max_length=100)
    quality_description: Optional[str] = None
    quantity: Optional[Decimal] = Field(None, gt=0, max_digits=12, decimal_places=2)
    unit: Optional[str] = Field(None, pattern="^(kg|quintal|ton|piece|dozen|bag)$")
    asking_price: Optional[Decimal] = Field(None, gt=0, max_digits=12, decimal_places=2)
    negotiability: Optional[str] = Field(None, pattern="^(fixed|negotiable|auction)$")
    available_from: Optional[datetime] = None
    harvest_date: Optional[datetime] = None
    location: Optional[str] = Field(None, max_length=500)
    village: Optional[str] = Field(None, max_length=255)
    taluka: Optional[str] = Field(None, max_length=255)
    district: Optional[str] = Field(None, max_length=255)
    pincode: Optional[str] = Field(None, pattern=r"^\d{6}$")
    delivery_preference: Optional[str] = Field(None, pattern="^(pickup|delivery|both)$")
    delivery_notes: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(active|paused|closed)$")


class ListingResponse(BaseModel):
    """Schema for listing response."""
    id: int
    seller_id: int
    crop_id: Optional[int] = None
    crop_name: str
    crop_variety: Optional[str] = None
    category: Optional[str] = None
    grade: Optional[str] = None
    quality_description: Optional[str] = None
    quantity: Decimal
    unit: str
    asking_price: Decimal
    price_currency: str
    negotiability: str
    available_from: Optional[datetime] = None
    harvest_date: Optional[datetime] = None
    location: Optional[str] = None
    village: Optional[str] = None
    taluka: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    delivery_preference: str
    delivery_notes: Optional[str] = None
    images: Optional[str] = None
    status: str
    view_count: int = 0
    offer_count: int = 0
    quantity_remaining: Optional[Decimal] = None
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime] = None

    # Seller info (joined)
    seller_name: Optional[str] = None
    seller_verified: Optional[bool] = None

    model_config = {"from_attributes": True}


class ListingSearch(BaseModel):
    """Schema for listing search filters."""
    q: Optional[str] = None  # text search
    crop_name: Optional[str] = None
    category: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    min_price: Optional[Decimal] = None
    max_price: Optional[Decimal] = None
    min_quantity: Optional[Decimal] = None
    max_quantity: Optional[Decimal] = None
    unit: Optional[str] = None
    grade: Optional[str] = None
    delivery_preference: Optional[str] = None
    sort_by: str = Field(default="created_at", pattern="^(created_at|asking_price|quantity|crop_name)$")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$")
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class PaginatedListings(BaseModel):
    """Paginated listing response."""
    items: List[ListingResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
