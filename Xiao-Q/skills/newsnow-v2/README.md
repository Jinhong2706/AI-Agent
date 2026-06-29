# newsnow 新闻聚合技能

> 基于 [NewsNow](https://github.com/ourongxing/newsnow) 的多源新闻聚合工具，支持 39 个新闻源。

## 文件结构

```
newsnow-skill/
├── newsnow.py      # 核心脚本（CLI + Python API）
├── __init__.py     # 包入口
├── SKILL.md        # 技能说明文档
└── README.md       # 本文件
```

## 快速开始

```bash
# 查看所有可用源
python newsnow.py --list-sources

# 获取 IT之家热榜
python newsnow.py --source ithome

# 多源并发获取
python newsnow.py --source zhihu,weibo,github --limit 10

# JSON格式
python newsnow.py --source cls,jin10 --format json

# 测试指定源
python newsnow.py --source ithome --test
```

## Python API

```python
import sys; sys.path.insert(0, ".")
from newsnow import fetch_news, fetch_multiple, list_sources

data = fetch_news("ithome")
print(f"{data.get('status')} - {len(data.get('items', []))} 条")

results = fetch_multiple(["zhihu","github","baidu"], limit=10)
for sid, d in results.items():
    if "error" in d: print(f"{sid}: ERR")
    else: print(f"{sid}: {len(d['items'])} 条")

for sid, info in list_sources().items():
    print(f"  {sid:15} {info['name']:10} [{info['type']}]")
```

## 新闻源分类速查

| 分类 | 新闻源 |
|------|--------|
| 科技媒体 | ithome, sspai, juejin, solidot |
| 国际科技 | github, hackernews, producthunt, steam |
| 财经 | wallstreetcn, xueqiu, jin10, cls, gelonghui |
| 社媒热榜 | weibo, zhihu, douyin, tieba, baidu |
| 综合新闻 | thepaper, ifeng, toutiao, tencent |
| 国际 | sputniknewscn, cankaoxiaoxi, zaobao |

## 依赖

- Python 3.8+
- 仅标准库（urllib, json, argparse, concurrent.futures）
- 无第三方依赖

---
*基于 NewsNow 项目封装 · 2026-04-17*
