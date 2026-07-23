from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.crud import stats as stats_crud
from app.schemas.stats import FiyatTrendi, IlceIstatistik, OzetIstatistik

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/summary", response_model=OzetIstatistik)
def ozet(db: Session = Depends(get_db)):
    """Yonetim ekrani ozet kartlari: toplam ilan/ilce, ortalama-min-max fiyat,
    ortalama m2 fiyati."""
    return stats_crud.ozet(db)


@router.get("/by-ilce", response_model=list[IlceIstatistik])
def ilce_bazinda(db: Session = Depends(get_db)):
    """Ilce bazinda ortalama m2 fiyati ve ilan sayisi (grafik verisi)."""
    return stats_crud.ilce_bazinda(db)


@router.get("/price-trend", response_model=list[FiyatTrendi])
def fiyat_trendi(db: Session = Depends(get_db)):
    """Zaman icindeki (aylik) ortalama fiyat/m2 fiyat degisimi."""
    return stats_crud.fiyat_trendi(db)
