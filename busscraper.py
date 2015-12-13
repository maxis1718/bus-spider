# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
from functional import seq
import requests
from datetime import datetime

def parse_bus_soup(rows):
    """ Parse bus rows to get the bus stop name and corresponding status

    Args:
        rows (list)
    Returns
        list
    """
    return seq(rows)\
        .map(lambda tr: seq(tr.select("td"))\
             .map(lambda td: td.text.strip())

def get_update_time(soup, now):
    """Extract the update time from the soup and convert it into the datetime.datetime format

    Args:
        soup (bs4.BeautifulSoup)
        now (datetime.datetime)
    Returns:
        datetime.datetime
    """
    text = soup.find(attrs={"class":"updatetime"}).get_text(strip=True)
    return datetime.strptime(text, '(更新時間：%H:%M:%S)').replace(now.year, now.month, now.day)

def get_bus_info(busnum):
    """Fetch and extract bus information given a bus number

    Args:
        busnum (str): The bus number in Taipei city

    Returns:
        dictionary: extracted information including
            1. inbound/outbound status (str)
            2. updatetime (datetime.datetime)
    """
    now = datetime.now()

    res = requests.get("http://pda.5284.com.tw/MQS/businfo2.jsp", params={"routename": busnum})
    soup = BeautifulSoup(res.text, "html.parser")

    info = {}

    tbl = soup.select("table > tr > td > table > tr")[1].select("> td ")
    inbound_tr = tbl[0].select("> table > tr")
    outbound_tr = tbl[1].select("> table > tr")

    info["inbound"] = parse_bus_soup(inbound_tr)
    info["outbound"] = parse_bus_soup(outbound_tr)

    info["updatetime"] = get_update_time(soup, now)

    return info
