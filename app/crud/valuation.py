from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.valuation import Valuation
from app.schemas.valuation import ValuationRequest, ValuationResponse


def create_valuation(
    db: Session,
    istek: ValuationRequest,
    sonuc: ValuationResponse,
) -> Valuation:
    """Yapilan bir degerlemeyi (girdi + tahmin sonucu) kayit altina alir."""
    kayit = Valuation(
        ilce=istek.ilce,
        mahalle=istek.mahalle,
        brut_m2=istek.brut_m2,
        net_m2=istek.net_m2,
        oda_sayisi=istek.oda_sayisi,
        banyo_sayisi=istek.banyo_sayisi,
        bina_yasi=istek.bina_yasi,
        bulundugu_kat=istek.bulundugu_kat,
        kat_sayisi=istek.kat_sayisi,
        isinma=istek.isinma,
        cephe=istek.cephe,
        esya_durumu=istek.esya_durumu,
        aidat=istek.aidat,
        tahmini_fiyat=sonuc.tahmini_fiyat,
        birim_m2_fiyat=sonuc.birim_m2_fiyat,
        fiyat_alt=sonuc.fiyat_araligi.alt,
        fiyat_ust=sonuc.fiyat_araligi.ust,
        beklenen_fiyat=istek.beklenen_fiyat,
        yorum_durum=sonuc.yorum.durum if sonuc.yorum else None,
    )
    db.add(kayit)
    db.commit()
    db.refresh(kayit)
    return kayit


def get_valuations(
    db: Session,
    ilce: str | None = None,
    skip: int = 0,
    limit: int = 50,
) -> list[Valuation]:
    """Gecmis degerlemeleri en yeniden eskiye dogru dondurur."""
    query = select(Valuation)
    if ilce:
        query = query.where(Valuation.ilce == ilce)
    query = query.order_by(Valuation.olusturulma_tarihi.desc())
    query = query.offset(skip).limit(limit)
    return list(db.execute(query).scalars().all())


def get_valuation(db: Session, valuation_id: int) -> Valuation | None:
    return db.get(Valuation, valuation_id)
