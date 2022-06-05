import time
from webbrowser import Chrome

import requests
from bs4 import BeautifulSoup
from selenium import webdriver

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.67 Safari/537.36"
}


def parse_url(url):
    req = requests.get(url=url, headers=headers)
    time.sleep(6)
    soup = BeautifulSoup(req.content, 'html.parser')
    time.sleep(3)
    print(soup)

