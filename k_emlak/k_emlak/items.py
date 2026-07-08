# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class KEmlakItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass

class IlanItem(scrapy.Item):
    ilan_adi = scrapy.Field()
    adres = scrapy.Field()
    fiyat = scrapy.Field()
    oda_sayisi = scrapy.Field()
    kat_sayisi = scrapy.Field() # bulunduğu kat
    brut_m2 = scrapy.Field()
    net_m2 = scrapy.Field()
    bina_yasi = scrapy.Field()
    esyali_mi = scrapy.Field()
    otoparkli_mi = scrapy.Field()