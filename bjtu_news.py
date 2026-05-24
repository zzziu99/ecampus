"""
BJTU 新闻爬取模块
只抓取 news.bjtu.edu.cn 公开数据，尊重 robots.txt
"""

import urllib.request
import re
import time

NEWS_BASE = 'http://news.bjtu.edu.cn'
CACHE_DURATION = 1800  # 30分钟缓存

_cache = {'data': None, 'time': 0}


def _fetch(url):
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) E-campus/1.0'
    })
    resp = urllib.request.urlopen(req, timeout=10)
    return resp.read().decode('utf-8', errors='ignore')


def _clean(text):
    """清理HTML标签和多余空白"""
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def parse_news_list(html):
    """解析 news.bjtu.edu.cn 首页新闻列表"""
    news_list = []
    seen = set()

    # 1. 解析主业新闻 (带 title 属性的 A 标签)
    items = re.findall(
        r'<A[^>]*href="(info/\d+/\d+\.htm)"[^>]*title="([^"]*)"[^>]*>(.*?)</A>',
        html, re.IGNORECASE | re.DOTALL
    )
    for href, title_attr, inner in items:
        title = title_attr or _clean(inner)
        full_url = NEWS_BASE + '/' + href
        if title and len(title) > 4 and full_url not in seen:
            seen.add(full_url)
            news_list.append({
                'title': title,
                'url': full_url,
                'source': 'news.bjtu.edu.cn'
            })

    # 2. 解析要闻列表 (带日期的)
    items = re.findall(
        r'<LI><SPAN>(\d{4}-\d{2}-\d{2})</SPAN><A[^>]*href="(info/\d+/\d+\.htm)"[^>]*>(.*?)</A></LI>',
        html, re.IGNORECASE | re.DOTALL
    )
    for date, href, title in items:
        title = _clean(title)
        full_url = NEWS_BASE + '/' + href
        if title and len(title) > 4 and full_url not in seen:
            seen.add(full_url)
            news_list.append({
                'title': title,
                'url': full_url,
                'date': date,
                'source': 'news.bjtu.edu.cn'
            })

    # 3. 解析校园生活列表 (campus_list)
    items = re.findall(
        r'<li><a[^>]*href="(info/\d+/\d+\.htm)"[^>]*title="([^"]*)"[^>]*>.*?</a></li>',
        html, re.IGNORECASE | re.DOTALL
    )
    for href, title in items:
        full_url = NEWS_BASE + '/' + href
        if title and len(title) > 4 and full_url not in seen:
            seen.add(full_url)
            news_list.append({
                'title': title,
                'url': full_url,
                'source': 'news.bjtu.edu.cn'
            })

    # 去重（按URL）
    unique = {}
    for item in news_list:
        if item['url'] not in unique:
            unique[item['url']] = item
    return list(unique.values())[:30]  # 最多30条


def get_latest_news(force_refresh=False):
    """获取最新新闻列表（带缓存）"""
    now = time.time()
    if not force_refresh and _cache['data'] and (now - _cache['time']) < CACHE_DURATION:
        return _cache['data']

    try:
        html = _fetch(NEWS_BASE)
        news = parse_news_list(html)
        _cache['data'] = news
        _cache['time'] = now
        return news
    except Exception as e:
        # 缓存过期了就返回空
        if _cache['data']:
            return _cache['data']
        return {'error': str(e), 'news': []}


