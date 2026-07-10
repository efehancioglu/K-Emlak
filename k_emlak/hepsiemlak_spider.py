import asyncio
import csv
import json
import os
import random

from patchright.async_api import async_playwright

PROFIL_DIR = os.path.join(os.path.dirname(__file__), "he_profil")
CIKTI_CSV = "hepsiemlak_ilanlar.csv"

LISTE_URL = "https://www.hepsiemlak.com/satilik"
ILAN_LINK_SEC = "a.card-link"
SPEC_SATIR_SEC = "tr.spec-item"
FIYAT_SEC = "p.price"

BEKLEME_MIN = 3
BEKLEME_MAX = 8

ALANLAR = [
    "ilan_no", "mahalle", "ilce", "il", "fiyat", "brut_m2", "net_m2",
    "oda_sayisi", "banyo_sayisi", "kat_sayisi", "bulundugu_kat", "bina_yasi",
    "isinma", "esya_durumu", "kullanim_durumu", "tapu_durumu", "aidat", "url",
]

ETIKET_ESLEME = {
    "İlan no": "ilan_no",
    "Oda Sayısı": "oda_sayisi",
    "Banyo Sayısı": "banyo_sayisi",
    "Kat Sayısı": "kat_sayisi",
    "Bulunduğu Kat": "bulundugu_kat",
    "Bina Yaşı": "bina_yasi",
    "Isınma Tipi": "isinma",
    "Eşya Durumu": "esya_durumu",
    "Kullanım Durumu": "kullanim_durumu",
    "Tapu Durumu": "tapu_durumu",
    "Aidat": "aidat",
}


class HepsiemlakSpider:
    def __init__(self, liste_url=LISTE_URL, max_sayfa=1, csv_dosya=CIKTI_CSV):
        self.liste_url = liste_url
        self.max_sayfa = max_sayfa
        self.csv_dosya = csv_dosya
        self.cekilen = self._mevcut_urlleri_yukle()

    async def crawl(self):
        toplam = 0
        async with async_playwright() as p:
            context = await p.chromium.launch_persistent_context(
                PROFIL_DIR, channel="chrome", headless=False, no_viewport=True,
            )
            page = context.pages[0] if context.pages else await context.new_page()
            await self._kaynaklari_engelle(context)

            try:
                for sayfa in range(1, self.max_sayfa + 1):
                    linkler = await self.ilan_linkleri(page, sayfa)
                    if not linkler:
                        print(f"Sayfa {sayfa}: link yok, duruluyor.")
                        break
                    print(f"Sayfa {sayfa}: {len(linkler)} ilan bulundu.")

                    for link in linkler:
                        if link in self.cekilen:
                            continue
                        try:
                            item = await self.ilan_detay(page, link)
                        except Exception as e:
                            print(f"  Ilan atlandi ({type(e).__name__}): {link}")
                            continue
                        if not item:
                            continue
                        self._csv_ekle(item)
                        self.cekilen.add(link)
                        toplam += 1
                        await self._insan_gecikmesi()
            except Exception as e:
                print(f"Kosu yarida kesildi ({type(e).__name__}). {toplam} ilan kaydedildi.")
            finally:
                try:
                    await context.close()
                except Exception:
                    pass
        return toplam

    async def git_ve_bekle(self, page, url, hedef_secici):
        await page.goto(url, wait_until="commit", timeout=60000)
        await self._cloudflare_bekle(page)
        try:
            await page.wait_for_selector(hedef_secici, timeout=20000)
            return True
        except Exception:
            return False

    async def _kaynaklari_engelle(self, context):
        """Resim/font/medya isteklerini iptal eder; Cloudflare varliklarina dokunmaz."""
        engelli = {"image", "media", "font"}
        korumali = ("cloudflare.com", "hcaptcha.com")

        async def yonlendir(route):
            if any(k in route.request.url for k in korumali):
                await route.continue_()
            elif route.request.resource_type in engelli:
                await route.abort()
            else:
                await route.continue_()

        await context.route("**/*", yonlendir)

    async def _cloudflare_bekle(self, page):
        """Cloudflare dogrulamasi cikarsa kullanicinin elle basmasini bekler."""
        if not await self._challenge_var(page):
            return
        print("\n" + "=" * 55)
        print("  >>> ELLE DOGRULAMA GEREKIYOR <<<")
        print("  Acik penceredeki checkbox'a BAS. Devam icin bekleniyor...")
        print("=" * 55 + "\a")
        beklenen = 0
        while await self._challenge_var(page):
            await page.wait_for_timeout(2000)
            beklenen += 2
            if beklenen % 20 == 0:
                print(f"  ...hala bekleniyor ({beklenen}sn). Checkbox'a bas.")
        print("  -> Dogrulama gecildi, devam ediliyor.\n")

    async def _challenge_var(self, page):
        try:
            baslik = (await page.title()).lower()
        except Exception:
            return False
        if "just a moment" in baslik or "doğrulama" in baslik:
            return True
        el = await page.query_selector(
            "#challenge-running, iframe[src*='challenges.cloudflare.com'], "
            "iframe[title*='Cloudflare'], iframe[src*='turnstile']"
        )
        return el is not None

    async def ilan_linkleri(self, page, sayfa):
        url = self.liste_url if sayfa == 1 else f"{self.liste_url}?page={sayfa}"
        if not await self.git_ve_bekle(page, url, ILAN_LINK_SEC):
            return []
        return await page.eval_on_selector_all(
            ILAN_LINK_SEC, "els => els.map(e => e.href)"
        )

    async def ilan_detay(self, page, url):
        if not await self.git_ve_bekle(page, url, SPEC_SATIR_SEC):
            print(f"  Detay yuklenemedi: {url}")
            return None

        specler = await self._spec_sozluk(page)

        item = {alan: None for alan in ALANLAR}
        for etiket, deger in specler.items():
            alan = ETIKET_ESLEME.get(etiket)
            if alan:
                item[alan] = deger
        item["fiyat"] = await self._ilk_metin(page, FIYAT_SEC)
        item["brut_m2"], item["net_m2"] = self._brut_net_ayir(specler.get("Brüt / Net M2"))
        item["mahalle"], item["ilce"], item["il"] = self._konum_ayir(
            await self._konum_metni(page)
        )
        item["url"] = url
        return item

    @staticmethod
    def _konum_ayir(deger):
        """'Mahalle, Ilce/Il' -> ('Mahalle', 'Ilce', 'Il')."""
        if not deger:
            return None, None, None
        mahalle, _, kalan = deger.partition(",")
        ilce, _, il = kalan.partition("/")
        temiz = lambda s: s.strip() or None
        return temiz(mahalle), temiz(ilce), temiz(il)

    @staticmethod
    def _brut_net_ayir(deger):
        """'83 m2 / 80 m2' -> ('83', '80')."""
        if not deger:
            return None, None
        temiz = deger.lower().replace("m2", "").replace("m²", "")
        parcalar = temiz.split("/")
        rakam = lambda s: "".join(ch for ch in s if ch.isdigit()) or None
        brut = rakam(parcalar[0]) if len(parcalar) >= 1 else None
        net = rakam(parcalar[1]) if len(parcalar) >= 2 else None
        return brut, net

    async def _spec_sozluk(self, page):
        ciftler = await page.eval_on_selector_all(
            SPEC_SATIR_SEC,
            """els => els.map(tr => {
                const th = tr.querySelector('th');
                const val = tr.querySelector('.value-txt')
                          || tr.querySelector('a')
                          || tr.querySelector('td');
                return [
                    th ? th.innerText.trim() : '',
                    val ? val.innerText.replace(/\\s+/g,' ').trim() : ''
                ];
            })""",
        )
        return {e: d for e, d in ciftler if e}

    async def _konum_metni(self, page):
        """JSON-LD adresinden 'Mahalle, Ilce/Il' metnini alir."""
        bloklar = await page.eval_on_selector_all(
            "script[type='application/ld+json']", "els => els.map(e => e.textContent)"
        )
        for blok in bloklar:
            try:
                data = json.loads(blok)
            except Exception:
                continue
            for node in data.get("@graph", [data]):
                about = node.get("about") if isinstance(node, dict) else None
                adres = (about or {}).get("address") or {}
                konum = adres.get("streetAddress") or adres.get("addressLocality")
                if konum:
                    return konum
        return None

    async def _ilk_metin(self, page, secici):
        try:
            metinler = await page.eval_on_selector_all(
                secici, "els => els.map(e => e.innerText.trim())"
            )
            return metinler[0] if metinler else None
        except Exception:
            return None

    async def _insan_gecikmesi(self):
        await asyncio.sleep(random.uniform(BEKLEME_MIN, BEKLEME_MAX))

    def _mevcut_urlleri_yukle(self):
        if not os.path.exists(self.csv_dosya):
            return set()
        with open(self.csv_dosya, newline="", encoding="utf-8") as f:
            return {s["url"] for s in csv.DictReader(f) if s.get("url")}

    def _csv_ekle(self, item):
        yeni = not os.path.exists(self.csv_dosya)
        with open(self.csv_dosya, "a", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=ALANLAR)
            if yeni:
                w.writeheader()
            w.writerow(item)


async def main():
    spider = HepsiemlakSpider(max_sayfa=30)
    toplam = await spider.crawl()
    print(f"Bu kosuda {toplam} yeni ilan eklendi -> {CIKTI_CSV}")


if __name__ == "__main__":
    asyncio.run(main())
