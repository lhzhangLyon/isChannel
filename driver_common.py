# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
File Name : driver_common.py
Description: 浏览器操作层
Author: lhzhang.Lyon
Date: '2018/6/5' '15:12'
"""
import sys
import os
import time, json, requests
from selenium import webdriver
import logging
import random
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

import shutil
import traceback


logging.basicConfig(level=logging.INFO,
                format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                datefmt='%a, %d %b %Y %H:%M:%S',
                )


class Chrome(object):
    def __init__(self, policyid, headless = False):
        self.Session = requests.session()
        self.policyid = policyid
        self.LOG = logging
        self.headless = headless
        # chrome exe and driver path
        self.chrome_path = None
        self.chrome_driver_path = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36',
            'Connection': 'close'
        }

    def copyChrome(self, name):
        """
        拷贝文件
        """
        pass

    def get_url(self, url, last_url = None, stream = False, timeout = 100):
        last_url = url
        self.headers['Referer'] = last_url
        return self.Session.get(url = url, headers = self.headers, stream = stream, timeout = timeout, verify = False)

    def chrome_init(self):
        """
        初始化浏览器
        """
        try:
            dec = DesiredCapabilities.CHROME
            dec['loggingPrefs'] = {'performance': 'ALL'}
            opts = webdriver.ChromeOptions()
            if self.headless:
                opts.add_argument('headless')
            opts.add_argument('--disable-gpu')
            opts.add_argument('--disable-images')
            opts.add_argument('--disable-plugins')
            driver = webdriver.Chrome(chrome_options=opts, desired_capabilities=dec)
            driver.implicitly_wait(30)
            driver.set_page_load_timeout(100)
            return driver
        except:
            self.LOG.error("chrome list driver init fail！")
            return None

    def getHttpStatus(self, browser):
        try:
            if self.get_url(browser.current_url).status_code == 200:
                self.LOG.info('{url} requests 请求成功'.format(url=browser.current_url))
                return 200
        except:
            self.LOG.info('{url} requests 请求失败'.format(url=browser.current_url))
            return None
        for responseReceived in browser.get_log('performance'):
            try:
                response = json.loads(responseReceived[u'message'])[u'message'][u'params'][u'response']
                if response[u'url'] == browser.current_url:
                    return response[u'status']
            except:
                self.LOG.info('{url} 当前页面无法访问'.format(url=browser.current_url))
                return None
        return None

    def open_url(self, url, driver):
        driver.get(url)
        # time.sleep(random.uniform(10, 15))
        Status = self.getHttpStatus(driver)
        try_num = 0
        while try_num < 60 and Status is None:
            time.sleep(0.5)
            try_num += 1
            Status = self.getHttpStatus(driver)
        # print Status
        assert Status == 200
        time.sleep(random.uniform(3, 5))

    def chrome_quit(self, driver):
        if driver is not None:
            driver.quit()

    def chrom_kill(self):
        pass


# 类接口
def chrome_option(policy, headlsee = False):
    return Chrome(policy, headlsee)


if __name__ == '__main__':
    chromedriver = chrome_option('test')
    test_driver = chromedriver.chrome_init()
    chromedriver.open_url("http://www.npc.gov.cn/", test_driver)
    print(test_driver.title)
    chromedriver.chrome_quit(test_driver)

