"""Crop listings API endpoints."""
import math
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from datetime import datetime, timezone

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User, UserRole
from app.models.listing import CropListing, ListingStatus, CropCatalogue
from app.schemas.listing import (
    ListingCreate, ListingUpdate, ListingResponse,
    ListingSearch, PaginatedListings,
)

router = APIRouter()


def _listing_to_response(listing: CropListing, seller: User = None) -> ListingResponse:
    """Convert a listing model to response schema."""
    data = {c.name: getattr(listing, c.name) for c in listing.__table__.columns}
    data["negotiability"] = data["negotiability"].value if data["negotiability"] else "negotiable"
    data["delivery_preference"] = data["delivery_preference"].value if data["delivery_preference"] else "both"
    data["status"] = data["status"].value if data["status"] else "draft"
    if seller:
        data["seller_name"] = seller.full_name
        data["seller_verified"] = seller.is_verified
    return ListingResponse(**data)


@router.get("", response_model=PaginatedListings)
def search_listings(
    q: str = Query(None),
    crop_name: str = Query(None),
    category: str = Query(None),
    district: str = Query(None),
    state: str = Query(None),
    min_price: float = Query(None, ge=0),
    max_price: float = Query(None, ge=0),
    min_quantity: float = Query(None, ge=0),
    max_quantity: float = Query(None, ge=0),
    unit: str = Query(None),
    grade: str = Query(None),
    delivery_preference: str = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Search and browse active crop listings."""
    query = db.query(CropListing).filter(CropListing.status == ListingStatus.ACTIVE)

    if q:
        search = f"%{q}%"
        query = query.filter(
            or_(
                CropListing.crop_name.ilike(search),
                CropListing.crop_variety.ilike(search),
                CropListing.quality_description.ilike(search),
                CropListing.district.ilike(search),
            )
        )
    if crop_name:
        query = query.filter(CropListing.crop_name.ilike(f"%{crop_name}%"))
    if category:
        query = query.filter(CropListing.category == category)
    if district:
        query = query.filter(CropListing.district.ilike(f"%{district}%"))
    if state:
        query = query.filter(CropListing.state == state)
    if min_price is not None:
        query = query.filter(CropListing.asking_price >= min_price)
    if max_price is not None:
        query = query.filter(CropListing.asking_price <= max_price)
    if min_quantity is not None:
        query = query.filter(CropListing.quantity >= min_quantity)
    if max_quantity is not None:
        query = query.filter(CropListing.quantity <= max_quantity)
    if unit:
        query = query.filter(CropListing.unit == unit)
    if grade:
        query = query.filter(CropListing.grade.ilike(f"%{grade}%"))

    # Count total
    total = query.count()

    # Sort
    sort_col = getattr(CropListing, sort_by, CropListing.created_at)
    if sort_order == "asc":
        query = query.order_by(sort_col.asc())
    else:
        query = query.order_by(sort_col.desc())

    # Paginate
    offset = (page - 1) * page_size
    listings = query.offset(offset).limit(page_size).all()

    # Get seller info
    seller_ids = {l.seller_id for l in listings}
    sellers = {u.id: u for u in db.query(User).filter(User.id.in_(seller_ids)).all()} if seller_ids else {}

    items = [_listing_to_response(l, sellers.get(l.seller_id)) for l in listings]

    return PaginatedListings(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total > 0 else 0,
    )


@router.get("/my", response_model=PaginatedListings)
def get_my_listings(
    status_filter: str = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the current user's own listings."""
    query = db.query(CropListing).filter(CropListing.seller_id == current_user.id)
    if status_filter:
        query = query.filter(CropListing.status == ListingStatus(status_filter))

    total = query.count()
    offset = (page - 1) * page_size
    listings = query.order_by(CropListing.created_at.desc()).offset(offset).limit(page_size).all()
    items = [_listing_to_response(l, current_user) for l in listings]

    return PaginatedListings(
        items=items, total=total, page=page, page_size=page_size,
        total_pages=math.ceil(total / page_size) if total > 0 else 0,
    )


@router.get("/catalogue")
def get_crop_catalogue(
    category: str = Query(None),
    q: str = Query(None),
    db: Session = Depends(get_db),
):
    """Get the crop catalogue for dropdowns."""
    query = db.query(CropCatalogue).filter(CropCatalogue.is_active == True)
    if category:
        query = query.filter(CropCatalogue.category == category)
    if q:
        query = query.filter(
            or_(CropCatalogue.name_en.ilike(f"%{q}%"), CropCatalogue.name_mr.ilike(f"%{q}%"))
        )
    crops = query.order_by(CropCatalogue.name_en).all()
    return [
        {"id": c.id, "name_en": c.name_en, "name_mr": c.name_mr,
         "category": c.category, "variety": c.variety, "unit_options": c.unit_options}
        for c in crops
    ]


@router.get("/{listing_id}", response_model=ListingResponse)
def get_listing(listing_id: int, db: Session = Depends(get_db)):
    """Get a single listing by ID."""
    listing = db.query(CropListing).filter(CropListing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    # Increment view count
    listing.view_count = (listing.view_count or 0) + 1
    db.commit()

    seller = db.query(User).filter(User.id == listing.seller_id).first()
    return _listing_to_response(listing, seller)


@router.post("", response_model=ListingResponse, status_code=status.HTTP_201_CREATED)
def create_listing(
    data: ListingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new crop listing. Only farmers and FPO admins can create listings."""
    if current_user.role not in (UserRole.FARMER, UserRole.FPO_ADMIN):
        raise HTTPException(status_code=403, detail="Only farmers and FPO admins can create listings")

    listing = CropListing(
        seller_id=current_user.id,
        crop_name=data.crop_name,
        crop_variety=data.crop_variety,
        category=data.category,
        crop_id=data.crop_id,
        grade=data.grade,
        quality_description=data.quality_description,
        quantity=data.quantity,
        quantity_remaining=data.quantity,
        unit=data.unit,
        asking_price=data.asking_price,
        price_currency=data.price_currency,
        negotiability=data.negotiability,
        available_from=data.available_from,
        harvest_date=data.harvest_date,
        location=data.location,
        village=data.village,
        taluka=data.taluka,
        district=data.district,
        state=data.state,
        pincode=data.pincode,
        delivery_preference=data.delivery_preference,
        delivery_notes=data.delivery_notes,
        status=ListingStatus.ACTIVE,
        published_at=datetime.now(timezone.utc),
    )
    db.add(listing)
    db.commit()
    db.refresh(listing)
    return _listing_to_response(listing, current_user)


@router.patch("/{listing_id}", response_model=ListingResponse)
def update_listing(
    listing_id: int,
    data: ListingUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update a listing. Only the owner can update."""
    listing = db.query(CropListing).filter(CropListing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    if listing.seller_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="You can only edit your own listings")

    updates = data.model_dump(exclude_unset=True)

    # Handle status transitions
    if "status" in updates:
        new_status = updates["status"]
        allowed_transitions = {
            "draft": ["active"],
            "active": ["paused", "closed"],
            "paused": ["active", "closed"],
        }
        current_status = listing.status.value
        if new_status not in allowed_transitions.get(current_status, []):
            raise HTTPException(
                status_code=400,
                detail=f"Cannot change status from '{current_status}' to '{new_status}'"
            )
        updates["status"] = ListingStatus(new_status)
        if new_status == "active" and not listing.published_at:
            updates["published_at"] = datetime.now(timezone.utc)

    for key, value in updates.items():
        setattr(listing, key, value)

    db.commit()
    db.refresh(listing)
    return _listing_to_response(listing, current_user)
