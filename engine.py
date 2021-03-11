from sites.base import BaseEngine
from spiders.comedy import ComedySpider


class Engine(BaseEngine):
    pass


if __name__ == '__main__':
    engine = Engine(spider_cls=ComedySpider)
    engine.run()
