"""
    from k_emlak.catboost.tahmin_egit import tahmin_et, egit, secenekler

    fiyat = tahmin_et(
        ilce="Kadikoy", mahalle="Suadiye", brut_m2=120, net_m2=100,
        oda_sayisi="3 + 1", banyo_sayisi=2, bina_yasi=10,
        bulundugu_kat="3. Kat", kat_sayisi=5, isinma="Kombi",
        cephe="Guney", esya_durumu="Esyali Degil", aidat=1500,
    )
    # -> 8450000 (TL)
"""

import os
import threading

import numpy as np
import pandas as pd
from catboost import CatBoostRegressor, Pool

_BURASI = os.path.dirname(os.path.abspath(__file__))
_KOK = os.path.dirname(os.path.dirname(_BURASI))

VERI_CSV = os.path.join(_KOK, "k_emlak", "hepsiemlak_istanbul.csv")
MODEL_DOSYA = os.path.join(_KOK, "k_emlak", "istanbul_model.cbm")

KATEGORIK = ["mahalle", "ilce", "isinma", "oda_sayisi", "cephe",
             "esya_durumu", "bulundugu_kat"]
SAYISAL = ["brut_m2", "net_m2", "banyo_sayisi", "kat_sayisi", "bina_yasi",
           "aidat", "kat_no"]
OZELLIKLER = KATEGORIK + SAYISAL

_BILINMIYOR = "Bilinmiyor"

_model = None
_kilit = threading.Lock()


def _sayiya(seri, doldur=0):
    temiz = (seri.astype(str)
                 .str.replace(r"[^\d]", "", regex=True)
                 .replace("", np.nan))
    return pd.to_numeric(temiz, errors="coerce").fillna(doldur).astype(int)


def _tek_sayiya(deger, doldur=0):
    if deger is None:
        return doldur
    rakamlar = "".join(ch for ch in str(deger) if ch.isdigit())
    return int(rakamlar) if rakamlar else doldur


def _veriyi_hazirla():
    data = pd.read_csv(VERI_CSV)

    data["fiyat"] = _sayiya(data["fiyat"])
    data["brut_m2"] = _sayiya(data["brut_m2"])
    data["net_m2"] = _sayiya(data["net_m2"])
    data["banyo_sayisi"] = _sayiya(data["banyo_sayisi"], doldur=1)
    data["kat_sayisi"] = _sayiya(data["kat_sayisi"], doldur=1)
    data["bina_yasi"] = _sayiya(data["bina_yasi"])
    data["aidat"] = _sayiya(data["aidat"])
    data["kat_no"] = _sayiya(data["bulundugu_kat"])

    data = data[data["fiyat"] > 0].reset_index(drop=True)

    for col in KATEGORIK:
        data[col] = data[col].fillna(_BILINMIYOR).astype(str)

    return data


def egit(kaydet=True):
    # Modeli sifirdan egitir, diske kaydeder ve dondurur. Yeni veri cekildikten sonra cagirilir.
    
    global _model

    data = _veriyi_hazirla()
    x = data[OZELLIKLER]
    y = np.log1p(data["fiyat"])

    model = CatBoostRegressor(
        iterations=1000,
        learning_rate=0.05,
        depth=6,
        loss_function="RMSE",
        random_seed=42,
        verbose=0,
    )
    model.fit(Pool(x, y, cat_features=KATEGORIK))

    if kaydet:
        model.save_model(MODEL_DOSYA)

    with _kilit:
        _model = model
    return model


def _modeli_al():
    global _model
    with _kilit:
        if _model is not None:
            return _model
    if os.path.exists(MODEL_DOSYA):
        model = CatBoostRegressor()
        model.load_model(MODEL_DOSYA)
        with _kilit:
            _model = model
        return model
    return egit()


def tahmin_et(ilce, mahalle=None, brut_m2=0, net_m2=0, oda_sayisi=None,
              banyo_sayisi=1, bina_yasi=0, bulundugu_kat=None, kat_sayisi=1,
              isinma=None, cephe=None, esya_durumu=None, aidat=0):
    """Verilen ozelliklerle konut fiyatini TL olarak tahmin eder.

    Bos birakilan kategorik alanlar 'Bilinmiyor' sayilir; model bu degeri
    egitimde de gordugu icin tahmin yine calisir.

    Donen deger: int (TL)
    """
    satir = {
        "mahalle": str(mahalle) if mahalle else _BILINMIYOR,
        "ilce": str(ilce) if ilce else _BILINMIYOR,
        "isinma": str(isinma) if isinma else _BILINMIYOR,
        "oda_sayisi": str(oda_sayisi) if oda_sayisi else _BILINMIYOR,
        "cephe": str(cephe) if cephe else _BILINMIYOR,
        "esya_durumu": str(esya_durumu) if esya_durumu else _BILINMIYOR,
        "bulundugu_kat": str(bulundugu_kat) if bulundugu_kat else _BILINMIYOR,
        "brut_m2": _tek_sayiya(brut_m2),
        "net_m2": _tek_sayiya(net_m2),
        "banyo_sayisi": _tek_sayiya(banyo_sayisi, doldur=1),
        "kat_sayisi": _tek_sayiya(kat_sayisi, doldur=1),
        "bina_yasi": _tek_sayiya(bina_yasi),
        "aidat": _tek_sayiya(aidat),
        "kat_no": _tek_sayiya(bulundugu_kat),
    }

    x = pd.DataFrame([satir])[OZELLIKLER]
    log_fiyat = _modeli_al().predict(x)[0]
    return int(np.expm1(log_fiyat))


def secenekler():
    """Arayuzdeki dropdown'lari doldurmak icin gecerli kategorik degerler.

    Donen deger: {"ilce": [...], "mahalle": [...], "isinma": [...], ...,
                  "mahalle_by_ilce": {"Kadikoy": [...], ...}}
    """
    data = _veriyi_hazirla()

    cikti = {}
    for col in KATEGORIK:
        cikti[col] = sorted(v for v in data[col].unique() if v != _BILINMIYOR)

    cikti["mahalle_by_ilce"] = {
        ilce: sorted(grup["mahalle"].unique())
        for ilce, grup in data.groupby("ilce")
    }
    return cikti
