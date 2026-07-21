from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ValuationRequest(BaseModel):
    """Degerleme ekranindan gelen ev ozellikleri.

    Alanlar tahmin modelinin (k_emlak.catboost.tahmin_egit.tahmin_et)
    bekledigi girdilerle birebir eslesir. Kategorik alanlarin gecerli
    degerleri /valuation/options ucundan alinir. Bos birakilan kategorik
    alanlar model tarafinda 'Bilinmiyor' sayilir.
    """

    ilce: str
    mahalle: str | None = None
    brut_m2: int = Field(gt=0)
    net_m2: int = Field(default=0, ge=0)
    oda_sayisi: str | None = None
    banyo_sayisi: int = Field(default=1, ge=0)
    bina_yasi: int = Field(default=0, ge=0)
    bulundugu_kat: str | None = None
    kat_sayisi: int = Field(default=1, ge=0)
    isinma: str | None = None
    cephe: str | None = None
    esya_durumu: str | None = None
    aidat: int = Field(default=0, ge=0)

    # Kullanicinin aklindaki/ilandaki fiyat. Verilirse sistem tahminle
    # karsilastirip pahali / normal / uygun yorumunu dondurur.
    beklenen_fiyat: int | None = Field(default=None, gt=0)


class FiyatAraligi(BaseModel):
    alt: int
    ust: int


class FiyatYorumu(BaseModel):
    durum: str          # "uygun" | "normal" | "pahali"
    mesaj: str
    fark_yuzdesi: float  # beklenen fiyatin tahmine gore yuzde farki (+ pahali)


class ValuationResponse(BaseModel):
    tahmini_fiyat: int
    fiyat_araligi: FiyatAraligi
    birim_m2_fiyat: int
    # Tahminin ne kadar isabetli olabilecegini gosteren guven payi (0-1 arasi
    # hata payinin tersi mantigiyla bilgilendirme amacli).
    tahmin_hata_payi: float
    yorum: FiyatYorumu | None = None


class IlanDegerlendirme(BaseModel):
    """Bir ilanin, ozelliklerine gore tahmin edilen piyasa degeriyle
    karsilastirilmasi: ilandaki fiyat piyasaya gore pahali/normal/uygun mi."""

    tahmini_fiyat: int
    fiyat_araligi: FiyatAraligi
    durum: str          # "uygun" | "normal" | "pahali"
    mesaj: str
    fark_yuzdesi: float  # ilan fiyatinin tahmine gore yuzde farki (+ pahali)


class PiyasaOzet(BaseModel):
    """Ilan liste kartindaki hafif piyasa onizlemesi: tiklamadan once ilanin
    piyasaya gore durumunu (uygun/normal/pahali) gostermek icin."""

    durum: str          # "uygun" | "normal" | "pahali"
    tahmini_fiyat: int
    fark_yuzdesi: float  # ilan fiyatinin tahmine gore yuzde farki (+ pahali)


class ValuationRead(BaseModel):
    """Kayit altina alinmis bir gecmis degerleme."""

    id: int
    ilce: str
    mahalle: str | None
    brut_m2: int
    oda_sayisi: str | None
    tahmini_fiyat: int
    birim_m2_fiyat: int
    fiyat_alt: int
    fiyat_ust: int
    beklenen_fiyat: int | None
    yorum_durum: str | None
    olusturulma_tarihi: datetime

    model_config = ConfigDict(from_attributes=True)
