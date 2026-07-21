from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.listing import Listing


def get_listing(db: Session, listing_id: int) -> Listing | None:
    return db.get(Listing, listing_id)


def _filtrele(query, ilce, min_fiyat, max_fiyat, oda_sayisi):
    # Hem listeleme hem sayim ayni filtreleri kullansin diye ortak yardimci.
    if ilce:
        query = query.where(Listing.ilce == ilce)
    if min_fiyat is not None:
        query = query.where(Listing.fiyat >= min_fiyat)
    if max_fiyat is not None:
        query = query.where(Listing.fiyat <= max_fiyat)
    if oda_sayisi:
        query = query.where(Listing.oda_sayisi == oda_sayisi)
    return query


def get_listings(
    db: Session,
    ilce: str | None = None,
    min_fiyat: int | None = None,
    max_fiyat: int | None = None,
    oda_sayisi: str | None = None,
    skip: int = 0,
    limit: int = 24,
) -> list[Listing]:
    query = _filtrele(select(Listing), ilce, min_fiyat, max_fiyat, oda_sayisi)
    # Sayfalar arasi tutarli siralama icin id'ye gore sabit sirala.
    query = query.order_by(Listing.id).offset(skip).limit(limit)
    return list(db.execute(query).scalars().all())


def count_listings(
    db: Session,
    ilce: str | None = None,
    min_fiyat: int | None = None,
    max_fiyat: int | None = None,
    oda_sayisi: str | None = None,
) -> int:
    """Verilen filtrelere uyan toplam ilan sayisi (pagination icin)."""
    query = _filtrele(
        select(func.count(Listing.id)), ilce, min_fiyat, max_fiyat, oda_sayisi
    )
    return db.execute(query).scalar_one()
