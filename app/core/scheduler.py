from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.services.scraper_service import scraping_ve_aktarim_calistir

scheduler = BackgroundScheduler()

def scheduler_baslat() -> None:
    scheduler.add_job(
        scraping_ve_aktarim_calistir,
        trigger=CronTrigger(hour=3, minute=0),
        id="gecelik_scrapping",
        replace_existing=True,
    )
    scheduler.start()

def scheduler_durdur() -> None:
    scheduler.shutdown()