"""Degerleme servisi.

Arkadasin hazirladigi CatBoost tahmin algoritmasini
(k_emlak.catboost.tahmin_egit) API katmanina baglar. Ham tahminin uzerine
bir guven araligi ve (kullanici bir beklenen fiyat verdiyse) pahali/normal/
uygun yorumunu ekler.
"""

from k_emlak.catboost.tahmin_egit import secenekler, tahmin_et

from app.models.listing import Listing
from app.schemas.valuation import (
    FiyatAraligi,
    FiyatYorumu,
    IlanDegerlendirme,
    ValuationRequest,
    ValuationResponse,
)

# Listing'in 4 ayri cephe boolean'ini, modelin bekledigi virgulle birlesik
# yon dizisine ("Kuzey, Guney, ...") cevirmek icin sira.
_CEPHE_YONLERI = [
    ("cephe_kuzey", "Kuzey"),
    ("cephe_guney", "Güney"),
    ("cephe_dogu", "Doğu"),
    ("cephe_bati", "Batı"),
]

# Modelin ortalama sapmasini temsil eden hata payi. Tahmini bir alt-ust
# araligi ("su fiyatla su fiyat arasinda") uretmek ve kullaniciya tahminin
# ne kadar isabetli olabilecegini gostermek icin kullanilir. Model yeniden
# egitilip gercek MAPE olctuldukce buradan guncellenebilir.
TAHMIN_HATA_PAYI = 0.12

# Beklenen fiyatin tahminden ne kadar sapinca "pahali"/"uygun" sayilacagi.
YORUM_ESIGI = 0.10


def _fiyat_yorumla(tahmin: int, beklenen: int) -> FiyatYorumu:
    fark = (beklenen - tahmin) / tahmin
    fark_yuzdesi = round(fark * 100, 1)

    if fark > YORUM_ESIGI:
        return FiyatYorumu(
            durum="pahali",
            mesaj="Bu fiyat, benzer evlerin piyasa degerinin uzerinde "
                  "gorunuyor.",
            fark_yuzdesi=fark_yuzdesi,
        )
    if fark < -YORUM_ESIGI:
        return FiyatYorumu(
            durum="uygun",
            mesaj="Bu fiyat, benzer evlerin piyasa degerinin altinda; "
                  "uygun gorunuyor.",
            fark_yuzdesi=fark_yuzdesi,
        )
    return FiyatYorumu(
        durum="normal",
        mesaj="Bu fiyat, benzer evlerin piyasa degeriyle uyumlu.",
        fark_yuzdesi=fark_yuzdesi,
    )


def degerle(istek: ValuationRequest) -> ValuationResponse:
    """Ev ozelliklerinden tahmini piyasa degerini ve yorumu uretir."""
    tahmin = tahmin_et(
        ilce=istek.ilce,
        mahalle=istek.mahalle,
        brut_m2=istek.brut_m2,
        net_m2=istek.net_m2,
        oda_sayisi=istek.oda_sayisi,
        banyo_sayisi=istek.banyo_sayisi,
        bina_yasi=istek.bina_yasi,
        bulundugu_kat=istek.bulundugu_kat,
        kat_sayisi=istek.kat_sayisi,
        isinma=istek.isinma,
        cephe=istek.cephe,
        esya_durumu=istek.esya_durumu,
        aidat=istek.aidat,
    )

    araligi = FiyatAraligi(
        alt=int(tahmin * (1 - TAHMIN_HATA_PAYI)),
        ust=int(tahmin * (1 + TAHMIN_HATA_PAYI)),
    )

    birim_m2 = int(tahmin / istek.brut_m2) if istek.brut_m2 else 0

    yorum = None
    if istek.beklenen_fiyat:
        yorum = _fiyat_yorumla(tahmin, istek.beklenen_fiyat)

    return ValuationResponse(
        tahmini_fiyat=tahmin,
        fiyat_araligi=araligi,
        birim_m2_fiyat=birim_m2,
        tahmin_hata_payi=TAHMIN_HATA_PAYI,
        yorum=yorum,
    )


def ilani_degerlendir(ilan: Listing) -> IlanDegerlendirme:
    """Bir ilanin ozelliklerini modele verip tahmini piyasa degerini uretir
    ve ilandaki fiyati bununla karsilastirir (piyasaya gore pahali mi?)."""
    cephe = ", ".join(
        ad for alan, ad in _CEPHE_YONLERI if getattr(ilan, alan)
    )
    esya_durumu = "Eşyalı" if ilan.esyali else "Eşyalı Değil"

    tahmin = tahmin_et(
        ilce=ilan.ilce,
        mahalle=ilan.mahalle,
        brut_m2=ilan.brut_metrekare,
        net_m2=ilan.net_metrekare,
        oda_sayisi=ilan.oda_sayisi,
        banyo_sayisi=int(ilan.banyo_sayisi),
        bina_yasi=ilan.bina_yasi,
        bulundugu_kat=ilan.bulundugu_kat,
        kat_sayisi=ilan.kat_sayisi,
        isinma=ilan.isitma_tipi.value,
        cephe=cephe or None,
        esya_durumu=esya_durumu,
        aidat=ilan.aidat or 0,
    )

    araligi = FiyatAraligi(
        alt=int(tahmin * (1 - TAHMIN_HATA_PAYI)),
        ust=int(tahmin * (1 + TAHMIN_HATA_PAYI)),
    )
    yorum = _fiyat_yorumla(tahmin, ilan.fiyat)

    return IlanDegerlendirme(
        tahmini_fiyat=tahmin,
        fiyat_araligi=araligi,
        durum=yorum.durum,
        mesaj=yorum.mesaj,
        fark_yuzdesi=yorum.fark_yuzdesi,
    )


def secenekleri_getir() -> dict:
    """Degerleme formundaki dropdown'lari doldurmak icin gecerli kategorik
    degerler (ilce, mahalle, isinma, oda_sayisi, cephe, esya_durumu ...)."""
    return secenekler()
