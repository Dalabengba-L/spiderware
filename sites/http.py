"""
发起GET请求的类
"""
import requests

from retrying import retry, RetryError
from fake_useragent import UserAgent

from sites.proxy import ProxyPool
from sites.utils import is_none
from settings import REQUEST_MOTHOD_MODE


# 采集失败重试次数
MAX_CRAWL_RETRY = 3
# 请求超时时间
REQUEST_TIME_OUT = 10


def create_session(proxy=None):
    session = requests.Session()

    headers = {
        'User-Agent': UserAgent().random,
    }
    # cookie要根据俄实际情况进行定制
    # if COOKIE_ENABLED:
    #     headers["Cookie"] = COOKIE

    session.headers = headers
    if proxy is not None:
        proxies = {"http": "http://" + proxy, "https": "https://" + proxy} if proxy is not None else proxy
        session.proxies = proxies
    return session


class GetCrawler:

    def __init__(self):
        self.proxy_pool = ProxyPool()

    @retry(stop_max_attempt_number=MAX_CRAWL_RETRY, retry_on_result=is_none)
    def _retry_get_with_proxy(self, url):
        """只考虑使用代理采集数据，尝试 MAX_CRAWL_RETRY"""
        proxy = self.proxy_pool.get()
        # print(proxy)
        assert proxy is not None
        session = create_session(proxy=proxy)
        try:
            resp = session.get(url, timeout=REQUEST_TIME_OUT)
            # print(resp.text)
            return session, resp
        except:
            session.close()

    def _get_with_proxy(self, url):
        try:
            get_result = self._retry_get_with_proxy(url)
            return get_result
        except (RetryError, AssertionError):
            return None

    def _get_by_local(self, url):
        """只考虑本地采集一次"""
        print(url)
        session = create_session()
        try:
            resp = session.get(url, timeout=REQUEST_TIME_OUT)
            return session, resp
        except:
            session.close()

    def _get_prior_proxy_then_local(self, url):
        """使用代理采集数据尝试 MAX_CRAWL_RETRY 依然失败，则使用本地采集采集一次"""
        proxy_get_result = self._get_with_proxy(url)

        if proxy_get_result is not None:
            return proxy_get_result
        # 代理获取数据失败， 进行本地获取
        local_get_result = self._get_by_local(url)
        return local_get_result

    @property
    def get(self):
        """
            0 只使用本地地址
            1 只使用代理
            2 优先使用代理，如果代理出错，使用本地地址
        """
        return {
            0: self._get_by_local,
            1: self._get_with_proxy,
            2: self._get_prior_proxy_then_local,
        }[REQUEST_MOTHOD_MODE]


if __name__ == '__main__':
    pass
