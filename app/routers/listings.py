from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.crud import listing as listing_crud
from app.schemas.listing import (
    ListingDetail,
    ListingListItem,
    ListingPage,
    ListingRead,
)
from app.services import valuation_service

router = APIRouter(prefix="/listings", tags=["listings"])

@router.get("/", response_model=ListingPage)
def list_listings(
    ilce: str | None = None,
    min_fiyat: int | None = None,
    max_fiyat: int | None = None,
    oda_sayisi: str | None = None,
    skip: int = 0,
    limit: int = Query(default=24, le=100),
    db: Session = Depends(get_db)
):
    """Filtreye uyan ilanlari sayfa sayfa dondurur. Her ilan icin, tiklamadan
    once piyasaya gore durumunu gosteren hafif bir onizleme (piyasa) da
    hesaplanir; bunun icin sayfadaki ilanlar modele sokulur."""
    toplam = listing_crud.count_listings(
        db=db,
        ilce=ilce,
        min_fiyat=min_fiyat,
        max_fiyat=max_fiyat,
        oda_sayisi=oda_sayisi,
    )
    kayitlar = listing_crud.get_listings(
        db=db,
        ilce=ilce,
        min_fiyat=min_fiyat,
        max_fiyat=max_fiyat,
        oda_sayisi=oda_sayisi,
        skip=skip,
        limit=limit,
    )
    ozetler = valuation_service.ilanlari_piyasa_ozeti(kayitlar)

    items = [
        ListingListItem(
            **ListingRead.model_validate(kayit).model_dump(),
            piyasa=ozet,
        )
        for kayit, ozet in zip(kayitlar, ozetler)
    ]
    return ListingPage(toplam=toplam, skip=skip, limit=limit, items=items)

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