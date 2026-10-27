"""Offer service: business logic with optimistic concurrency control."""

from datetime import datetime, timedelta, timezone
from typing import List

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.offer import Offer, OfferEvent, OfferStatus, OfferEventType
from app.models.listing import CropListing, ListingStatus
from app.models.user import User
from app.schemas.offer import OfferCreate, OfferCounterOffer, OfferStatusUpdate


def create_offer(db: Session, offer_data: OfferCreate, buyer: User) -> Offer:
    """Create a new purchase offer on a listing.

    Validates that the listing is active and the buyer isn't the seller.
    Sets a 48-hour default expiry.
    """
    # Get listing
    listing = db.query(CropListing).filter(CropListing.id == offer_data.listing_id).first()
    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found",
        )

    if listing.status != ListingStatus.active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only make offers on active listings",
        )

    if listing.seller_id == buyer.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot make an offer on your own listing",
        )

    # Check quantity doesn't exceed available
    if offer_data.quantity > listing.available_quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Requested quantity exceeds available quantity ({listing.available_quantity})",
        )

    # Create offer with 48-hour expiry
    offer = Offer(
        listing_id=offer_data.listing_id,
        buyer_id=buyer.id,
        offered_price=offer_data.offered_price,
        quantity=offer_data.quantity,
        unit=offer_data.unit,
        message=offer_data.message,
        status=OfferStatus.pending,
        version=1,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=48),
    )
    db.add(offer)
    db.flush()

    # Record creation event
    event = OfferEvent(
        offer_id=offer.id,
        event_type=OfferEventType.created,
        actor_id=buyer.id,
        new_price=offer_data.offered_price,
        message=offer_data.message,
    )
    db.add(event)
    db.commit()
    db.refresh(offer)
    return offer


def get_offer(db: Session, offer_id: int) -> Offer:
    """Get an offer by ID. Raises 404 if not found."""
    offer = db.query(Offer).filter(Offer.id == offer_id).first()
    if not offer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Offer not found",
        )
    return offer


def counter_offer(
    db: Session, offer_id: int, data: OfferCounterOffer, current_user: User
) -> Offer:
    """Make a counter-offer. Uses optimistic concurrency control via version check.

    Only the listing seller can counter-offer.
    """
    offer = get_offer(db, offer_id)

    # Version check for optimistic concurrency
    if offer.version != data.version:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Offer has been modified by another user. Please refresh and try again.",
        )

    # Only seller can counter
    listing = db.query(CropListing).filter(CropListing.id == offer.listing_id).first()
    if listing.seller_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the listing seller can make counter-offers",
        )

    if offer.status not in (OfferStatus.pending, OfferStatus.counter_offered):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot counter an offer with status '{offer.status.value}'",
        )

    old_price = offer.counter_price or offer.offered_price

    # Update offer
    offer.counter_price = data.counter_price
    offer.status = OfferStatus.counter_offered
    offer.version += 1
    offer.expires_at = datetime.now(timezone.utc) + timedelta(hours=48)

    # Record event
    event = OfferEvent(
        offer_id=offer.id,
        event_type=OfferEventType.counter_offer,
        actor_id=current_user.id,
        old_price=old_price,
        new_price=data.counter_price,
        message=data.message,
    )
    db.add(event)
    db.commit()
    db.refresh(offer)
    return offer


def update_offer_status(
    db: Session, offer_id: int, data: OfferStatusUpdate, current_user: User
) -> Offer:
    """Accept, reject, or withdraw an offer with optimistic concurrency control.

    Accept/reject: only listing seller.
    Withdraw: only the buyer who made the offer.
    """
    offer = get_offer(db, offer_id)

    # Version check
    if offer.version != data.version:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Offer has been modified by another user. Please refresh and try again.",
        )

    listing = db.query(CropListing).filter(CropListing.id == offer.listing_id).first()
    new_status = OfferStatus(data.status)

    # Permission checks
    if new_status in (OfferStatus.accepted, OfferStatus.rejected):
        if listing.seller_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the listing seller can accept or reject offers",
            )
    elif new_status == OfferStatus.withdrawn:
        if offer.buyer_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the buyer can withdraw their offer",
            )

    # Status transition validation
    valid_transitions = {
        OfferStatus.pending: {OfferStatus.accepted, OfferStatus.rejected, OfferStatus.withdrawn},
        OfferStatus.counter_offered: {OfferStatus.accepted, OfferStatus.rejected, OfferStatus.withdrawn},
    }

    if offer.status not in valid_transitions or new_status not in valid_transitions.get(offer.status, set()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot transition from '{offer.status.value}' to '{new_status.value}'",
        )

    # Update offer
    offer.status = new_status
    offer.version += 1

    # If accepted, update listing available quantity
    if new_status == OfferStatus.accepted:
        listing.available_quantity -= offer.quantity
        if listing.available_quantity <= 0:
            listing.status = ListingStatus.sold
        else:
            listing.status = ListingStatus.reserved

    # Map to event type
    event_type_map = {
        OfferStatus.accepted: OfferEventType.accepted,
        OfferStatus.rejected: OfferEventType.rejected,
        OfferStatus.withdrawn: OfferEventType.withdrawn,
    }

    event = OfferEvent(
        offer_id=offer.id,
        event_type=event_type_map[new_status],
        actor_id=current_user.id,
        message=data.message,
    )
    db.add(event)
    db.commit()
    db.refresh(offer)
    return offer


def get_offers_for_listing(db: Session, listing_id: int) -> List[Offer]:
    """Get all offers for a specific listing."""
    return (
        db.query(Offer)
        .filter(Offer.listing_id == listing_id)
        .order_by(Offer.created_at.desc())
        .all()
    )


def get_offers_by_buyer(db: Session, buyer_id: int) -> List[Offer]:
    """Get all offers made by a specific buyer."""
    return (
        db.query(Offer)
        .filter(Offer.buyer_id == buyer_id)
        .order_by(Offer.created_at.desc())
        .all()
    )


def get_offer_events(db: Session, offer_id: int) -> List[OfferEvent]:
    """Get the full event history for an offer."""
    return (
        db.query(OfferEvent)
        .filter(OfferEvent.offer_id == offer_id)
        .order_by(OfferEvent.created_at.asc())
        .all()
    )
