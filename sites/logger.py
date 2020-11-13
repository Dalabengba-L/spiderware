import os
import logging.config
from settings import LOG_FILENAME, LOG_FILE_LEVEL, LOG_STREAN_LEVEL

# 日志大小 5M
LOG_MAX_BYTES = 1024 * 1024 * 5
# 备份
LOG_BACKUP_COUNT = 5

CURRENT_PATH = os.path.dirname(os.path.abspath(__file__))
ROOT_PATH = os.path.join(CURRENT_PATH, os.pardir)
LOG_PATH = os.path.join(ROOT_PATH, 'log')

if not os.path.exists(LOG_PATH):
    os.mkdir(LOG_PATH)


LOGGING_DIC = {
    'version': 1,
    # 禁用已经存在的logger实例
    'disable_existing_loggers': False,
    # 定义日志 格式化的 工具
    'formatters': {
        'simple': {
            'format': "%(levelname)s %(asctime)s [%(filename)s line:%(lineno)d]: %(message)s",
            'datefmt': '%Y/%m/%d %H:%M:%S'
        },

    },

    'handlers': {
        # 打印到终端的日志
        'stream': {
            'level': LOG_STREAN_LEVEL,
            'class': 'logging.StreamHandler',  # 打印到屏幕
            'formatter': 'simple'
        },
        # 打印到文件的日志,收集info及以上的日志
        'file': {
            'level': LOG_FILE_LEVEL,
            'class': 'logging.handlers.RotatingFileHandler',  # 保存到文件
            'formatter': 'simple',
            'filename': os.path.join(LOG_PATH, LOG_FILENAME),  # 日志文件路径
            'maxBytes': LOG_MAX_BYTES,  # 日志大小 5M
            'backupCount': LOG_BACKUP_COUNT,
            'encoding': 'utf-8',  # 日志文件的编码，再也不用担心中文log乱码了
        },
    },
    # logger实例
    'loggers': {
        # 默认的logger应用如下配置
        '': {
            'handlers': ['stream', 'file'],  # 这里把上面定义的两个handler都加上，即log数据既写入文件又打印到屏幕
            'level': 'INFO',
            'propagate': True,  # 向上（更高level的logger）传递
        },
        # logging.getLogger(__name__)拿到的logger配置
        # 这样我们再取logger对象时logging.getLogger(__name__)，不同的文件__name__不同，这保证了打印日志时标识信息不同，
        # 但是拿着该名字去loggers里找key名时却发现找不到，于是默认使用key=''的配置
    },
}

logging.config.dictConfig(LOGGING_DIC)
logger = logging.getLogger(__name__)

if __name__ == '__main__':
    logger.info("This is a Info msg")