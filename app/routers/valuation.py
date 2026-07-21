from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.crud import valuation as valuation_crud
from app.schemas.valuation import (
    ValuationRead,
    ValuationRequest,
    ValuationResponse,
)
from app.services import valuation_service

router = APIRouter(prefix="/valuation", tags=["valuation"])


@router.post("/predict", response_model=ValuationResponse)
def degerle(istek: ValuationRequest, db: Session = Depends(get_db)):
    """Girilen ev ozelliklerinden tahmini piyasa degerini dondurur ve
    yapilan degerlemeyi gecmise kaydeder.

    Istekte beklenen_fiyat verilirse ayrica pahali/normal/uygun yorumu da
    doner.
    """
    sonuc = valuation_service.degerle(istek)
    valuation_crud.create_valuation(db, istek, sonuc)
    return sonuc


@router.get("/history", response_model=list[ValuationRead])
def gecmis(
    ilce: str | None = None,
    skip: int = 0,
    limit: int = Query(default=50, le=200),
    db: Session = Depends(get_db),
):
    """Gecmiste yapilan degerlemeleri en yeniden eskiye listeler."""
    return valuation_crud.get_valuations(
        db=db, ilce=ilce, skip=skip, limit=limit
    )


@router.get("/history/{valuation_id}", response_model=ValuationRead)
def gecmis_detay(valuation_id: int, db: Session = Depends(get_db)):
    kayit = valuation_crud.get_valuation(db, valuation_id)
    if kayit is None:
        raise HTTPException(status_code=404, detail="degerleme bulunamadi")
    return kayit


@router.get("/options")
def secenekler():
    """Degerleme formundaki dropdown'lar icin gecerli kategorik degerler."""
    return valuation_service.secenekleri_getir()
