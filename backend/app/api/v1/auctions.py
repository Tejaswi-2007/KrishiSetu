
"""Auction API endpoints."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.auction import Auction, Bid, AuctionStatus
from app.schemas.auction import (
    AuctionCreate,
    AuctionOut,
    BidCreate,
    BidOut,
    PaginatedAuctions,
)

router = APIRouter()


def get_bid_summary(db: Session, auction_id: int):
    """Return the highest bid and total number of bids."""
    highest = (
        db.query(Bid.amount)
        .filter(Bid.auction_id == auction_id)
        .order_by(Bid.amount.desc())
        .first()
    )
    count = db.query(Bid).filter(Bid.auction_id == auction_id).count()
    return (highest[0] if highest else None), count


def _update_auction_statuses(db: Session) -> None:
    """Move scheduled auctions live when their window opens and complete expired ones."""
    now = datetime.now(timezone.utc)
    changed = False

    auctions = db.query(Auction).filter(
        Auction.status.in_([AuctionStatus.SCHEDULED, AuctionStatus.LIVE])
    ).all()

    for auction in auctions:
        start_time = auction.start_time
        end_time = auction.end_time
        if start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=timezone.utc)
        if end_time.tzinfo is None:
            end_time = end_time.replace(tzinfo=timezone.utc)

        new_status = auction.status
        if now < start_time:
            new_status = AuctionStatus.SCHEDULED
        elif now <= end_time:
            new_status = AuctionStatus.LIVE
        else:
            new_status = AuctionStatus.COMPLETED

        if auction.status != new_status:
            auction.status = new_status
            changed = True

    if changed:
        try:
            db.commit()
        except SQLAlchemyError:
            db.rollback()
            raise



@router.post(
    "/",
    response_model=AuctionOut,
    status_code=status.HTTP_201_CREATED,
)
def create_auction(
    auction_in: AuctionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create an auction for the authenticated user."""
    if auction_in.start_time >= auction_in.end_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_time must be before end_time",
        )

    db_auction = Auction(
        seller_id=current_user.id,
        crop_name=auction_in.crop_name,
        crop_variety=auction_in.crop_variety,
        category=auction_in.category,
        quantity=auction_in.quantity,
        unit=auction_in.unit,
        starting_price=auction_in.starting_price,
        expected_price=auction_in.expected_price,
        location=auction_in.location,
        start_time=auction_in.start_time,
        end_time=auction_in.end_time,
        status=AuctionStatus.SCHEDULED,
    )

    try:
        db.add(db_auction)
        db.commit()
        db.refresh(db_auction)
        return db_auction
    except SQLAlchemyError:
        db.rollback()
        # Keep database details in the backend logs, not the API response.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save auction. Check backend logs for the database error.",
        )


@router.get("/", response_model=PaginatedAuctions)
def list_auctions(
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
):
    """Return a paginated list of auctions."""
    if page < 1 or page_size < 1 or page_size > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="page must be >= 1 and page_size must be between 1 and 100",
        )

    total = db.query(Auction).count()
    auctions = (
        db.query(Auction)
        .order_by(Auction.start_time.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items = []
    for auction in auctions:
        out = AuctionOut.model_validate(auction)
        highest, count = get_bid_summary(db, auction.id)
        out.highest_bid = highest
        out.bid_count = count
        items.append(out)

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


@router.get("/{auction_id}", response_model=AuctionOut)
def get_auction(
    auction_id: int,
    db: Session = Depends(get_db),
):
    """Return details for one auction."""
    auction = db.query(Auction).filter(Auction.id == auction_id).first()

    if not auction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Auction not found",
        )

    out = AuctionOut.model_validate(auction)
    highest, count = get_bid_summary(db, auction.id)
    out.highest_bid = highest
    out.bid_count = count
    return out


@router.post(
    "/{auction_id}/bid",
    response_model=BidOut,
    status_code=status.HTTP_201_CREATED,
)
def place_bid(
    auction_id: int,
    bid_in: BidCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Place a bid on an active auction."""
    # Lock the auction row while validating and creating a bid. On PostgreSQL
    # this serializes competing bids so two requests cannot both validate
    # against the same stale highest-bid value.
    auction = (
        db.query(Auction)
        .filter(Auction.id == auction_id)
        .with_for_update()
        .first()
    )

    if not auction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Auction not found",
        )

    now = datetime.now(timezone.utc)

    start_time = auction.start_time
    end_time = auction.end_time

    # Handle timestamps stored without timezone information.
    if start_time.tzinfo is None:
        start_time = start_time.replace(tzinfo=timezone.utc)
    if end_time.tzinfo is None:
        end_time = end_time.replace(tzinfo=timezone.utc)

    if not (start_time <= now <= end_time):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Auction is outside its bidding time window",
        )

    if auction.status != AuctionStatus.LIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Auction is not live",
        )

    if auction.seller_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Seller cannot bid on own auction",
        )

    highest, _ = get_bid_summary(db, auction.id)

    minimum = highest if highest is not None else auction.starting_price
    if bid_in.amount <= minimum:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bid must be higher than the current highest bid or starting price",
        )

    db_bid = Bid(
        auction_id=auction.id,
        bidder_id=current_user.id,
        amount=bid_in.amount,
    )

    try:
        db.add(db_bid)
        db.commit()
        db.refresh(db_bid)
        return db_bid
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save bid. Check backend logs for the database error.",
        )
