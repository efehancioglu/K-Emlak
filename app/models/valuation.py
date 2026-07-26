from datetime import datetime

from sqlalchemy import String, Integer, BigInteger, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Valuation(Base):
    """Kullanicinin degerleme ekranindan yaptigi her tahmin kayit altina
    alinir; boylece gecmiste yapilan degerlemeler daha sonra
    goruntulenebilir (proje tanimi geregi)."""

    __tablename__ = "valuations"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Girdi olarak verilen ev ozellikleri (tahmin aninin anlik goruntusu).
    ilce: Mapped[str] = mapped_column(String(50), index=True)
    mahalle: Mapped[str | None] = mapped_column(String(100), nullable=True)
    brut_m2: Mapped[int] = mapped_column(Integer)
    net_m2: Mapped[int] = mapped_column(Integer, default=0)
    oda_sayisi: Mapped[str | None] = mapped_column(String(20), nullable=True)
    banyo_sayisi: Mapped[int] = mapped_column(Integer, default=1)
    bina_yasi: Mapped[int] = mapped_column(Integer, default=0)
    bulundugu_kat: Mapped[str | None] = mapped_column(String(20), nullable=True)
    kat_sayisi: Mapped[int] = mapped_column(Integer, default=1)
    isinma: Mapped[str | None] = mapped_column(String(50), nullable=True)
    cephe: Mapped[str | None] = mapped_column(String(50), nullable=True)
    esya_durumu: Mapped[str | None] = mapped_column(String(50), nullable=True)
    aidat: Mapped[int] = mapped_column(Integer, default=0)

    # Tahmin sonucu. BigInteger: pahali konutlarda tutarlar 2,1 milyar TL'yi
    # (int4 siniri) asabilir.
    tahmini_fiyat: Mapped[int] = mapped_column(BigInteger)
    birim_m2_fiyat: Mapped[int] = mapped_column(BigInteger)
    fiyat_alt: Mapped[int] = mapped_column(BigInteger)
    fiyat_ust: Mapped[int] = mapped_column(BigInteger)

    # Kullanici bir beklenen fiyat girdiyse: fiyat + yorum ("uygun"/"normal"/
    # "pahali"). Girmediyse null kalir.
    beklenen_fiyat: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    yorum_durum: Mapped[str | None] = mapped_column(String(20), nullable=True)

    olusturulma_tarihi: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
