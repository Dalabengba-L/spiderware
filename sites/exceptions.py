"""
    定义一些异常类，方便进行错误追踪
    多用于spider类中进行抛出，BaseEngine类中进行捕获
"""

class BAD_URL_ERROR(Exception):
    pass


class BAD_ORIG_ITEM_ERROR(Exception):
    pass
