---
name: newsnow
description: NewsNow 新闻聚合技能，支持 39 个新闻源（科技、财经、社媒、综合新闻等）
homepage: https://github.com/ourongxing/newsnow
metadata:
  openclaw:
    emoji: 📰
    requires:
      bins: ["python3"]
    install:
      - id: python
        kind: python
        bins: ["newsnow.py"]
        module: "newsnow"
        label: "Install newsnow skill"
---

# NewsNow 新闻聚合

基于 [NewsNow](https://github.com/ourongxing/newsnow) 项目的新闻源聚合技能。

## 支持的新闻源 (39个)

| 分类 | 源ID | 名称 |
|------|------|------|
| 科技媒体 | ithome, sspai, solidot, freebuf | IT之家, 少数派, Solidot, FreeBuf |
| 技术社区 | juejin, v2ex, pcbeta, coolapk, github, hackernews, producthunt | 稀土掘金, V2EX, 远景论坛, 酷安, GitHub, Hacker News, Product Hunt |
| 财经媒体 | wallstreetcn, jin10, mktnews, gelonghui, cls | 华尔街见闻, 金十数据, 市场快讯, 格隆汇, 财联社 |
| 社交媒体 | weibo, zhihu, douyin, bilibili, tieba, douban | 微博, 知乎, 抖音, B站, 贴吧, 豆瓣 |
| 综合新闻 | thepaper, ifeng, toutiao, baidu, tencent, sputniknewscn, cankaoxiaoxi, zaobao | 澎湃, 凤凰, 头条, 百度, 腾讯, 卫星社, 参考消息, 联合早报 |
| 其他 | steam, xueqiu, hupu, nowcoder, iqiyi, qqvideo, chongbuluo, kaopu | Steam, 雪球, 虎扑, 牛客, 爱奇艺, 腾讯视频, 虫部落, 靠谱新闻 |

> ⚠️ 已验证不可用: linuxdo, kuaishou, xiaohongshu, smzdm, _36kr, ghxi

## 使用方式

```bash
# 查看帮助
python newsnow.py --help

# 列出所有新闻源
python newsnow.py --list-sources

# 获取单个新闻源
python newsnow.py --source ithome

# 获取多个新闻源（并发）
python newsnow.py --source zhihu,weibo,github --limit 20

# 测试新闻源可用性
python newsnow.py --source ithome --test

# 输出为 JSON 格式
python newsnow.py --source ithome --format json

# 输出为 Markdown 格式
python newsnow.py --source github --format markdown
```

## Python API

```python
from newsnow import fetch_news, fetch_multiple, list_sources, test_source

# 获取单个源
data = fetch_news("ithome")
for item in data["items"]:
    print(item["title"])

# 获取多个源（自动并发）
results = fetch_multiple(["zhihu", "github", "baidu"], limit=10)
for sid, data in results.items():
    print(f"=== {sid} ===")
    for item in data["items"]:
        print(f"  {item['title']}")
```

## 特性

- **并发请求**: 多源自动 ThreadPoolExecutor (max_workers=6)
- **超时处理**: 默认 12 秒，单源失败不影响其他源
- **缓存支持**: 服务器缓存约 30 分钟
- **依赖**: 仅 Python 标准库 (Python 3.8+)
