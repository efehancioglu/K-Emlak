from os import replace
import random

from catboost import CatBoostRegressor, Pool
from sklearn.model_selection import train_test_split
import numpy as np
import pandas as pd

data = pd.read_csv("k_emlak/hepsiemlak_ilanlar_camoufox.csv")

# Fiyat düzeltme
data["fiyat"] = data["fiyat"].fillna("0").astype(str).str.replace(" TL", "", regex=False).str.replace(".", "", regex=False).astype(int)

# Metrekare sütunları (Olası boş değerlere karşı fillna eklendi)
data["brut_m2"] = data["brut_m2"].fillna(0).astype(int)
data["net_m2"] = data["net_m2"].fillna(0).astype(int)

# Banyo ve Kat Sayısı (Zaten düzeltmiştiniz, aynen kalabilir)
data["binyo_sayisi"] = data["banyo_sayisi"].fillna(0).astype(int)
data["kat_sayisi"] = data["kat_sayisi"].fillna("1").astype(str).str.replace(" Katlı", "", regex=False).astype(int)

# Bina Yaşı
data["bina_yasi"] = data["bina_yasi"].fillna("0").astype(str).str.replace("Sıfır Bina", "0", regex=False).str.replace(" Yaşında", "", regex=False).astype(int)

data["aidat"] = data["aidat"].astype(str).str.replace(" TL", "", regex=False).str.replace(".", "", regex=False).replace("nan", "0").fillna(0).astype(int)


cat_features = ["mahalle", "ilce", "il", "isinma", "oda_sayisi", "cephe", "esya_durumu", "bulundugu_kat"]
feature_cols = cat_features + ["brut_m2", "net_m2", "banyo_sayisi", "kat_sayisi", "bina_yasi", "aidat"]

for col in cat_features:
    data[col] = data[col].fillna("Bilinmiyor").astype(str)

x = data[feature_cols]
y = np.log1p(data["fiyat"])

x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=42)

train_pool = Pool(x_train, y_train, cat_features=cat_features)
val_pool = Pool(x_test, y_test, cat_features=cat_features)

model = CatBoostRegressor(
        iterations=1000,
        learning_rate=0.05,
        depth=6,
        loss_function="RMSE",
        eval_metric="MAPE",
        early_stopping_rounds=50,
        verbose=100
    )

model.fit(train_pool, eval_set=val_pool)

from sklearn.metrics import mean_absolute_percentage_error, mean_absolute_error

model_prediction = model.predict(x_test)

preds = np.expm1(model_prediction)
actual = np.expm1(y_test)

print(f"Model prediction: {np.expm1(model_prediction)}")
print(f"Actual: {np.expm1(y_test)}")
print("MAPE:", mean_absolute_percentage_error(actual, preds))
print("MAE (TL):", mean_absolute_error(actual, preds))