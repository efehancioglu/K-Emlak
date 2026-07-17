from fastapi import APIRouter, BackgroundTasks

from app.services.scraper_service import scraping_ve_aktarim_calistir

router = APIRouter(prefix="/scraper",tags=["scraper"])

@router.post("/run")
def scraper_calistir(background_tasks: BackgroundTasks):
    background_tasks.add_task(scraping_ve_aktarim_calistir)
    return {"message":"scraping basariyla arkaplanda baslatildi."}