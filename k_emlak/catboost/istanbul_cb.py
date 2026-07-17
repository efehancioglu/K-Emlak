from catboost import CatBoostRegressor, Pool
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_percentage_error, mean_absolute_error
import numpy as np
import pandas as pd

data = pd.read_csv("k_emlak/hepsiemlak_istanbul.csv")


def _sayiya(seri, doldur=0):
    temiz = (seri.astype(str)
                 .str.replace(r"[^\d]", "", regex=True)
                 .replace("", np.nan))
    return pd.to_numeric(temiz, errors="coerce").fillna(doldur).astype(int)


data["fiyat"] = _sayiya(data["fiyat"])
data["brut_m2"] = _sayiya(data["brut_m2"])
data["net_m2"] = _sayiya(data["net_m2"])
data["banyo_sayisi"] = _sayiya(data["banyo_sayisi"], doldur=1)
data["kat_sayisi"] = _sayiya(data["kat_sayisi"], doldur=1)
data["bina_yasi"] = _sayiya(data["bina_yasi"])
data["aidat"] = _sayiya(data["aidat"])
data["kat_no"] = _sayiya(data["bulundugu_kat"])

data = data[data["fiyat"] > 0].reset_index(drop=True)

cat_features = ["mahalle", "ilce", "isinma", "oda_sayisi", "cephe",
                "esya_durumu", "bulundugu_kat"]
feature_cols = cat_features + ["brut_m2", "net_m2", "banyo_sayisi",
                               "kat_sayisi", "bina_yasi", "aidat", "kat_no"]

for col in cat_features:
    data[col] = data[col].fillna("Bilinmiyor").astype(str)

x = data[feature_cols]
y = np.log1p(data["fiyat"])

x_train, x_test, y_train, y_test = train_test_split(
    x, y, test_size=0.2, random_state=42
)

train_pool = Pool(x_train, y_train, cat_features=cat_features)
val_pool = Pool(x_test, y_test, cat_features=cat_features)

model = CatBoostRegressor(
    iterations=1000,
    learning_rate=0.05,
    depth=6,
    loss_function="RMSE",
    eval_metric="RMSE",
    early_stopping_rounds=50,
    random_seed=42,
    verbose=100,
)

model.fit(train_pool, eval_set=val_pool)

preds = np.expm1(model.predict(x_test))
actual = np.expm1(y_test)

print(f"\nIlan sayisi: {len(data)}")
print("MAPE:", round(mean_absolute_percentage_error(actual, preds), 4))
print("MAE (TL):", f"{mean_absolute_error(actual, preds):,.0f}")

print("\nOzellik onemi:")
for ad, deger in sorted(zip(feature_cols, model.get_feature_importance()),
                        key=lambda t: t[1], reverse=True):
    print(f"  {deger:6.2f}  {ad}")
