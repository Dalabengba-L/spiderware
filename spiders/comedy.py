"""
    豆瓣电影分类排行榜 - 喜剧片 的 爬虫demo
"""

import time
import pymongo
import pymongo.errors


from sites.http import GetCrawler
from settings import MONGO_META_URL, MONGO_DB_NAME, MONGO_TABLE_NAME, MONGO_DATA_TABLE_NAME
from settings import STATUS_DEFAULT, STATUS_TAKEAWAY, STATUS_ERROR
from settings import DEBUG_TEST, CRAWL_TRY_COUNTER
from sites.captcha import Captcha

from sites.logger import logger
from sites.utils import _insert_many, _insert_one


class ComedySpider:

    def __init__(self):

        self.mode = "comedy"
        self.mongo_client = pymongo.MongoClient(MONGO_META_URL)
        self.mongo_db = self.mongo_client[MONGO_DB_NAME]
        # 中间表
        self.mongo_table = self.mongo_db[MONGO_TABLE_NAME]
        # 数据存储表
        self.mongo_data_table = self.mongo_db[MONGO_DATA_TABLE_NAME]
        # 采集尝试次数字段
        self.CRAEL_COUNTER_KET = "_CrawlCounter"
        # 状态字段
        self.STATUS_KRY = "_Status"
        # 主键字段，通过该字段识别对应数据，进而设置状态码， mongo一般为 _id
        self.status_pk = "_id"
        self.query_fields = ["Start", self.CRAEL_COUNTER_KET]
        self.crawler = GetCrawler()
        self.T_FETCH_NUM = 1
        self.T_CRAWL_NUM = 5
        self.T_PARSE_NUM = 1
        self.captcha = Captcha()

    def prepare(self):
        """构造中间表"""
        self.mongo_table.create_index([(self.STATUS_KRY, pymongo.ASCENDING), (self.CRAEL_COUNTER_KET, pymongo.ASCENDING)], background=True)
        self.mongo_table.create_index([("Start", pymongo.ASCENDING)], unique=True)
        self.mongo_data_table.create_index([("id", pymongo.ASCENDING)], unique=True)
        list_url = "https://movie.douban.com/j/chart/top_list_count?type=24&interval_id=100:90"
        session, response = self.crawler.get(list_url)
        session.close()
        total = response.json()["total"]
        print(total)

        for start in range(total // 20 + bool(total % 20)):
            item = {
                "Start": start,
                self.STATUS_KRY: STATUS_DEFAULT,
                self.CRAEL_COUNTER_KET: 0
            }
            _insert_one(self.mongo_table, item)

    def fetch(self):
        filter_dict = {
            self.STATUS_KRY: {
                "$in": [STATUS_DEFAULT, STATUS_ERROR]},

            self.CRAEL_COUNTER_KET: {
                "$lt": CRAWL_TRY_COUNTER
            }
        }
        # fetch 之前， 将拿去处理的数据 进行置零，
        # 如果采用分布式， 则置零需全部程序停止，手动执行置零操作
        r = self.mongo_table.update_many(
            {
                self.STATUS_KRY: STATUS_TAKEAWAY
            },
            {
                "$set": {
                    self.STATUS_KRY: STATUS_DEFAULT
                }
            }
        )
        logger.info("STATUS_TAKEAWAY(1)->STATUS_DEFAULT(0): %s" % r.modified_count)
        while True:
            orig_item = self.mongo_table.find_one_and_update(

                filter=filter_dict,
                update={"$set": {self.STATUS_KRY: STATUS_TAKEAWAY}},
                projection={k: 1 for k in self.query_fields}
            )

            if orig_item is None:
                # 此时已经没有符合条件的数据, 但是正在采集的数据，失败之后有可能会被重新搜索到, 所以我们要进行逻辑的判断
                # 1. 判断是否存在正在采集的数据
                state_crawling = self.mongo_table.find_one({self.STATUS_KRY: STATUS_TAKEAWAY})
                # 2. 判断是否存在filter的数据
                state_filter = self.mongo_table.find_one(filter=filter_dict, projection={"_id": 1})
                # print(state_crawling, state_filter)
                if (state_crawling is None) and (state_filter is None):
                    # 两者皆无，则采集必然完毕
                    break
                # 略微等待一段时间，防止死循环
                time.sleep(2)
                continue

            yield orig_item
            if DEBUG_TEST:
                break

    def crawl(self, orig_item):
        """构造URL，采集函数"""
        start = orig_item["Start"]
        # 知识产权
        url = "https://movie.douban.com/j/chart/top_list?type=24&interval_id=100:90&action=&start=%s&limit=20" % start
        get_result = self.crawler.get(url)
        if get_result is None:
            return
        resp = self.captcha.detect_captcha(get_result, url)
        return resp

    def slove(self, orig_item, response):
        """响应解析，存储函数"""
        data = response.json()
        _insert_many(self.mongo_data_table, data)


    def close(self):
        # 关闭资源， 如有其他关闭资源的操作，请补充在这里
        self.mongo_client.close()

    def set_status_and_add_crawl_counter(self, orig_item, status_code):
        """设置状态和采集次数的函数， 一般不需要修改"""
        after_crawl_counter = int(orig_item[self.CRAEL_COUNTER_KET] + 1)
        self.mongo_table.update_one(
            {"_id": orig_item["_id"]},
            {
                "$set": {
                    self.STATUS_KRY: status_code,
                    self.CRAEL_COUNTER_KET: after_crawl_counter
                }
            }
        )


if __name__ == '__main__':
    spider = ComedySpider()
    spider.prepare()
