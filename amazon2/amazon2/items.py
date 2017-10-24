# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class Amazon2Item(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    review_id = scrapy.Field()
    ASIN = scrapy.Field()
    review_title = scrapy.Field()
    review_rating = scrapy.Field()
    review_date = scrapy.Field()
    review_body = scrapy.Field()
