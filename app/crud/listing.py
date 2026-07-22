from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.listing import Listing


def get_listing(db: Session, listing_id: int) -> Listing | None:
    return db.get(Listing, listing_id)


# Cephe filtresi icin: istekten gelen yon -> ilgili boolean sutun.
_CEPHE_SUTUN = {
    "kuzey": Listing.cephe_kuzey,
    "guney": Listing.cephe_guney,
    "dogu": Listing.cephe_dogu,
    "bati": Listing.cephe_bati,
}

# Siralama secenekleri -> order_by ifadesi. Varsayilan "en_yeni".
_SIRALAMA = {
    "en_yeni": Listing.olusturulma_tarihi.desc(),
    "en_eski": Listing.olusturulma_tarihi.asc(),
    "fiyat_artan": Listing.fiyat.asc(),
    "fiyat_azalan": Listing.fiyat.desc(),
    "m2_artan": Listing.brut_metrekare.asc(),
    "m2_azalan": Listing.brut_metrekare.desc(),
}


def _filtrele(query, f: dict):
    """Hem listeleme hem sayim ayni filtreleri kullansin diye ortak yardimci.
    f: router'dan gelen filtre sozlugu (None degerler yok sayilir)."""
    if f.get("ilce"):
        query = query.where(Listing.ilce == f["ilce"])
    if f.get("mahalle"):
        query = query.where(Listing.mahalle == f["mahalle"])
    if f.get("oda_sayisi"):
        query = query.where(Listing.oda_sayisi == f["oda_sayisi"])
    if f.get("min_fiyat") is not None:
        query = query.where(Listing.fiyat >= f["min_fiyat"])
    if f.get("max_fiyat") is not None:
        query = query.where(Listing.fiyat <= f["max_fiyat"])
    if f.get("min_m2") is not None:
        query = query.where(Listing.brut_metrekare >= f["min_m2"])
    if f.get("max_m2") is not None:
        query = query.where(Listing.brut_metrekare <= f["max_m2"])
    if f.get("min_banyo") is not None:
        query = query.where(Listing.banyo_sayisi >= f["min_banyo"])
    if f.get("max_bina_yasi") is not None:
        query = query.where(Listing.bina_yasi <= f["max_bina_yasi"])
    if f.get("isitma_tipi"):
        query = query.where(Listing.isitma_tipi == f["isitma_tipi"])
    if f.get("kullanim_durumu"):
        query = query.where(Listing.kullanim_durumu == f["kullanim_durumu"])
    if f.get("esyali") is not None:
        query = query.where(Listing.esyali == f["esyali"])
    if f.get("cephe"):
        sutun = _CEPHE_SUTUN.get(f["cephe"])
        if sutun is not None:
            query = query.where(sutun.is_(True))
    return query


def get_listings(
    db: Session,
    filtre: dict,
    sirala: str = "en_yeni",
    skip: int = 0,
    limit: int = 24,
) -> list[Listing]:
    query = _filtrele(select(Listing), filtre)
    # Secilen siralama + esitlikte sayfalar arasi tutarlilik icin id kirici.
    duzen = _SIRALAMA.get(sirala, _SIRALAMA["en_yeni"])
    query = query.order_by(duzen, Listing.id).offset(skip).limit(limit)
    return list(db.execute(query).scalars().all())


def count_listings(db: Session, filtre: dict) -> int:
    """Verilen filtrelere uyan toplam ilan sayisi (pagination icin)."""
    query = _filtrele(select(func.count(Listing.id)), filtre)
    return db.execute(query).scalar_one()
