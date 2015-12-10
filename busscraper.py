from bs4 import BeautifulSoup
from functional import seq
import requests

def parse_bus_soup(soup):
    return seq(soup)\
        .map(lambda tr: seq(tr.select("td"))\
             .map(lambda td: td.text.strip()))\
        .for_each(print)

def get_bus(busnum):
    res = requests.get("http://pda.5284.com.tw/MQS/businfo2.jsp", params={"routename": busnum})
    soup = BeautifulSoup(res.text, "html.parser")
    tbl = soup.select("table > tr > td > table > tr")[1].select("> td ")
    inbound_tr = tbl[0].select("> table > tr")
    outbound_tr = tbl[1].select("> table > tr")
    return parse_bus_soup(inbound_tr), parse_bus_soup(outbound_tr)

