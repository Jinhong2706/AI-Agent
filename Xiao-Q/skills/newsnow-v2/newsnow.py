#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""newsnow - NewsNow 新闻聚合技能核心脚本 封装自 https://github.com/ourongxing/newsnow"""

import argparse, json, sys, time, urllib.error, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

DEFAULT_BASE_URL = "https://newsnow.busiyi.world"
TIMEOUT = 12
REQUEST_DELAY = 0.3

SOURCES = {
    "weibo":          {"name": "微博",        "type": "社交媒体"},
    "zhihu":          {"name": "知乎",        "type": "问答社区"},
    "douyin":         {"name": "抖音",        "type": "短视频"},
    "kuaishou":       {"name": "快手",        "type": "短视频"},
    "bilibili":       {"name": "哔哩哔哩",    "type": "视频平台"},
    "tieba":          {"name": "百度贴吧",    "type": "社区论坛"},
    "douban":         {"name": "豆瓣",         "type": "社区"},
    "xiaohongshu":    {"name": "小红书",      "type": "社区"},
    "ithome":         {"name": "IT之家",      "type": "科技媒体"},
    "sspai":          {"name": "少数派",      "type": "科技媒体"},
    "juejin":         {"name": "稀土掘金",    "type": "技术社区"},
    "nowcoder":       {"name": "牛客网",      "type": "求职社区"},
    "linuxdo":        {"name": "Linux.do",    "type": "技术社区"},
    "v2ex":           {"name": "V2EX",         "type": "技术社区"},
    "pcbeta":         {"name": "远景论坛",    "type": "技术论坛"},
    "coolapk":        {"name": "酷安",         "type": "数码社区"},
    "smzdm":          {"name": "什么值得买",  "type": "购物推荐"},
    "freebuf":        {"name": "FreeBuf",      "type": "网络安全"},
    "github":         {"name": "GitHub",       "type": "开源社区"},
    "hackernews":     {"name": "Hacker News",  "type": "科技新闻"},
    "producthunt":    {"name": "Product Hunt", "type": "产品发现"},
    "steam":          {"name": "Steam",        "type": "游戏平台"},
    "wallstreetcn":   {"name": "华尔街见闻",  "type": "财经媒体"},
    "xueqiu":         {"name": "雪球",         "type": "投资社区"},
    "jin10":          {"name": "金十数据",    "type": "财经数据"},
    "mktnews":        {"name": "市场快讯",     "type": "财经新闻"},
    "fastbull":       {"name": "快牛财经",    "type": "财经媒体"},
    "gelonghui":      {"name": "格隆汇",       "type": "财经媒体"},
    "thepaper":       {"name": "澎湃新闻",    "type": "综合新闻"},
    "ifeng":          {"name": "凤凰网",       "type": "综合新闻"},
    "toutiao":        {"name": "今日头条",    "type": "新闻聚合"},
    "baidu":          {"name": "百度热搜",    "type": "热搜榜"},
    "tencent":        {"name": "腾讯新闻",    "type": "综合新闻"},
    "sputniknewscn": {"name": "卫星通讯社",  "type": "国际新闻"},
    "cankaoxiaoxi":   {"name": "参考消息",    "type": "国际新闻"},
    "zaobao":         {"name": "联合早报",    "type": "国际新闻"},
    "_36kr":          {"name": "36氪",          "type": "科技商业"},
    "hupu":           {"name": "虎扑",          "type": "体育社区"},
    "cls":            {"name": "财联社",        "type": "财经快讯"},
    "iqiyi":          {"name": "爱奇艺",        "type": "视频平台"},
    "qqvideo":        {"name": "腾讯视频",     "type": "视频平台"},
    "chongbuluo":     {"name": "虫部落",        "type": "资源导航"},
    "ghxi":           {"name": "果核剥壳",    "type": "软件分享"},
    "kaopu":          {"name": "靠谱新闻",    "type": "新闻聚合"},
    "solidot":        {"name": "Solidot",       "type": "科技资讯"},
}

BROKEN = {"linuxdo", "kuaishou", "xiaohongshu", "smzdm", "_36kr", "ghxi"}

def _hdrs():
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json, text/html, */*",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Referer": "https://newsnow.busiyi.world/",
    }

def fetch_news(sid, base=DEFAULT_BASE_URL, tout=TIMEOUT):
    url = f"{base.rstrip('/')}/api/s?id={sid}"
    try:
        req = urllib.request.Request(url, headers=_hdrs())
        with urllib.request.urlopen(req, timeout=tout) as r:
            b = r.read()
            if b.startswith(b"<"): return {"error": "服务器返回HTML", "id": sid}
            d = json.loads(b)
            if "items" not in d: return {"error": "响应缺少items", "id": sid}
            return d
    except urllib.error.HTTPError as e: return {"error": f"HTTP {e.code}", "id": sid}
    except urllib.error.URLError as e: return {"error": f"网络错误 {e.reason}", "id": sid}
    except Exception as e: return {"error": str(e), "id": sid}

def fetch_multiple(sids, base=DEFAULT_BASE_URL, limit=30, tout=TIMEOUT, concurrent=True):
    res = {}
    if concurrent and len(sids) > 1:
        with ThreadPoolExecutor(max_workers=6) as p:
            futs = {p.submit(fetch_news, s, tout=tout): s for s in sids}
            for f in as_completed(futs):
                s = futs[f]
                try:
                    d = f.result()
                    if "error" not in d: d["items"] = d.get("items", [])[:limit]
                    res[s] = d
                except Exception as e: res[s] = {"error": str(e), "id": s}
    else:
        for s in sids:
            d = fetch_news(s, tout=tout)
            if "error" not in d: d["items"] = d.get("items", [])[:limit]
            res[s] = d
            time.sleep(REQUEST_DELAY)
    return res

def test_source(sid, base=DEFAULT_BASE_URL):
    d = fetch_news(sid, base)
    return "error" not in d and len(d.get("items", [])) > 0

def list_sources(include_broken=False):
    if include_broken: return SOURCES
    return {k: v for k, v in SOURCES.items() if k not in BROKEN}

def _t(it): return it.get("title", "(无标题)")
def _u(it): return it.get("url", "")
def _p(it): return it.get("pubDate") or (it.get("extra", {}).get("date") if it.get("extra") else "")
def _i(it): return (it.get("extra", {}).get("info") or "") if it.get("extra") else ""

def fmt_text(res, limit=30):
    out = []
    for sid, data in res.items():
        name = SOURCES.get(sid, {}).get("name", sid)
        if "error" in data: out.append(f"[{name}]  ERR: {data['error']}"); continue
        icon = "📦" if data.get("status") == "cache" else "✅"
        out.append(f"\n{icon} {name}（{sid}）- {len(data.get('items', []))} 条")
        out.append("─" * 50)
        for idx, it in enumerate(data.get("items", [])[:limit], 1):
            t, u, p, i_ = _t(it), _u(it), _p(it), _i(it)
            ln = f"  {idx:2}. {t}"
            if i_: ln += f"  [{i_}]"
            out.append(ln)
            if u: out.append(f"      🔗 {u}")
            if p: out.append(f"      🕐 {p}")
    return "\n".join(out)

def fmt_md(res, limit=30):
    sec = ["# 📰 NewsNow 新闻聚合\n"]
    for sid, data in res.items():
        name = SOURCES.get(sid, {}).get("name", sid)
        if "error" in data: sec.append(f"## ❌ {name}\n\n> ERR: {data['error']}\n"); continue
        sec.append(f"## ✅ {name}（{sid}）\n")
        for idx, it in enumerate(data.get("items", [])[:limit], 1):
            t, u, p = _t(it), _u(it), _p(it)
            sec.append(f"{idx}. **{t}**")
            if u: sec.append(f"   🔗 [链接]({u})")
            if p: sec.append(f"   🕐 {p}")
            sec.append("")
    return "\n".join(sec)

def fmt_json(res): return json.dumps(res, ensure_ascii=False, indent=2)

def list_src_txt(inc=False):
    by = {}
    for s, i in list_sources(inc).items(): by.setdefault(i["type"], []).append(f"  - `{s}` {i['name']}")
    out = ["# 📡 NewsNow 支持的新闻源\n"]
    for t, itms in sorted(by.items()): out.append(f"## {t}\n" + "\n".join(itms) + "\n")
    if inc:
        out.append("\n## ⚠️ 已验证不可用\n")
        for s in sorted(BROKEN): out.append(f"  - `{s}` {SOURCES.get(s, {}).get('name', s)}")
    out.append(f"\n总计: {len(list_sources(False))} 个可用源")
    return "\n".join(out)

def main():
    p = argparse.ArgumentParser(description="📰 newsnow - NewsNow 新闻聚合工具", formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("-s", "--source", help="新闻源 ID（必填，逗号分隔多源）")
    p.add_argument("-l", "--limit", type=int, default=30, help="每源最多返回条数（默认30）")
    p.add_argument("-f", "--format", choices=["json", "text", "markdown"], default="text", help="输出格式")
    p.add_argument("--base-url", default=DEFAULT_BASE_URL)
    p.add_argument("--list-sources", action="store_true")
    p.add_argument("--list-all", action="store_true")
    p.add_argument("--test", action="store_true")
    p.add_argument("--test-all", action="store_true")
    a = p.parse_args()
    if a.list_all: print(list_src_txt(True)); return
    if a.list_sources: print(list_src_txt(False)); return
    if a.test_all:
        print("正在测试所有新闻源...\n")
        for s in SOURCES:
            ok = test_source(s, a.base_url)
            print(f"{'✅' if ok else '❌'} {s}: {SOURCES[s]['name']}")
            time.sleep(REQUEST_DELAY)
        return
    if a.test:
        if not a.source: print("❌ --test 需要 --source", file=sys.stderr); sys.exit(1)
        for s in [x.strip() for x in a.source.split(",")]:
            ok = test_source(s, a.base_url)
            print(f"{'✅' if ok else '❌'} {s} ({SOURCES.get(s, {}).get('name', s)}): {'可用' if ok else '不可用'}")
        return
    if not a.source: print("❌ 请指定 --source（或用 --list-sources）", file=sys.stderr); sys.exit(1)
    sids = [x.strip() for x in a.source.split(",")]
    print(f"📡 正在获取 {len(sids)} 个新闻源...", file=sys.stderr)
    res = fetch_multiple(sids, a.base_url, limit=a.limit)
    if a.format == "json": print(fmt_json(res))
    elif a.format == "markdown": print(fmt_md(res, limit=a.limit))
    else: print(fmt_text(res, limit=a.limit))

if __name__ == "__main__": main()
