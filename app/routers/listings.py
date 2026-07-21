from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.crud import listing as listing_crud
from app.schemas.listing import ListingDetail, ListingRead
from app.services import valuation_service

router = APIRouter(prefix="/listings", tags=["listings"])

@router.get("/", response_model= list[ListingRead])
def list_listings(
    ilce: str | None = None,
    min_fiyat: int | None = None,
    max_fiyat: int | None = None,
    oda_sayisi: str | None = None,
    skip: int = 0,
    limit: int = Query(default=50, le=200),
    db: Session = Depends(get_db)
):
    return listing_crud.get_listings(
        db= db,
        ilce= ilce,
        limit= limit,
        max_fiyat= max_fiyat,
        min_fiyat= min_fiyat,
        oda_sayisi= oda_sayisi,
        skip= skip
    )

@router.get("/{listing_id}", response_model=ListingDetail)
def get_listing(listing_id: int, db: Session = Depends(get_db)):
    listing = listing_crud.get_listing(db,listing_id)
    if listing is None:
        raise HTTPException(status_code=404, detail="ilan bulunamadi")

    degerlendirme = valuation_service.ilani_degerlendir(listing)
    return ListingDetail(
        **ListingRead.model_validate(listing).model_dump(),
        fiyat_degerlendirmesi=degerlendirme,
    )