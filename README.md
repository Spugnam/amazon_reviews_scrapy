# Amazon Reviews scrapy

P

This project uses 2 separate scrapy instances. It would have been possible to have 2 spiders that share settings & pipelines but the current solution was faster to set up and more flexible to use.
The first program identifies products to scrape based on input category URLs ('Routers' or 'In-ear headphones' pages) and loads a PostgreSQL 'products' table hosted on an AWS RDS server. The products -identified by their ASIN (Amazon Standard Identification Number)- are also loaded into a Redis set.
The second program reads the ASINs to process in Redis and fills a second 'reviews' table. The tables share ASIN as a foreign key. Several instances of the reviews scrapy can be run (locally or remotely).
