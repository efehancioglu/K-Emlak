from fastapi import APIRouter

from app.services.scraper_service import yonetici

router = APIRouter(prefix="/scraper", tags=["scraper"])


@router.post("/run")
def scraper_calistir():
    """Veri cekmeyi arka planda baslatir. Zaten calisiyorsa yeniden
    baslatmaz. Ilerleme /scraper/status'tan izlenir."""
    return yonetici.baslat()


@router.post("/stop")
def scraper_durdur():
    """Calisan veri cekmeyi durdurur; o ana kadar cekilen ilanlar
    veritabanina aktarilir."""
    return yonetici.durdur()


@router.get("/status")
def scraper_durum():
    """Anlik durum: cekme asamasi, bu kosuda bulunan yeni ilan sayisi ve
    (kayit bittiyse) veritabanina eklenen ilan ozeti."""
    return yonetici.durum_bilgisi()
