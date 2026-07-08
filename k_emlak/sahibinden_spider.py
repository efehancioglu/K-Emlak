import asyncio
import csv
import json
import os

from patchright.async_api import async_playwright

PROFIL_DIR = os.path.join(os.path.dirname(__file__), "pw_profil")
CIKTI_CSV = "ilanlar.csv"

ALANLAR = [
    "ilan_id", "il_adi", "ilce_adi", "fiyat", "oda_sayisi", "kat_sayisi",
    "banyo_sayisi", "brut_m2", "net_m2", "bina_yasi", "esyali_mi",
    "otoparkli_mi", "asansorlu_mi", "sitede_mi",
]


class SahibindenSpider:
    def __init__(self, urls):
        self.urls = urls

    async def crawl(self):
        sonuclar = []
        async with async_playwright() as p:
            context = await p.chromium.launch_persistent_context(
                PROFIL_DIR, channel="chrome", headless=False, no_viewport=True,
            )
            page = context.pages[0] if context.pages else await context.new_page()
            for url in self.urls:
                item = await self.parse(page, url)
                if item:
                    sonuclar.append(item)
            await context.close()
        return sonuclar

    async def parse(self, page, url):
        await page.goto(url, wait_until="commit", timeout=60000)

        frame = await self.ilan_frame_bekle(page)
        if not frame:
            print(f"Ilan yuklenemedi (challenge/login): {url}")
            return None

        raw_json = await frame.eval_on_selector(
            "div#gaPageViewTrackingJson", "el => el.getAttribute('data-json')"
        )
        return self.parse_json(raw_json)

    async def ilan_frame_bekle(self, page, deneme=12, aralik_ms=5000):
        """Ilan div'i (iframe icinde olabilir) gorunene kadar tum frame'leri tarar.

        Navigasyon sirasinda frame'ler yok olabilecegi (detached) icin her
        sorgu hataya karsi korunur.
        """
        for _ in range(deneme):
            for frame in page.frames:
                try:
                    if await frame.query_selector("div#gaPageViewTrackingJson"):
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


def csv_yaz(items, dosya=CIKTI_CSV):
    with open(dosya, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=ALANLAR)
        w.writeheader()
        w.writerows(items)


async def main():
    urls = [
        "https://www.sahibinden.com/ilan/emlak-konut-satilik-kardeskoy-firsat-villa-1325607132/detay",
    ]
    spider = SahibindenSpider(urls)
    items = await spider.crawl()
    csv_yaz(items)
    print(f"{len(items)} ilan cekildi -> {CIKTI_CSV}")


if __name__ == "__main__":
    asyncio.run(main())
