"""Pydantic schemas for market prices."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field


class MarketPriceResponse(BaseModel):
    """Schema for market price response."""
    id: int
    crop_name: str
    variety: Optional[str] = None
    market_name: str
    district: Optional[str] = None
    state: Optional[str] = None
    min_price: Optional[Decimal] = None
    max_price: Optional[Decimal] = None
    modal_price: Optional[Decimal] = None
    price_unit: str
    currency: str
    reporting_date: date
    arrival_quantity: Optional[Decimal] = None
    arrival_unit: Optional[str] = None
    source_name: Optional[str] = None
    freshness: str
    retrieval_timestamp: Optional[datetime] = None

    model_config = {"from_attributes": True}


class MarketPriceSearch(BaseModel):
    """Schema for searching market prices."""
    crop_name: Optional[str] = None
    market_name: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=200)


class PaginatedMarketPrices(BaseModel):
    """Paginated market price response."""
    items: List[MarketPriceResponse]
    total: int
    page: int
    page_size: int


class PriceSourceStatus(BaseModel):
    """Schema for price source status."""
    id: int
    name: str
    source_type: str
    is_active: bool
    last_sync_at: Optional[datetime] = None
    last_sync_status: Optional[str] = None
    last_sync_error: Optional[str] = None
    record_count: int

    model_config = {"from_attributes": True}


class NetProceedsInput(BaseModel):
    """Input for net proceeds calculation."""
    rate_per_unit: Decimal = Field(..., gt=0, max_digits=12, decimal_places=2)
    quantity: Decimal = Field(..., gt=0, max_digits=12, decimal_places=2)
    unit: str = Field(..., pattern="^(kg|quintal|ton|piece|dozen|bag)$")
    currency: str = Field(default="INR")
    transportation_cost: Optional[Decimal] = Field(None, ge=0)
    loading_unloading_cost: Optional[Decimal] = Field(None, ge=0)
    packaging_cost: Optional[Decimal] = Field(None, ge=0)
    commission_percent: Optional[Decimal] = Field(None, ge=0, le=100)
    other_costs: Optional[Decimal] = Field(None, ge=0)
    other_costs_description: Optional[str] = None


class NetProceedsResult(BaseModel):
    """Result of net proceeds calculation."""
    gross_value: Decimal
    transportation_cost: Optional[Decimal] = None
    loading_unloading_cost: Optional[Decimal] = None
    packaging_cost: Optional[Decimal] = None
    commission_amount: Optional[Decimal] = None
    commission_percent: Optional[Decimal] = None
    other_costs: Optional[Decimal] = None
    other_costs_description: Optional[str] = None
    total_deductions: Decimal
    estimated_net_proceeds: Decimal
    unknown_costs_note: str
    currency: str
    unit: str
    quantity: Decimal
    rate_per_unit: Decimal

    model_config = {"from_attributes": True}


class OfferComparison(BaseModel):
    """Comparison of multiple offers with net proceeds."""
    offer_id: int
    buyer_name: Optional[str] = None
    offered_price: Decimal
    quantity: Decimal
    unit: str
    gross_value: Decimal
    estimated_net_proceeds: Optional[Decimal] = None
    total_deductions: Optional[Decimal] = None
    unknown_costs: bool = False
