import csv
import re
from pathlib import Path

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.enums import Cephe, IsitmaTipi, KullanimDurumu
from app.models.listing import Listing

CSV_PATH = Path(__file__).resolve().parent.parent / "k_emlak" / "hepsiemlak_istanbul.csv"

# Proje ilk etapta yalnizca Istanbul ilanlariyla calisir. Kaynak veride
# (eski Turkiye geneli scrape'lerden) Istanbul disi satirlar bulunabilir;
# bunlar veritabanina alinmaz.
HEDEF_IL = "istanbul"


def il_istanbul_mu(il: str) -> bool:
    # "Istanbul", "istanbul", "ISTANBUL" -> True. Turkce buyuk I'nin
    # kucultulmesinde olusan birlesik nokta (U+0307) temizlenir.
    return il.strip().lower().replace("̇", "") == HEDEF_IL

CEPHE_ALANLARI = {
    Cephe.KUZEY: "cephe_kuzey",
    Cephe.GUNEY: "cephe_guney",
    Cephe.DOGU: "cephe_dogu",
    Cephe.BATI: "cephe_bati",
}


def sayiya_cevir(deger: str) -> int:
    # "9.250.000 TL" -> 9250000 ; "1 TL" -> 1
    rakamlar = re.sub(r"[^\d]", "", deger)
    if not rakamlar:
        raise ValueError(f"sayı bulunamadı: {deger!r}")
    return int(rakamlar)


def aidat_cevir(deger: str) -> int | None:
    temiz = deger.strip()
    if not temiz:
        return None
    return sayiya_cevir(temiz)


def int_veya_varsayilan(deger: str, varsayilan: int) -> int:
    temiz = deger.strip()
    if not temiz:
        return varsayilan
    return int(temiz)


def str_veya_varsayilan(deger: str, varsayilan: str) -> str:
    temiz = deger.strip()
    return temiz if temiz else varsayilan


def ilk_sayi(deger: str, varsayilan: int | None = None) -> int:
    # "24 Yaşında" -> 24 ; "4 Katlı" -> 4 ; "Sıfır Bina" -> 0
    temiz = deger.strip()
    if not temiz:
        if varsayilan is not None:
            return varsayilan
        raise ValueError(f"boş değer: {deger!r}")
    if "sıfır" in temiz.lower():
        return 0
    eslesme = re.search(r"\d+", temiz)
    if not eslesme:
        if varsayilan is not None:
            return varsayilan
        raise ValueError(f"sayı bulunamadı: {deger!r}")
    return int(eslesme.group())


def esyali_cevir(deger: str) -> bool:
    return deger.strip().lower() == "eşyalı"


def kullanim_cevir(deger: str) -> KullanimDurumu:
    temiz = deger.strip()
    if not temiz:
        return KullanimDurumu.BELIRTILMEMIS
    return KullanimDurumu(temiz)


def isitma_cevir(deger: str) -> IsitmaTipi:
    temiz = deger.strip()
    if not temiz:
        return IsitmaTipi.BELIRTILMEMIS
    return IsitmaTipi(temiz)


def cephe_bayraklarini_cikar(deger: str) -> dict:
    bayraklar = {alan: False for alan in CEPHE_ALANLARI.values()}
    for parca in [p.strip() for p in deger.split(",") if p.strip()]:
        for cephe_enum, alan_adi in CEPHE_ALANLARI.items():
            if parca == cephe_enum.value:
                bayraklar[alan_adi] = True
    return bayraklar


def satiri_temizle(satir: dict) -> dict | None:
    try:
        temiz = {
            "ilan_no": satir["ilan_no"].strip(),
            "il": satir["il"].strip(),
            "ilce": satir["ilce"].strip(),
            "mahalle": satir["mahalle"].strip() or None,
            "fiyat": sayiya_cevir(satir["fiyat"]),
            "brut_metrekare": int(satir["brut_m2"]),
            "net_metrekare": int(satir["net_m2"]),
            "oda_sayisi": satir["oda_sayisi"].strip(),
            "banyo_sayisi": int_veya_varsayilan(satir["banyo_sayisi"], 1),
            "kat_sayisi": ilk_sayi(satir["kat_sayisi"], varsayilan=1),
            "bulundugu_kat": str_veya_varsayilan(satir["bulundugu_kat"], "1. Kat"),
            "bina_yasi": ilk_sayi(satir["bina_yasi"]),
            "isitma_tipi": isitma_cevir(satir["isinma"]),
            "esyali": esyali_cevir(satir["esya_durumu"]),
            "kullanim_durumu": kullanim_cevir(satir["kullanim_durumu"]),
            "aidat": aidat_cevir(satir["aidat"]),
            "kaynak_url": satir["url"].strip(),
        }
        temiz.update(cephe_bayraklarini_cikar(satir["cephe"]))
        return temiz
    except (KeyError, ValueError) as hata:
        print(f"Satır atlandı ({hata}) — ilan_no: {satir.get('ilan_no', '?')}")
        return None


def calistir() -> dict:
    """CSV'deki ilanlari (yalnizca Istanbul, henuz kayitli olmayanlar) DB'ye
    aktarir. Ozet sayilari bir sozluk olarak dondurur (scraper yoneticisi
    ekranda 'kac ilan kaydedildi' gostersin diye)."""
    if not CSV_PATH.exists():
        print(f"CSV bulunamadı: {CSV_PATH}")
        return {"eklenen": 0, "zaten_var": 0, "atlanan": 0, "istanbul_disi": 0}

    db = SessionLocal()
    eklenen = zaten_var = atlanan = istanbul_disi = 0

    try:
        with open(CSV_PATH, newline="", encoding="utf-8") as dosya:
            for satir in csv.DictReader(dosya):
                temiz = satiri_temizle(satir)
                if temiz is None:
                    atlanan += 1
                    continue

                if not il_istanbul_mu(temiz["il"]):
                    istanbul_disi += 1
                    continue

                mevcut = db.execute(
                    select(Listing).where(Listing.kaynak_url == temiz["kaynak_url"])
                ).scalar_one_or_none()
                if mevcut:
                    zaten_var += 1
                    continue

                db.add(Listing(**temiz))
                eklenen += 1

            db.commit()
    finally:
        db.close()

    print(
        f"Eklenen: {eklenen}, zaten vardı: {zaten_var}, "
        f"atlanan (hatalı): {atlanan}, İstanbul dışı: {istanbul_disi}"
    )
    return {
        "eklenen": eklenen,
        "zaten_var": zaten_var,
        "atlanan": atlanan,
        "istanbul_disi": istanbul_disi,
    }


if __name__ == "__main__":
    calistir()