# -*- coding:utf-8 -*-

__author__ = 'cht'
'''
Bleacher Report NBA photo downloader

thoughts: 
- 传入单一图片链接地址，打开图片并下载，读取图片像素尺寸如果过小则删除，足够大则保留
- try to make this function atomic. that is to say, it only downloads and does nothing else.
- return - True: successfully downloaded or exists; False: failed to download due to different reasons.
credits:
- https://www.zhihu.com/question/64477438/answer/224824535
- https://stackoverflow.com/questions/7391945/how-do-i-read-image-data-from-a-url-in-python
'''


import re
import requests
import time
import os
import sys
from io import BytesIO
from PIL import Image
import logging
log = logging.getLogger(__name__)


def strip_slash(slash_str):
    slash_str = slash_str.replace('/', '')
    return slash_str


def validate_name(title):
    res = r"[\/\\\:\*\?\"\<\>\|]"  # '/\:*?"<>|'
    new_title = re.sub(res, "", title)
    new_title = new_title.replace('jpeg', 'jpg')
    return new_title


def _get_headers():
    headers = {}
    headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36'
    headers['Host'] = 'bleacherreport.com'
    headers['Connection'] = 'keep-alive'
    headers['Cache-Control'] = 'no-cache'
    headers['Accept-Language'] = 'zh-CN,zh;q=0.9,en;q=0.8,en-US;q=0.7'
    headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8'
    # headers['Referer'] = ''
    headers["Upgrade-Insecure-Requests"] = '1'
    return headers


def check_n_save_pictures(article_key, picture_link, picture_index, path, ignore_small=True):
    # 最基本的情况；crop在前面；fullimage；其他网站
    append_suffix = '?h=10000&w=10000'  # assume the largest pictures wont exceed 10k*10k pixels.
    picture_url = re.search(r'http(.+?)jpg(.*?)', picture_link).group(0)
    alternative_url = picture_url
    res1 = 'crop_[a-zA-Z]+'  # find the crop_north or else in the link
    temp1_url = re.sub(res1, "crop_exact", picture_url)
    temp2_url = re.sub(res1, "crop_exact_full_image", picture_url)
    if 'bleacherreport' not in picture_url:
        # not a BR photo. try my best to resolve it.
        print('not a BR photo. try anyway.')
    else:
        picture_url = temp1_url + append_suffix
        alternative_url = temp2_url + append_suffix

    file_name = temp1_url[temp1_url.rindex("/")+1:]
    res2 = '(.+?)(jpg|jpeg)'
    file_name = re.search(res2, file_name, re.I).group(0)
    file_name = validate_name(file_name)
    # print(file_name)
    # print(picture_url)
    path_of_picture = path + '/' + '[' + article_key + ']' + '(' + str(picture_index) + ')' + validate_name(file_name)
    if os.path.isfile(path_of_picture):
        warn_message = 'article [' + article_key + '] pic # ' + str(picture_index) + ' already exist.'
        print(warn_message)
        log.warning(warn_message)
        return True
    # handle the request of the link
    try:
        response = requests.get(picture_url, _get_headers())
    except (requests.exceptions.Timeout, requests.exceptions.ConnectTimeout):
        print('timeout occurred. just wait like 3 seconds and try again')
        try:
            time.sleep(3)
            response = requests.get(picture_url, _get_headers())
        except requests.exceptions.RequestException:
            err_message = 'Timeout. 臣妾真的努力了，还是超时实在拿不到图片啊嘤嘤嘤 TAT'
            sys.stderr.write(err_message)
            log.error('article [' + article_key + '] pic #' + str(picture_index) + err_message)
            return False
    except (requests.exceptions.HTTPError, requests.exceptions.ConnectionError):
        try:
            response = requests.get(alternative_url, _get_headers())
        except requests.exceptions.RequestException:
            err_message = 'HTTPError or ConnectionError. check your connectivity. being banned?!'
            sys.stderr.write(err_message)
            log.error('article [' + article_key + '] pic #' + str(picture_index) + err_message)
            return False

    try:
        im = Image.open(BytesIO(response.content))
    except IOError:
        err_message = 'Error! IOError, check your connectivity or disk status.'
        sys.stderr.write(err_message)
        log.error('article [' + article_key + '] pic #' + str(picture_index) + err_message)
        return False  # returning False will cause the main program stop. not sure if it is the best practice.
    # print(im.format, im.size, im.mode)

    if ignore_small:  # flag to save smaller pictures
        if im.size[0] < 1279 or im.size[1] < 799:
            # forfeit the picture
            print('the picture is too small. just abandon it.')
        else:
            # save the picture
            with open(path_of_picture, 'wb') as picture:
                picture.write(response.content)
            # return True means the pic is successfully downloaded.
            return True
    else:
        with open(path_of_picture, 'wb') as picture:
            picture.write(response.content)
        # return True means the pic is successfully downloaded.
        return True
