# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class AmazonproductsItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    category = scrapy.Field()
    company = scrapy.Field()
    product_desc = scrapy.Field()
    ASIN = scrapy.Field()
    num_review = scrapy.Field()
    rating = scrapy.Field()
