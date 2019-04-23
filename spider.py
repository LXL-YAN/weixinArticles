from urllib.parse import urlencode
import pymongo
import requests
from requests.exceptions import ConnectionError
from pyquery import PyQuery as pq
from config import *

#client = pymongo.MongoClient('localhost')
#db = client['weixin']

client = pymongo.MongoClient(MONGO_URL)
db = client[MONGO_DB]


base_url = 'https://weixin.sogou.com/weixin?'

headers = {
    'Cookie': 'ABTEST=0|1556031884|v1; IPLOC=CN3301; SUID=746DC7734018960A000000005CBF298C; SUID=746DC7732113940A000000005CBF298C; weixinIndexVisited=1; SUV=009EC7C673C76D745CBF298D5EA1B924; ppinf=5|1556031933|1557241533|dHJ1c3Q6MToxfGNsaWVudGlkOjQ6MjAxN3x1bmlxbmFtZTozOllhbnxjcnQ6MTA6MTU1NjAzMTkzM3xyZWZuaWNrOjM6WWFufHVzZXJpZDo0NDpvOXQybHVQWS1RUmh0T0cxbGJmWmw0YkZRdC1jQHdlaXhpbi5zb2h1LmNvbXw; pprdig=OzO0nVcC8P1Usx0TXd-W-ZRy9nkFlCAF7RhJuQpJRWg_ix4z3rxS94m6HuVT8gIjprZdQaFtd0XMj71_0IXQExFkGiRV6AtM4pk9PWW1w_e9nFUPmDAPRbbNsRtaoKC0b-PLk23DFnXMVpYo8lzNjI8aJdE9NP1ET8L4WfuKCjk; sgid=25-33350019-AVyicKb1G8wgl59ibvlrqU0z8; ppmdig=1556033657000000720837aab617941dac7372e025c8792c; sct=3; PHPSESSID=sm0i1iet2vgag0rtmc5o3nk171; SNUID=D8C06ADFADA92B99FF220857ADF86990; successCount=1|Tue, 23 Apr 2019 15:38:51 GMT; JSESSIONID=aaamtNHi5wbaihwjmG1Ow',
    'Host': 'weixin.sogou.com',
    'Referer': 'https://weixin.sogou.com/weixin?type=2&query=%E9%A3%8E%E6%99%AF&ie=utf8&s_from=input&_sug_=n&_sug_type_=1&w=01015002&oq=&ri=0&sourceid=sugg&sut=0&sst0=1556033614431&lkt=0,0,0&p=40040108',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36',
    'X-Requested-With': 'XMLHttpRequest'
}

#keyword = '风景'
#proxy_pool_url = 'http://localhost:5000/get'

proxy = None
#max_count = 5


def get_proxy():
    try:
        #response = requests.get(proxy_pool_url)
        response = requests.get(PROXY_POOL_URL)
        if response.status_code == 200:
            return response.text
        return None
    except ConnectionError:
        return None


def get_html(url, count=1):
    global proxy
    print('ip', proxy)
    print('Crawling', url)
    print('Trying Count', count)

    if count == MAX_COUNT:
    #if count == max_count:
        print('Tried Too Many Counts')
        return None
    try:
        if proxy:
            proxies = {
                'http': 'http://' + proxy
            }
            response = requests.get(url, allow_redirects=False, headers=headers, proxies=proxies) #allow_redirects 跳转
        else:
            response = requests.get(url, allow_redirects=False, headers=headers)
        if response.status_code == 200: #两个等于号
            return response.text
        if response.status_code == 302:
            # Need Proxy
            print('302')
            proxy = get_proxy()
            if proxy:
                print('Using Proxy', proxy)
                return get_html(url)
            else:
                print('Get Proxy Failed')
                return get_html(url)
    except ConnectionError as e:
        print('Error Occurred', e.args)
        proxy = get_proxy()
        count += 1
        return get_html(url, count)


def get_index(keyword, page):
    data = {
        'query': keyword,
        'type': 2,
        'page': page
    }
    queries = urlencode(data)
    url = base_url + queries
    html = get_html(url)
    #print(html)
    return html


def parse_index(html):
    doc = pq(html)
    items = doc('.news-box .news-list li .txt-box h3 a').items() #得到连接生成器
    for item in items:
        yield item.attr('href')


def get_detail(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
        return None
    except ConnectionError:
        return None


def parse_detail(html):
    try:
        doc = pq(html)
        title = doc('.rich_media_title').text()
        # content = doc('.rich_media_content ').text()
        # date = doc('#publish_time').text()
        # nickname = doc('.rich_media_meta_list #js_name').text()
        # wechat = doc('#js_profile_qrcode').text()
        return {
            'title': title,
            # 'content': content,
            # 'date': date,
            # 'nickname': nickname,
            # 'wechat': wechat
        }
    except XMLSyntaxError:
        return None


def save_to_mongo(data):
    if db['articles'].update({'title': data['title']},{'$set': data}, True):
        print('Saved to Mongo', data['title'])
    else:
        print('aved to Mongo Failed', data['title'])


def main():
    for page in range(1,4):
        #html = get_index(keyword, page)
        html = get_index(KEYWORD, page)
        #print(html)
        if html:
            article_urls = parse_index(html)
            for article_url in article_urls:
                #print(article_url)
                article_html = get_detail(article_url)
                if article_html:
                    article_data = parse_detail(article_html)
                    #print(article_data)
                    if article_data:
                        save_to_mongo(article_data)


if __name__ == '__main__': #两个等于号
    main()

