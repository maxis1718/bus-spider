# -*- coding: utf-8 -*-

import threading
from urllib import request, parse
import datetime
import os
import time
import sched

BASE_URL = 'http://pda.5284.com.tw/MQS/businfo2.jsp?'
TEMP_DIR = 'pages'
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

def read_url(url, bus_num, now, result):
    print('Fetching %s ...' % (bus_num))
    start = time.time()
    data = ''
    error = {}
    try:
        data = request.urlopen(url).read()
    except URLError as err:
        # prevent from interupting the spider
        data = ''
        error = {'code': err.code, 'msg': err.reason, 'header': err.header}
    end = time.time()
    print('Fetched %s (%.3f sec)' % (bus_num, end-start))
    result.append({'bus_num':bus_num, 'url': url, 'page': data, 'date': now, 'error': error})

def fetch_parallel(urls, now):
    result = []
    threads = [threading.Thread(target=read_url, args=(url, bus_num, now, result)) for bus_num, url in urls]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return result

def save_to_files(result):
    for res in result:
        fn = '.'.join([res['bus_num'],res['date'].strftime("%Y-%m-%d_%H-%M-%S"),'html'])
        with open(os.path.join(TEMP_DIR, fn), 'wb') as fw:
            fw.write(res['page'])
            print('Saved %s' % (res['bus_num']))

def is_sleep_time(now, start=0, end=6):
    return now.hour >= start and now.hour <= end

def run_spider(bus_nums):
    now = datetime.datetime.now()
    if is_sleep_time(now):
        # ignore buses between 0 am to 6 am
        print('sleep time...zzZ')
        pass
    else:
        urls = map(lambda x: (x, BASE_URL+parse.urlencode({'routename': x})), bus_nums)
        result = fetch_parallel(urls, now)
        if not os.path.exists(TEMP_DIR):
            os.makedirs(TEMP_DIR)
        save_to_files(result)

if __name__ == '__main__':

    while True:
        s = sched.scheduler(time.time, time.sleep)
        s.enter(INTERVAL, 1, run_spider, argument=(bus_nums,))
        s.run()

