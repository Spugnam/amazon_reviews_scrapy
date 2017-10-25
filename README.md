# Amazon Reviews scrapy

This project uses 2 separate scrapy instances. It would have been possible to have 2 spiders that share settings & pipelines but the current solution was faster to set up and more flexible to use.  
'amazonproducts' identifies products to scrape based on input category URLs ('Routers' or 'In-ear headphones' pages) and loads a PostgreSQL 'products' table hosted on an AWS RDS server. The products -identified by their ASIN (Amazon Standard Identification Number)- are also loaded into a Redis set.  
'amazon2' reads the ASINs to process in Redis queue and fills a second 'reviews' table in the PostgreSQL database.The 2 tables share ASIN as a foreign key. Several instances of the amazon2 scrapy can be run (locally or remotely), all feeding from the same Redis queue.  

The program leverage the scrapy.proxies package to rotate PIs.  
To use this program:  
 - select the start_urls to parse in amazonproducts_spider_py  
 - udpate all servers config in both setttings.py (PostgreSQL, Redis)  
 - create a txt file with IP addresses or remove the use of scrapy_proxies.RandomProxy in both settings.py  
