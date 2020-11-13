from sites.base import BaseEngine
from spider.demo import DemoSpider


class Engine(BaseEngine):
    pass


if __name__ == '__main__':
    engine = Engine(spider_cls=DemoSpider)
    engine.run()