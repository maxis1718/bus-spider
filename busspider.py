# -*- coding: utf-8 -*-

import requests
import datetime
import os
import time
import sched
from pathlib import Path
from bs4 import BeautifulSoup
import json
from functional import seq
from concurrent.futures import ThreadPoolExecutor
from collections import namedtuple
from lib import logtime
import arrow
import functional
from retry import retry
# from retry.api import retry_call

BASE_URL = 'http://pda.5284.com.tw/MQS/businfo2.jsp'
TEMP_DIR = Path('busarrival')
INTERVAL = 30
bus_nums = ['706', '857', '綠2右', '212', '793', '306', '307', '284', '270']

# entry: http://pda.5284.com.tw/MQS/businfo1.jsp
# route: http://pda.5284.com.tw/MQS/businfo2.jsp?routename=311%E5%8D%80

# 台北等公車最熱門路線前五名：
# 706 三峽-西門
# 857 淡海-板橋
# 307 撫遠街-板橋前站
# 綠2右 景美女中-中永和
# 793 樹林-木柵

import logging


def get_logger(logfile):
    logger = logging.getLogger('busspider')
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] - %(message)s')

    fh = logging.FileHandler(logfile)
    ch = logging.StreamHandler()
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)
    # logger = logging.getLogger()
    return logger


logger = get_logger('busspider.log')


def get_update_time(soup):
    """Extract the update time from the soup and convert it into the datetime.datetime format

    Args:
        soup (bs4.BeautifulSoup)
        now (datetime.datetime)
    Returns:
        arrow
    """
    now = arrow.now()
    text = soup.find(attrs={"class": "updatetime"})\
               .get_text(strip=True)
    updatetime = arrow.Arrow\
                      .strptime(text, '(更新時間：%H:%M:%S)')\
                      .replace(year=now.year, month=now.month, day=now.day)
    return updatetime


def extract_subroute(bus_id_tag):
    res = {}
    bus_subroute_tag = bus_id_tag.find('span')
    if bus_subroute_tag:
        bus_subroute_tag = bus_subroute_tag.extract()
        res['bus_subroute'] = bus_subroute_tag.text
    res['bus_id'] = bus_id_tag.text
    return res


def extract_busstop_info(td):
    return {
        'buses': [extract_subroute(bus_id_tag.extract()) for bus_id_tag in td.find_all('font')],
        'arrival_at': td.text}


def parse_bus_soup(rows):
    """ Parse bus rows to get the bus stop name and corresponding status

    Args:
        rows (list)
    Returns
        list
    """
    return seq(rows)\
        .map(lambda tr: tr.find_all('td'))\
        .map(lambda tds: {"stop": tds[0].text, **extract_busstop_info(tds[1])})


def extract_bus_info(text):
    soup = BeautifulSoup(text, "html.parser")
    tbl = soup.select("table > tr > td > table > tr")[1].select("> td ")
    inbound_tr = tbl[0].select("> table > tr")
    outbound_tr = tbl[1].select("> table > tr")

    businfo = {
        "inbound": parse_bus_soup(inbound_tr),
        "outbound": parse_bus_soup(outbound_tr),
        "updatetime": get_update_time(soup)
    }
    
    return businfo


@retry(tries=15, delay=1, logger=logger)
def crawl_bus_info(bus_num):
    businfo = {'bus_num': bus_num}

    res = requests.get(BASE_URL, params={'routename': bus_num})

    return {'bus_num': bus_num,  **extract_bus_info(res.text)}



@logtime(logger=logger)
def get_bus_info(bus_num):
    businfo = {'bus_num': bus_num, 'crawltime': arrow.now()}

    try:
        businfo.update(crawl_bus_info(bus_num))
    except (requests.exceptions.RequestException, Exception) as err:
        # prevent from interupting the spider
        businfo['error'] = str(err)

    return businfo


def fetch_parallel(urls, now):
    with ThreadPoolExecutor(max_workers=10) as e:
        return e.map(get_bus_info, urls)


def json_encoder_default(o):
    if isinstance(o, functional.pipeline.Sequence):
        return o.to_list()
    elif isinstance(o, arrow.arrow.Arrow):
        return o.format()
    else:
        return o


def save_to_files(result):
    for res in result:
        with (TEMP_DIR
              / res['bus_num']
              / (res['crawltime'].format('YYYY-MM-DD') + '.json')
              ).open('a') as f:
            print(json.dumps(res, default=json_encoder_default), file=f)
            # print('Saved %s' % (res['bus_num']))


def is_sleep_time(now, start=0, end=6):
    # return False
    return now.hour >= start and now.hour <= end


def run_spider(bus_nums):
    now = datetime.datetime.now()
    if is_sleep_time(now):
        # ignore buses between 0 am to 6 am
        print('sleep time...zzZ')
    else:
        result = fetch_parallel(bus_nums, now)
        save_to_files(result)

if __name__ == '__main__':
    for bus_num in bus_nums:
        dest = TEMP_DIR / bus_num
        if not dest.is_dir():
            dest.mkdir(parents=True)

    while True:
        # run_spider(bus_nums)
        # time.sleep(30)
        s = sched.scheduler(time.time, time.sleep)
        s.enter(INTERVAL, 30, run_spider, argument=(bus_nums,))
        s.run()


