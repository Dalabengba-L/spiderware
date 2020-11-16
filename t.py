import requests
from fake_useragent import UserAgent

form_data = {"data": {'CONTRACT_GOODS_ID':'fb411485c9f64d23a8959aefaf1f33ba','GOODS_ID':'4ee2f14cc70f41f99025f231984008d2','IS_PUBLIC':'1'}}

headers = {
    # 'User-Agent': UserAgent().random,

    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Connection": "keep-alive",
    "Content-Length": "137",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Cookie": "sensorsdata2015jssdkcross=%7B%22distinct_id%22%3A%22173d6f665112cd-0e86bce1cf9242-5d492f12-2073600-173d6f66513355%22%2C%22%24device_id%22%3A%22173d6f665112cd-0e86bce1cf9242-5d492f12-2073600-173d6f66513355%22%2C%22props%22%3A%7B%22%24latest_referrer%22%3A%22%22%2C%22%24latest_referrer_host%22%3A%22%22%2C%22%24latest_traffic_source_type%22%3A%22%E7%9B%B4%E6%8E%A5%E6%B5%81%E9%87%8F%22%2C%22%24latest_search_keyword%22%3A%22%E6%9C%AA%E5%8F%96%E5%88%B0%E5%80%BC_%E7%9B%B4%E6%8E%A5%E6%89%93%E5%BC%80%22%7D%7D; __d_s_=3F83AF1A6703122484826D8DFA93BDFD; __s_f_c_s_=3F83AF1A6703122484826D8DFA93BDFD; PURCHASE_CLOUD_SESSION_ID=2f37b658-b047-4f1a-850d-ff151ea2c0d4; PUBLIC_101002002=4",
    "Host": "gpep.esgcc.com.cn",
    "Origin": "http://gpep.esgcc.com.cn",
    "Referer": "http://gpep.esgcc.com.cn/purchase_mall/home/goodsDetail?goods_id=4ee2f14cc70f41f99025f231984008d2&contract_goods_id=fb411485c9f64d23a8959aefaf1f33ba&catgory_id=7c9441c3da194356a772c9e6004e96fb",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest",
}
resp = requests.post("http://gpep.esgcc.com.cn/purchase_mall/goodsCenter/goods/getGoodsDetails", headers=headers, data=form_data)
print(resp.status_code)
print(resp.text)