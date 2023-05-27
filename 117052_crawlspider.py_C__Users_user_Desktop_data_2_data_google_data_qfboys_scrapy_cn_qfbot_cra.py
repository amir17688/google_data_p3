#!/usr/bin/env python
# encoding: utf-8
# vim: set et sw=4 ts=4 sts=4 fenc=utf-8
# Author: YuanLin

"""Crawl Parsing script.
   Parse data form html format.
"""

from scrapy.spider import Spider
from scrapy.http import Request
from scrapy.selector import Selector
from scrapy import log

from ..items import CrawlItem

class ListSpider(Spider):
    """To build linkbase"""

    def __init__(self, name):
       self.name = name

    def parse(self, response):
        doc = Selector(response)
        item = CrawlItem()
        section = doc.xpath("//li[@class='subject-item']")
        for sect in section:
            pass

class DetailSpider(Spider):
    """To crawl linkbase"""
    def __init__(self, name):
        self.name = name

    def parse(self, response):
        pass
