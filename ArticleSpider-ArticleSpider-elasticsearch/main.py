# encoding: utf-8
__author__ = 'xuda'
__date__ = '2018/3/23 0017 19:50'
from scrapy.cmdline import execute

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print(os.path.abspath(__file__))
# D:\CodeSpace\PythonProject\ArticleSpider\main.py

print(os.path.dirname(os.path.abspath(__file__)))
# D:\CodeSpace\PythonProject\ArticleSpider

# 调用execute函数执行scrapy命令，相当于在控制台cmd输入该命令
# 可以传递一个数组参数进来:
#常熟理工新闻网
# execute(["scrapy", "crawl" , "jobbole"])
#计算机科学与工程学院新闻网
execute(["scrapy", "crawl" , "csenews"])