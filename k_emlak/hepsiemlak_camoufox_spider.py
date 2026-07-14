"""Hepsiemlak spider'inin Camoufox varyanti.

Amac: patchright (Chromium) surumu ile Camoufox (Firefox tabanli, anti-tespit
odakli) surumunu ayni is mantigi uzerinde kiyaslamak. Tum parsing, CSV yazma,
durum yonetimi ve Cloudflare *bekleme* mantigi ana HepsiemlakSpider'dan miras
alinir; burada yalnizca tarayici katmani degisir.

NOT: Bu dosya Cloudflare korumasini otomatik "gecmez/cozmez". Sadece daha az
tetikleyen bir tarayici fingerprint'i kullanir; challenge cikarsa yine elle
gecilir (miras alinan _cloudflare_bekle mantigi).

Kurulum (bir kez):
    pip install camoufox[geoip]
    python -m camoufox fetch
"""

import asyncio
import os

from camoufox.async_api import AsyncCamoufox

from hepsiemlak_spider import HepsiemlakSpider

# Camoufox icin ayri profil/cikti dosyalari; patchright surumuyle karismaz.
CF_PROFIL_DIR = os.path.join(os.path.dirname(__file__), "he_camoufox_profil")
CF_CIKTI_CSV = os.path.join(os.path.dirname(__file__), "hepsiemlak_ilanlar_camoufox.csv")
CF_DURUM_DOSYA = os.path.join(os.path.dirname(__file__), ".durum_camoufox.json")


class _CamoufoxBaglam:
    """Camoufox ile kalici profil acan async context manager.

    persistent_context=True verildiginde AsyncCamoufox dogrudan bir
    BrowserContext dondurur; boylece clearance cerezi profilde saklanir.
    """

    async def __aenter__(self):
        os.makedirs(CF_PROFIL_DIR, exist_ok=True)
        self._cm = AsyncCamoufox(
            headless=False,
            persistent_context=True,
            user_data_dir=CF_PROFIL_DIR,
            # Turkiye cikisli gorunum; GeoIP ile tutarli fingerprint uretir.
            geoip=True,
            locale="tr-TR",
            # Insan benzeri kucuk gecikmeler ve humanize hareketler.
            humanize=True,
        )
        self._context = await self._cm.__aenter__()
        return self._context

    async def __aexit__(self, *exc):
        await self._cm.__aexit__(*exc)


class HepsiemlakCamoufoxSpider(HepsiemlakSpider):
    """patchright yerine Camoufox kullanan varyant."""

    def __init__(self, liste_url=None, max_sayfa=1, kaynak_engelle=False):
        # Ana sinifin varsayilan LISTE_URL'ini kullan; ayri CSV/durum dosyalari ver.
        kwargs = dict(max_sayfa=max_sayfa, csv_dosya=CF_CIKTI_CSV,
                      durum_dosya=CF_DURUM_DOSYA, kaynak_engelle=kaynak_engelle)
        if liste_url is not None:
            kwargs["liste_url"] = liste_url
        super().__init__(**kwargs)

    def _tarayici(self):
        return _CamoufoxBaglam()


async def main():
    spider = HepsiemlakCamoufoxSpider(max_sayfa=100)
    toplam = await spider.crawl()
    print(f"Bu kosuda {toplam} yeni ilan eklendi -> {CF_CIKTI_CSV}")


if __name__ == "__main__":
    asyncio.run(main())
