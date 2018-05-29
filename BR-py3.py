# -*- coding:utf-8 -*-

__author__ = 'cht'
'''
 Bleacher Report NBA photo downloader
credits: 
- https://blog.csdn.net/junbujianwpl/article/details/73194846
- http://www.cnblogs.com/mayi0312/p/6840931.html
- https://docs.python.org/3/library/csv.html#csv.DictReader
- https://www.cnblogs.com/jiaxin359/p/7324077.html
- https://stackoverflow.com/questions/15727420/using-python-logging-in-multiple-modules
'''

import sys
import re
import os
import time
import csv
import multiprocessing

from links_temp_articles import links_temp
from download_pic_threading import MyThread
from get_picture_links import get_picture_links
from check_n_save_picture import check_n_save_pictures
from smtp_notifier import send_mail

import logging
logging.basicConfig(filename='BR.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)


def replace_quote(quote_str):
    quote_str = quote_str.replace('"', "'")
    return quote_str


def strip_tag(tag_str):
    dr = re.compile(r'</?\w+[^>]*>', re.S)
    tag_str = re.sub(dr, '', tag_str)
    tag_str.replace(' ', '')
    return tag_str


def strip_slash(slash_str):
    slash_str.replace('/', '')
    return slash_str


def main():
    # 0. global variables definition
    host = 'http://bleacherreport.com'
    # the database for links, csv files
    links_all_filename = 'links_all'
    picture_links_all_filename = 'pics_all'
    file_length_threshold = 1000
    picture_download_timeout = 30  # in seconds, 30 in GFW should be ok
    BR_save_path = 'C:/Users/yo-ch/Desktop/BR'
    if not os.path.exists(BR_save_path):
        os.makedirs(BR_save_path)
    # if you want to exclude pictures with dimensions less than 1280*800, use True. otherwise False.
    ignore_small = True
    # Timeout, HTTPError/IOError/Timeout could happen. if you want to ignore those errors and continue,
    # please use True. if you want to assert the program to stop at errors, use False.
    ignore_download_errors = True
    send_email_report = False
    # links per archive page
    links_per_page = 25
    # by default to be 1, but you can choose which page to start from. useful when manually downloads from certain page.
    from_page_number = 352
    # by default it wont be reached. use only if you want to manually stop at certain page.
    to_page_number = 360  # 360 is always a good guess for the largest page number.
    if to_page_number < from_page_number:
        err_message = 'Error! page range cannot be negative. check your settings!'
        sys.stderr.write(err_message)
        log.error(err_message)
        return -1
    # now time indicator, to record time stamp of an execution.
    now_time = time.strftime('%Y-%m-%d %H:%M', time.localtime(time.time()))
    eight_digit_YMD = time.strftime('%Y%m%d', time.localtime(time.time()))
    # create the pool
    pool1 = multiprocessing.Pool(processes=4)
    # create a full list to store all temps and save to file after finished
    keys_full_list = []
    titles_full_list = []
    article_links_full_list = []
    picture_links_full_list = []

    # 1. here we go!
    print('1. start to parse the links.')
    with open(links_all_filename + '.csv', 'r', encoding='UTF-8') as csv_file:
        reader = csv.DictReader(csv_file, dialect="excel", quoting=csv.QUOTE_NONNUMERIC)
        old_rows = [row for row in reader]
    # !!!after update if exceeding 1000 create another file and rename
    print('Until today, ' + now_time + ', the # of links scraped from BR/nba is: ' + str(len(old_rows)))
    # by default, if we meet last_key_0 or last_key_1 or reach to_page_number, we stop. still will stop out of bounds
    last_key_0 = old_rows[0]['id']
    last_key_1 = old_rows[1]['id']
    # use two keys to ensure no infinite loop!
    print('starts to scrap the new ones. last one was: ' + last_key_0 + ', last second was: ' + last_key_1)

    # 2. the majestic part
    current_page = from_page_number
    while current_page < to_page_number:
        threads = []  # clear the threads to ensure nothing unwanted happens
        keys_list, titles_list, links_list, job_done_flag = links_temp(current_page, last_key_0, last_key_1, links_per_page)
        assert (len(keys_list) == len(titles_list) == len(links_list))  # if not equal, ugly.
        # store the temps in time-descending order (from newest to oldest before last_key_1)
        keys_full_list.extend(keys_list)
        titles_full_list.extend(titles_list)
        article_links_full_list.extend(links_list)
        # 下面开始多线程加载当前links_list中的图片
        for i in range(len(links_list)):
            t = MyThread(get_picture_links, args=(keys_list[i], titles_list[i], host + links_list[i]))
            threads.append(t)
            t.start()
        for t in threads:
            t.join()  # wait until all threads finish or crush, worst case is linear exec.
            picture_links_list, picture_links_count, article_key, single_article_title = t.get_result()
            picture_links_full_list.extend(picture_links_list)  # just gather the src for further convenience
            if picture_links_count < 7:
                # put into big pool
                path = BR_save_path + '/' + eight_digit_YMD
                print('Pictures amount in article[' + article_key + '] is less than 7, dive into HUGE POOL!! Yay!')
            else:
                path = BR_save_path + '/' + eight_digit_YMD + '/' + '[' + article_key + ']' + single_article_title
                print('Pictures amount in article[' + article_key + '] exceeded 7, will create a folder for it.')
            if not os.path.exists(path):
                os.makedirs(path)
            for i in range(picture_links_count):  # 0~6
                # I don't want to pass all the args as a list. so I gave up the chunking performance edge.
                download_status_flag = pool1.apply_async(check_n_save_pictures, args=(
                    article_key, picture_links_list[i], (i + 1), path, ignore_small)).get(picture_download_timeout)
                # this part need to be polished.
                assert(download_status_flag or ignore_download_errors)  # both False abort the main program
        if job_done_flag:
            print('already reached last time record. job done!')
            break
        current_page = current_page + 1

    # 3. wrap-up part
    # write files
    # first, dump the source link for pictures into pic_all.csv
    with open(picture_links_all_filename + '.csv', 'a', encoding='UTF-8', newline="") as csv_file:
        writer = csv.writer(csv_file, dialect="excel", quoting=csv.QUOTE_NONNUMERIC)
        for i in range(len(picture_links_full_list)):
            writer.writerow([picture_links_full_list[i]])  # turn the string into a list object
    # second, write the links_all.csv with attention
    if len(article_links_full_list) + len(old_rows) > file_length_threshold:
        # directly write into a new file, and change the previous filename with date.
        os.rename(links_all_filename + '.csv', links_all_filename + '_archived_at_' + eight_digit_YMD + '.csv')
        with open(links_all_filename + '.csv', 'a', encoding='UTF-8', newline="") as csv_file:
            fieldnames = ["id", "title", "link"]
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames, dialect="excel", quoting=csv.QUOTE_NONNUMERIC)
            writer.writeheader()
            for i in range(len(article_links_full_list)):
                writer.writerow(
                    {'id': keys_full_list[i], 'title': titles_full_list[i], 'link': article_links_full_list[i]})
    else:
        # append to existing file
        with open(links_all_filename + '.csv', 'w', encoding='UTF-8', newline="") as csv_file:
            fieldnames = ["id", "title", "link"]
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames, dialect="excel", quoting=csv.QUOTE_NONNUMERIC)
            writer.writeheader()
            for i in range(len(article_links_full_list)):
                writer.writerow(
                    {'id': keys_full_list[i], 'title': titles_full_list[i], 'link': article_links_full_list[i]})
            for i in range(len(old_rows)):
                writer.writerow(old_rows[i])
    # summarize todays pictures
    pictures_count = 0
    max_picture_size = 0
    min_picture_size = 12.34
    total_size = 0
    for dir_path, dir_names, files in os.walk(BR_save_path + '/' + eight_digit_YMD):
        for filename in files:
            path = os.path.join(dir_path, filename)
            if filename.endswith('jpg') or filename.endswith('jpeg'):
                pictures_count += 1
                file_size = os.path.getsize(path)
                file_size = file_size / float(1024 * 1024)
                total_size = total_size + file_size
                max_picture_size = max(round(file_size, 2), max_picture_size)
                min_picture_size = min(round(file_size, 2), min_picture_size)

    # 4. logging to save status
    summary_info = 'there are ' + str(pictures_count) + ' pictures in today download'
    summary_info_max_file_size = 'the maximum file is: ' + str(max_picture_size) + 'MB'
    summary_info_min_file_size = 'the minimum file is: ' + str(min_picture_size) + 'MB'
    summary_info_total_size = 'the total file size is: ' + str(round(total_size, 2)) + 'MB'
    summary_info_mail = summary_info + '\n' + summary_info_max_file_size + '\n' + summary_info_min_file_size + '\n' + summary_info_total_size
    log.info(summary_info + ', ' + summary_info_max_file_size + ', ' + summary_info_min_file_size + ', ' + summary_info_total_size)
    print(summary_info)
    print(summary_info_max_file_size)
    print(summary_info_min_file_size)
    # heh heh heh
    if min_picture_size > 5:
        print('Wow! seems your crops today are heavy!')
    # send notification mail if needed
    if send_email_report:
        send_mail('mailfrom', 'pwd', 'mailto', 'mailserver', "日常BR抓图情况报告", 465, summary_info_mail)
    # clean-up and close the pool!
    pool1.close()
    pool1.join()


if __name__ == '__main__':
    main()
