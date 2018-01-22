# -*- coding: utf-8 -*-

import re
from pyquery import PyQuery as pq
from pymongo import MongoClient
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from config import *

client = MongoClient(MONGO_URI)
db = client[MONGO_DB]

browser = webdriver.Firefox()
wait = WebDriverWait(browser, 10)


def search():
    try:
        browser.get('https://www.taobao.com')
        input_box = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#q')))
        submit_box = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '.btn-search')))
        input_box.send_keys(KEYWORD)
        submit_box.click()
        total = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.total')))
        get_products()
        return total.text
    except TimeoutException:
        return search()


def next_page(page_number):
    try:
        input_box = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input.input:nth-child(2)')))
        submit_box = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'span.btn:nth-child(4)')))
        input_box.clear()
        input_box.send_keys(page_number)
        submit_box.click()
        wait.until(EC.text_to_be_present_in_element(
            (By.CSS_SELECTOR, 'li.active > span:nth-child(1)'), str(page_number)))
        get_products()
    except TimeoutException:
        next_page(page_number)


def get_products():
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#mainsrp-itemlist .items .item')))
    html = browser.page_source
    doc = pq(html)
    items = doc('#mainsrp-itemlist .items .item').items()
    for item in items:
        product = {
            'image': item.find('.pic .img').attr('src'),
            'price': item.find('.price').text(),
            'deal': item.find('.deal-cnt').text()[:-3],
            'title': item.find('.title').text(),
            'shop': item.find('.shop').text(),
            'location': item.find('.location').text()
        }
        print(product)
        save_to_mongodb(product)


def save_to_mongodb(result):
    try:
        if db[MONGO_TABLE].insert(result):
            print('Successfully Saved!', result)
    except Exception as e:
        print(e)


def main():
    try:
        total = search()
        total_ = int(re.compile('(\d+)').search(total).group(1))
        for i in range(2, total_ + 1):
            next_page(i)
    except Exception as e:
        print(e)
    finally:
        browser.close()


if __name__ == '__main__':
    main()
