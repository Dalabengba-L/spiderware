"""
    @目的 通过for update 实现类似于 mongo find_one_and_update的功能
    一些测试
    # 1.当 where所在的查询条件列 并没有索引或者是普通索引时，for update 所用的锁是表锁， 锁表之后 新的查询请求将会阻塞， 直至本次查询更新结束
    # 2.而当 where所在的查询条件列 为主键索引或者唯一索引时， for update 所用的表是行锁， 所行之后， 新的查询会跳过锁行，继续查询
    # 3.试图 通过 like 'xx%' 的方式， 将status进行 0_order 的拼装，这样既索引既不会失效， 也可以使用的状态码， 测试发现此种情况会阻塞，现象与1一致（注意: 是锁全表， 并非只锁like匹配到数据）
    # 目前 采用的是 1 的方式， 因为没有用到索引， 所以这是一个待优化的地方

    sql = "select pk, countryKey, attr, url, status from %s where status = 0 order by pk limit 1 for update;" % MYSQL_TABLE
"""
import pymysql
from dbutils.pooled_db import PooledDB

from settings import MYSQL_HOST, MYSQL_DBNAME, MYSQL_PASS, MYSQL_PORT, MYSQL_USER

# 数据库连接编码
DB_CHARSET = "utf8"

# mincached : 启动时开启的闲置连接数量(缺省值 0 开始时不创建连接)
DB_MIN_CACHED = 0

# maxcached : 连接池中允许的闲置的最多连接数量(缺省值 0 代表不闲置连接池大小)
DB_MAX_CACHED = 20

# maxshared : 共享连接数允许的最大数量(缺省值 0 代表所有连接都是专用的)如果达到了最大数量,被请求为共享的连接将会被共享使用
DB_MAX_SHARED = 20

# maxconnecyions : 创建连接池的最大数量(缺省值 0 代表不限制)
DB_MAX_CONNECYIONS = 100

# blocking : 设置在连接池达到最大数量时的行为(缺省值 0 或 False 代表返回一个错误<toMany......> 其他代表阻塞直到连接数减少,连接被分配)
DB_BLOCKING = True

# maxusage : 单个连接的最大允许复用次数(缺省值 0 或 False 代表不限制的复用).当达到最大数时,连接会自动重新连接(关闭和重新打开)
DB_MAX_USAGE = 0

# setsession : 一个可选的SQL命令列表用于准备每个会话，如["set datestyle to german", ...]
DB_SET_SESSION = None

# creator : 使用连接数据库的模块
DB_CREATOR = pymysql


class MysqlConnPool(object):
    """
    @功能：创建数据库连接池
    """
    __pool = None

    # 创建数据库连接conn和游标cursor
    def __enter__(self):
        self.conn = self.__get_conn()
        self.cursor = self.conn.cursor()

    # 创建数据库连接池
    def __get_conn(self):
        if self.__pool is None:
            self.__pool = PooledDB(
                creator=DB_CREATOR,
                mincached=DB_MIN_CACHED,
                maxcached=DB_MAX_CACHED,
                maxshared=DB_MAX_SHARED,
                maxconnections=DB_MAX_CONNECYIONS,
                blocking=DB_BLOCKING,
                maxusage=DB_MAX_USAGE,
                setsession=DB_SET_SESSION,
                host=MYSQL_HOST,
                port=MYSQL_PORT,
                user=MYSQL_USER,
                passwd=MYSQL_PASS,
                db=MYSQL_DBNAME,
                use_unicode=False,
                charset=DB_CHARSET
            )
        return self.__pool.connection()

    # 释放连接池资源
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cursor.close()
        self.conn.close()

    # 从连接池中取出一个连接
    def get_conn(self):
        conn = self.__get_conn()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        return cursor, conn



PRIMARY_KEY = "Pk"


class MysqlApi(object):

    def __init__(self, table):
        self.table = table
        # 创建mysql连接池
        self.conn_pool = MysqlConnPool()

    # 封装执行命令
    def execute(self, sql, param=None):
        """
        @return 改变的数据条目，或者异常(IntegrityError返回0)Reason
        """
        # 从连接池获取连接
        cursor, conn = self.conn_pool.get_conn()
        count = 0
        try:
            # count : 为改变的数据条数
            if param:
                count = cursor.execute(sql, param)
            else:
                count = cursor.execute(sql)

            conn.commit()
        # eg. IntegrityError: (1062, "Duplicate entry 'xx' for key 'xxxxx'")
        except pymysql.err.IntegrityError as r1:
            pass

        except Exception as reason:
            print(reason)
            print(sql)
            conn.rollback()
            return reason

        finally:
            self.close(cursor, conn)
            return count

    def fetchone(self, sql):
        cursor, conn = self.conn_pool.get_conn()
        try:
            cursor.execute(sql)
            # 有数据返回第一条数据，数据的各项用元组包起来，没有返回 None
            return cursor.fetchone()
        finally:
            self.close(cursor, conn)

    def close(self, cursor, conn):
        cursor.close()
        conn.close()

    def find_one_and_update(self, filter_dict, update_dict, projection):
        """
            @功能，实现类似mongo的该函数， 仅用来处理值为Int的数据
            @参数 e.g.
            filter_dict = {
                "one": {">": "1"},
                "two": {"=": "2"},
                "three": {"!=": "3"},
            }

            update_dict = {
                "Status": 1
            }
            @返回值
                1. 异常，返回异常Reason
                2. 成功返回数据
                3. 数据库中无符合条件的数据返回None
        """
        cursor, conn = self.conn_pool.get_conn()

        try:
            query_sql = "select {PRIMARY_KEY}, {projection} from {table} where {filter} order by Pk limit 1 for update;".format(
                PRIMARY_KEY=PRIMARY_KEY,
                projection=",".join(projection),
                table=self.table,
                filter=" and ".join(["%s%s%s" % (k, o, v) for k, vs in filter_dict.items() for o, v in vs.items()])
            )
            cursor.execute(query_sql)
            result = cursor.fetchone()

            if result is None:
                conn.commit()
                return None

            # 更新status
            update_sql = "update {table} set {update_str} where {pk_name} = {pk_value};".format(
                table=self.table,
                update_str=",".join(["%s=%s" % it for it in update_dict.items()]),
                pk_name=PRIMARY_KEY,
                pk_value=result[PRIMARY_KEY],
            )
            cursor.execute(update_sql)
            conn.commit()
            # 将 bytes 进行解码
            return {k: (v.decode() if isinstance(v, bytes) else v) for k, v in result.items()}

        except Exception as reason:
            # (reason)
            conn.rollback()
            return reason

        finally:
            conn.close()
            cursor.close()

    # t_temp_爱企查_mark_20200818
    def set_status(self, primary_key, update_dict):
        # pk 为 int 类型，负责需要 更改
        update_sql = "update {table} set {update_str} where {pk_name} = {pk_value};".format(
            table=self.table,
            update_str=",".join(["%s=%s" % it for it in update_dict.items()]),
            pk_name=PRIMARY_KEY,
            pk_value=primary_key
        )
        return self.execute(update_sql)


def test_demo():
    table = "t_temp_test_lpc"
    mysql_api = MysqlApi(table)
    # find_one_and_update
    r = mysql_api.find_one_and_update(
        filter_dict={
            "Status": {"=": 0},
            "Pk": {">=": 2},
        },
        update_dict={
            "Status": 1
        },
        projection=["Company"]
    )
    # set_status
    rr = mysql_api.set_status(2, update_dict={"status": 3})
    print(r)  # {'Pk': 3, 'Company': b'c'}
    print(rr)  # 1


if __name__ == '__main__':
    test_demo()
