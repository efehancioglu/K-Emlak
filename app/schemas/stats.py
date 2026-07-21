from pydantic import BaseModel


class OzetIstatistik(BaseModel):
    """Yonetim ekraninin ust kismindaki ozet kartlar."""

    toplam_ilan: int
    toplam_ilce: int
    ortalama_fiyat: int
    ortalama_m2_fiyat: int
    en_dusuk_fiyat: int
    en_yuksek_fiyat: int


class IlceIstatistik(BaseModel):
    """Ilce bazinda ozet: grafik/tablo icin."""

    ilce: str
    ilan_sayisi: int
    ortalama_fiyat: int
    ortalama_m2_fiyat: int


class FiyatTrendi(BaseModel):
    """Zaman icindeki (aylik) fiyat degisimi grafigi icin tek nokta."""

    donem: str  # "YYYY-MM"
    ilan_sayisi: int
    ortalama_fiyat: int
    ortalama_m2_fiyat: int
