# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

from datetime import datetime
from scrapy.exceptions import DropItem
from scrapy.exporters import CsvItemExporter
import redis
from amazonproducts import settings


import psycopg2

# Open Redis connection
print("Opening Redis connection")
redis_conn = redis.StrictRedis(host=settings.redis_host,
                               port=settings.redis_port,
                               db=settings.redis_db)


class WriteItemPipeline(object):

    def __init__(self):
        self.filename = str(datetime.now()) + 'Amazon_products.csv'

        print("Opening AWS RDS (PostgreSQL) connection")
        try:
            self.connection = psycopg2.connect(**settings.DATABASE)
            self.cursor = self.connection.cursor()
        except Exception as error:
            print("=" * 30)
            print("Connection Error: %s" % error)


    def open_spider(self, spider):
        self.csvfile = open(self.filename, 'wb')
        self.exporter = CsvItemExporter(self.csvfile)
        self.exporter.start_exporting()

    def close_spider(self, spider):
        self.exporter.finish_exporting()
        self.csvfile.close()
        if self.connection is not None:
            print("=" * 30)
            print("Closing connection: %s" % self.connection)
            self.connection.close()

    def process_item(self, item, spider):

        out = redis_conn.sadd('ASINs', item['ASIN'])
        if out != 0:
            self.exporter.export_item(item)  # don't print duplicates to file
            try:
                self.cursor.execute(
                    """INSERT INTO products (asin, category, company, product_desc, num_review, rating) VALUES(%s, %s, %s, %s, %s, %s)""",
                    (item['ASIN'], item['category'], item['company'], item['product_desc'], item['num_review'],
                     item['rating'],))
                self.connection.commit()
            except psycopg2.DatabaseError as error:
                self.connection.rollback()
                print("=" * 30)
                print("DatabaseError: %s" % error)
                print(item['ASIN'], item['category'], item['company'], item['num_review'], item['rating'],
                      item['product_desc'])
        else:
            print("Already present: ", item['ASIN'])
        return item

