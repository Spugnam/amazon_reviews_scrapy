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
    # Activity tracker
    category_start_url = [
        'https://www.amazon.com/b/ref=s9_acss_bw_cg_WTSHEAD_1a1_w?node=8849526011&pf_rd_m=ATVPDKIKX0DER&pf_rd_s=merchandised-search-1&pf_rd_r=1TEVA3TGV0JNYZ1K4W8Q&pf_rd_t=101&pf_rd_p=4896a448-8d92-4aa5-bab1-30c5b5c3b3ac&pf_rd_i=10048700011']

    category_URL_list = ["https://www.amazon.com/s/ref=lp_8849526011_pg_" + str(i) +
                         "?rh=n%3A8849526011&page=" + str(i) +
                         "&ie=UTF8&qid=1508886262" for i in range(2, 7)]

    start_urls = start_urls + category_start_url + category_URL_list  # add new links

    # Sports/ GPS Watches
    category_start_url = [
        'https://www.amazon.com/b/ref=s9_acss_bw_cg_WTSHEAD_1b1_w?node=8916179011&pf_rd_m=ATVPDKIKX0DER&pf_rd_s=merchandised-search-1&pf_rd_r=YVPE7RRS0XW63SXQJ98G&pf_rd_t=101&pf_rd_p=6330968a-454b-4d9e-9b58-296a6545826c&pf_rd_i=8849526011']

    category_URL_list = ["https://www.amazon.com/s/ref=lp_8916179011_pg_" + str(i) +
                         "?rh=n%3A172282%2Cn%3A%2113900851%2Cn%3A%212334089011%2Cn%3A%212334151011%2Cn%3A8916179011&page=" + str(
        i) +
                         "&ie=UTF8&qid=1508886536" for i in range(2, 128)]

    start_urls = start_urls + category_start_url + category_URL_list  # add new links

    # Smart watches
    category_start_url = [
        'https://www.amazon.com/b/ref=s9_acss_bw_cg_WTSHEAD_1c1_w?node=7939901011&pf_rd_m=ATVPDKIKX0DER&pf_rd_s=merchandised-search-1&pf_rd_r=G43X3YCSEK3VERXDXDKN&pf_rd_t=101&pf_rd_p=008c91d9-d829-4d59-a153-d947968afc2f&pf_rd_i=8916179011']

    category_URL_list = ["https://www.amazon.com/s/ref=lp_7939901011_pg_" + str(i) +
                         "?rh=n%3A172282%2Cn%3A%21493964%2Cn%3A10048700011%2Cn%3A7939901011&page=" + str(i) +
                         "&ie=UTF8&qid=1508886637" for i in range(2, 302)]

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
