from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.models.enums import KullanimDurumu,Cephe,IsitmaTipi

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
    bulundugu_kat: str
    bina_yasi: int
    isitma_tipi: IsitmaTipi
    esyali: bool
    kullanim_durumu: KullanimDurumu
    cephe_kuzey: Cephe
    aidat: int | None = None

class ListingCreate(ListingBase):
    pass

class ListingRead(ListingBase):
    id: int
    olusturulma_tarihi: datetime

    model_config = ConfigDict(from_attributes=True)