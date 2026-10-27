# """Digi-Mandi FastAPI Application."""

import logging
import asyncio
from app.core.database import SessionLocal
from app.api.v1.auctions import _update_auction_statuses
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .core.config import get_settings
from .api.v1.router import api_v1_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("digimandi")

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)

    logger.info("[Digi-Mandi] Starting in %s mode", settings.ENVIRONMENT)
    logger.info("[Digi-Mandi] Upload directory: %s", upload_dir.resolve())

    # Start background auction status updater
    async def updater():
        while True:
            db = None
            try:
                db = SessionLocal()
                _update_auction_statuses(db)
            except asyncio.CancelledError:
                raise
            except Exception:
                # Keep the API process alive if the database is temporarily
                # unavailable; include a traceback to make diagnosis possible.
                logger.exception("Auction status updater failed")
            finally:
                if db is not None:
                    db.close()
            await asyncio.sleep(30)

    task = asyncio.create_task(updater())

    async def daily_market_price_updater():
        """Refresh official prices daily when the operator configured an API key."""
        if not settings.DATA_GOV_IN_API_KEY:
            logger.info("Daily market-price sync is disabled: DATA_GOV_IN_API_KEY is not configured")
            return
        while True:
            try:
                from app.services.official_market_prices import sync_official_market_prices
                def run_sync():
                    db = SessionLocal()
                    try:
                        return sync_official_market_prices(db, 1000)
                    finally:
                        db.close()
                result = await asyncio.to_thread(run_sync)
                logger.info("Daily official market-price sync completed: %s", result)
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Daily official market-price sync failed; existing saved prices are retained")
            await asyncio.sleep(24 * 60 * 60)

    price_task = asyncio.create_task(daily_market_price_updater())
    app.state.auction_updater_task = task
    app.state.market_price_updater_task = price_task

    yield

    # Shutdown handling
    logger.info("[Digi-Mandi] Shutting down")
    task.cancel()
    price_task.cancel()
    for background_task in (task, price_task):
        try:
            await background_task
        except asyncio.CancelledError:
            pass

app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "A Complete Ecosystem for Agriculture — "
        "B2B Agricultural Marketplace"
    ),
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(
    request: Request,
    exc: Exception,
):
    """Log the complete traceback for development diagnostics."""
    logger.exception(
        "Unhandled exception on %s %s",
        request.method,
        request.url.path,
    )

    # DEVELOPMENT ONLY: exposes the error in the API response.
    # Do not expose exception details in production.
    if settings.ENVIRONMENT == "development":
        detail = f"{type(exc).__name__}: {exc}"
    else:
        detail = (
            "An internal error occurred. "
            "Please check the backend terminal logs."
        )

    return JSONResponse(
        status_code=500,
        content={"detail": detail},
    )

# Health check
@app.get("/health", tags=["Health"]) 
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }

# API routes
app.include_router(api_v1_router, prefix="/api/v1")
