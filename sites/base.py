import queue
import traceback
import threading

# 为了保证数据拿取不重复， STATUS_TAKEAWAY 会在spider中进行设置
# 一些特殊的错误，也会在spider中进行定制， 我们会空出对应的设置函数，继承之后直接覆盖即可

from settings import DEBUG_TEST, STATUS_ERROR, STATUS_SUCCESS
from settings import Q_ORIG_SIZE, Q_PAGE_SIZE

from sites.logger import logger
from sites.utils import LoopTimer


# 数据采集完毕之后，发送SIGNAL_END来终止程序
SIGNAL_END = None


class BaseEngine:

    def __init__(self, spider_cls):
        self.spider = spider_cls()
        # 加载 spiders 组件
        self.fetch = self.spider.fetch
        self.crawl = self.spider.crawl
        self.slove = self.spider.slove
        # spider的一些属性，用来打印时区分 spiders
        self.mode = self.spider.mode

        self.Lock = threading.RLock()

        # 一些采集进度的数据，用来打印
        self.crawl_total_number = 0
        self.last_crawl_number = 0
        self.solve_success_number = 0

        # 2大解耦队列
        self.queue_orig = queue.Queue(Q_ORIG_SIZE)
        self.queue_page = queue.Queue(Q_PAGE_SIZE)

        # 定时循环打印采集信息的程序
        self.tt_timer = LoopTimer(60, self.show_queue_msg) # interval = 60  # 秒

        # 调式模式与非调试模式  各自线程数的设置
        if DEBUG_TEST:
            self.T_FETCH_NUM, self.T_CRAWL_NUM, self.T_PARSE_NUM = 1, 1, 1
        else:
            self.T_FETCH_NUM = self.spider.T_FETCH_NUM
            self.T_CRAWL_NUM = self.spider.T_CRAWL_NUM
            self.T_PARSE_NUM = self.spider.T_PARSE_NUM

        # 定义打印模块
        self.logger = logger

    def show_queue_msg(self):

        self.logger.info(
            "%s: fetch_queue_size=%d/%d, page_queue_size=%d/%d, crawl_total_number=%s, solve_success_number=%s, crawl_last_min=%s, active_thread_counter=%s" % (
                self.mode,
                self.queue_orig.qsize(),
                self.queue_orig.maxsize,
                self.queue_page.qsize(),
                self.queue_page.maxsize,
                self.crawl_total_number,
                self.solve_success_number,
                self.crawl_total_number - self.last_crawl_number,
                threading.active_count()

            )
        )
        self.last_crawl_number = self.crawl_total_number

    def set_status(self, orgi_item, status_code):
        self.spider.set_status_and_add_crawl_counter(
            orgi_item,
            status_code
        )

    def t_fetch(self):

        for orgi_item in self.fetch():
            # print(orgi_item)
            self.logger.info("[FETCH] %s" % orgi_item)
            self.queue_orig.put(orgi_item)
            if DEBUG_TEST:
                break

    def t_crawl(self):
        while True:
            r = self.queue_orig.get()
            if r == SIGNAL_END:
                self.queue_orig.task_done()
                # self.logger.info("线程 t_crawl 退出")
                break
            orgi_item = r
            try:
                self.logger.info("[CRAWL] %s" % orgi_item)
                response = self.crawl(orgi_item)
                # print(response)
                # 加一些断言
                assert response is not None
                # print(response.url)
                self.queue_page.put((orgi_item, response))

            except AssertionError:
                self.set_status(orgi_item, STATUS_ERROR)
                self.logger.error("[CRAWL Assert Error] %s" % orgi_item)

            except:
                traceback.print_exc()
                self.set_status(orgi_item, STATUS_ERROR)
                self.logger.error("[CRAWL Error] %s" % orgi_item)

            finally:
                self.Lock.acquire()
                self.crawl_total_number += 1
                self.Lock.release()
                self.queue_orig.task_done()

    def t_sovle(self):
        while True:
            r = self.queue_page.get()
            if r == SIGNAL_END:
                self.queue_page.task_done()
                break
            (orgi_item, response) = r
            result = 0
            try:
                self.slove(orgi_item, response)
                result = 1
                self.logger.info("[%s SOLVE SUCCESS] %s" % (self.mode, orgi_item))
                self.set_status(orgi_item, STATUS_SUCCESS)

            except:
                # print(response.url)
                traceback.print_exc()
                self.set_status(orgi_item, STATUS_ERROR)
                self.logger.error("[SOVLE Error] %s" % orgi_item)
            finally:
                self.Lock.acquire()
                self.solve_success_number += result
                self.Lock.release()
                self.queue_page.task_done()

    def close(self):

        self.spider.close()
        self.tt_timer.cancel()

        for i in range(self.T_CRAWL_NUM):
            self.queue_orig.put(SIGNAL_END)
        for i in range(self.T_PARSE_NUM):
            self.queue_page.put(SIGNAL_END)

        self.queue_orig.join()
        self.queue_page.join()

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
            tt_crawl = threading.Thread(target=self.t_crawl)  #, name="Crawl_Thread_%s" % (i + 1))
            daemon_t.append(tt_crawl)
        # 创建parse线程
        for i in range(self.T_PARSE_NUM):
            tt_slove = threading.Thread(target=self.t_sovle)
            daemon_t.append(tt_slove)

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

        # 数据采集存储完毕，关闭资源
        self.close()
        # url全部入队列，且各个队列中的数据全部处理完毕，则程序执行完毕
        self.logger.info("[........................ SPIDER END ...........................]")
        self.show_queue_msg()
