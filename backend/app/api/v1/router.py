"""API v1 router — aggregates all sub-routers."""
from fastapi import APIRouter

from .auth import router as auth_router
from .listings import router as listings_router
from .offers import router as offers_router
from .market_prices import router as market_prices_router
from .deal_rooms import router as deal_rooms_router
from .notifications import router as notifications_router
from .admin import router as admin_router
from .calculator import router as calculator_router

api_v1_router = APIRouter()

api_v1_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_v1_router.include_router(listings_router, prefix="/listings", tags=["Listings"])
api_v1_router.include_router(offers_router, prefix="/offers", tags=["Offers"])
api_v1_router.include_router(market_prices_router, prefix="/market-prices", tags=["Market Prices"])
api_v1_router.include_router(deal_rooms_router, prefix="/deal-rooms", tags=["Deal Rooms"])
api_v1_router.include_router(notifications_router, prefix="/notifications", tags=["Notifications"])
api_v1_router.include_router(admin_router, prefix="/admin", tags=["Admin"])
api_v1_router.include_router(calculator_router, prefix="/calculator", tags=["Calculator"])
# Auctions router
from .auctions import router as auctions_router
api_v1_router.include_router(auctions_router, prefix="/auctions", tags=["Auctions"])

from .community_content import router as community_content_router
api_v1_router.include_router(community_content_router, prefix="/content", tags=["Community, Schemes and News"])
