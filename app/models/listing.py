from datetime import datetime

from sqlalchemy import String, Integer, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

class Listing(Base):
    __tablename__ = "listings"

    id: Mapped[int] = mapped_column(primary_key=True)

    ilan_id: Mapped[int] = mapped_column(Integer)
    il_adi: Mapped[str] = mapped_column(String)
    ilce_adi: Mapped[str] = mapped_column(String)
    fiyat: Mapped[int] = mapped_column(String)
    oda_sayisi: Mapped[int] = mapped_column(Integer)
    kat_sayisi: Mapped[int] = mapped_column(Integer)
    banyo_sayisi: Mapped[int] = mapped_column(Integer)
    brut_metrakare: Mapped[int] = mapped_column(Integer)
    net_metrekare: Mapped[int] = mapped_column(Integer)
    bina_yasi: Mapped[int] = mapped_column(Integer)

    esyali_mi: Mapped[bool] = mapped_column(Boolean, default= False)
    otoparkli_mi: Mapped[bool] = mapped_column(Boolean, default= False)
    asansorlu_mu: Mapped[bool] = mapped_column(Boolean, default= False)
    sitede_mi: Mapped[bool] = mapped_column(Boolean, default= False)

    kaynak_site: Mapped[str] = mapped_column(String)
    olusturulma_tarihi: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

