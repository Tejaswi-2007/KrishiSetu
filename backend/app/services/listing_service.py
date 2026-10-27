"""Listing service: business logic for crop listings."""

import math
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import asc, desc
from fastapi import HTTPException, status

from app.models.listing import CropListing, ListingStatus, QualityGrade, UnitType
from app.models.user import User
from app.schemas.listing import ListingCreate, ListingUpdate, ListingSearchParams


def create_listing(db: Session, listing_data: ListingCreate, seller: User) -> CropListing:
    """Create a new crop listing for the given seller.

    Sets available_quantity equal to quantity and status to draft.
    """
    listing = CropListing(
        seller_id=seller.id,
        crop_catalogue_id=listing_data.crop_catalogue_id,
        title=listing_data.title,
        description=listing_data.description,
        variety=listing_data.variety,
        quality_grade=QualityGrade(listing_data.quality_grade) if listing_data.quality_grade else None,
        quantity=listing_data.quantity,
        unit=UnitType(listing_data.unit),
        available_quantity=listing_data.quantity,  # Initially all quantity is available
        price_per_unit=listing_data.price_per_unit,
        min_order_quantity=listing_data.min_order_quantity,
        harvest_date=listing_data.harvest_date,
        expiry_date=listing_data.expiry_date,
        location_district=listing_data.location_district,
        location_state=listing_data.location_state,
        location_pin_code=listing_data.location_pin_code,
        is_organic=listing_data.is_organic,
        certification_info=listing_data.certification_info,
        moisture_content=listing_data.moisture_content,
        status=ListingStatus.draft,
    )
    db.add(listing)
    db.commit()
    db.refresh(listing)
    return listing


def get_listing(db: Session, listing_id: int) -> CropListing:
    """Get a listing by ID. Raises 404 if not found."""
    listing = db.query(CropListing).filter(CropListing.id == listing_id).first()
    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found",
        )
    return listing


def update_listing(
    db: Session, listing_id: int, listing_data: ListingUpdate, current_user: User
) -> CropListing:
    """Update an existing listing. Only the seller can update their own listing."""
    listing = get_listing(db, listing_id)

    if listing.seller_id != current_user.id and current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own listings",
        )

    update_data = listing_data.model_dump(exclude_unset=True)

    # Handle enum conversions
    if "quality_grade" in update_data and update_data["quality_grade"] is not None:
        update_data["quality_grade"] = QualityGrade(update_data["quality_grade"])
    if "status" in update_data and update_data["status"] is not None:
        update_data["status"] = ListingStatus(update_data["status"])

    for field, value in update_data.items():
        setattr(listing, field, value)

    # If quantity changed and listing is draft, update available_quantity too
    if "quantity" in update_data and listing.status == ListingStatus.draft:
        listing.available_quantity = update_data["quantity"]

    db.commit()
    db.refresh(listing)
    return listing


def delete_listing(db: Session, listing_id: int, current_user: User) -> None:
    """Delete a listing. Only the seller or admin can delete."""
    listing = get_listing(db, listing_id)

    if listing.seller_id != current_user.id and current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own listings",
        )

    if listing.status in (ListingStatus.reserved, ListingStatus.sold):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete a reserved or sold listing",
        )

    db.delete(listing)
    db.commit()


def search_listings(db: Session, params: ListingSearchParams) -> dict:
    """Search and filter listings with pagination.

    Returns a dict with items, total count, page info.
    """
    query = db.query(CropListing)

    # Apply filters
    if params.status:
        query = query.filter(CropListing.status == ListingStatus(params.status))

    if params.crop_catalogue_id:
        query = query.filter(CropListing.crop_catalogue_id == params.crop_catalogue_id)

    if params.quality_grade:
        query = query.filter(CropListing.quality_grade == QualityGrade(params.quality_grade))

    if params.location_state:
        query = query.filter(CropListing.location_state == params.location_state)

    if params.location_district:
        query = query.filter(CropListing.location_district == params.location_district)

    if params.min_price is not None:
        query = query.filter(CropListing.price_per_unit >= params.min_price)

    if params.max_price is not None:
        query = query.filter(CropListing.price_per_unit <= params.max_price)

    if params.is_organic is not None:
        query = query.filter(CropListing.is_organic == params.is_organic)

    # Get total count
    total = query.count()

    # Apply sorting
    sort_column = getattr(CropListing, params.sort_by, CropListing.created_at)
    if params.sort_order == "asc":
        query = query.order_by(asc(sort_column))
    else:
        query = query.order_by(desc(sort_column))

    # Apply pagination
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


def increment_view_count(db: Session, listing_id: int) -> None:
    """Increment the view count for a listing."""
    db.query(CropListing).filter(CropListing.id == listing_id).update(
        {"view_count": CropListing.view_count + 1}
    )
    db.commit()
