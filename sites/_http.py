import time
import requests
from fake_useragent import UserAgent

from sites.proxy import ProxyPool
from settings import COOKIE_ENABLED, COOKIE, REQUEST_MOTHOD_MODE


class Crawler:

    def __init__(self):
        self.proxy_pool = ProxyPool()
        self.timeout = 5
        self.MAX_RETRY = 5

    def get_with_proxy(self, url, proxy):
        headers = {
            'User-Agent': UserAgent().random,
        }
        if COOKIE_ENABLED:
            headers["Cookie"] = COOKIE
        proxies = {"http": "http://" + proxy, "https": "https://" + proxy} if proxy is not None else proxy
        try:
            resp = requests.get(url, headers=headers, proxies=proxies, timeout=self.timeout)
            return resp
        except:
            # traceback.print_exc()
            return None

    def get_0(self, url):
        """使用本地地址进行采集"""
        headers = {
            'User-Agent': UserAgent().random,
        }
        if COOKIE_ENABLED:
            headers["Cookie"] = COOKIE
        try:
            resp = requests.get(url, headers=headers, timeout=self.timeout)
            return resp
        except:
            # traceback.print_exc()
            return None

    def get_1(self, url, deep=1):
        """
        只考虑使用代理进行数据采集，尝试MAX_RETRY次
        """
        proxy = self.proxy_pool.get()
        while proxy is None:
            time.sleep(1)
            proxy = proxy.random
        response = self.get_with_proxy(url, proxy)
        while response is None:
            deep += 1
            if deep >= self.MAX_RETRY:
                break
            return self.get_1(url, deep)
        return response

    def get_2(self, url):
        """
        优先使用代理，代理采集失败，则采用本地地址
        """
        proxy = self.proxy_pool.get()
        while proxy is None:
            time.sleep(1)
            proxy = proxy.random
        response = self.get_with_proxy(url, proxy)
        if response is None:
            return self.get_0(url)

    @staticmethod
    def get(self):
        return {
            0: self.get_0,
            1: self.get_1,
            2: self.get_2,
        }[REQUEST_MOTHOD_MODE]


if __name__ == '__main__':
   pass

