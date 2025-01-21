# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy

class BookingItem(scrapy.Item):
    name = scrapy.Field()
    address = scrapy.Field()
    #city = scrapy.Field()
    rating = scrapy.Field()
    rating1 = scrapy.Field()
    rating2 = scrapy.Field()
    rating3 = scrapy.Field()
    rating4 = scrapy.Field()
    rating5 = scrapy.Field()
    price = scrapy.Field()
    pos_reviews = scrapy.Field()
    neg_reviews = scrapy.Field()
