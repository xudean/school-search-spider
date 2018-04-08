# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import  traceback

class ArticlespiderPipeline(object):
    def process_item(self, item, spider):
        return item


class ElasticSearchPipeline(object):
    # 将新闻数据写入到es中
    def process_item(self, item, spider):
        # 将item转换为es数据。
        item.save_to_es()
        return item
