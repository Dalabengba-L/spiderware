import json
import queue
import threading
import time
from threading import Thread, Event


class LoopTimer(Thread):
    """Call a function after a specified number of seconds:

            t = Timer(30.0, f, args=None, kwargs=None)
            t.start()
            t.cancel()     # stop the timer's action if it's still waiting

    """

    def __init__(self, interval, function, args=None, kwargs=None):
        Thread.__init__(self)
        self.interval = interval
        self.function = function
        self.args = args if args is not None else []
        self.kwargs = kwargs if kwargs is not None else {}
        self.finished = Event()

    def cancel(self):
        """Stop the timer if it hasn't finished yet."""
        self.finished.set()

    def run(self):
        while True:
            self.finished.wait(self.interval)
            if not self.finished.is_set():
                self.function(*self.args, **self.kwargs)
            else:
                break


def fetch_first(dom_tree, xpath_str):
    r = dom_tree.xpath(xpath_str)
    if r:
        return r[0].strip()
    return ""


def try_tools(s, tool):
    try:
        return tool(s)
    except:
        return s


def decoupling_work(put_func, get_func, queue_size=1000, put_thread_num=1, get_thread_num=1):
    """
    put_func, get_func 有且只有一个参数，即解耦的队列， 且不需要定义
    :param put_func:  入队函数
    :param get_func: 出队函数
    :param queue_size: 解耦队列最大存放元素的个数
    :param put_thread_num: 入队函数的线程数
    :param get_thread_num: 出队函数的线程数
    :return: put_func,get_func结束即结束
    """
    q = queue.Queue(queue_size)
    tt = []

    for i in range(put_thread_num):
        t_p = threading.Thread(target=put_func, args=(q, ))
        tt.append(t_p)

    for i in range(get_thread_num):
        t_g = threading.Thread(target=get_func, args=(q, ))
        tt.append(t_g)

    for ttt in tt:
        ttt.start()


class TimeStamp():
    # time.time()   10.7  以s为单位，小数点前面有10位，后面有7位，共17位
    @property
    def timestamp(self):
        return time.time()

    @property
    def timestamp_10(self):
        # 精确到秒
        return int(time.time())

    @property
    def timestamp_13(self):
        # 精确到毫秒
        return int(time.time() * 1000)

    @property
    def timestamp_17(self):
        return int(time.time() * 1000 * 10000)


def _read(filename):
    with open(filename, "r", encoding="utf-8") as f:
        return f.read()


def _write(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        f.write(data)


def _awrite(filename, data, end="\n"):
    with open(filename, "a", encoding="utf-8") as f:
        f.write(data)
        if end:
            f.write("\n")


def json_print(data):
    print(json.dumps(data, indent=4, ensure_ascii=False))


def json_read(filename):
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)


def json_write(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        return json.dump(data, f, indent=4, ensure_ascii=False)
