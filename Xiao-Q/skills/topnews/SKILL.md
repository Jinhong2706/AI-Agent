# 早盘舆情分析技能

每日开盘前自动采集全球市场数据与财经资讯，生成结构化早盘简报。

## 功能概述

- **美股行情**：道琼斯、纳斯达克、标普500 实时收盘数据
- **期货市场**：富时A50期指、原油、黄金、铜、铁矿石等
- **财联社快讯**：7×24小时财经电报，自动情感分类（利好/利空/中性）
- **宏观与国际**：国内政策要闻 + 国际财经新闻
- **资金面**：北向资金、融资融券
- **智能结论**：综合多维度数据，自动判断当日市场环境（偏多/偏空/震荡）

## 定时任务

| cron | 时间 | 任务 | action |
|------|------|------|--------|
| 30 6 * * 1-5 | 06:30 | 执行早盘简报采集并推送 | run_now |

## 技能入口

```python
from news_skill_handler import skill_handler

# 立即执行一次
result = skill_handler({'action': 'run_now'})
print(result['report'])

# 仅采集数据（不生成报告）
result = skill_handler({'action': 'collect'})
print(result['data'])

# 查看支持的 action 列表
result = skill_handler({'action': 'help'})
```

## Actions 说明

| Action | 参数 | 说明 |
|--------|------|------|
| `run_now` | 无 | 完整执行：采集→分析→生成简报→推送 |
| `collect` | 无 | 仅采集原始数据，返回 JSON |
| `help` | 无 | 返回可用 actions 列表 |

## 返回值格式

```json
{
    "success": true,
    "action": "run_now",
    "timestamp": "2026-04-09 06:30:00",
    "report": "完整简报文本...",
    "data_summary": {
        "us_stock": 3,
        "futures": 9,
        "cls_news": 20,
        "macro_news": 30,
        "capital_flow": 0
    },
    "verdict": "偏多"
}
```

## 文件结构

```
news_product_stock/
├── SKILL.md              # 技能文档（本文件）
├── skill.json            # 技能元数据
├── news_skill_handler.py # 技能统一入口
├── main.py               # 独立运行入口
├── config.py             # 配置管理
├── scheduler.py          # 定时调度
├── collectors/           # 数据采集模块
│   ├── base.py           #   基础采集器
│   ├── us_stock.py       #   美股行情
│   ├── futures.py        #   期货市场
│   ├── cls_news.py       #   财联社快讯
│   ├── macro_news.py     #   宏观政策/国际要闻
│   └── capital_flow.py   #   资金面
├── report/
│   └── generator.py      #   简报生成器
├── notifiers/
│   └── __init__.py       #   推送模块（企业微信/控制台/文件）
├── reports/              # 简报存档目录
├── .env.example          # 环境变量模板
└── requirements.txt      # Python 依赖
```

## 数据源

| 数据源 | 接口 | 类型 |
|--------|------|------|
| 东方财富 API | push2.eastmoney.com | 美股指数 / 期货行情 / 新闻 |
| 新浪财经 | hq.sinajs.cn | 行情备用源 |
| 财联社 API | cls.cn/nodeapi | 7×24 电报快讯 |
| 新浪 Feed | feed.mix.sina.com.cn | 国际财经新闻 |
| akshare | Tushare/AKShare | 北向资金（可选） |

## 配置说明

复制 `.env.example` 为 `.env` 并填入：

```bash
WECOM_WEBHOOK_URL=    # 企业微信机器人 Webhook（选填）
DEEPSEEK_API_KEY=     # DeepSeek API Key（LLM增强分析用）
REPORT_TIME=06:30     # 定时推送时间
```

## 依赖

```
httpx==0.27.0
beautifulsoup4==4.12.3
lxml==5.1.0
apscheduler==3.10.4
python-dotenv==1.0.1
akshare==1.14.0
```
