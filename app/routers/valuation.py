from fastapi import APIRouter

from app.schemas.valuation import ValuationRequest, ValuationResponse
from app.services import valuation_service

router = APIRouter(prefix="/valuation", tags=["valuation"])


@router.post("/predict", response_model=ValuationResponse)
def degerle(istek: ValuationRequest):
    """Girilen ev ozelliklerinden tahmini piyasa degerini dondurur.

    Istekte beklenen_fiyat verilirse ayrica pahali/normal/uygun yorumu da
    doner.
    """
    return valuation_service.degerle(istek)


@router.get("/options")
def secenekler():
    """Degerleme formundaki dropdown'lar icin gecerli kategorik degerler."""
    return valuation_service.secenekleri_getir()
