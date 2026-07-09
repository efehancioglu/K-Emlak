import asyncio
import csv
import json
import os
import random

from patchright.async_api import async_playwright

PROFIL_DIR = os.path.join(os.path.dirname(__file__), "pw_profil")
CIKTI_CSV = "sahibinden_ilanlar.csv"

LISTE_URL = "https://www.sahibinden.com/satilik"
SAYFA_BOYUTU = 20          # sahibinden her liste sayfasinda 20 ilan gosterir
ILAN_LINK_SEC = "a.classifiedTitle"
ILAN_DIV_SEC = "div#gaPageViewTrackingJson"

# Insan hizinda gezinme icin ilanlar arasi rastgele bekleme (saniye)
BEKLEME_MIN = 8
BEKLEME_MAX = 20

ALANLAR = [
    "ilan_id", "il_adi", "ilce_adi", "fiyat", "oda_sayisi", "kat_sayisi",
    "banyo_sayisi", "brut_m2", "net_m2", "bina_yasi", "esyali_mi",
    "otoparkli_mi", "asansorlu_mi", "sitede_mi",
]


class SahibindenSpider:
    def __init__(self, liste_url=LISTE_URL, max_sayfa=1, csv_dosya=CIKTI_CSV):
        self.liste_url = liste_url
        self.max_sayfa = max_sayfa
        self.csv_dosya = csv_dosya
        self.cekilen_idler = self._mevcut_idleri_yukle()

    async def crawl(self):
        toplam = 0
        async with async_playwright() as p:
            context = await p.chromium.launch_persistent_context(
                PROFIL_DIR, channel="chrome", headless=False, no_viewport=True,
            )
            page = context.pages[0] if context.pages else await context.new_page()

            try:
                for sayfa in range(self.max_sayfa):
                    offset = sayfa * SAYFA_BOYUTU
                    linkler = await self.ilan_linkleri(page, offset)
                    if not linkler:
                        print(f"Sayfa {sayfa + 1}: link yok (muhtemelen engel), duruluyor.")
                        break
                    print(f"Sayfa {sayfa + 1}: {len(linkler)} ilan bulundu.")

                    for link in linkler:
                        item = await self.ilan_detay(page, link)
                        if item is None:
                            continue
                        if not item.get("ilan_id"):
                            # Bos veri = anti-bot uyari sayfasi. Devam etmek riskli, dur.
                            print("  Bos veri geldi (anti-bot). Guvenli sekilde duruluyor.")
                            return toplam
                        if item["ilan_id"] in self.cekilen_idler:
                            continue
                        self._csv_ekle(item)
                        self.cekilen_idler.add(item["ilan_id"])
                        toplam += 1
                        await self._insan_gecikmesi()
            except Exception as e:
                # Tarayici kapandi / engel / ag hatasi: o ana kadarki veri CSV'de.
                print(f"Kosu yarida kesildi ({type(e).__name__}). "
                      f"{toplam} ilan kaydedildi, sonra durdu.")
            finally:
                try:
                    await context.close()
                except Exception:
                    pass
        return toplam

    async def ilan_linkleri(self, page, offset):
        url = f"{self.liste_url}?pagingOffset={offset}"
        await page.goto(url, wait_until="commit", timeout=60000)
        frame = await self.frame_bekle(page, ILAN_LINK_SEC)
        if not frame:
            return []
        return await frame.eval_on_selector_all(
            ILAN_LINK_SEC, "els => els.map(e => e.href)"
        )

    async def ilan_detay(self, page, url):
        await page.goto(url, wait_until="commit", timeout=60000)
        frame = await self.frame_bekle(page, ILAN_DIV_SEC)
        if not frame:
            print(f"  Ilan yuklenemedi: {url}")
            return None
        raw_json = await frame.eval_on_selector(
            ILAN_DIV_SEC, "el => el.getAttribute('data-json')"
        )
        return self.parse_json(raw_json)

    async def frame_bekle(self, page, secici, deneme=12, aralik_ms=5000):
        """Verilen secici gorunene kadar tum frame'leri tarar (iframe dahil).

        Navigasyon sirasinda frame'ler yok olabilecegi (detached) icin her
        sorgu hataya karsi korunur.
        """
        for _ in range(deneme):
            for frame in page.frames:
                try:
                    if await frame.query_selector(secici):
                        return frame
                except Exception:
                    continue
            await page.wait_for_timeout(aralik_ms)
        return None

    def parse_json(self, raw_json):
        data = json.loads(raw_json)
        dmp = {i["name"]: i["value"] for i in data.get("dmpData", [])}
        cv = {i["name"]: i["value"] for i in data.get("customVars", [])}
        return {
            "ilan_id": cv.get("İlan No"),
            "il_adi": dmp.get("loc2"),
            "ilce_adi": dmp.get("loc3"),
            "fiyat": dmp.get("fiyat"),
            "oda_sayisi": dmp.get("oda_sayisi"),
            "kat_sayisi": dmp.get("kat_sayisi"),
            "banyo_sayisi": dmp.get("banyo_sayisi"),
            "brut_m2": dmp.get("m2_brut"),
            "net_m2": dmp.get("m2_net"),
            "bina_yasi": dmp.get("bina_yasi"),
            "esyali_mi": dmp.get("esyali"),
            "otoparkli_mi": dmp.get("otopark"),
            "asansorlu_mi": dmp.get("asansor"),
            "sitede_mi": dmp.get("site_icerisinde"),
        }

    async def _insan_gecikmesi(self):
        await asyncio.sleep(random.uniform(BEKLEME_MIN, BEKLEME_MAX))

    def _mevcut_idleri_yukle(self):
        """Onceki kosudan kalan ID'leri okur; kaldigi yerden devam icin."""
        if not os.path.exists(self.csv_dosya):
            return set()
        with open(self.csv_dosya, newline="", encoding="utf-8") as f:
            return {satir["ilan_id"] for satir in csv.DictReader(f) if satir.get("ilan_id")}

    def _csv_ekle(self, item):
        """Her ilani anlik olarak CSV'ye ekler (cokerse veri kaybolmasin)."""
        yeni = not os.path.exists(self.csv_dosya)
        with open(self.csv_dosya, "a", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=ALANLAR)
            if yeni:
                w.writeheader()
            w.writerow(item)


async def main():
    spider = SahibindenSpider(max_sayfa=1)
    toplam = await spider.crawl()
    print(f"Bu kosuda {toplam} yeni ilan eklendi -> {CIKTI_CSV}")


if __name__ == "__main__":
    asyncio.run(main())
