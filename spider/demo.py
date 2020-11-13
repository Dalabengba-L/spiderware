import threading
import pymongo
import pymongo.errors

from db.mysql_mq import MysqlApi
from settings import MONGO_META_URL, DEBUG_TEST
from sites._http import Crawler


class DemoSpider:

    def __init__(self):
        self.mode = "demo"
        # MONGO_DB,  MONGO_COLLECTION 可根据需求在settings中进行全局配置
        MONGO_DB = "DemoUnCom"
        MONGO_COLLECTION = "TEST" if DEBUG_TEST else "DATA"
        # 原数据
        self.meta_mongo = pymongo.MongoClient(MONGO_META_URL)
        mongo_db = self.meta_mongo[MONGO_DB]
        self.meta_collection = mongo_db[MONGO_COLLECTION]

        self.table = "mysql_ware_table_name"
        self.mysql = MysqlApi(self.table)
        self.status_pk = "Pk"
        self.status_field = "Status"

        # 定义采集， 解析，存储的线程数
        self.crawler = Crawler()
        # # 默认fetch 的线程数是 1，因为我们发现 fetch往往不是瓶颈
        self.t_fetch_number = 1
        self.t_crawl_number = 30
        self.t_parse_number = 1
        self.t_store_number = 1

        self.begin_pk = 1
        self.lock = threading.RLock()

    def reset_begin_pk(self, pk):
        self.lock.acquire()
        self.begin_pk = pk
        self.lock.release()

    def fetch(self):
        while True:
            orig_item = self.mysql.find_one_and_update(
                filter_dict={
                    "Status": {"=": 0},
                    "Pk": {">=": self.begin_pk},
                },
                update_dict={
                    "Status": 1
                },
                projection=["Category", "Period"]
            )
            if orig_item is None:
                break
            self.reset_begin_pk(orig_item[self.status_pk])
            yield orig_item

    def crawl(self, orig_item):
        url = orig_item["Url"]
        resp = self.crawler.get(url)
        return resp

    def parse(self, orig_item, response):
        # 判断图片流是否正确完整
        # 返回值为列表
        # print(response.text)
        parse_results = []
        dataset = response.json()["dataset"]

        for data in dataset:
            r = {
                "ProductType": "Goods",
                "Category": orig_item["Category"],
                "CommodityCode": data["cmdCode"],
                "CommodityDescribe": data["cmdDescE"],
                "AggrLevel": data["aggrLevel"],
                "Freq": orig_item["Freq"],
                "Year": data["yr"],
                "Period": data["period"],
                "TradeFlowCode": data["rgCode"],
                "TradeFlow": data["rgDesc"],
                "PartnerCode": data["ptCode"],
                "Partner": data["ptTitle"],
                "ReporterCode": data["rtCode"],
                "Reporter": data["rtTitle"],
                "NetWeight": data["NetWeight"],
                "TradeValue": data["TradeValue"],
                "TradeQuantity": data["TradeQuantity"],
                "TradeQuantityUnit": data["qtDesc"],
                "Flag": data["estCode"],
            }
            parse_results.append(r)
        return parse_results

    def store(self, parse_results):
        store_counter = 0
        for parse_item in parse_results:
            try:
                self.meta_collection.insert_one(parse_item)
                # print(parse_item)
                store_counter += 1
            except pymongo.errors.BulkWriteError as reason:
                pass
            except pymongo.errors.DuplicateKeyError:
                pass
        return store_counter

    def close(self):
        self.meta_mongo.close()

    def set_status(self, pk, status_code):
        self.mysql.set_status(
            primary_key=pk,
            update_dict={"status": status_code}
        )
