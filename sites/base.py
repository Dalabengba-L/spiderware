import json
import queue
import traceback
import threading

# 为了保证数据拿取不重复， STATUS_TAKEAWAY 会在spider中进行设置
# 一些特殊的错误，也会在spider中进行定制， 我们会空出对应的设置函数，继承之后直接覆盖即可
from settings import STATUS_SUCCESS, STATUS_BAD_URL, STATUS_BAD_ORIG, STATUS_ERROR_CRAWL, STATUS_ERROR_PARSE, STATUS_ERROR_STORE
from settings import DEBUG_TEST, SIGNAL_END
from settings import Q_DATA_SIZE, Q_ORIG_SIZE, Q_PAGE_SIZE
from sites.exceptions import BAD_ORIG_ITEM_ERROR, BAD_URL_ERROR
from sites.logger import logger
from sites.utils import LoopTimer

class BaseEngine:

    def __init__(self, spider_cls):
        self.spider = spider_cls()
        # 加载 spider 组件
        self.fetch = self.spider.fetch
        self.crawl = self.spider.crawl
        self.store = self.spider.store
        self.parse = self.spider.parse
        # spider的一些属性，用来打印时区分 spider
        self.mode = self.spider.mode

        # 用来设置状态的 用来检索的 主键
        # 一般来说中间表
        self.status_pk = self.spider.status_pk

        self.Lock = threading.RLock()

        # 一些采集进度的数据，用来打印
        self.crawl_total_number = 0
        self.last_crawl_number = 0
        self.unqualified_number = 0
        self.store_number = 0

        # 3大解耦队列
        self.queue_orig = queue.Queue(Q_ORIG_SIZE)
        self.queue_page = queue.Queue(Q_PAGE_SIZE)
        self.queue_data = queue.Queue(Q_DATA_SIZE)

        # 定时循环打印采集信息的程序
        self.tt_timer = LoopTimer(60, self.show_queue_msg) # interval = 60  # 秒

        # 调式模式与非调试模式  各自线程数的设置
        if DEBUG_TEST:
            self.T_FETCH_NUM, self.T_CRAWL_NUM, self.T_PARSE_NUM, self.T_STORE_NUM = 1, 1, 1, 1
        else:
            self.T_FETCH_NUM = self.spider.t_fetch_number
            self.T_CRAWL_NUM = self.spider.t_crawl_number
            self.T_PARSE_NUM = self.spider.t_parse_number
            self.T_STORE_NUM = self.spider.t_store_number

        # 定义打印模块
        self.logger = logger

    def engine_fetch_debug(self, action, orig_item):

        self.logger.info("[{action} {mode}], orig_item={orig_item}".format(
            action=action,
            mode=self.mode,
            orig_item=json.dumps(orig_item, ensure_ascii=False)
        ))

    def engine_debug(self, action, orig_item, length=None):
        if length is not None:
            self.logger.info("[{action} {mode}] length={length}, orig_item={orig_item}".format(
                action=action,
                length=length,
                mode=self.mode,
                orig_item=json.dumps(orig_item, ensure_ascii=False)
            ))
        else:
            self.logger.info("[{action} {mode}] orig_item={orig_item}".format(
                action=action,
                mode=self.mode,
                orig_item=json.dumps(orig_item, ensure_ascii=False)
            ))

    def engine_error(self, action, orig_item):
        self.logger.error("[{action}] mode={mode} orig_item={orig_item}, Error={error}".format(
            action=action,
            mode=self.mode,
            orig_item=json.dumps(orig_item, ensure_ascii=False),
            error=traceback.format_exc()
        ))

    def show_queue_msg(self):

        self.logger.info(
            "%s: fetch_queue_size=%d/%d, page_queue_size=%d/%d, store_queue_size=%d/%d, crawl_number=%s, crawl_last_min=%s, store_total_number=%s" % (
                self.mode,
                self.queue_orig.qsize(),
                self.queue_orig.maxsize,
                self.queue_page.qsize(),
                self.queue_page.maxsize,
                self.queue_data.qsize(),
                self.queue_data.maxsize,
                self.crawl_total_number,
                self.crawl_total_number - self.last_crawl_number,
                self.store_number
            )
        )
        self.last_crawl_number = self.crawl_total_number

    def before_crawl(self, orgi_item):
        pass

    def after_crawl(self, response):
        pass

    def after_parse(self, parse_results):
        pass

    def before_fetch(self, orgi_item):
        pass

    def set_status(self, orgi_item, code):
        self.spider.set_status(
            orgi_item[self.status_pk],
            code
        )

    def t_fetch(self):

        for orgi_item in self.fetch():
            # print(orgi_item)
            try:
                self.before_fetch(orgi_item)
                self.engine_fetch_debug("FETCH", orgi_item)
                self.queue_orig.put(orgi_item)
                if DEBUG_TEST:
                    break

            except BAD_ORIG_ITEM_ERROR:
                self.logger("[BAD FETCH] %s=%s" % (self.status_pk, orgi_item[self.status_pk]))
                self.set_status(orgi_item, STATUS_BAD_ORIG)

        self.logger.info("[..................... FETCH END ........................]")

    def t_crawl(self):
        action = "CRAWL"
        while True:
            r = self.queue_orig.get()
            if r == SIGNAL_END:
                self.queue_orig.task_done()
                # self.logger.info("线程 t_crawl 退出")
                break
            orgi_item = r
            try:
                self.engine_debug(action, orgi_item)
                # crawl 前 可以进行的操作， 如 url合法性检测
                # 此处可以抛出特定的异常， 并进行捕获处理
                self.before_crawl(orgi_item)
                response = self.crawl(orgi_item)
                self.after_crawl(response)
                self.queue_page.put((orgi_item, response))

            except BAD_URL_ERROR:
                # 打印错误消息， 设置状态码
                self.engine_error(action, orgi_item)
                self.set_status(orgi_item, STATUS_BAD_URL)


            except Exception:
                # 打印错误消息， 设置状态码
                self.engine_error(action, orgi_item)
                self.set_status(orgi_item, STATUS_ERROR_CRAWL)

            finally:
                self.Lock.acquire()
                self.crawl_total_number += 1
                self.Lock.release()
                self.queue_orig.task_done()

    def t_parse(self):
        action = "PARSE"
        while True:
            r = self.queue_page.get()
            if r == SIGNAL_END:
                self.queue_page.task_done()
                # self.logger.info("线程 t_parse 退出")
                break
            (orgi_item, page) = r
            try:
                parse_results = self.parse(orgi_item, page)

                # 写在解析之后的检测，如解析之后的数据列表为空，则无需再进行存储
                # self.before_parse(parse_results)
                self.engine_debug(action, orgi_item, len(parse_results))
                self.queue_data.put((orgi_item, parse_results))

            except Exception as reason:
                self.engine_error(action, orgi_item)
                self.set_status(orgi_item, STATUS_ERROR_PARSE)

            finally:
                self.queue_page.task_done()

    def t_store(self):
        action = "STORE"

        while True:
            r = self.queue_data.get()
            if r == SIGNAL_END:
                self.queue_data.task_done()
                # self.logger.info("线程 t_store 退出")
                break

            (orgi_item, parse_results) = r
            try:
                rr = self.store(parse_results)

                self.Lock.acquire()
                self.store_number += rr
                self.Lock.release()
                self.engine_debug(action, orgi_item, rr)
                self.set_status(orgi_item, STATUS_SUCCESS)

            except:
                self.engine_error(action, orgi_item)
                self.set_status(orgi_item, STATUS_ERROR_STORE)

            finally:
                self.queue_data.task_done()

    def close(self):

        self.spider.close()
        self.tt_timer.cancel()

        for i in range(self.T_CRAWL_NUM):
            self.queue_orig.put(SIGNAL_END)
        for i in range(self.T_PARSE_NUM):
            self.queue_page.put(SIGNAL_END)
        for i in range(self.T_STORE_NUM):
            self.queue_data.put(SIGNAL_END)

        self.queue_orig.join()
        self.queue_page.join()
        self.queue_data.join()
        # print("当前活跃的线程数: %s, 当前线程为 %s" % (threading.active_count(), threading.current_thread().name))

    def run(self):
        # 获取 fetch crawl parse store 的线程数

        daemon_t = []
        fetch_t = []

        daemon_t.append(self.tt_timer)

        # 创建fetch线程
        for i in range(self.T_FETCH_NUM):
            tt_fetch = threading.Thread(target=self.t_fetch)
            fetch_t.append(tt_fetch)
        # 创建crawl线程
        for i in range(self.T_CRAWL_NUM):

            tt_crawl = threading.Thread(target=self.t_crawl, name="Crawl_Thread_%s" % (i + 1))
            daemon_t.append(tt_crawl)
        # 创建parse线程
        for i in range(self.T_PARSE_NUM):
            tt_parse = threading.Thread(target=self.t_parse)
            daemon_t.append(tt_parse)
        # 创建store线程
        for i in range(self.T_STORE_NUM):
            tt_store = threading.Thread(target=self.t_store)
            daemon_t.append(tt_store)

        # 启动守护线程
        for tt in fetch_t + daemon_t:
            # tt.setDaemon(True)
            tt.start()

        # 对守护线程进行join, 等待守护线程即 fetch 执行完毕， 即保证将数据库的url全部放入队列中
        for ttt in fetch_t:
            ttt.join()

        # self.logger.info("............. Fetch End ................")
        # 对三个队列进行jion,保证 fetch 结束之后， 各个队列的数据能够逻辑执行完毕
        self.queue_orig.join()
        # self.logger.info("............. Crawl End ................")
        self.queue_page.join()
        # self.logger.info("............. Parse End ................")
        self.queue_data.join()
        # self.logger.info("............. Store End ................")
        # 数据采集存储完毕，关闭资源
        self.close()
        # url全部入队列，且各个队列中的数据全部处理完毕，则程序执行完毕
        self.logger.info("[........................ SPIDER END ...........................]")
        self.show_queue_msg()
