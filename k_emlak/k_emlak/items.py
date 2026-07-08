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
    ilan_id = scrapy.Field()
    il_adi = scrapy.Field()
    ilce_adi = scrapy.Field()
    fiyat = scrapy.Field()
    oda_sayisi = scrapy.Field()
    kat_sayisi = scrapy.Field()
    banyo_sayisi = scrapy.Field()
    brut_m2 = scrapy.Field()
    net_m2 = scrapy.Field()
    bina_yasi = scrapy.Field()
    esyali_mi = scrapy.Field()
    otoparkli_mi = scrapy.Field()
    asansorlu_mi = scrapy.Field()
    sitede_mi = scrapy.Field()