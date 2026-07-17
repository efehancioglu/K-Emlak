import subprocess

from  app.core.config import settings
from scripts.ingest_listings import calistir as verileri_ice_aktar

def scraping_ve_aktarim_calistir() -> dict:
    sonuc = {"scraper_basarili":False, "ingestion_calisti": False, "hata":None}

    try:
        subprocess.run(
            [settings.scraper_python_path, settings.scraper_script_path],
            cwd = settings.scraper_working_dir,
            check=True 
        )
        sonuc["scraper_basarili"] = True
    except subprocess.CalledProcessError as hata:
        sonuc["hata"] = f"Scraper calisirken hata: {hata}"
        print(sonuc["hata"])
        return sonuc
    
    try:
        verileri_ice_aktar()
        sonuc["ingestion_calisti"] = True
    except Exception as hata:
        sonuc["hata"] = f"Ingestion calisirken hata: {hata}"
    return sonuc