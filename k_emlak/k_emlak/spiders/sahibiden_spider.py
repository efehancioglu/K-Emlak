from pathlib import Path
from urllib.request import Request

import scrapy

class SahibindenSpider(scrapy.Spider):
    name = "ilanlar"

    async def start(self):
        urls = [
            "https://www.sahibinden.com/ilan/emlak-konut-satilik-kardeskoy-firsat-villa-1325607132/detay"
        ]

        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
