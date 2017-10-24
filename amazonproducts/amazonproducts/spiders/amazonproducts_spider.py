#! /usr/local/bin/python3

from scrapy import Spider
from scrapy import Request
from scrapy.selector import Selector
from scrapy.shell import inspect_response
from scrapy.crawler import CrawlerProcess
from amazonproducts.items import AmazonproductsItem
from scrapy_proxies import *
from datetime import datetime
import csv
import numpy
import redis
from amazonproducts import settings

# Open Redis connection
redis_conn = redis.StrictRedis(host=settings.redis_host,
                               port=settings.redis_port,
                               db=settings.redis_db)


class AmazonproductsSpider(Spider):
    name = "amazonproducts"
    allowed_urls = ['https://www.amazon.com']
    start_urls = []

    # START HARD CODED SECTION -get category URLs
    # Earbud Headphones
    category_start_url = [
        'https://www.amazon.com/b/ref=lp_172541_ln_0?node=12097478011&ie=UTF8&qid=1508730723']

    category_URL_list = ["https://www.amazon.com/s/ref=lp_12097478011_pg_" + str(i) +
                         "?rh=n%3A172282%2Cn%3A%21493964%2Cn%3A172541%2Cn%3A12097478011&page=" + str(i) +
                         "&ie=UTF8&qid=1508730739" for i in range(2, 401)]

    start_urls = start_urls + category_start_url + category_URL_list  # add new links

    # On-ear Headphones
    category_start_url = [
        'https://www.amazon.com/On-Ear-Headphones/b/ref=sn_gfs_co_coins_12097480011_2?ie=UTF8&node=12097480011&pf_rd_p=28d73b43-f35e-4996-90fe-fb4130c98842&pf_rd_r=4VJ9ANC8CP0Q8MB6WVC5&pf_rd_s=home-audio-subnav-flyout-content-2&pf_rd_t=SubnavFlyout']

    category_URL_list = ["https://www.amazon.com/s/ref=lp_12097480011_pg_" + str(i) +
                         "?rh=n%3A172282%2Cn%3A%21493964%2Cn%3A172541%2Cn%3A12097480011&page=" + str(i) +
                         "&ie=UTF8&qid=1508731077" for i in range(2, 227)]

    start_urls = start_urls + category_start_url + category_URL_list  # add new links

    # Over-ear Headphones
    category_start_url = [
        'https://www.amazon.com/Over-Ear-Headphones/b/ref=sn_gfs_co_coins_12097479011_3?ie=UTF8&node=12097479011&pf_rd_p=28d73b43-f35e-4996-90fe-fb4130c98842&pf_rd_r=YHPFTPPV99V769NNBQEY&pf_rd_s=home-audio-subnav-flyout-content-2&pf_rd_t=SubnavFlyout']

    category_URL_list = ["https://www.amazon.com/s/ref=lp_12097479011_pg_" + str(i) +
                         "?rh=n%3A172282%2Cn%3A%21493964%2Cn%3A172541%2Cn%3A12097479011&page=" + str(i) +
                         "&ie=UTF8&qid=1508731230" for i in range(2, 401)]

    start_urls = start_urls + category_start_url + category_URL_list  # add new links
    # END HARD CODED SECTION

    # add urls to queue
    for url in start_urls:
        redis_conn.sadd('Category_URLs', url)

    def start_requests(self):
        # Parse category pages randomly
        while redis_conn.scard('Category_URLs') > 0:
            category_url = redis_conn.spop('Category_URLs').decode("utf-8")
            yield Request(category_url, self.parse,  meta={'cookiejar': numpy.random.randint(1000)})

    def parse(self, response):

        # TO DO: get category 'Routers'
        category = response.xpath('//h4[@class="a-size-small a-color-base a-text-bold"]/text()').extract_first() # u'Routers'
        if category is None:
            print("=" * 30)
            print("No category found")
            category = " "
        else:
            print("Analyzing category: ", category)

        product_node_list = response.xpath('//li[contains(@id, "result_")]')

        for product in product_node_list:

            product_desc = product.xpath('.//a[@class="a-link-normal s-access-detail-page  s-color-twister-title-link a-text-normal"]/@title').extract_first()
            # 'ARRlS TG862G Telephony DOCSlS 3.0 Wireless Modem, 4 Port Router (Xfinity Triple Play)'

            ASIN = product.xpath('./@data-asin').extract_first()  # 'B075XLWML4'
            # num_review = scrapy.Field()
            num_review = product.xpath('.//a[@class="a-size-small a-link-normal a-text-normal" and contains(@href, "customerReviews")]/text()').extract_first()
            # u'2,402'
            if num_review is not None: # articles with 0 reviews
                num_review = int(num_review.replace(',',''))
            else:
                num_review =0
            rating = product.xpath('.//i[contains(@class, "a-icon-star")]/span/text()').extract_first()  # u'4.4 out of 5 stars'
            try:
                rating = float(rating.split(' ')[0])  # throws Nonetype error
            except:
                rating = 0  # for articles without reviews -be careful to filter out when doing averages...
                print("=" * 30)
                print("No rating for product: ", ASIN)

            try:
                company = product.xpath('.//span[@class="a-size-small a-color-secondary"]/text()').extract()[1]  # first element is 'by' (by Arris)
            except:
                print("=" * 30)
                print("No Company for product: ", ASIN)
                company = " "

            item = AmazonproductsItem()
            item['category'] = category
            item['company'] = company
            item['product_desc'] = product_desc
            item['ASIN'] = ASIN
            item['num_review'] = num_review
            item['rating'] = rating

            yield item
