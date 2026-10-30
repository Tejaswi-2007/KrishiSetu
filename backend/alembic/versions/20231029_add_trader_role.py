'''Add trader role and trader_profiles table.

Revision ID: 20231029_add_trader_role
Revises: 5d2a91c7b840
Create Date: 2023-10-29 00:00:00
'''

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20231029_add_trader_role"
 down_revision: Union[str, None] = "5d2a91c7b840"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Add new value to existing userrole enum
    op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'trader'")

    # Create trader_profiles table
    op.create_table(
        "trader_profiles",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False),
        sa.Column("business_name", sa.String(length=500), nullable=True),
        sa.Column("business_type", sa.String(length=100), nullable=True),
        sa.Column("gst_number", sa.String(length=20), nullable=True),
        sa.Column("business_address", sa.Text(), nullable=True),
        sa.Column("city", sa.String(length=255), nullable=True),
        sa.Column("district", sa.String(length=255), nullable=True),
        sa.Column("state", sa.String(length=100), nullable=False, server_default="Maharashtra"),
        sa.Column("pincode", sa.String(length=10), nullable=True),
        sa.Column("preferred_crops", sa.JSON(), nullable=True),
        sa.Column("avg_monthly_volume", sa.String(length=100), nullable=True),
        sa.Column("business_verified", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Index("ix_trader_district", "district"),
        sa.Index("ix_trader_business_type", "business_type"),
    )

def downgrade() -> None:
    op.drop_table("trader_profiles")
    # NOTE: PostgreSQL does not support removing enum values easily; skipping enum rollback.

