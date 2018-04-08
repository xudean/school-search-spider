# -*- coding: utf-8 -*-
import datetime
import re

import scrapy
from scrapy.http import Request

from urllib import parse

from ArticleSpider.items import JobBoleArticleItem, ArticleItemLoader
from ArticleSpider.utils.common import get_md5
from scrapy.loader import ItemLoader
from scrapy.xlib.pydispatch import dispatcher
from scrapy import signals


class JobboleSpider(scrapy.Spider):
    name = "jobbole"
    allowed_domains = ["news.cslg.edu.cn"]
    start_urls = ['http://news.cslg.edu.cn/Index/newslist/id/17/p/202.html']

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
            yield Request(url=parse.urljoin("http://news.cslg.edu.cn", post_node),  callback=self.parse_detail)

        # 提取下一页并交给scrapy进行下载
        page_urls = response.css("a[href$='.html']::attr(href)").extract()
        next_url = page_urls[len(page_urls)-2]
        # 如果.next .pagenumber 是指两个class为层级关系。而不加空格为同一个标签
        if next_url:
            # 如果还有next url 就调用下载下一页，回调parse函数找出下一页的url。
            yield Request(url=parse.urljoin("http://news.cslg.edu.cn", next_url), callback=self.parse)

    def parse_detail(self, response):
        # 实例化
        article_item = JobBoleArticleItem()

        # 通过item loader加载item
        item_loader = ArticleItemLoader(item=JobBoleArticleItem(), response=response)
        if response.url.find("/Index/newslist") or response.url.find("/index"):
            # 通过css选择器将后面的指定规则进行解析。
            item_loader.add_css("title", ".article-title::text")
            item_loader.add_value("url", response.url)
            item_loader.add_value("url_object_id", get_md5(response.url))
            item_loader.add_css("create_date", "#date-topic::text")
            item_loader.add_css("content", ".article-content")

            # 调用这个方法来对规则进行解析生成item对象
            article_item = item_loader.load_item()
        else:
            item_loader.add_css("title", "title::text")
            item_loader.add_value("url", response.url)
            item_loader.add_value("url_object_id", get_md5(response.url))
            item_loader.add_css("create_date", "title::text")
            item_loader.add_css("content", "body::text")
        # 已经填充好了值调用yield传输至pipeline
        yield article_item

