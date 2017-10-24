import scrapy
from twisted.internet import reactor
from scrapy.crawler import CrawlerRunner

from amazon2.spiders.amazon2_spider import Amazon2Spider
#from amazon2.spiders.amazon2_spider import Amazon2Spider

#settings = get_project_settings()
#runner = CrawlerRunner(settings)

runner = CrawlerRunner()
runner.crawl(Amazon2Spider)
#runner.crawl(MySpider2)
d = runner.join()
d.addBoth(lambda _: reactor.stop())

reactor.run()