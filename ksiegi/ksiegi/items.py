# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

from scrapy import Item, Field


class KsiegiItem(Item):
    numerKsiegi = Field()
    polozenieDzialki = Field()
    wlascicielKsiegi = Field()
    dzialki = Field()
    errorMessage = Field()
    typKsiegi = Field()
    roszczeniaPrawaOgraniczeniaKsiegi = Field()
    hipotekaKsiegi = Field()
