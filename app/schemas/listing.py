from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import KullanimDurumu, IsitmaTipi


class ListingBase(BaseModel):
    ilan_no: str
    il: str
    ilce: str
    mahalle: str | None = None
    fiyat: int
    brut_metrekare: int
    net_metrekare: int
    oda_sayisi: str
    banyo_sayisi: int
    kat_sayisi: int
    bulundugu_kat: str | None = None
    bina_yasi: int
    isitma_tipi: IsitmaTipi
    esyali: bool
    kullanim_durumu: KullanimDurumu
    cephe_kuzey: bool
    cephe_guney: bool
    cephe_dogu: bool
    cephe_bati: bool
    aidat: int | None = None
    kaynak_url: str


class ListingCreate(ListingBase):
    pass


class ListingRead(ListingBase):
    id: int
    olusturulma_tarihi: datetime

    model_config = ConfigDict(from_attributes=True)