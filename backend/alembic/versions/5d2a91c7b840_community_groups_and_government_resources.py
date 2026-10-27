"""Add region/crop communities and seed official farmer scheme directory."""

from typing import Sequence, Union
from datetime import datetime, timezone

from alembic import op
import sqlalchemy as sa


revision: str = "5d2a91c7b840"
down_revision: Union[str, None] = "41c9a0b7d3e2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


SCHEMES = [
    (
        "PM-KISAN Samman Nidhi",
        "Income-support scheme for eligible landholding farmer families. "
        "Check eligibility, exclusions and payment status on the official portal.",
        "PM-KISAN",
        "https://pmkisan.gov.in/",
    ),
    (
        "Pradhan Mantri Fasal Bima Yojana (PMFBY)",
        "Crop insurance for notified crops and areas, subject to the current "
        "season notification and enrolment window.",
        "PMFBY",
        "https://pmfby.gov.in/",
    ),
    (
        "Kisan Credit Card (KCC)",
        "Institutional agricultural credit for eligible farmers and allied "
        "activities through participating banks.",
        "Department of Financial Services / participating bank",
        "https://www.myscheme.gov.in/",
    ),
    (
        "Pradhan Mantri Krishi Sinchayee Yojana (PMKSY)",
        "Supports irrigation and water-use efficiency through state and "
        "component-specific programmes.",
        "Ministry of Agriculture and Farmers Welfare",
        "https://pmksy.gov.in/",
    ),
    (
        "Soil Health Card Scheme",
        "Provides soil nutrient information and fertiliser recommendations "
        "based on soil testing.",
        "Soil Health Card portal",
        "https://soilhealth.dac.gov.in/",
    ),
    (
        "National Agriculture Market (e-NAM)",
        "Electronic trading platform connecting participating mandis.",
        "e-NAM",
        "https://www.enam.gov.in/",
    ),
    (
        "PM-KUSUM",
        "Supports eligible solar pumps and decentralised solar projects "
        "through notified implementing agencies and state-specific calls.",
        "PM-KUSUM",
        "https://pmkusum.mnre.gov.in/",
    ),
    (
        "Agriculture Infrastructure Fund (AIF)",
        "Financing facility for eligible agriculture infrastructure projects "
        "through participating lenders.",
        "Agriculture Infrastructure Fund",
        "https://agriinfra.dac.gov.in/",
    ),
    (
        "Rashtriya Krishi Vikas Yojana (RKVY)",
        "Agriculture development programme implemented through approved "
        "projects and state priorities.",
        "Department of Agriculture and Farmers Welfare",
        "https://rkvy.nic.in/",
    ),
    (
        "Pradhan Mantri Annadata Aay Sanrakshan Abhiyan (PM-AASHA)",
        "Price-support mechanisms for notified crops, subject to state "
        "procurement operations and current season arrangements.",
        "Department of Agriculture and Farmers Welfare",
        "https://agriwelfare.gov.in/",
    ),
    (
        "Sub-Mission on Agricultural Mechanization (SMAM)",
        "Support for eligible agricultural machinery and custom hiring "
        "arrangements through state-specific implementation.",
        "Department of Agriculture and Farmers Welfare",
        "https://agrimachinery.nic.in/",
    ),
    (
        "National Beekeeping and Honey Mission (NBHM)",
        "Promotes scientific beekeeping and honey-related value chains "
        "through approved activities and implementing agencies.",
        "National Bee Board",
        "https://nbb.gov.in/",
    ),
]

CROPS = [
    "Cotton",
    "Papaya",
    "Banana",
    "Jowar",
    "Wheat",
    "Bajra",
    "Fruits",
    "Vegetables",
]


def upgrade() -> None:
    op.create_table(
        "community_groups",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("kind", sa.String(length=20), nullable=False),
        sa.Column("crop", sa.String(length=80), nullable=True),
        sa.Column("state", sa.String(length=120), nullable=True),
        sa.Column("district", sa.String(length=120), nullable=True),
        sa.Column("taluka", sa.String(length=120), nullable=True),
        sa.Column("village", sa.String(length=120), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "kind",
            "name",
            "crop",
            "state",
            "district",
            "taluka",
            "village",
            name="uq_community_group_identity",
        ),
    )

    for col in ("kind", "crop", "state", "district", "taluka", "village"):
        op.create_index(
            f"ix_community_groups_{col}",
            "community_groups",
            [col],
        )

    op.create_table(
        "community_memberships",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("community_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column(
            "joined_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["community_id"],
            ["community_groups.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "community_id",
            "user_id",
            name="uq_community_member",
        ),
    )

    op.create_index(
        "ix_community_memberships_community_id",
        "community_memberships",
        ["community_id"],
    )
    op.create_index(
        "ix_community_memberships_user_id",
        "community_memberships",
        ["user_id"],
    )

    op.add_column(
        "community_posts",
        sa.Column("community_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_community_posts_community_id",
        "community_posts",
        "community_groups",
        ["community_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_community_posts_community_id",
        "community_posts",
        ["community_id"],
    )

    op.add_column(
        "public_resources",
        sa.Column("documents", sa.Text(), nullable=True),
    )

    conn = op.get_bind()
    now = datetime.now(timezone.utc)

    # Seed crop communities. Existing matching rows are left unchanged.
    for crop in CROPS:
        conn.execute(
            sa.text(
                """
                INSERT INTO community_groups
                    (name, kind, crop, state, district, taluka, village, created_at)
                VALUES
                    (:name, 'crop', :crop, NULL, NULL, NULL, NULL, :created_at)
                ON CONFLICT DO NOTHING
                """
            ),
            {
                "name": f"{crop} Farmers",
                "crop": crop,
                "created_at": now,
            },
        )

    # Seed scheme directory entries without duplicating existing schemes.
    for title, summary, source_name, url in SCHEMES:
        documents = (
            "Document requirements vary by scheme, state and application route. "
            "Keep identity proof, bank details and relevant land/crop records "
            "ready only where applicable. Confirm the exact checklist on the "
            "official portal before applying."
        )

        if "PM-KISAN" in title:
            documents = (
                "Aadhaar; bank account/passbook details; landholding or "
                "land-record details; e-KYC as required. Eligibility and "
                "exclusions apply."
            )
        elif "Fasal Bima" in title:
            documents = (
                "Identity/Aadhaar; bank details; land records or valid "
                "tenancy/cultivation proof; crop and sowing details, as "
                "required by the current notified season."
            )
        elif "Credit Card" in title:
            documents = (
                "Identity and address proof; photographs; land/cropping "
                "details; bank application and documents requested by "
                "the participating bank."
            )
        elif "Soil Health" in title:
            documents = (
                "Contact the local soil-testing laboratory or agriculture "
                "office. Farmer identity and farm location/land details "
                "may be requested."
            )
        elif "e-NAM" in title:
            documents = (
                "Farmer identity/KYC; bank details; local mandi/APMC farmer "
                "registration details where applicable."
            )
        elif "KUSUM" in title:
            documents = (
                "Check the active state/component notification. Identity, "
                "land/beneficiary details, bank details and pump/project "
                "information may be required."
            )
        elif "Infrastructure Fund" in title:
            documents = (
                "Project report/business details; identity/entity documents; "
                "bank and financial documents required by the lender."
            )
        elif "Mechanization" in title:
            documents = (
                "Check the state application window. Identity, bank details, "
                "beneficiary/category details, relevant land details and "
                "machinery quotation may be required."
            )

        conn.execute(
            sa.text(
                """
                INSERT INTO public_resources
                    (
                        kind,
                        title,
                        summary,
                        documents,
                        source_name,
                        source_url,
                        published_at,
                        created_at
                    )
                SELECT
                    'scheme',
                    CAST(:title_insert AS VARCHAR),
                    CAST(:summary AS TEXT),
                    CAST(:documents AS TEXT),
                    CAST(:source_name AS VARCHAR),
                    CAST(:url AS VARCHAR),
                    NULL,
                    :created_at
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM public_resources
                    WHERE kind = 'scheme'
                      AND title = CAST(:title_check AS VARCHAR)
                )
                """
            ),
            {
                "title_insert": title,
                "title_check": title,
                "summary": summary,
                "documents": documents,
                "source_name": source_name,
                "url": url,
                "created_at": now,
            },
        )


def downgrade() -> None:
    op.drop_column("public_resources", "documents")

    op.drop_index(
        "ix_community_posts_community_id",
        table_name="community_posts",
    )
    op.drop_constraint(
        "fk_community_posts_community_id",
        "community_posts",
        type_="foreignkey",
    )
    op.drop_column("community_posts", "community_id")

    op.drop_index(
        "ix_community_memberships_user_id",
        table_name="community_memberships",
    )
    op.drop_index(
        "ix_community_memberships_community_id",
        table_name="community_memberships",
    )
    op.drop_table("community_memberships")

    for col in ("village", "taluka", "district", "state", "crop", "kind"):
        op.drop_index(
            f"ix_community_groups_{col}",
            table_name="community_groups",
        )

    op.drop_table("community_groups")