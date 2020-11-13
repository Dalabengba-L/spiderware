import logging


COOKIE_ENABLED = False
COOKIE = ""

# 调试模式是否开启
DEBUG_TEST = False

# 解耦队列的队列长度，存放 orig_item
Q_ORIG_SIZE = 5
# 数据爬取和页面解析 解耦, 存放响应
Q_PAGE_SIZE = 10
# 数据存储
Q_DATA_SIZE = 100

# 数据采集完毕之后，发送SIGNAL_END来终止程序
SIGNAL_END = None

# 有关数据库的服务器信息
# MONGO ===========================================================
# mongo 普通表
MONGO_META_URL = "mongodb://xx:27017/"
# mongo 附件表
MONGO_ANNEX_URL = "mongodb://xx:27017/"

# 库
MONGO_DB = ""
# 表
MONGO_COLLECTION = ""
# =================================================================


# MYSQL ===========================================================
# 通常用来做临时的中间表
# Mysql连接名
MYSQL_HOST = 'xx.xx.xx.xx'
# 连接端口号
MYSQL_PORT = 3306
# Mysql用户名
MYSQL_USER = 'xx'
# Mysql用户密码
MYSQL_PASS = 'xx'
# Mysql数据库名
MYSQL_DBNAME = 'xx'
# =================================================================


# REDIS ===========================================================
# 通常用来连接代理池
REDIS_HOST = 'xx.xx.xx.xx'
REDIS_PORT = 6379
# 短效代理
SHORT_REDIS_DB = 0
# 长效代理
LONG_REDIS_DB = 14
# =================================================================

# 有关LOG的配置 =====================================================
# 日志文件的名称
LOG_FILENAME = "log.txt"
# log 终端打印的 日志级别
LOG_STREAN_LEVEL = logging.DEBUG
# log写入文件 的 日志级别
LOG_FILE_LEVEL = logging.DEBUG
# =================================================================

# status 字段的含义 =================================================
# 入库的初始化状态
STATUS_DEFAULT = 0
# 该数据被查询， 拿去处理
STATUS_TAKEAWAY = 1
# 该数据处理结果成功
STATUS_SUCCESS = 2

# 详情页爬取异常
STATUS_ERROR_CRAWL = 3
# 页面解析异常
STATUS_ERROR_PARSE = 4
# 页面存储异常
STATUS_ERROR_STORE = 5

# 以下状态我们是可以预期的
# 重复抓取
STATUS_ERROR_REPEAT = 6
# 响应成功，但是数据为空
STATUS_EMPTY_PARSE = 7
# 用来采集的 URL 不合法
STATUS_BAD_URL = 8

STATUS_BAD_ORIG = 9
# =================================================================

# REQUEST_MOTHOD_MODE： 0 只使用本地地址, 1 尽可能使用代理  会因为代理的不稳定，造成失败的概率增大, 2 优先使用代理，如果代理出错， 使用本地地址
REQUEST_MOTHOD_MODE = 1
