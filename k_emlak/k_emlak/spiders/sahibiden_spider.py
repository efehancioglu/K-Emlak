from pathlib import Path
import json

import scrapy
import scrapy_playwright as playwright
from playwright_stealth import Stealth
from ..items import IlanItem

class SahibindenSpider(scrapy.Spider):
    name = "sahibinden_ilanlar"

    start_urls = [
            "https://www.sahibinden.com/ilan/emlak-konut-satilik-kardeskoy-firsat-villa-1325607132/detay"
    ]

    def start_requests(self):

        for url in self.start_urls:
            print(f">>> YIELD EDILECEK URL: {url} <<<")
            yield scrapy.Request(url=url, callback=self.parse, dont_filter=True, meta={"playwright": True,
                                                                     "playwright_include_page": True,
                                                                     "playwright_page_init_callback": self.init_page,
                                                                     "handle_httpstatus_list": [403]
                                                                     })

    async def init_page(self, page, request):
        await Stealth().apply_stealth_async(page.context)

    def parse(self, response):
        if response.status == 403:
            self.logger.error("HTTP 403: Bağlantı WAF tarafından reddedildi.")
            return

        raw_json = response.css('div#gaPageViewTrackingJson::attr(data-json)').get()

        data = json.loads(raw_json)

        dmp_data = {item["name"]: item["value"] for item in data.get("dmpData", [])}
        custom_vars = {item["name"]: item["value"] for item in data.get("customVars", [])}
        
        item = IlanItem()

        item['ilan_id'] = custom_vars.get('İlan No')
        item['il_adi'] = dmp_data.get('loc2')
        item['ilce_adi'] = dmp_data.get('loc3')
        item['fiyat'] = dmp_data.get('fiyat')
        item['oda_sayisi'] = dmp_data.get('oda_sayisi')
        item['kat_sayisi'] = dmp_data.get('bulundugu_kat')
        item['banyo_sayisi'] = dmp_data.get('banyo_sayisi')
        item['brut_m2'] = dmp_data.get('m2_brut')
        item['net_m2'] = dmp_data.get('m2_net')
        item['bina_yasi'] = dmp_data.get('bina_yasi')
        item['esyali_mi'] = dmp_data.get('esyali')
        item['otoparkli_mi'] = dmp_data.get('otopark')
        item['asansorlu_mi'] = dmp_data.get('asansor')
        item['sitede_mi'] = dmp_data.get('site_icerisinde')
        
        yield item
