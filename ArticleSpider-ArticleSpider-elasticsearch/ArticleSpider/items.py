# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html
import datetime
import pickle
import re

from ArticleSpider.settings import SQL_DATETIME_FORMAT
from ArticleSpider.utils.common import extract_num
import scrapy
from scrapy.loader import ItemLoader
from scrapy.loader.processors import TakeFirst, MapCompose, Join
from w3lib.html import remove_tags
from ArticleSpider.models.es_jobbole import ArticleType
from elasticsearch_dsl.connections import connections
# 与es进行连接生成搜索建议
es_article = connections.create_connection(ArticleType._doc_type.using)

# redis实现抓取数据同步显示
import redis
redis_cli = redis.StrictRedis()
## 设置数据初始值
JOB_COUNT_INIT = 161042
ZHIHU_COUNT_INIT = 173057
JOBBOLE_COUNT_INIT = 5003



class ArticlespiderItem(scrapy.Item):
    pass


def gen_suggests(es_con,index, info_tuple):
    es = es_con
    # 根据字符串生成搜索建议数组
    used_words = set()
    # 去重以先来的为主
    suggests = []
    for text, weight in info_tuple:
        if text:
            # 调用es的analyze接口分析字符串：分词并做大小写的转换
            words = es.indices.analyze(index=index, body=text, params={'filter':["lowercase"]})
            # words = es.indices.analyze(index=index, body=text, params={'filter': ["lowercase"]})
            anylyzed_words = set([r["token"] for r in words["tokens"] if len(r["token"])>1])
            new_words = anylyzed_words - used_words
        else:
            new_words = set()

        if new_words:
            suggests.append({"input":list(new_words), "weight":weight})

    return suggests


# 字符串转换时间方法
def date_convert(value):
    try:
        value.strip().replace("·", "").strip()
        create_date = datetime.datetime.strptime(value, "%Y/%m/%d").date()
    except Exception as e:
        create_date = datetime.datetime.now().date()

    return create_date


# 获取字符串内数字方法
def get_nums(value):
    match_re = re.match(".*?(\d+).*", value)
    if match_re:
        nums = int(match_re.group(1))
    else:
        nums = 0

    return nums


# 去除标签中提取的评论方法
def remove_comment_tags(value):
    if "评论" in value:
        return ""
    else:
        return value


# 直接获取值方法
def return_value(value):
    return value

# 排除none值


def exclude_none(value):
    if value:
        return value
    else:
        value = "无"
        return value

# 自定义itemloader实现默认取第一个值


class ArticleItemLoader(ItemLoader):
    default_output_processor = TakeFirst()


# 常熟理工新闻网items类
class JobBoleArticleItem(scrapy.Item):
    title = scrapy.Field()
    create_date = scrapy.Field()
    url = scrapy.Field()
    url_object_id = scrapy.Field()
    content = scrapy.Field()
    crawl_time = scrapy.Field()

    def make_data_clean(self):
        # 对日期格式进行清洗，提取出日期
        #                 来源：本站 作者：钱诚 发布时间：
        #                 2018年04月03日16时27分                        浏览次数：44
        new_str = self["create_date"].strip().replace("·", "").strip()
        minute_index = new_str.find("分")
        year_index = new_str.find("年")
        # 2018年03月22日16时10分
        self["create_date"] = new_str[year_index - 4:minute_index + 1]

    # 保存常熟理工新闻网新闻到es中
    def save_to_es(self):
        self.make_data_clean()
        article = ArticleType()
        article.title = self['title']
        article.create_date = self["create_date"]
        article.content = remove_tags(self["content"])
        article.url = self["url"]
        article.meta.id = self["url_object_id"]

        # 在保存数据时便传入suggest
        article.suggest = gen_suggests(es_article,ArticleType._doc_type.index, ((article.title, 10), (article.content, 3)))
        if redis_cli.get("jobbole_count"):
            jobbole_count = pickle.loads(redis_cli.get("jobbole_count"))
            jobbole_count = jobbole_count + 1
            jobbole_count = pickle.dumps(jobbole_count)
            redis_cli.set("jobbole_count", jobbole_count)
        else:
            jobbole_count = pickle.dumps(JOBBOLE_COUNT_INIT)
            redis_cli.set("jobbole_count",jobbole_count)
        article.save()



def remove_splash(value):
    # 去掉工作城市的斜线
    return value.replace("/", "")



