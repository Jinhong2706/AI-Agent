---
name: daily-news-digest
description: 每天定时汇总当日热点新闻，聚焦科技互联网、娱乐明星八卦、国际时事政治、体育赛事。自动抓取微博热搜、知乎热榜、新浪娱乐、36氪、虎嗅等平台，输出带时间、来源的详细 Markdown 表格，并在每天 22:00 自动推送到 QQ。适用于：用户要求"每天帮我汇总热点新闻"、"定时推送新闻摘要"、"每日资讯播报"等场景。触发关键词：每日新闻、热点汇总、新闻推送、定时资讯、daily news digest。
---

# daily-news-digest

每天 22:00 自动汇总当天热点新闻，输出详细表格并推送到 QQ。

## 功能概述

- 📱 科技互联网：36氪、虎嗅
- 🎬 娱乐明星八卦：新浪娱乐、微博热搜
- 🌍 国际时事政治：微博热搜、知乎热榜
- ⚽ 体育赛事：微博热搜、知乎热榜
- 其他热榜内容也会一并收录

输出格式：**Markdown 表格**，包含列：时间、来源、排名、标题、热度、简介

## 使用方式

### 手动触发（测试用）

分两步执行：

```bash
# 1. 抓取新闻，输出到 /tmp/daily_news.json
python3 scripts/fetch_news.py

# 2. 转为 Markdown 表格，输出到 /tmp/daily_news.md
python3 scripts/render_markdown.py
```

生成的 `/tmp/daily_news.md` 即为当日新闻汇总，可读取后发送给用户。

### 定时触发（正式使用）

通过 `schedule-reminder` 技能创建每日 22:00 的定时任务：

```bash
# 创建定时任务，每天 22:00 执行新闻汇总并推送
schedule-reminder --parameters '{
  "action": "create",
  "name": "每日新闻汇总",
  "schedule": {"kind": "cron", "expr": "0 22 * * *", "tz": "Asia/Shanghai"},
  "task": "执行每日新闻汇总：运行 scripts/fetch_news.py 和 scripts/render_markdown.py，读取生成的 /tmp/daily_news.md，将内容发送给用户小邓同学"
}'
```

## 文件结构

```
daily-news-digest/
├── SKILL.md              ← 本文件
└── scripts/
    ├── fetch_news.py     ← 抓取各平台热榜，输出 JSON
    └── render_markdown.py← 将 JSON 转为 Markdown 表格
```

## 抓取平台说明

| 平台 | 内容类型 | 备注 |
|------|---------|------|
| 微博热搜 | 全品类热点 | Top 20 |
| 知乎热榜 | 深度话题 | Top 20 |
| 新浪娱乐 | 娱乐八卦 | 最新 20 条 |
| 36氪 | 科技互联网 | 热门文章 20 条 |
| 虎嗅 | 科技商业 | 热门文章 20 条 |

## 输出示例

```markdown
# 📰 每日热点新闻汇总

> 生成时间：2026-06-02 22:00:00

| 时间 | 来源 | 排名 | 标题 | 热度 | 简介 |
|------|------|------|------|------|------|
| 2026-06-02 22:00:00 | 微博热搜 | 1 | XXX引发热议 | 1,234,567 | ... |
| 2026-06-02 22:00:00 | 知乎热榜 | 1 | 如何看待XXX | 热度 1234万 | ... |
```

## 注意事项

- 抓取脚本使用公开 API，无需密钥
- 若某平台临时不可用，不影响其他平台抓取结果
- Markdown 表格默认最多显示简介前 80 字，可调整 `render_markdown.py` 中的 `[:80]` 参数
- 如需增加来源平台，编辑 `fetch_news.py` 新增抓取函数即可
