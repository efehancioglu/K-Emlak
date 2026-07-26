"""para kolonlarini BigInteger yap (int4 tasmasi)

Revision ID: a1f2c3d4e5f6
Revises: 7b8cd5ed3ccf
Create Date: 2026-07-23

Istanbul'da ilan fiyati 2,1 milyar TL'yi (int4 siniri) asabildiginden
listings.fiyat ve valuations tutar kolonlari BigInteger'a cevrilir.
"""
from alembic import op
import sqlalchemy as sa

revision = "a1f2c3d4e5f6"
down_revision = "7b8cd5ed3ccf"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("listings", "fiyat",
                    existing_type=sa.Integer(), type_=sa.BigInteger(),
                    existing_nullable=False)
    for kol in ("tahmini_fiyat", "birim_m2_fiyat", "fiyat_alt", "fiyat_ust"):
        op.alter_column("valuations", kol,
                        existing_type=sa.Integer(), type_=sa.BigInteger(),
                        existing_nullable=False)
    op.alter_column("valuations", "beklenen_fiyat",
                    existing_type=sa.Integer(), type_=sa.BigInteger(),
                    existing_nullable=True)


def downgrade() -> None:
    op.alter_column("listings", "fiyat",
                    existing_type=sa.BigInteger(), type_=sa.Integer(),
                    existing_nullable=False)
    for kol in ("tahmini_fiyat", "birim_m2_fiyat", "fiyat_alt", "fiyat_ust"):
        op.alter_column("valuations", kol,
                        existing_type=sa.BigInteger(), type_=sa.Integer(),
                        existing_nullable=False)
    op.alter_column("valuations", "beklenen_fiyat",
                    existing_type=sa.BigInteger(), type_=sa.Integer(),
                    existing_nullable=True)
