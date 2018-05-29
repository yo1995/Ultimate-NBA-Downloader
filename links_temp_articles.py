# -*- coding:utf-8 -*-


import urllib
import re
import http.cookiejar

from bs4 import BeautifulSoup
from urllib import request
import logging
log = logging.getLogger(__name__)


# to validate a title for csv file and Windows naming pattern, different approaches are needed.
def validate_name(title):
    res = r"[\/\\\:\*\?\"\<\>\|]"  # '/\:*?"<>|'
    new_title = re.sub(res, "", title)
    new_title = new_title.replace(",", "")
    new_title = new_title.replace('"', "'")
    return new_title


def strip_slash(slash_str):
    slash_str = slash_str.replace('/', '')
    return slash_str


class BRArticles(object):

    def __init__(self):
        self.cj = http.cookiejar.LWPCookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cj))
        urllib.request.install_opener(self.opener)

    @staticmethod
    def _get_headers():
        headers = {}
        headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36'
        headers['Host'] = 'bleacherreport.com'
        headers['Connection'] = 'keep-alive'
        headers['Cache-Control'] = 'max-age=0'
        headers['Accept-Language'] = 'zh-CN,zh;q=0.9,en;q=0.8,en-US;q=0.7'
        headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8'
        return headers

    def get_article_links(self, page_link, last_key_0, last_key_1, links_per_page):
        links_count = 0
        req = urllib.request.Request(page_link, headers=self._get_headers())
        response = self.opener.open(req)
        soup = BeautifulSoup(response.read(), "html.parser")
        archive_list = soup.find_all('ol', class_="archive-list")
        links_list = []
        titles_list = []
        articles_keys_list = []
        job_done_flag = False
        for li in archive_list:
            links = li.find_all('li')
            for link in links:
                current_link = link.find('a').get('href')
                current_title = link.find('a').contents[0]  # returns a list object, and choose the first element
                current_key = strip_slash(re.findall('/[1-9]\d*', current_link, re.I)[0])
                # print(current_title)
                if (current_key == last_key_0) or (current_key == last_key_1):
                    print('already reached last time record. job done!')
                    job_done_flag = True
                    break
                links_list.append(current_link)
                titles_list.append(validate_name(current_title))
                articles_keys_list.append(current_key)
                links_count = links_count + 1  # should be 25 each page. check to see if sth odd happens
        if links_count != links_per_page:
            print('might have reached the final to page or overall. is it page 360+?')
        return articles_keys_list, titles_list, links_list, job_done_flag


def links_temp(current_page, last_key_0, last_key_1, links_per_page):
    # base_link = 'http://bleacherreport.com/nba/archives/newest/1?filter=all'
    current_page_link = 'http://bleacherreport.com/nba/archives/newest/{page}?filter=all'.format(page=current_page)
    print('-----current page is: page ' + str(current_page) + '-----')
    article_links = BRArticles()
    keys_list, titles_list, links_list, job_done_flag = article_links.get_article_links(current_page_link, last_key_0, last_key_1, links_per_page)
    print(links_list)
    return keys_list, titles_list, links_list, job_done_flag

