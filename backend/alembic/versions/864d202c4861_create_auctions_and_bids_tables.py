
"""create auctions and bids tables

Revision ID: 864d202c4861
Revises: 107a3fbc1480
Create Date: 2026-10-27 14:00:20.518782
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "864d202c4861"
down_revision: Union[str, None] = "107a3fbc1480"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create auctions and bids tables."""

    auction_status = sa.Enum(
        "SCHEDULED",
        "LIVE",
        "COMPLETED",
        "CANCELLED",
        name="auctionstatus",
    )

    op.create_table(
        "auctions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("seller_id", sa.Integer(), nullable=False),
        sa.Column("listing_id", sa.Integer(), nullable=True),
        sa.Column("crop_name", sa.String(length=255), nullable=False),
        sa.Column("crop_variety", sa.String(length=255), nullable=True),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("quantity", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("unit", sa.String(length=20), nullable=False),
        sa.Column("starting_price", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("expected_price", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("location", sa.String(length=500), nullable=True),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", auction_status, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "quantity > 0",
            name="ck_auction_positive_quantity",
        ),
        sa.CheckConstraint(
            "starting_price > 0",
            name="ck_auction_positive_start_price",
        ),
        sa.ForeignKeyConstraint(
            ["listing_id"],
            ["crop_listings.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["seller_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_auction_seller",
        "auctions",
        ["seller_id"],
        unique=False,
    )
    op.create_index(
        "ix_auction_status",
        "auctions",
        ["status"],
        unique=False,
    )

    op.create_table(
        "bids",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("auction_id", sa.Integer(), nullable=False),
        sa.Column("bidder_id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("amount > 0", name="ck_bid_positive_amount"),
        sa.ForeignKeyConstraint(
            ["auction_id"],
            ["auctions.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["bidder_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_bid_auction_bidder",
        "bids",
        ["auction_id", "bidder_id"],
        unique=False,
    )


def downgrade() -> None:
    """Remove auctions and bids tables."""

    op.drop_table("bids")
    op.drop_table("auctions")

    sa.Enum(
        "SCHEDULED",
        "LIVE",
        "COMPLETED",
        "CANCELLED",
        name="auctionstatus",
    ).drop(op.get_bind(), checkfirst=True)
