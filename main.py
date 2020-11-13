import time

import schedule

from engine import Engine
from sites.utils import _awrite
from spider import demo


class Scheduler():

    def __init__(self):
        self.project_name = "Mark IMAGE"
        self.collect_map = {
            "demo": demo.DemoSpider,
        }
        self.log_filename = "result.txt"

    def sche_info(self, mode, store_number):
        data = "[INFO] 时间: %s, mode: %s, 此次采集成功存储的数量: %s" % (
            time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            mode,
            store_number
        )
        print(data)
        _awrite(
            filename=self.log_filename,
            data = data
        )

    def sche_error(self, mode, reason):
        data = "[ERROR] 时间: %s, mode: %s, 异常原因: %s" % (
            time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            mode,
            reason.__repr__()
        )
        print(data)
        _awrite(
            filename=self.log_filename,
            data=data
        )

    def run(self, modes):

        print('...Starting Collect %s...' % self.project_name)
        for mode in modes:
            try:
                engine = Engine(
                    spider_cls=self.collect_map[mode],
                )
                print(f'.......................... starting collect {mode} ...........................')
                store_number = engine.run()
                self.sche_info(mode, store_number)
                print(
                    f'.......................... collect {mode} end, update = {store_number}...........................')
            except Exception as reason:
                self.sche_error(mode, reason)

    def loop_run(self, modes):
        # 每天的中午12点定时采集数据
        daily_spider_time = "12:00"
        print("定时采集任务启动，时间为每日%s" % daily_spider_time)
        schedule.every().day.at(daily_spider_time).do(self.run, modes)
        while True:
            schedule.run_pending()
            time.sleep(1)


if __name__ == '__main__':

    modes = ["demo"]
    scheduler = Scheduler()
    scheduler.run(modes)


