from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.listing import Listing


def get_listing(db: Session, listing_id: int) -> Listing | None:
    return db.get(Listing, listing_id)


def get_listings(
    db: Session,
    ilce: str | None = None,
    min_fiyat: int | None = None,
    max_fiyat: int | None = None,
    oda_sayisi: str | None = None,
    skip: int = 0,
    limit: int = 50,
) -> list[Listing]:
    query = select(Listing)

    if ilce:
        query = query.where(Listing.ilce == ilce)
    if min_fiyat is not None:
        query = query.where(Listing.fiyat >= min_fiyat)
    if max_fiyat is not None:
        query = query.where(Listing.fiyat <= max_fiyat)
    if oda_sayisi:
        query = query.where(Listing.oda_sayisi == oda_sayisi)

    query = query.offset(skip).limit(limit)

    return list(db.execute(query).scalars().all())