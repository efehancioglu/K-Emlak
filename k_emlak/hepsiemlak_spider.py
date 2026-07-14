import asyncio
import csv
import json
import os
import random

from patchright.async_api import async_playwright

PROFIL_DIR = os.path.join(os.path.dirname(__file__), "he_profil")
CIKTI_CSV = os.path.join(os.path.dirname(__file__), "hepsiemlak_ilanlar.csv")
DURUM_DOSYA = os.path.join(os.path.dirname(__file__), ".durum.json")

# Ust uste bu kadar "tamamen bilinen" liste sayfasi gorulunce tarama durur.
BOS_SAYFA_ESIGI = 3

LISTE_URL = "https://www.hepsiemlak.com/satilik"
ILAN_LINK_SEC = "a.card-link"
SPEC_SATIR_SEC = "tr.spec-item"
FIYAT_SEC = "p.price"

# Ilan detaylari arasindaki insan benzeri bekleme (saniye).
BEKLEME_MIN = 0.8
BEKLEME_MAX = 2

# Liste sayfalari arasindaki bekleme; detaydan biraz daha uzun tutulur cunku
# ardarda liste sayfasi cekmek Cloudflare'i en cok tetikleyen davranistir.
SAYFA_BEKLEME_MIN = 2
SAYFA_BEKLEME_MAX = 4

ALANLAR = [
    "ilan_no", "mahalle", "ilce", "il", "fiyat", "brut_m2", "net_m2",
    "oda_sayisi", "banyo_sayisi", "kat_sayisi", "bulundugu_kat", "bina_yasi",
    "isinma", "esya_durumu", "kullanim_durumu", "tapu_durumu", "cephe", "aidat", "url",
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
    "Cephe": "cephe",
    "Aidat": "aidat",
}


class _PatchrightBaglam:
    """patchright ile kalici Chrome profili acan async context manager."""

    async def __aenter__(self):
        self._pw_cm = async_playwright()
        p = await self._pw_cm.__aenter__()
        self._context = await p.chromium.launch_persistent_context(
            PROFIL_DIR, channel="chrome", headless=False, no_viewport=True,
        )
        return self._context

    async def __aexit__(self, *exc):
        try:
            await self._context.close()
        except Exception:
            pass
        await self._pw_cm.__aexit__(*exc)


class HepsiemlakSpider:
    def __init__(self, liste_url=LISTE_URL, max_sayfa=1, csv_dosya=CIKTI_CSV,
                 durum_dosya=DURUM_DOSYA, kaynak_engelle=False):
        self.liste_url = liste_url
        self.max_sayfa = max_sayfa
        self.csv_dosya = csv_dosya
        self.durum_dosya = durum_dosya
        # Kaynak (resim/medya) engelleme VARSAYILAN OLARAK KAPALI. Olculdu:
        # engelleme acikken Cloudflare cok daha sik challenge cikardi (gercek
        # tarayici alt kaynaklari bloklamaz -> bot sinyali). Kapaliyken 3 sayfa
        # boyunca hic elle dogrulama gerekmedi. Bant genisligi onemliyse
        # True yapilabilir (o zaman sadece resim/medya iptal edilir).
        self.kaynak_engelle = kaynak_engelle
        self.cekilen = self._mevcut_urlleri_yukle()
        # Onceki kosuda basariyla islenmis en derin liste sayfasi.
        self.ulasilan_sayfa = self._ulasilan_sayfa_yukle()

    def _tarayici(self):
        """Tarayici baglamini (BrowserContext) veren async context manager.

        Alt siniflar (or. Camoufox varyanti) farkli bir tarayici saglamak icin
        bu metodu override eder. Varsayilan: patchright ile kalici Chrome profili.
        """
        return _PatchrightBaglam()

    async def crawl(self):
        toplam = 0
        async with self._tarayici() as context:
            page = context.pages[0] if context.pages else await context.new_page()
            if self.kaynak_engelle:
                await self._kaynaklari_engelle(context)

            try:
                # Yeni ilanlar genelde ilk sayfalarda cikar, o yuzden hep 1'den
                # baslanir. Ardarda tamamen bilinen sayfa gorulunce durulur; ancak
                # onceki kosuda ulasilan derinlige kadar erken durma devreye girmez.
                bos_ardarda = 0
                for sayfa in range(1, self.max_sayfa + 1):
                    linkler = await self.ilan_linkleri(page, sayfa)
                    if not linkler:
                        print(f"Sayfa {sayfa}: link yok, duruluyor.")
                        break

                    yeni_linkler = [l for l in linkler if l not in self.cekilen]
                    print(f"Sayfa {sayfa}: {len(linkler)} ilan "
                          f"({len(yeni_linkler)} yeni).")

                    if not yeni_linkler and sayfa > self.ulasilan_sayfa:
                        bos_ardarda += 1
                        if bos_ardarda >= BOS_SAYFA_ESIGI:
                            print(f"  {bos_ardarda} sayfa ust uste yeni ilan yok, "
                                  f"tarama tamamlandi.")
                            break
                    else:
                        bos_ardarda = 0

                    for link in yeni_linkler:
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

                    # Sayfa bitti; ilerlemeyi kalici olarak isaretle.
                    if sayfa > self.ulasilan_sayfa:
                        self.ulasilan_sayfa = sayfa
                    self._durum_kaydet()

                    # Bir sonraki liste sayfasina gecmeden once insan benzeri ara.
                    if sayfa < self.max_sayfa:
                        await self._sayfa_gecikmesi()
            except Exception as e:
                print(f"Kosu yarida kesildi ({type(e).__name__}). {toplam} ilan kaydedildi.")
            # Baglam kapatma _tarayici() context manager'inda yapilir.
        return toplam

    async def git_ve_bekle(self, page, url, hedef_secici):
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        await self._cloudflare_bekle(page)
        # Challenge gecince Cloudflare sayfayi yeniden yonlendirir; hedef secici
        # gorunmesi bu navigation'in oturmasina bagli. Cift kontrol: secici bir
        # kez gorunmezse (arada yeni challenge cikmis olabilir) tekrar bekle.
        for _ in range(2):
            try:
                await page.wait_for_selector(hedef_secici, timeout=45000)
                return True
            except Exception:
                if await self._challenge_var(page):
                    await self._cloudflare_bekle(page)
                    continue
                return False
        return False

    async def _kaynaklari_engelle(self, context):
        """Sadece resim/medyayi iptal eder; CSS ve font yuklenir.

        CSS/font'u da bloklamak Cloudflare icin guclu bir bot sinyalidir ve
        her sayfada challenge tetikler (olculdu: engelli={image,media,font,
        stylesheet} -> 2 sayfada 4 challenge; sadece image/media -> 0 challenge).
        Resim/medya en buyuk bant genisligi kalemi oldugu icin onlari
        engellemek hizi korur, bot riskini artirmaz.
        """
        engelli = {"image", "media"}
        korumali = ("cloudflare.com", "hcaptcha.com", "turnstile", "challenges.cloudflare.com")

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
                print(f"  ...hala bekleniyor ({beklenen}sn). Checkbox'a bas.\a")
        # Clearance cerezinin profile yazilmasi ve sayfanin oturmasi icin kisa ara.
        await page.wait_for_timeout(1500)
        print("  -> Dogrulama gecildi, devam ediliyor.\n")

    async def _challenge_var(self, page):
        try:
            baslik = (await page.title()).lower()
        except Exception:
            return False
        # patchright/Chrome "Just a moment...", Camoufox/Firefox ise
        # "Bir dakika lutfen..." baslikli challenge sayfasi gosterir.
        if any(k in baslik for k in ("just a moment", "bir dakika", "doğrulama")):
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

    async def _sayfa_gecikmesi(self):
        await asyncio.sleep(random.uniform(SAYFA_BEKLEME_MIN, SAYFA_BEKLEME_MAX))

    def _mevcut_urlleri_yukle(self):
        if not os.path.exists(self.csv_dosya):
            return set()
        with open(self.csv_dosya, newline="", encoding="utf-8") as f:
            return {s["url"] for s in csv.DictReader(f) if s.get("url")}

    def _ulasilan_sayfa_yukle(self):
        try:
            with open(self.durum_dosya, encoding="utf-8") as f:
                return int(json.load(f).get("ulasilan_sayfa", 0))
        except (OSError, ValueError, json.JSONDecodeError):
            return 0

    def _durum_kaydet(self):
        try:
            with open(self.durum_dosya, "w", encoding="utf-8") as f:
                json.dump({"ulasilan_sayfa": self.ulasilan_sayfa}, f)
        except OSError as e:
            print(f"  Durum kaydedilemedi ({type(e).__name__}).")

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
