"""Market prices API endpoints."""
import math
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.models.user import User, UserRole
from app.models.market_price import MarketPrice, PriceSource, DataFreshness
from app.schemas.market_price import (
    MarketPriceResponse, PaginatedMarketPrices, PriceSourceStatus,
)

router = APIRouter()


@router.get("", response_model=PaginatedMarketPrices)
def search_market_prices(
    crop_name: str = Query(None),
    market_name: str = Query(None),
    district: str = Query(None),
    state: str = Query(None),
    date_from: date = Query(None),
    date_to: date = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Search market price records."""
    query = db.query(MarketPrice)

    if crop_name:
        query = query.filter(MarketPrice.crop_name.ilike(f"%{crop_name}%"))
    if market_name:
        query = query.filter(MarketPrice.market_name.ilike(f"%{market_name}%"))
    if district:
        query = query.filter(MarketPrice.district.ilike(f"%{district}%"))
    if state:
        query = query.filter(MarketPrice.state.ilike(f"%{state}%"))
    if date_from:
        query = query.filter(MarketPrice.reporting_date >= date_from)
    if date_to:
        query = query.filter(MarketPrice.reporting_date <= date_to)

    total = query.count()
    offset = (page - 1) * page_size
    records = query.order_by(MarketPrice.reporting_date.desc()).offset(offset).limit(page_size).all()

    # Add source name
    source_ids = {r.source_id for r in records}
    sources = {s.id: s.name for s in db.query(PriceSource).filter(PriceSource.id.in_(source_ids)).all()} if source_ids else {}

    items = []
    for r in records:
        data = {c.name: getattr(r, c.name) for c in r.__table__.columns}
        data["freshness"] = data["freshness"].value if data["freshness"] else "unavailable"
        data["source_name"] = sources.get(r.source_id, "Unknown")
        items.append(MarketPriceResponse(**data))

    return PaginatedMarketPrices(
        items=items, total=total, page=page, page_size=page_size,
    )


@router.get("/crops")
def get_available_crops(db: Session = Depends(get_db)):
    """Get list of crops that have price data."""
    crops = db.query(MarketPrice.crop_name).distinct().order_by(MarketPrice.crop_name).all()
    return [c[0] for c in crops]


@router.get("/markets")
def get_available_markets(
    district: str = Query(None),
    db: Session = Depends(get_db)
):
    """Get list of markets that have price data."""
    query = db.query(MarketPrice.market_name, MarketPrice.district).distinct()
    if district:
        query = query.filter(MarketPrice.district.ilike(f"%{district}%"))
    markets = query.order_by(MarketPrice.market_name).all()
    return [{"market_name": m[0], "district": m[1]} for m in markets]


@router.get("/sources", response_model=list[PriceSourceStatus])
def get_price_sources(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get status of all price data sources (authenticated users only)."""
    sources = db.query(PriceSource).all()
    return [PriceSourceStatus.model_validate(s) for s in sources]


@router.get("/latest")
def get_latest_prices(
    crop_name: str = Query(...),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """Get the latest prices for a specific crop across markets."""
    # Subquery for most recent date per market
    subquery = (
        db.query(
            MarketPrice.market_name,
            func.max(MarketPrice.reporting_date).label("latest_date"),
        )
        .filter(MarketPrice.crop_name.ilike(f"%{crop_name}%"))
        .group_by(MarketPrice.market_name)
        .subquery()
    )

    records = (
        db.query(MarketPrice)
        .join(
            subquery,
            (MarketPrice.market_name == subquery.c.market_name)
            & (MarketPrice.reporting_date == subquery.c.latest_date),
        )
        .filter(MarketPrice.crop_name.ilike(f"%{crop_name}%"))
        .limit(limit)
        .all()
    )

    return [
        {
            "crop_name": r.crop_name, "variety": r.variety,
            "market_name": r.market_name, "district": r.district,
            "min_price": str(r.min_price) if r.min_price else None,
            "max_price": str(r.max_price) if r.max_price else None,
            "modal_price": str(r.modal_price) if r.modal_price else None,
            "price_unit": r.price_unit, "currency": r.currency,
            "reporting_date": r.reporting_date.isoformat(),
            "freshness": r.freshness.value if r.freshness else "unavailable",
        }
        for r in records
    ]

@router.post("/sync", tags=["Market Prices"])
def sync_official_market_prices(
    limit: int = Query(500, ge=1, le=5000),
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """Fetch official Agmarknet mandi prices through data.gov.in and upsert them."""
    from app.services.official_market_prices import sync_official_market_prices as sync_prices
    return sync_prices(db, limit=limit)
