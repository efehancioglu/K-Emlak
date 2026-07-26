from datetime import datetime

from sqlalchemy import String, Integer, BigInteger, Float, Boolean, DateTime, func
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.enums import KullanimDurumu, IsitmaTipi


class Listing(Base):
    __tablename__ = "listings"

    id: Mapped[int] = mapped_column(primary_key=True)

    ilan_no: Mapped[str] = mapped_column(String(50))

    il: Mapped[str] = mapped_column(String(50), index=True)
    ilce: Mapped[str] = mapped_column(String(50), index=True)
    mahalle: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # BigInteger: Istanbul'da fiyat 2,1 milyar TL'yi (int4 siniri) asabiliyor.
    fiyat: Mapped[int] = mapped_column(BigInteger, index=True)
    brut_metrekare: Mapped[int] = mapped_column(Integer)
    net_metrekare: Mapped[int] = mapped_column(Integer)
    oda_sayisi: Mapped[str] = mapped_column(String(10))
    banyo_sayisi: Mapped[float] = mapped_column(Float)
    kat_sayisi: Mapped[int] = mapped_column(Integer)
    bulundugu_kat: Mapped[str | None] = mapped_column(String(20), nullable=True)
    bina_yasi: Mapped[int] = mapped_column(Integer)

    isitma_tipi: Mapped[IsitmaTipi] = mapped_column(SqlEnum(IsitmaTipi, name="isitma_tipi_enum"))
    esyali: Mapped[bool] = mapped_column(Boolean, default=False)
    kullanim_durumu: Mapped[KullanimDurumu] = mapped_column(SqlEnum(KullanimDurumu, name="kullanim_durumu_enum"))

    cephe_kuzey: Mapped[bool] = mapped_column(Boolean, default=False)
    cephe_guney: Mapped[bool] = mapped_column(Boolean, default=False)
    cephe_dogu: Mapped[bool] = mapped_column(Boolean, default=False)
    cephe_bati: Mapped[bool] = mapped_column(Boolean, default=False)

    aidat: Mapped[int | None] = mapped_column(Integer, nullable=True)

    kaynak_url: Mapped[str] = mapped_column(String(500), unique=True)

    olusturulma_tarihi: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )