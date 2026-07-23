"""Modelin gercek tahmin hatasini (MAPE) olcer.

Arkadasin egitim modulundeki ayni veri hazirligi ve ayni hiperparametrelerle,
verinin %80'inde egitip tutulan %20'lik test setinde tahmin yapar ve ortalama
mutlak yuzde hatayi (MAPE) hesaplar. Cikan sayi, degerleme ekranindaki
"±%X guven payi" (app/services/valuation_service.py -> TAHMIN_HATA_PAYI) icin
gercek, olculmus bir degerdir.

Kullanim (kok dizinden):  ./venv/Scripts/python.exe -m scripts.mape_olc
Veri her guncellendiginde tekrar calistirilip sabit guncellenebilir.
"""

import numpy as np
from catboost import CatBoostRegressor, Pool
from sklearn.model_selection import train_test_split

from k_emlak.catboost.tahmin_egit import KATEGORIK, OZELLIKLER, _veriyi_hazirla


def olc(test_orani: float = 0.2, seed: int = 42) -> dict:
    data = _veriyi_hazirla()
    x = data[OZELLIKLER]
    y = np.log1p(data["fiyat"])          # model log-fiyat ogreniyor
    gercek_fiyat = data["fiyat"].to_numpy()

    x_tr, x_te, y_tr, y_te, _, fiyat_te = train_test_split(
        x, y, gercek_fiyat, test_size=test_orani, random_state=seed
    )

    model = CatBoostRegressor(
        iterations=1000,
        learning_rate=0.05,
        depth=6,
        loss_function="RMSE",
        random_seed=seed,
        verbose=0,
    )
    model.fit(Pool(x_tr, y_tr, cat_features=KATEGORIK))

    tahmin = np.expm1(model.predict(x_te))   # TL uzayina geri don
    ape = np.abs(tahmin - fiyat_te) / fiyat_te   # her ilan icin mutlak yuzde hata

    return {
        "test_adet": int(len(fiyat_te)),
        "mape": float(np.mean(ape)),           # ortalama -> ± bandi icin
        "medyan_ape": float(np.median(ape)),   # daha dayanikli referans
    }


if __name__ == "__main__":
    s = olc()
    print(f"Test ornek sayisi : {s['test_adet']}")
    print(f"MAPE (ortalama)   : {s['mape'] * 100:.1f}%")
    print(f"Medyan APE        : {s['medyan_ape'] * 100:.1f}%")
    print()
    print(f">> TAHMIN_HATA_PAYI = {s['mape']:.2f}")
