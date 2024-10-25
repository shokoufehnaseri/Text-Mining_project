# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class BookingScraperItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass

class BookingItem(scrapy.Item):
    name = scrapy.Field()
    address = scrapy.Field()
    rating = scrapy.Field()
    rating1 = scrapy.Field()
    rating2 = scrapy.Field()
    rating3 = scrapy.Field()
    rating4 = scrapy.Field()
    rating5 = scrapy.Field()
    price = scrapy.Field()
