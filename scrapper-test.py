from lxml.html import fromstring
from itertools import cycle
from bs4 import BeautifulSoup
import traceback
import random
import requests
import csv
import logging
import time

USER_AGENT_SCRAPER_BASE_URL = 'http://www.useragentstring.com/pages/useragentstring.php?name='

POPULAR_BROWSERS = ['Chrome', 'Firefox', 'Mozilla', 'Safari', 'Opera', 'Opera Mini', 'Edge', 'Internet Explorer']

def get_user_agent_strings_for_this_browser(browser):
    """
    Get the latest User-Agent strings of the given Browser
    :param browser: string of given Browser
    :return: list of User agents of the given Browser
    """
    url = USER_AGENT_SCRAPER_BASE_URL + browser
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    user_agent_links = soup.find('div', {'id': 'liste'}).findAll('a')[:20]

    return [str(user_agent.text) for user_agent in user_agent_links]

def get_user_agents():
    """
    Gather a list of some active User-Agent strings from
    http://www.useragentstring.com of some of the Popular Browsers
    :return: list of User-Agent strings
    """
    user_agents = []
    for browser in POPULAR_BROWSERS:
        user_agents.extend(get_user_agent_strings_for_this_browser(browser))
    return user_agents[3:] # Remove the first 3 Google Header texts from Chrome's user agents

def get_proxies():
    url = 'https://free-proxy-list.net/'
    response = requests.get(url)
    parser = fromstring(response.text)
    proxies = set()
    for i in parser.xpath('//tbody/tr')[:200]:
        if i.xpath('.//td[7][contains(text(),"yes")]') and i.xpath('.//td[5][contains(text(),"elite")]'):
            # Grabbing IP and corresponding PORT
            proxy = ":".join([i.xpath('.//td[1]/text()')[0], i.xpath('.//td[2]/text()')[0]])
            proxies.add(proxy)
    return proxies

def http_client(random_user_agent):
    session = requests.Session()
    session.headers.update(
        {
        "User-Agent": random_user_agent
        }
    )

    def log_url(res, *args, **kwargs):
        logging.info(f"{res.url}, {res.status_code}")

    session.hooks["response"] = log_url
    return session

def open_asins_from_file(filename: str):
    logging.info(f"opening {filename}")
    lines = []
    with open(filename, newline='') as f:
        reader = csv.reader(f)
        data = list(reader)
        for line in data:
            lines.append(line[0])
    return lines

def make_request(session, proxy, baseurl: str, asin: str):
    try:
        response = session.get(baseurl + asin, proxies={"http": proxy, "https": proxy})
    except requests.RequestException:
        logging.warning(f"HTTP Error for {asin}")
        return
    if response.status_code == 200:
        return response, asin

def extract_data(response: tuple):
    soup = BeautifulSoup(response[0].text, 'lxml')
    asin = response[1]
    try:
        item = (
            asin,
            soup.select_one("span#productTitle").text.strip(),
            soup.select_one("span.a-price span").text,
            #soup.select_one("span.a-size-base span").text,
        )
        logging.info(f'scraped item successfully {item}')
        print(f'scraped {item}')
        return item
    except AttributeError:
        logging.info(f"No Matching Selectors found for {asin}")
        print(f'No matching selectors found for {asin}')
        item = (asin, "no data", "no data")
        return item

def save_to_csv(results: list):
    with open('results.csv', 'w') as f:
        csv_writer = csv.writer(f)
        for line in results:
            csv_writer.writerow(line)
    logging.info("saved file sucessfully")

def main():
    logging.basicConfig(filename='amzscraper.log', format='%(asctime)s %(message)s', level=logging.INFO)
    logging.info(f"---starting new---")

    # Get Proxies 
    proxies = get_proxies()
    # Generate User-Agents
    proxy_user_agents = get_user_agents()
    # Randomly select an User-Agent from the collected user-agent strings
    random_user_agent = random.choice(proxy_user_agents)

    session = http_client(random_user_agent)
    baseurl = "https://www.amazon.co.uk/dp/"
    asins = open_asins_from_file('asins.csv')

    proxy_pool = cycle(proxies)
    proxy = next(proxy_pool)
    
    results = []

    for asin in asins:
        html = make_request(session, proxy, baseurl, asin)
        if html is None:
            logging.info("passing due to make_request error")
        else:
            results.append(extract_data(html))
            print(results.json())
            time.sleep(3)

    save_to_csv(results)
    logging.info(f"---finished---")
    print("---finished---")

if __name__ == '__main__':
    main()

