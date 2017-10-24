#! /usr/local/bin/python3

from scrapy import Spider
from scrapy import Request
from scrapy.selector import Selector
from scrapy.shell import inspect_response
from scrapy.crawler import CrawlerProcess
from amazon2.items import Amazon2Item
from scrapy_proxies import *
from datetime import datetime
import csv
import numpy
import redis
from amazon2 import settings

# Open Redis connection
redis_conn = redis.StrictRedis(host=settings.redis_host,
                               port=settings.redis_port,
                               db=settings.redis_db)



class Amazon2Spider(Spider):
    name = "amazon2"
    allowed_urls = ['https://www.amazon.com']


    start_urls = ['https://www.amazon.com/product-reviews/B014S3UBYO'] # format works for all products including no reviews

    def start_requests(self):

        # products = list()
        # # ASIN.csv format
        # # B014S3UBYO, B074PDGMHH, B01C4AD8RA,... (single line)
        # with open('./amazon2/ASIN.csv', 'r+') as csvfile:
        #     csvreader = csv.reader(csvfile)
        #     for row in csvreader:
        #         for product in row:
        #             products.append(product)

        base_reviews_url = 'https://www.amazon.com/product-reviews/'

        # page_reviews_URL template:
        # https://www.amazon.com/product-reviews/B0001DHHIY/ref=cm_cr_arp_d_paging_btm_3?pageNumber=11

        # parse first review pages
        while redis_conn.scard('ASINs') > 0:
            ASIN = redis_conn.spop('ASINs').decode("utf-8")
            print("=" * 30)
            print("ASIN: ", ASIN)
            first_page_reviews_URL = base_reviews_url + ASIN
            yield Request(first_page_reviews_URL, self.parse, meta={'ASIN': ASIN, 'cookiejar': numpy.random.randint(1000), 'first_page': True})

        # also parse following pages
        while redis_conn.scard('reviews_URLs') > 0:
            review_url = redis_conn.spop('reviews_URLs').decode("utf-8")
            print("="*30)
            print("URL: ", review_url)
            yield Request(review_url, self.parse, meta={'ASIN': review_url[39:49], 'cookiejar': numpy.random.randint(1000)}) # recover ASIN from url


    def parse(self, response): # parsing of product-reviews

        ASIN = response.meta['ASIN']  # 'B075XLWML4'

        try:
            if response.meta['first_page']:  # if this is a first page, get urls for next ones
                # get number of review to populate reviews_url
                num_review = response.xpath('//span[@data-hook="total-review-count"]/text()').extract_first()
                print("Number of reviews: ", num_review)
                print("Loading review pages...")
                # u'2,402'
                if num_review is not None:  # catch products with 0 reviews
                    num_review = int(num_review.replace(',', ''))
                    print("Cleaned num_review: ", num_review)
                    # add urls to queue
                    reviews_URL_list = ["https://www.amazon.com/product-reviews/" + ASIN +
                                    "/ref=cm_cr_arp_d_paging_btm_3?pageNumber=" + str(i) for i in
                                    range(2, (num_review // 10 + 2))]
                    print(reviews_URL_list)
                    # Example: if 178 reviews go till 18 (10 reviews per page)
                    with open('B00CDT4OR6_urls.txt', 'w+') as f:
                        for url in reviews_URL_list:
                            f.write(url + "\n")
                            redis_conn.sadd('reviews_URLs', url)

        except:
            num_review = 0

        reviews = response.xpath('//div[@data-hook="review"]')  # top node to use for all review elements
        for review in reviews:


            review_id = review.xpath('.//div[contains(@id, "customer_review")]/@id').extract_first()
            # 'customer_review-R3BLVOCJHX4BVZ'
            review_id=review_id.split('-')[1]

            review_title = review.xpath('.//a[@data-hook="review-title"]/text()').extract_first()

            review_rating = review.xpath('.//i[@data-hook="review-star-rating"]//text()').extract_first()
            # u'4.4 out of 5 stars'
            review_rating = float(review_rating.split(' ')[0])

            review_date = review.xpath('.//span[@data-hook="review-date"]//text()').extract_first()
            # u'on December 7, 2016'
            review_date = ' '.join(review_date.split(' ')[1:])  # 'December 7, 2016'
            review_date = datetime.strptime(review_date, '%B %d, %Y').strftime(
                '%x')  # convert to locale 08/16/1988 (en_US)

            review_body = review.xpath('.//span[@data-hook="review-body"]//text()').extract()
            review_body = ' '.join(review_body)

            item = Amazon2Item()
            item['review_id'] = review_id
            item['ASIN'] = ASIN
            item['review_title'] = review_title
            item['review_rating'] = review_rating
            item['review_date'] = review_date
            item['review_body'] = review_body

            yield item

