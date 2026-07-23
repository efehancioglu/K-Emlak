"""Scraper yoneticisi.

Veri cekmeyi (ayri bir Python surecinde calisan Camoufox scraper'i) baslatir,
canli olarak kac yeni ilan cekildigini izler ve kullanicinin istedigi anda
durdurulmasini saglar. Surec durunca (kendiliginden bitti ya da kullanici
durdurdu) o ana kadar CSV'ye yazilan ilanlar veritabanina aktarilir.

Tasarim: scraper bir subprocess olarak calisir ve her ilani CSV'ye ekleyerek
(append) yazar. Bu yuzden surec ortada kesilse bile o ana dek yazilan satirlar
CSV'de kalir; "durdur" bu sureci sonlandirip hemen ingest'i tetikler.
"""

import subprocess
import threading
import time

from k_emlak.catboost.tahmin_egit import egit

from app.core.config import settings
from scripts.ingest_listings import CSV_PATH
from scripts.ingest_listings import calistir as verileri_ice_aktar

# Durum makinesi:
#   bosta        -> hic calismadi / onceki kosu bitti-sifirlandi
#   cekiliyor    -> scraper subprocess'i calisiyor
#   kaydediliyor -> scraper durdu, veriler DB'ye yaziliyor
#   egitiliyor   -> veriler kaydedildi, model guncel veriyle yeniden egitiliyor
#   bitti        -> scraper kendiliginden bitti + kayit + egitim tamam
#   durduruldu   -> kullanici durdurdu + kayit + egitim tamam
#   hata         -> scraper baslatilamadi / kayit / egitim sirasinda hata


class _ScraperYoneticisi:
    def __init__(self):
        self._lock = threading.Lock()
        self._sifirla()

    def _sifirla(self):
        self.durum = "bosta"
        self.yeni_ilan = 0          # bu kosuda cekilen yeni ilan sayisi
        self._baslangic_satir = 0   # kosu basinda CSV'deki satir sayisi
        self.ingest_ozeti = None    # {eklenen, zaten_var, ...} kayit sonrasi
        self.hata = None
        self._proc = None
        self._thread = None
        self._durdur_istendi = False

    # --- yardimcilar ---
    def _csv_satir_say(self) -> int:
        # Veri satiri sayisi (baslik haric).
        try:
            with open(CSV_PATH, encoding="utf-8") as f:
                toplam = sum(1 for _ in f)
            return max(0, toplam - 1)
        except FileNotFoundError:
            return 0

    def _calisiyor_mu(self) -> bool:
        return self.durum in ("cekiliyor", "kaydediliyor", "egitiliyor")

    # --- dis API ---
    def baslat(self) -> dict:
        with self._lock:
            if self._calisiyor_mu():
                return {"baslatildi": False, "mesaj": "Veri çekme zaten çalışıyor."}
            self._sifirla()
            self._baslangic_satir = self._csv_satir_say()
            self.durum = "cekiliyor"
            self._thread = threading.Thread(target=self._calis, daemon=True)
            self._thread.start()
            return {"baslatildi": True}

    def durdur(self) -> dict:
        with self._lock:
            if self.durum != "cekiliyor":
                return {"durduruldu": False, "mesaj": "Çalışan bir veri çekme yok."}
            self._durdur_istendi = True
            return {"durduruldu": True, "mesaj": "Durduruluyor, veriler kaydedilecek…"}

    def durum_bilgisi(self) -> dict:
        # Cekiliyorken sayaci taze oku.
        if self._calisiyor_mu():
            self.yeni_ilan = max(0, self._csv_satir_say() - self._baslangic_satir)
        return {
            "durum": self.durum,
            "yeni_ilan": self.yeni_ilan,
            "ingest_ozeti": self.ingest_ozeti,
            "hata": self.hata,
        }

    # --- arka plan is akisi ---
    def _calis(self):
        try:
            self._proc = subprocess.Popen(
                [settings.scraper_python_path, settings.scraper_script_path],
                cwd=settings.scraper_working_dir,
            )
        except Exception as hata:  # noqa: BLE001
            self.durum = "hata"
            self.hata = f"Scraper başlatılamadı: {hata}"
            return

        # Surec bitene ya da durdurulana kadar bekle; bu arada sayac guncellenir.
        while self._proc.poll() is None:
            if self._durdur_istendi:
                self._sureci_sonlandir()
                break
            time.sleep(1.0)

        self.yeni_ilan = max(0, self._csv_satir_say() - self._baslangic_satir)

        # Scraper durdu -> o ana kadarki CSV verisini DB'ye aktar.
        self.durum = "kaydediliyor"
        try:
            self.ingest_ozeti = verileri_ice_aktar()
        except Exception as hata:  # noqa: BLE001
            self.durum = "hata"
            self.hata = f"Veritabanına kaydederken hata: {hata}"
            return

        # Yeni veri geldi -> model guncel veriyle yeniden egitilsin.
        self.durum = "egitiliyor"
        try:
            egit(kaydet=True)
        except Exception as hata:  # noqa: BLE001
            # Veriler DB'ye yazildi ama model tazelenemedi; veriyi kaybetme,
            # sadece uyar.
            self.durum = "hata"
            self.hata = f"Veriler kaydedildi ama model eğitilemedi: {hata}"
            return

        self.durum = "durduruldu" if self._durdur_istendi else "bitti"

    def _sureci_sonlandir(self):
        # Once nazikce, olmazsa Windows'ta tum surec agacini (tarayici dahil) oldur.
        proc = self._proc
        if proc is None:
            return
        try:
            proc.terminate()
            proc.wait(timeout=8)
        except Exception:  # noqa: BLE001
            try:
                subprocess.run(
                    ["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                    capture_output=True,
                )
            except Exception:  # noqa: BLE001
                pass


yonetici = _ScraperYoneticisi()


def scraping_ve_aktarim_calistir() -> dict:
    """Zamanlanmis (gecelik) otomatik cekme icin: scraper'i sonuna kadar
    calistirir, verileri DB'ye aktarir ve modeli guncel veriyle yeniden egitir.
    Interaktif yonetici'nin (durdurma/canli sayac) aksine bu bloklar ve
    mudahalesiz calisir; APScheduler zaten kendi arka plan thread'inde cagirir."""
    sonuc = {
        "scraper_basarili": False,
        "ingestion_calisti": False,
        "egitim_calisti": False,
        "hata": None,
    }

    try:
        subprocess.run(
            [settings.scraper_python_path, settings.scraper_script_path],
            cwd=settings.scraper_working_dir,
            check=True,
        )
        sonuc["scraper_basarili"] = True
    except subprocess.CalledProcessError as hata:
        sonuc["hata"] = f"Scraper calisirken hata: {hata}"
        print(sonuc["hata"])
        return sonuc

    try:
        verileri_ice_aktar()
        sonuc["ingestion_calisti"] = True
    except Exception as hata:  # noqa: BLE001
        sonuc["hata"] = f"Ingestion calisirken hata: {hata}"
        return sonuc

    try:
        egit(kaydet=True)
        sonuc["egitim_calisti"] = True
    except Exception as hata:  # noqa: BLE001
        sonuc["hata"] = f"Model egitilirken hata: {hata}"
    return sonuc
