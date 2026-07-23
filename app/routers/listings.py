from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.crud import listing as listing_crud
from app.models.enums import IsitmaTipi, KullanimDurumu
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
    mahalle: str | None = None,
    oda_sayisi: str | None = None,
    min_fiyat: int | None = None,
    max_fiyat: int | None = None,
    min_m2: int | None = None,
    max_m2: int | None = None,
    min_banyo: int | None = None,
    max_bina_yasi: int | None = None,
    isitma_tipi: IsitmaTipi | None = None,
    kullanim_durumu: KullanimDurumu | None = None,
    esyali: bool | None = None,
    cephe: str | None = Query(default=None, pattern="^(kuzey|guney|dogu|bati)$"),
    piyasa: str | None = Query(default=None, pattern="^(uygun|normal|pahali)$"),
    sirala: str = "en_yeni",
    skip: int = 0,
    limit: int = Query(default=24, le=100),
    db: Session = Depends(get_db)
):
    """Filtreye uyan ilanlari secilen siraya gore sayfa sayfa dondurur. Her
    ilan icin, tiklamadan once piyasaya gore durumunu gosteren hafif bir
    onizleme (piyasa) da hesaplanir; bunun icin sayfadaki ilanlar modele
    sokulur.

    piyasa (uygun/normal/pahali) verilirse, bu durum DB'de tutulmadigindan
    filtreye uyan TUM ilanlar puanlanip duruma gore elenir, sonra sayfalanir."""
    filtre = {
        "ilce": ilce,
        "mahalle": mahalle,
        "oda_sayisi": oda_sayisi,
        "min_fiyat": min_fiyat,
        "max_fiyat": max_fiyat,
        "min_m2": min_m2,
        "max_m2": max_m2,
        "min_banyo": min_banyo,
        "max_bina_yasi": max_bina_yasi,
        "isitma_tipi": isitma_tipi,
        "kullanim_durumu": kullanim_durumu,
        "esyali": esyali,
        "cephe": cephe,
    }

    if piyasa:
        # Durum hesaplanan bir alan: once tum eslesen ilanlari (siralanmis)
        # cek, hepsini puanla, istenen duruma gore ele, sonra sayfa dilimini al.
        hepsi = listing_crud.get_listings(
            db=db, filtre=filtre, sirala=sirala, skip=0, limit=None
        )
        ozetler = valuation_service.ilanlari_piyasa_ozeti(hepsi)
        eslesen = [
            (kayit, ozet)
            for kayit, ozet in zip(hepsi, ozetler)
            if ozet is not None and ozet.durum == piyasa
        ]
        toplam = len(eslesen)
        dilim = eslesen[skip : skip + limit]
        items = [
            ListingListItem(
                **ListingRead.model_validate(kayit).model_dump(),
                piyasa=ozet,
            )
            for kayit, ozet in dilim
        ]
        return ListingPage(toplam=toplam, skip=skip, limit=limit, items=items)

    toplam = listing_crud.count_listings(db=db, filtre=filtre)
    kayitlar = listing_crud.get_listings(
        db=db,
        filtre=filtre,
        sirala=sirala,
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

@router.get("/filtre-secenekleri")
def filtre_secenekleri():
    """Ilan filtresindeki dropdown'lar icin DB enum degerleri. Deger =
    veritabanindaki gercek deger (filtre birebir eslessin), etiket = ekranda
    gosterilecek okunakli metin."""
    return {
        "isitma_tipi": [
            {"deger": t.value, "etiket": t.value} for t in IsitmaTipi
        ],
        "kullanim_durumu": [
            {"deger": k.value, "etiket": k.value} for k in KullanimDurumu
        ],
        "cephe": [
            {"deger": "kuzey", "etiket": "Kuzey"},
            {"deger": "guney", "etiket": "Güney"},
            {"deger": "dogu", "etiket": "Doğu"},
            {"deger": "bati", "etiket": "Batı"},
        ],
        "sirala": [
            {"deger": "en_yeni", "etiket": "En yeni"},
            {"deger": "en_eski", "etiket": "En eski"},
            {"deger": "fiyat_artan", "etiket": "Fiyat: artan"},
            {"deger": "fiyat_azalan", "etiket": "Fiyat: azalan"},
            {"deger": "m2_azalan", "etiket": "m²: büyükten küçüğe"},
            {"deger": "m2_artan", "etiket": "m²: küçükten büyüğe"},
        ],
    }

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