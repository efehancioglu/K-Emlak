from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.services.scraper_service import scraping_ve_aktarim_calistir

scheduler = BackgroundScheduler()

def scheduler_baslat() -> None:
    scheduler.add_job(
        scraping_ve_aktarim_calistir,
        
        #gercekte bu caliscak 
        trigger=CronTrigger(hour=3, minute=0),

        #test icin
        #trigger=CronTrigger(hour=12, minute=1),

        id="gecelik_scrapping",
        replace_existing=True,
    )
    scheduler.start()

def scheduler_durdur() -> None:
    scheduler.shutdown()