
"""Pydantic schemas for auction and bid endpoints."""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class AuctionCreate(BaseModel):
    """Schema for creating an auction."""

    crop_name: str = Field(..., min_length=1, max_length=255)
    crop_variety: Optional[str] = Field(None, max_length=255)
    category: Optional[str] = Field(None, max_length=100)
    quantity: Decimal = Field(
        ..., gt=0, max_digits=12, decimal_places=2
    )
    unit: str = Field(
        ..., pattern=r"^(kg|quintal|ton|piece|dozen|bag)$"
    )
    starting_price: Decimal = Field(
        ..., gt=0, max_digits=12, decimal_places=2
    )
    expected_price: Optional[Decimal] = Field(
        None, gt=0, max_digits=12, decimal_places=2
    )
    location: Optional[str] = Field(None, max_length=500)
    start_time: datetime
    end_time: datetime

    @model_validator(mode="after")
    def validate_time_window(self):
        """Ensure the auction ends after it starts."""
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        return self


class AuctionOut(BaseModel):
    """Schema for auction responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    seller_id: int
    crop_name: str
    crop_variety: Optional[str] = None
    category: Optional[str] = None
    quantity: Decimal
    unit: str
    starting_price: Decimal
    expected_price: Optional[Decimal] = None
    location: Optional[str] = None
    start_time: datetime
    end_time: datetime
    status: str
    created_at: datetime
    updated_at: datetime
    highest_bid: Optional[Decimal] = None
    bid_count: int = 0


class BidCreate(BaseModel):
    """Schema for submitting a bid."""

    amount: Decimal = Field(
        ..., gt=0, max_digits=12, decimal_places=2
    )


class BidOut(BaseModel):
    """Schema for bid responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    auction_id: int
    bidder_id: int
    amount: Decimal
    created_at: datetime


class PaginatedAuctions(BaseModel):
    """Schema for paginated auction listings."""

    items: List[AuctionOut]
    total: int
    page: int
    page_size: int
    total_pages: int
