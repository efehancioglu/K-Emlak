"""DB'deki Istanbul disi kalinti ilanlari temizler.

Proje ilk etapta yalnizca Istanbul ile calisir. Eski Turkiye geneli
scrape'lerden gelmis Istanbul disi satirlar veritabaninda kalmis olabilir.
Bu script once ne silinecegini gosterir (dry-run); --uygula verilirse siler.

Kullanim:
    python -m scripts.istanbul_disi_temizle          # sadece rapor (silmez)
    python -m scripts.istanbul_disi_temizle --uygula  # Istanbul disini siler
"""

import sys

from sqlalchemy import func, select

from app.core.database import SessionLocal
from app.models.listing import Listing

# Postgres tarafinda il degerini normalize eder: bosluk kirp, kucuk harf,
# Turkce buyuk I kucultmesindeki birlesik noktayi (U+0307 = chr(775)) sil.
_NORM_IL = func.replace(func.lower(func.trim(Listing.il)), chr(775), "")
_ISTANBUL_DISI = _NORM_IL != "istanbul"


def rapor(db) -> int:
    toplam = db.execute(select(func.count(Listing.id))).scalar_one()
    disi = db.execute(
        select(func.count(Listing.id)).where(_ISTANBUL_DISI)
    ).scalar_one()

    print(f"Toplam ilan       : {toplam}")
    print(f"Istanbul disi     : {disi}")
    print(f"Kalacak (Istanbul): {toplam - disi}")

    ornek = db.execute(
        select(Listing.il, func.count(Listing.id))
        .where(_ISTANBUL_DISI)
        .group_by(Listing.il)
        .order_by(func.count(Listing.id).desc())
        .limit(10)
    ).all()
    if ornek:
        print("\nSilinecek il dagilimi (ilk 10):")
        for il, adet in ornek:
            print(f"  {adet:5}  {il!r}")
    return disi


def calistir(uygula: bool = False) -> None:
    db = SessionLocal()
    try:
        disi = rapor(db)
        if not uygula:
            print("\n[dry-run] Hicbir sey silinmedi. Silmek icin --uygula ekleyin.")
            return
        if disi == 0:
            print("\nSilinecek Istanbul disi kayit yok.")
            return

        silinen = db.query(Listing).filter(_ISTANBUL_DISI).delete(
            synchronize_session=False
        )
        db.commit()
        print(f"\nSilindi: {silinen} Istanbul disi ilan.")
    finally:
        db.close()


if __name__ == "__main__":
    calistir(uygula="--uygula" in sys.argv)
