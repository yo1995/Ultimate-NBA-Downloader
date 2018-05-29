# -*- coding:utf-8 -*-

__author__ = 'cht'
'''
Bleacher Report NBA photo downloader

thoughts: 
- 自适应地从各类文章链接中获取所有相关图片。主要找主段落分栏的图片
credits:
- https://stackoverflow.com/questions/19351541/excluding-unwanted-results-of-findall-using-beautifulsoup
- https://cuiqingcai.com/1319.html
'''


import urllib
from bs4 import BeautifulSoup
from urllib import request
import logging
log = logging.getLogger(__name__)


def _get_headers():
    headers = {}
    headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36'
    headers['Host'] = 'bleacherreport.com'
    headers['Connection'] = 'keep-alive'
    headers['Cache-Control'] = 'max-age=0'
    headers['Accept-Language'] = 'zh-CN,zh;q=0.9,en;q=0.8,en-US;q=0.7'
    headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8'
    return headers


def get_picture_links(single_article_key, single_article_title, single_article_link):
    req = urllib.request.Request(single_article_link, headers=_get_headers())
    response = urllib.request.urlopen(req)
    soup = BeautifulSoup(response.read(), "html.parser")
    main_div = soup.find_all('div', class_="contentStream")[0]  # the first with cS class is the main body.
    links_set = main_div.find_all('img', class_='lazyImage')
    picture_links_count = 0
    picture_links_list = []
    for pic in links_set:
        # at here I used a fragile condition which could CAUSE PROBLEMS!!!
        # there is a case that in an article, a video list exists, hence
        # the carousel contains irrelevant pictures.
        # to get rid of them, I exclude the photos with less than 300px in height,
        # which by default the thumb for video is 288px in height.

        # the best approach should be selecting the wanted divisions in cascade fashion.
        # here I just used a brutal and not responsive method. >_<
        if int(pic.get('width')) < 300:
            continue
        pic_link = pic.get('src')
        picture_links_count = picture_links_count + 1
        picture_links_list.append(pic_link)
        # print(pic_link)
    # print(links_count)
    return picture_links_list, picture_links_count, single_article_key, single_article_title

