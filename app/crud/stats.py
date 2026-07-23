from sqlalchemy import Float, cast, func, select
from sqlalchemy.orm import Session

from app.models.listing import Listing

# Birim m2 fiyati: fiyat / brut_metrekare. Integer bolme olmamasi icin
# Float'a cast edilir; brut_metrekare=0 olan ilanlar disari alinir.
_M2_FIYAT = cast(Listing.fiyat, Float) / Listing.brut_metrekare
_GECERLI_M2 = Listing.brut_metrekare > 0


def ozet(db: Session) -> dict:
    """Yonetim ekrani ozet kartlari icin toplam degerler."""
    satir = db.execute(
        select(
            func.count(Listing.id),
            func.count(func.distinct(Listing.ilce)),
            func.coalesce(func.avg(Listing.fiyat), 0),
            func.coalesce(func.min(Listing.fiyat), 0),
            func.coalesce(func.max(Listing.fiyat), 0),
        )
    ).one()

    ort_m2 = db.execute(
        select(func.coalesce(func.avg(_M2_FIYAT), 0)).where(_GECERLI_M2)
    ).scalar_one()

    return {
        "toplam_ilan": satir[0],
        "toplam_ilce": satir[1],
        "ortalama_fiyat": int(satir[2]),
        "en_dusuk_fiyat": int(satir[3]),
        "en_yuksek_fiyat": int(satir[4]),
        "ortalama_m2_fiyat": int(ort_m2),
    }


def ilce_bazinda(db: Session) -> list[dict]:
    """Her ilce icin ilan sayisi, ortalama fiyat ve ortalama m2 fiyati.

    Ilan sayisi cok olan ilceler once gelir (grafikte anlamli siralama)."""
    rows = db.execute(
        select(
            Listing.ilce,
            func.count(Listing.id),
            func.avg(Listing.fiyat),
            func.avg(func.nullif(_M2_FIYAT, None)),
        )
        .where(_GECERLI_M2)
        .group_by(Listing.ilce)
        .order_by(func.count(Listing.id).desc())
    ).all()

    return [
        {
            "ilce": r[0],
            "ilan_sayisi": r[1],
            "ortalama_fiyat": int(r[2] or 0),
            "ortalama_m2_fiyat": int(r[3] or 0),
        }
        for r in rows
    ]


def fiyat_trendi(db: Session) -> list[dict]:
    """Ilanlarin toplanma tarihine gore aylik ortalama fiyat/m2 fiyat.

    'Zaman icindeki fiyat degisimi' grafigi icin en eskiden yeniye siralidir.
    """
    donem = func.to_char(
        func.date_trunc("month", Listing.olusturulma_tarihi), "YYYY-MM"
    )
    rows = db.execute(
        select(
            donem,
            func.count(Listing.id),
            func.avg(Listing.fiyat),
            func.avg(func.nullif(_M2_FIYAT, None)),
        )
        .where(_GECERLI_M2)
        .group_by(donem)
        .order_by(donem)
    ).all()

    return [
        {
            "donem": r[0],
            "ilan_sayisi": r[1],
            "ortalama_fiyat": int(r[2] or 0),
            "ortalama_m2_fiyat": int(r[3] or 0),
        }
        for r in rows
    ]
