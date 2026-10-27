"""Market price service: ingestion and querying of mandi price data."""

import math
from datetime import date, timedelta
from typing import Optional, List

from sqlalchemy.orm import Session
from sqlalchemy import asc, desc

from app.models.market_price import MarketPrice, PriceSource, PriceSourceType
from app.schemas.market_price import MarketPriceQuery


def get_or_create_source(
    db: Session, name: str, source_type: PriceSourceType, base_url: Optional[str] = None
) -> PriceSource:
    """Get an existing price source by name, or create a new one."""
    source = db.query(PriceSource).filter(PriceSource.name == name).first()
    if not source:
        source = PriceSource(
            name=name,
            source_type=source_type,
            base_url=base_url,
        )
        db.add(source)
        db.commit()
        db.refresh(source)
    return source


def ingest_price_record(
    db: Session,
    source_id: int,
    commodity: str,
    market_name: str,
    modal_price: float,
    price_date: date,
    variety: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    district: Optional[str] = None,
    state: Optional[str] = None,
    unit: str = "quintal",
    arrival_quantity: Optional[float] = None,
) -> MarketPrice:
    """Ingest a single market price record, updating if it already exists (upsert).

    Uses the unique constraint on (source_id, commodity, variety, market_name, price_date)
    to detect duplicates.
    """
    existing = (
        db.query(MarketPrice)
        .filter(
            MarketPrice.source_id == source_id,
            MarketPrice.commodity == commodity,
            MarketPrice.variety == variety,
            MarketPrice.market_name == market_name,
            MarketPrice.price_date == price_date,
        )
        .first()
    )

    if existing:
        existing.modal_price = modal_price
        existing.min_price = min_price
        existing.max_price = max_price
        existing.arrival_quantity = arrival_quantity
        db.commit()
        db.refresh(existing)
        return existing

    price = MarketPrice(
        source_id=source_id,
        commodity=commodity,
        variety=variety,
        market_name=market_name,
        district=district,
        state=state,
        min_price=min_price,
        max_price=max_price,
        modal_price=modal_price,
        unit=unit,
        price_date=price_date,
        arrival_quantity=arrival_quantity,
    )
    db.add(price)
    db.commit()
    db.refresh(price)
    return price


def query_prices(db: Session, params: MarketPriceQuery) -> dict:
    """Query market prices with filters and pagination.

    Returns a dict with items, total, page info.
    """
    query = db.query(MarketPrice)

    if params.commodity:
        query = query.filter(MarketPrice.commodity.ilike(f"%{params.commodity}%"))

    if params.market_name:
        query = query.filter(MarketPrice.market_name.ilike(f"%{params.market_name}%"))

    if params.state:
        query = query.filter(MarketPrice.state == params.state)

    if params.district:
        query = query.filter(MarketPrice.district == params.district)

    if params.date_from:
        query = query.filter(MarketPrice.price_date >= params.date_from)

    if params.date_to:
        query = query.filter(MarketPrice.price_date <= params.date_to)

    total = query.count()

    query = query.order_by(desc(MarketPrice.price_date), MarketPrice.commodity)
    offset = (params.page - 1) * params.page_size
    items = query.offset(offset).limit(params.page_size).all()
    pages = math.ceil(total / params.page_size) if total > 0 else 0

    return {
        "items": items,
        "total": total,
        "page": params.page,
        "page_size": params.page_size,
        "pages": pages,
    }


def get_price_trend(
    db: Session,
    commodity: str,
    market_name: str,
    days: int = 30,
) -> List[MarketPrice]:
    """Get price trend data for a commodity at a specific market over the last N days."""
    since = date.today() - timedelta(days=days)
    return (
        db.query(MarketPrice)
        .filter(
            MarketPrice.commodity.ilike(f"%{commodity}%"),
            MarketPrice.market_name.ilike(f"%{market_name}%"),
            MarketPrice.price_date >= since,
        )
        .order_by(asc(MarketPrice.price_date))
        .all()
    )


def get_latest_prices(
    db: Session, commodity: str, state: Optional[str] = None, limit: int = 20
) -> List[MarketPrice]:
    """Get the latest market prices for a commodity, optionally filtered by state."""
    query = db.query(MarketPrice).filter(
        MarketPrice.commodity.ilike(f"%{commodity}%")
    )
    if state:
        query = query.filter(MarketPrice.state == state)

    return (
        query.order_by(desc(MarketPrice.price_date))
        .limit(limit)
        .all()
    )
