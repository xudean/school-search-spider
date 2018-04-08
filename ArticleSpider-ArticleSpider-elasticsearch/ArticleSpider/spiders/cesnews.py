# -*- coding: utf-8 -*-
import datetime
import re

import scrapy
from scrapy.http import Request

# python3中当url不完整时的解决
from urllib import parse
# Python2中url不完整的解决
# import urlparse
from selenium import webdriver

from ArticleSpider.items import JobBoleArticleItem, ArticleItemLoader
from ArticleSpider.utils.common import get_md5
from scrapy.loader import ItemLoader
from scrapy.xlib.pydispatch import dispatcher
from scrapy import signals


class CseNewsSpider(scrapy.Spider):
    name = "csenews"
    allowed_domains = ["http://web.cse.cslg.cn/"]
    start_urls = ['http://web.cse.cslg.cn/index.php/Index/newslist/id/6/p/1.html']

    # 收集新闻网所有404的url以及404页面数
    handle_httpstatus_list = [404]

    def __init__(self,**kwargs):
        self.fail_urls = []
        dispatcher.connect(self.handle_spider_cosed, signals.spider_closed)

    def handle_spider_cosed(self, spider, reason):
        self.crawler.stats.set_value("failed_urls", ",".join(self.fail_urls))
        pass

    def parse(self, response):
        """
        1. 获取文章列表页中的文章url交给scrapy下载并进行解析
        2. 获取下一页的url并交给scrapy进行下载,  下载完成后交给parse
        """
        # 如果状态值为404
        if response.status == 404:
            # 如果状态值为404那就填充一些任意值，以防止后面抛出异常
            item_loader = ArticleItemLoader(item=JobBoleArticleItem(), response=response)
            item_loader.add_value("title", "null")
            item_loader.add_value("url", response.url)
            item_loader.add_value("url_object_id", get_md5(response.url))
            item_loader.add_value("create_date", "null")
            item_loader.add_value("content", "null")
            self.fail_urls.append(response.url)
            self.crawler.stats.inc_value("failed_url")
            article_item = item_loader.load_item()
            yield article_item

        # 解析列表页中的所有新闻url并交给scrapy下载后并进行解析
        # 不使用extra成值的list可以进行二次筛选
        # post_urls = response.css("#archive .floated-thumb .post-thumb a::attr(href)").extract()
        post_nodes = response.css(".mst0 a::attr(href)").extract()
        for post_node in post_nodes:
            yield Request(url=parse.urljoin("http://web.cse.cslg.cn", post_node),  callback=self.parse_detail,dont_filter=True)
        # 提取下一页并交给scrapy进行下载
        page_urls = response.css("a[href$='.html']::attr(href)").extract()
        next_url = page_urls[len(page_urls)-2]
        if next_url:
            # 如果还有next url 就调用下载下一页，回调parse函数找出下一页的url。
            yield Request(url=parse.urljoin("http://web.cse.cslg.cn", next_url), callback=self.parse,dont_filter=True)


