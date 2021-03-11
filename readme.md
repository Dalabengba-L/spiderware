# spiderware

#### 如何提高采集效率？

1. 必然是支持分布式的
2. 程序支持多线程设置
3. 往往采集程序的瓶颈在与远端服务器的请求响应，我们让采集功能与其他功能通过队列解耦，让采集功能不受其他因素的影响

#### 特点

1. 支持分布式
2. URL获取，采集，解析存储通过队列解耦
3. 可以设置采集失败重试的次数，方便管理
4. 可以定义spider类， 方便进行采集项目的扩展
5. 支持session的管理，可以方便接入验证码接口，验证码相关处理只需要编写验证码接口文件即可
6. 支持redis代理池接口，有自己的超时，重试机制，多种代理使用方式可通过REQUEST_MOTHOD_MODE进行配置
7. 有自己的日志打印设置，并定时打印采集的总数，成功数，每分钟采集数量， 线程数等相关信息
8. 支持定时采集，代码可以参照main.py

#### Demo

我们以 豆瓣电影分类排行榜 - 喜剧片 作为Demo进行爬虫的样例

网址： [https://movie.douban.com/typerank?type_name=%E5%96%9C%E5%89%A7&type=24&interval_id=100:90&action=](https://movie.douban.com/typerank?type_name=喜剧&type=24&interval_id=100:90&action=)

<img src="https://github.com/Dalabengba-L/spiderware/blob/master/image/03.png" alt="03" style="zoom: 67%;" />

Mongo中间表:  DownLoadList

运行，spiders/comdy.py 文件，将构造URL的必要条件 Start 加入到中间表， 下图中的数据为已经成功采集数据之后的中间表截图

~~~python
if __name__ == '__main__':
    spider = ComedySpider()
    spider.prepare()
~~~



<img src="https://github.com/Dalabengba-L/spiderware/blob/master/image/01.png" alt="01"  />

Mongo 数据表: BasicData

运行engine.py , 开启采集程序， 其中fetch的线程数建议为1， crawl线程看电脑配置设置， 5-50皆可， solve线程数一般设置 5个以下。下图为最终的数据存储的表的截图

~~~python
if __name__ == '__main__':
    engine = Engine(spider_cls=ComedySpider)
    engine.run()
~~~



<img src="https://github.com/Dalabengba-L/spiderware/blob/master/image/02.png" alt="02"/>



#### 写在最后

​	请求模块是基于requests模块进行开发的，我们进行一个代码开发的时候，如果数据存储的数据库只涉及mongo的时候，一般情况下，只需要移植Spider， 构造中间表，代码开发crawl, solve方法即可，

本人会定期花时间进行优化，并希望能对读者有点用处。
