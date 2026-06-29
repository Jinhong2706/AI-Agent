#!/usr/bin/env python3
"""
每日热点新闻汇总脚本
抓取微博热搜、知乎热榜、新浪娱乐、36氪、虎嗅等平台热点
输出带时间、来源的详细表格
"""

import json
import time
import datetime
import urllib.request
import urllib.error

def fetch_json(url, headers=None):
    """简单封装 urlopen，返回解析后的 JSON"""
    try:
        req = urllib.request.Request(url, headers=headers or {
            "User-Agent": "Mozilla/5.0 (compatible; NewsBot/1.0)"
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"error": str(e)}

# ── 各平台抓取函数 ──────────────────────────────────────────────

def fetch_weibo():
    """微博热搜榜"""
    url = "https://weibo.com/ajax/side/hotSearch"
    data = fetch_json(url)
    results = []
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    items = data.get("data", {}).get("realtime", [])
    for i, item in enumerate(items[:20]):
        results.append({
            "时间": now,
            "来源": "微博热搜",
            "排名": i + 1,
            "标题": item.get("note", item.get("word", "")),
            "热度": item.get("num", ""),
            "简介": item.get("expand", ""),
        })
    return results


def fetch_zhihu():
    """知乎热榜"""
    url = "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total?limit=20"
    data = fetch_json(url, {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"})
    results = []
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    items = data.get("data", [])
    for i, entry in enumerate(items[:20]):
        target = entry.get("target", {})
        results.append({
            "时间": now,
            "来源": "知乎热榜",
            "排名": i + 1,
            "标题": target.get("title", ""),
            "热度": entry.get("detail_text", ""),
            "简介": "",
        })
    return results


def fetch_sina_ent():
    """新浪娱乐热点"""
    # 使用新浪新闻 API（娱乐频道）
    url = "https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2509&num=20&versionNumber=1.2.4&page=1"
    data = fetch_json(url)
    results = []
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    items = data.get("result", {}).get("data", [])
    for i, item in enumerate(items[:20]):
        results.append({
            "时间": now,
            "来源": "新浪娱乐",
            "排名": i + 1,
            "标题": item.get("title", ""),
            "热度": "",
            "简介": item.get("intro", item.get("summary", "")),
        })
    return results


def fetch_36kr():
    """36氪 热门文章"""
    url = "https://www.36kr.com/api/feed?category=hot&per_page=20"
    data = fetch_json(url, {"User-Agent": "Mozilla/5.0"})
    results = []
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    items = data.get("data", {}).get("items", [])
    for i, item in enumerate(items[:20]):
        results.append({
            "时间": now,
            "来源": "36氪",
            "排名": i + 1,
            "标题": item.get("title", ""),
            "热度": "",
            "简介": item.get("summary", ""),
        })
    return results


def fetch_huxiu():
    """虎嗅 热门文章"""
    url = "https://www.huxiu.com/rest/articles?limit=20&orderby=hot"
    data = fetch_json(url, {"User-Agent": "Mozilla/5.0"})
    results = []
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    items = data.get("data", {}).get("datalist", data.get("data", []))
    for i, item in enumerate(items[:20]):
        detail = item.get("data", item)
        results.append({
            "时间": now,
            "来源": "虎嗅",
            "排名": i + 1,
            "标题": detail.get("title", ""),
            "热度": "",
            "简介": detail.get("summary", ""),
        })
    return results


# ── 主流程 ────────────────────────────────────────────────────────

def main():
    print("开始抓取今日热点新闻...\n")

    all_news = []

    print("抓取微博热搜...")
    all_news.extend(fetch_weibo())

    print("抓取知乎热榜...")
    all_news.extend(fetch_zhihu())

    print("抓取新浪娱乐...")
    all_news.extend(fetch_sina_ent())

    print("抓取36氪...")
    all_news.extend(fetch_36kr())

    print("抓取虎嗅...")
    all_news.extend(fetch_huxiu())

    # 输出为 JSON（供下一步格式化）
    output_path = "/tmp/daily_news.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_news, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 共抓取 {len(all_news)} 条新闻，已保存到 {output_path}")
    return output_path


if __name__ == "__main__":
    main()
