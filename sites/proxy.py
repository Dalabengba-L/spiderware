import random
import redis
import requests

from settings import REDIS_HOST, REDIS_PORT, SHORT_REDIS_DB, LONG_REDIS_DB


class ProxyPool:

    def __init__(self):
        # 拿到一个redis的连接池
        self.short_redis_pool = redis.ConnectionPool(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=SHORT_REDIS_DB,
            max_connections=5
        )
        self.long_redis_pool = redis.ConnectionPool(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=LONG_REDIS_DB,
            max_connections=5
        )
        # 短效代理的长度
        self.SHORT_POOL_LEN = 30 # [1, 30]

    def get_order_proxy(self, order):
        """从短效代理池中获取指定order的代理"""
        conn = redis.Redis(connection_pool=self.short_redis_pool, decode_responses=True)
        try:
            proxy = conn.get("proxy:Proxy%s" % order)
            # print(proxy)
            if proxy is not None:
                return proxy.decode("utf-8")[7:]
        except:
            return None
        finally:
            conn.close()

    def get_long_proxy(self):
        """从长效代理中获取代理"""
        conn = redis.Redis(connection_pool=self.long_redis_pool, decode_responses=True)
        try:
            proxy = conn.get("IP1")
            # 返回 value 的 字节类型，或者 None
            return proxy.decode("utf-8") if proxy else None

        finally:
            conn.close()

    def random(self):
        order = random.choice(range(self.SHORT_POOL_LEN + 1))
        if order == 0:
            return self.get_long_proxy()
        return self.get_order_proxy(order)

    def get(self):
        return self.random()

    def validate(self, proxy):
        """
        自定义validator函数，校验代理是否可用
        """
        proxies = {"http": "http://{proxy}".format(proxy=proxy), "https": "https://{proxy}".format(proxy=proxy)}
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:34.0) Gecko/20100101 Firefox/34.0',
            'Accept': '*/*',
            'Connection': 'keep-alive',
            'Accept-Language': 'zh-CN,zh;q=0.8'
        }
        try:
            proxy_ip = proxy.split(":")[0]
            real_ip = requests.get('http://httpbin.org/ip', headers=headers, proxies=proxies, timeout=5).json()["origin"]

            # 当代理为普通透明代理时，real_ip 为 , join的 代理链路字符串
            # 以下判断会对透明代理直接进行过滤
            if real_ip == proxy_ip:
                return True
        except Exception as reason:
            # import traceback
            # traceback.print_exc()
            print(reason)
            pass
        return False


if __name__ == '__main__':
    pass
