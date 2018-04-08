# _*_ coding: utf-8 _*_
__author__ = 'xuda'
__date__ = '2018/3/24 22:57'

from datetime import datetime
from elasticsearch_dsl import DocType, Date, Nested, Boolean, \
    analyzer, InnerObjectWrapper, Completion, Keyword, Text, Integer

from elasticsearch_dsl.analysis import CustomAnalyzer as _CustomAnalyzer

from elasticsearch_dsl.connections import connections

# 与服务器进行连接，允许多个
connections.create_connection(hosts=["localhost"])


# 解决建议的bug问题自定义分词器。
class CustomAnalyzer(_CustomAnalyzer):
    def get_analysis_definition(self):
        return {}


ik_analyzer = CustomAnalyzer("ik_max_word", filter=["lowercase"])


class ArticleType(DocType):
    # 新闻类型
    suggest = Completion(analyzer=ik_analyzer)
    title = Text(analyzer="ik_max_word")
    create_date = Text()
    url = Keyword()
    url_object_id = Keyword()
    content = Text(analyzer="ik_max_word")
    crawl_time = Date()

    class Meta:
        index = "jobbole"
        doc_type = "article"


if __name__ == "__main__":
    ArticleType.init()
