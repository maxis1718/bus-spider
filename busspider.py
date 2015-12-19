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
import  functional


BASE_URL = 'http://pda.5284.com.tw/MQS/businfo2.jsp'
TEMP_DIR = Path('busarrival')
INTERVAL = 5
bus_nums = ['706', '857', '綠2右', '212', '793', '306', '307', '284', '270']

# entry: http://pda.5284.com.tw/MQS/businfo1.jsp
# route: http://pda.5284.com.tw/MQS/businfo2.jsp?routename=311%E5%8D%80

# 台北等公車最熱門路線前五名：
# 706 三峽-西門
# 857 淡海-板橋
# 307 撫遠街-板橋前站
# 綠2右 景美女中-中永和
# 793 樹林-木柵




# FetchRes = namedtuple('FetchRes', 'busnum, url, page, date, error')



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


def parse_bus_soup(rows):
    """ Parse bus rows to get the bus stop name and corresponding status

    Args:
        rows (list)
    Returns
        list
    """
    return seq(rows)\
        .map(lambda tr: seq(tr.select("td"))
             .map(lambda td: td.text.strip())
             ).map(lambda tds: {"stop": tds[0], "arrival_time": tds[1]})


@logtime()
def get_bus_info(bus_num):
    info = {'bus_num': bus_num}

    try:
        res = requests.get(BASE_URL, params={'routename': bus_num})
    except requests.exceptions.RequestException as err:
        # prevent from interupting the spider
        info['error'] = str(err)
        return info

    soup = BeautifulSoup(res.text, "html.parser")
    tbl = soup.select("table > tr > td > table > tr")[1].select("> td ")
    inbound_tr = tbl[0].select("> table > tr")
    outbound_tr = tbl[1].select("> table > tr")

    info["inbound"] = parse_bus_soup(inbound_tr)
    info["outbound"] = parse_bus_soup(outbound_tr)
    info["time"] = get_update_time(soup)

    return info


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
              / (res['time'].format('YYYY-MM-DD') + '.json')
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
        run_spider(bus_nums)
        time.sleep(1)
        # s = sched.scheduler(time.time, time.sleep)
        # s.enter(INTERVAL, 1, run_spider, argument=(bus_nums,))
        # s.run()
