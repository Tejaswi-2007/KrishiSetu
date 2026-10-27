"""Synchronise official data.gov.in Agmarknet records into PostgreSQL."""
from datetime import datetime, timezone
import httpx
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.core.config import get_settings
from app.models.market_price import MarketPrice, PriceSource, DataFreshness

RESOURCE_ID = "9ef84268-d588-465a-a308-a864a43d0070"
ENDPOINT = f"https://api.data.gov.in/resource/{RESOURCE_ID}"

def sync_official_market_prices(db: Session, limit: int = 500) -> dict:
    settings = get_settings()
    if not settings.DATA_GOV_IN_API_KEY:
        raise HTTPException(status_code=503, detail="DATA_GOV_IN_API_KEY is not configured. Add an official data.gov.in API key to the backend .env before syncing live market prices.")
    try:
        response = httpx.get(ENDPOINT, params={"api-key": settings.DATA_GOV_IN_API_KEY, "format": "json", "limit": limit}, timeout=30.0)
        response.raise_for_status()
        payload = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(status_code=502, detail=f"Official market-price source request failed: {exc}") from exc
    records = payload.get("records", [])
    if not isinstance(records, list):
        raise HTTPException(status_code=502, detail="Official source returned an unexpected response format")
    source = db.query(PriceSource).filter(PriceSource.name == "data.gov.in Agmarknet").first()
    if source is None:
        source = PriceSource(name="data.gov.in Agmarknet", source_type="api", base_url=ENDPOINT, description="Official Agmarknet market prices via data.gov.in", is_active=True)
        db.add(source); db.flush()
    inserted = updated = skipped = 0
    for item in records:
        try:
            crop = str(item.get("commodity") or "").strip()
            market = str(item.get("market") or "").strip()
            state = str(item.get("state") or "").strip() or None
            district = str(item.get("district") or "").strip() or None
            variety = str(item.get("variety") or "").strip() or None
            raw_date = str(item.get("arrival_date") or "").strip()
            report_date = None
            for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
                try:
                    report_date = datetime.strptime(raw_date, fmt).date(); break
                except ValueError:
                    continue
            def price_value(key):
                raw = str(item.get(key) or "").replace(",", "").strip()
                try: return float(raw) if raw else None
                except ValueError: return None
            minimum, maximum, modal = price_value("min_price"), price_value("max_price"), price_value("modal_price")
            if not crop or not market or not report_date or modal is None:
                skipped += 1; continue
            existing = db.query(MarketPrice).filter(MarketPrice.source_id == source.id, MarketPrice.crop_name == crop, MarketPrice.variety == variety, MarketPrice.market_name == market, MarketPrice.reporting_date == report_date).first()
            values = {"district": district, "state": state, "min_price": minimum, "max_price": maximum, "modal_price": modal, "price_unit": "quintal", "currency": "INR", "source_record_id": str(item.get("id") or ""), "retrieval_timestamp": datetime.now(timezone.utc), "is_validated": True, "freshness": DataFreshness.CURRENT}
            if existing:
                for key, value in values.items(): setattr(existing, key, value)
                updated += 1
            else:
                db.add(MarketPrice(source_id=source.id, crop_name=crop, variety=variety, market_name=market, reporting_date=report_date, **values)); inserted += 1
        except Exception:
            skipped += 1
    source.last_sync_at = datetime.now(timezone.utc)
    source.last_sync_status = "success" if not skipped else "partial"
    source.last_sync_error = None
    db.flush()
    source.record_count = db.query(MarketPrice).filter(MarketPrice.source_id == source.id).count()
    db.commit()
    return {"source": source.name, "fetched": len(records), "inserted": inserted, "updated": updated, "skipped": skipped, "message": "Official records are stored in PostgreSQL with source and reporting date."}
