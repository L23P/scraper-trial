from lxml.html import fromstring
from itertools import cycle
from bs4 import BeautifulSoup
import requests
import logging
import time


def make_request(session, proxy, baseurl: str, asin: str):
    try:
        response = session.get(baseurl + asin, proxies={"http": proxy, "https": proxy})
    except requests.RequestException:
        logging.warning(f"HTTP Error for {asin}")
        return
    if response.status_code == 200:
        return response, asin

def http_client():
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                          " AppleWebKit/537.36 (KHTML, like Gecko)"
                          "Chrome/74.0.3729.157 Safari/537.36"
        }
    )

    def log_url(res, *args, **kwargs):
        logging.info(f"{res.url}, {res.status_code}")

    session.hooks["response"] = log_url
    return session

session = http_client()
proxy = '163.116.177.49:808'
baseurl = 'https://www.amazon.co.uk/dp/'
asin = 'B0864F9N3X'

results = []

html = make_request(session, proxy, baseurl, asin)
if html is None:
    logging.info("passing due to make_request error")
else:
    print(results.json())
    time.sleep(3)
