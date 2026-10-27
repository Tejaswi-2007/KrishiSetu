"""Offers API endpoints."""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User, UserRole
from app.models.listing import CropListing, ListingStatus
from app.models.offer import Offer, OfferEvent, OfferStatus, OfferEventType
from app.schemas.offer import (
    OfferCreate, OfferResponse, OfferAction, CounterOffer, PaginatedOffers,
)

router = APIRouter()


def _offer_to_response(offer: Offer, db: Session) -> OfferResponse:
    """Convert offer model to response."""
    data = {c.name: getattr(offer, c.name) for c in offer.__table__.columns}
    data["status"] = data["status"].value if data["status"] else "pending"

    buyer = db.query(User).filter(User.id == offer.buyer_id).first()
    seller = db.query(User).filter(User.id == offer.seller_id).first()
    listing = db.query(CropListing).filter(CropListing.id == offer.listing_id).first()

    data["buyer_name"] = buyer.full_name if buyer else None
    data["seller_name"] = seller.full_name if seller else None
    data["listing_crop_name"] = listing.crop_name if listing else None

    return OfferResponse(**data)


@router.post("", response_model=OfferResponse, status_code=status.HTTP_201_CREATED)
def create_offer(
    data: OfferCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Submit an offer on a listing. Only buyers can submit offers."""
    if current_user.role not in (UserRole.BUYER, UserRole.FPO_ADMIN):
        raise HTTPException(status_code=403, detail="Only buyers can submit offers")

    # Check idempotency
    if data.idempotency_key:
        existing = db.query(Offer).filter(Offer.idempotency_key == data.idempotency_key).first()
        if existing:
            return _offer_to_response(existing, db)

    listing = db.query(CropListing).filter(CropListing.id == data.listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    if listing.status != ListingStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Listing is not active")
    if listing.seller_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot make an offer on your own listing")

    # Check quantity doesn't exceed remaining
    remaining = listing.quantity_remaining or listing.quantity
    if data.quantity > remaining:
        raise HTTPException(status_code=400, detail=f"Requested quantity exceeds available ({remaining} {listing.unit})")

    offer = Offer(
        listing_id=data.listing_id,
        buyer_id=current_user.id,
        seller_id=listing.seller_id,
        offered_price=data.offered_price,
        currency=data.currency,
        quantity=data.quantity,
        unit=data.unit,
        delivery_terms=data.delivery_terms,
        payment_terms=data.payment_terms,
        notes=data.notes,
        expires_at=data.expires_at,
        idempotency_key=data.idempotency_key,
        status=OfferStatus.PENDING,
    )
    db.add(offer)
    db.flush()

    # Update listing offer count
    listing.offer_count = (listing.offer_count or 0) + 1

    # Audit event
    event = OfferEvent(
        offer_id=offer.id,
        event_type=OfferEventType.CREATED,
        actor_id=current_user.id,
        new_status="pending",
        new_price=data.offered_price,
        notes=data.notes,
    )
    db.add(event)
    db.commit()
    db.refresh(offer)

    return _offer_to_response(offer, db)


@router.get("/my/sent", response_model=PaginatedOffers)
def get_sent_offers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get offers sent by the current user (buyer view)."""
    query = db.query(Offer).filter(Offer.buyer_id == current_user.id)
    total = query.count()
    offers = query.order_by(Offer.created_at.desc()).offset((page-1)*page_size).limit(page_size).all()
    return PaginatedOffers(
        items=[_offer_to_response(o, db) for o in offers],
        total=total, page=page, page_size=page_size,
    )


@router.get("/my/received", response_model=PaginatedOffers)
def get_received_offers(
    listing_id: int = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get offers received by the current user (seller view)."""
    query = db.query(Offer).filter(Offer.seller_id == current_user.id)
    if listing_id:
        query = query.filter(Offer.listing_id == listing_id)
    total = query.count()
    offers = query.order_by(Offer.created_at.desc()).offset((page-1)*page_size).limit(page_size).all()
    return PaginatedOffers(
        items=[_offer_to_response(o, db) for o in offers],
        total=total, page=page, page_size=page_size,
    )


@router.get("/{offer_id}", response_model=OfferResponse)
def get_offer(
    offer_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific offer. Only buyer, seller, or admin can view."""
    offer = db.query(Offer).filter(Offer.id == offer_id).first()
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    if offer.buyer_id != current_user.id and offer.seller_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized to view this offer")
    return _offer_to_response(offer, db)


@router.post("/{offer_id}/action", response_model=OfferResponse)
def offer_action(
    offer_id: int,
    data: OfferAction,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Accept, reject, or withdraw an offer."""
    # Use SELECT FOR UPDATE to prevent concurrent acceptance
    offer = db.query(Offer).filter(Offer.id == offer_id).with_for_update().first()
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")

    if data.action == "accept":
        if offer.seller_id != current_user.id:
            raise HTTPException(status_code=403, detail="Only the seller can accept an offer")
        if offer.status != OfferStatus.PENDING:
            raise HTTPException(status_code=400, detail=f"Cannot accept an offer with status '{offer.status.value}'")

        # Check remaining quantity on listing
        listing = db.query(CropListing).filter(CropListing.id == offer.listing_id).with_for_update().first()
        remaining = listing.quantity_remaining or listing.quantity
        if offer.quantity > remaining:
            raise HTTPException(status_code=409, detail="Insufficient remaining quantity")

        # Reserve the quantity
        listing.quantity_remaining = remaining - offer.quantity
        if listing.quantity_remaining <= 0:
            listing.status = ListingStatus.SOLD

        offer.status = OfferStatus.ACCEPTED
        offer.responded_at = datetime.now(timezone.utc)

    elif data.action == "reject":
        if offer.seller_id != current_user.id:
            raise HTTPException(status_code=403, detail="Only the seller can reject an offer")
        if offer.status != OfferStatus.PENDING:
            raise HTTPException(status_code=400, detail=f"Cannot reject an offer with status '{offer.status.value}'")
        offer.status = OfferStatus.REJECTED
        offer.responded_at = datetime.now(timezone.utc)

    elif data.action == "withdraw":
        if offer.buyer_id != current_user.id:
            raise HTTPException(status_code=403, detail="Only the buyer can withdraw an offer")
        if offer.status not in (OfferStatus.PENDING, OfferStatus.COUNTERED):
            raise HTTPException(status_code=400, detail=f"Cannot withdraw an offer with status '{offer.status.value}'")
        offer.status = OfferStatus.WITHDRAWN
        offer.responded_at = datetime.now(timezone.utc)

    # Audit event
    event_map = {"accept": OfferEventType.ACCEPTED, "reject": OfferEventType.REJECTED, "withdraw": OfferEventType.WITHDRAWN}
    event = OfferEvent(
        offer_id=offer.id,
        event_type=event_map[data.action],
        actor_id=current_user.id,
        old_status=offer.status.value,
        new_status=offer.status.value,
        notes=data.notes,
    )
    db.add(event)
    db.commit()
    db.refresh(offer)

    return _offer_to_response(offer, db)


@router.post("/{offer_id}/counter", response_model=OfferResponse, status_code=status.HTTP_201_CREATED)
def counter_offer(
    offer_id: int,
    data: CounterOffer,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Make a counter-offer."""
    original = db.query(Offer).filter(Offer.id == offer_id).first()
    if not original:
        raise HTTPException(status_code=404, detail="Offer not found")
    if original.status != OfferStatus.PENDING:
        raise HTTPException(status_code=400, detail="Can only counter a pending offer")

    # Either party can counter
    if original.buyer_id != current_user.id and original.seller_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to counter this offer")

    # Mark original as countered
    original.status = OfferStatus.COUNTERED
    original.responded_at = datetime.now(timezone.utc)

    counter = Offer(
        listing_id=original.listing_id,
        buyer_id=original.buyer_id,
        seller_id=original.seller_id,
        offered_price=data.offered_price,
        currency=original.currency,
        quantity=data.quantity or original.quantity,
        unit=original.unit,
        delivery_terms=data.delivery_terms or original.delivery_terms,
        payment_terms=data.payment_terms or original.payment_terms,
        notes=data.notes,
        expires_at=data.expires_at,
        parent_offer_id=original.id,
        status=OfferStatus.PENDING,
        version=original.version + 1,
    )
    db.add(counter)
    db.flush()

    # Audit events
    db.add(OfferEvent(
        offer_id=original.id, event_type=OfferEventType.COUNTERED,
        actor_id=current_user.id, old_status="pending", new_status="countered",
    ))
    db.add(OfferEvent(
        offer_id=counter.id, event_type=OfferEventType.CREATED,
        actor_id=current_user.id, new_status="pending", new_price=data.offered_price,
    ))
    db.commit()
    db.refresh(counter)

    return _offer_to_response(counter, db)


@router.get("/{offer_id}/history")
def get_offer_history(
    offer_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the audit history of an offer."""
    offer = db.query(Offer).filter(Offer.id == offer_id).first()
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    if offer.buyer_id != current_user.id and offer.seller_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized")

    events = db.query(OfferEvent).filter(OfferEvent.offer_id == offer_id).order_by(OfferEvent.created_at).all()
    return [
        {
            "id": e.id, "event_type": e.event_type.value, "actor_id": e.actor_id,
            "old_status": e.old_status, "new_status": e.new_status,
            "old_price": str(e.old_price) if e.old_price else None,
            "new_price": str(e.new_price) if e.new_price else None,
            "notes": e.notes, "created_at": e.created_at.isoformat(),
        }
        for e in events
    ]
