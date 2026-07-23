"""Degerleme servisi.

Arkadasin hazirladigi CatBoost tahmin algoritmasini
(k_emlak.catboost.tahmin_egit) API katmanina baglar. Ham tahminin uzerine
bir guven araligi ve (kullanici bir beklenen fiyat verdiyse) pahali/normal/
uygun yorumunu ekler.
"""

import numpy as np
import pandas as pd

from k_emlak.catboost.tahmin_egit import (
    OZELLIKLER,
    _BILINMIYOR,
    _modeli_al,
    _tek_sayiya,
    secenekler,
    tahmin_et,
)

from app.models.listing import Listing
from app.schemas.valuation import (
    FiyatAraligi,
    FiyatYorumu,
    IlanDegerlendirme,
    PiyasaOzet,
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

# Modelin tipik sapmasini temsil eden hata payi; tahmini bir alt-ust araligi
# uretmek ve kullaniciya isabet hissi vermek icin kullanilir.
# scripts/mape_olc.py ile tutulan test setinde OLCULMUS deger: medyan APE
# ~%16 (ilanlarin yarisi bu bandin icinde). Not: ortalama MAPE ~%51 cikiyor
# ama birkac uc/hatali ilan onu sisirdigi icin band olarak medyan kullaniyoruz.
# Veri her guncellenip model yeniden egitildiginde mape_olc tekrar calistirilip
# bu deger guncellenmeli.
TAHMIN_HATA_PAYI = 0.16

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


def _ilan_model_satiri(ilan: Listing) -> dict:
    """Bir Listing'i modelin bekledigi ozellik satirina cevirir. tahmin_et'in
    tek satir icin yaptigi eslemeyi birebir yansitir (toplu tahmin icin)."""
    cephe = ", ".join(ad for alan, ad in _CEPHE_YONLERI if getattr(ilan, alan))
    esya = "Eşyalı" if ilan.esyali else "Eşyalı Değil"
    return {
        "mahalle": str(ilan.mahalle) if ilan.mahalle else _BILINMIYOR,
        "ilce": str(ilan.ilce) if ilan.ilce else _BILINMIYOR,
        "isinma": str(ilan.isitma_tipi.value) if ilan.isitma_tipi.value else _BILINMIYOR,
        "oda_sayisi": str(ilan.oda_sayisi) if ilan.oda_sayisi else _BILINMIYOR,
        "cephe": str(cephe) if cephe else _BILINMIYOR,
        "esya_durumu": str(esya) if esya else _BILINMIYOR,
        "bulundugu_kat": str(ilan.bulundugu_kat) if ilan.bulundugu_kat else _BILINMIYOR,
        "brut_m2": _tek_sayiya(ilan.brut_metrekare),
        "net_m2": _tek_sayiya(ilan.net_metrekare),
        "banyo_sayisi": _tek_sayiya(int(ilan.banyo_sayisi), doldur=1),
        "kat_sayisi": _tek_sayiya(ilan.kat_sayisi, doldur=1),
        "bina_yasi": _tek_sayiya(ilan.bina_yasi),
        "aidat": _tek_sayiya(ilan.aidat or 0),
        "kat_no": _tek_sayiya(ilan.bulundugu_kat),
    }


def _tek_ozet(ilan: Listing) -> PiyasaOzet | None:
    try:
        d = ilani_degerlendir(ilan)
        return PiyasaOzet(
            durum=d.durum, tahmini_fiyat=d.tahmini_fiyat, fark_yuzdesi=d.fark_yuzdesi
        )
    except Exception:
        return None


def ilanlari_piyasa_ozeti(ilanlar: list[Listing]) -> list[PiyasaOzet | None]:
    """Ilanlarin her biri icin liste kartinda gosterilecek hafif piyasa
    onizlemesi (durum + tahmini fiyat + fark). Ilanlarla ayni sirada doner;
    bir ilan degerlendirilemezse yerine None konur.

    Performans: tum ilanlar TEK bir model.predict cagrisinda toplu puanlanir
    (piyasa filtresi binlerce ilani puanlayabildigi icin onemli). Toplu yol
    beklenmedik bir sebeple patlarsa, guvenli sekilde tek tek puanlamaya duser.
    """
    if not ilanlar:
        return []

    try:
        satirlar = [_ilan_model_satiri(ilan) for ilan in ilanlar]
        x = pd.DataFrame(satirlar)[OZELLIKLER]
        tahminler = np.expm1(_modeli_al().predict(x))
    except Exception:
        return [_tek_ozet(ilan) for ilan in ilanlar]

    ozetler: list[PiyasaOzet | None] = []
    for ilan, ham in zip(ilanlar, tahminler):
        try:
            tahmin = int(ham)
            yorum = _fiyat_yorumla(tahmin, ilan.fiyat)
            ozetler.append(
                PiyasaOzet(
                    durum=yorum.durum,
                    tahmini_fiyat=tahmin,
                    fark_yuzdesi=yorum.fark_yuzdesi,
                )
            )
        except Exception:
            ozetler.append(None)
    return ozetler


def secenekleri_getir() -> dict:
    """Degerleme formundaki dropdown'lari doldurmak icin gecerli kategorik
    degerler (ilce, mahalle, isinma, oda_sayisi, cephe, esya_durumu ...)."""
    return secenekler()
