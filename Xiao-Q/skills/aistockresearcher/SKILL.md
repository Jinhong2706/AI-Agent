---
name: ai-stock-researcher
version: 2.3.0
description: "AI股票研究员 — A股智能投研工具。7位AI分析师多智能体、三维分析、量化选股、基金研究、好友持仓分析。全功能国内零VPN依赖。"
metadata:
  openclaw:
    emoji: "📈"
    requires: {bins: ["python3"], packages: ["akshare","pandas","numpy","matplotlib","flask","requests","playwright","empyrical","arch"]}
    tags: ["stock","A-shares","quant","fund","finance","investment","multi-agent","AI","friend-analysis"]
triggers:
  keywords: [股票, 行情, 分析, 选股, 基金, 板块, 涨跌, 估值, 量化, 投资, 好友分析, 朋友分析, 添加好友]
  patterns:
    - "(分析|查询|查看) (股票|行情|基金)"
    - "(量化|条件|因子) 选股"
    - "(对比|比较) (股票|基金)"
    - "(板块|行业) (分析|预测)"
    - "(生成|导出) (报告|分析)"
    - "(好友|朋友).*分析"
    - "添加.*好友"
---

# AI-Stock-Researcher v2.3 — A股智能投研工具

## 好友分析功能

支持为好友分析股票/基金持仓，适合帮朋友查看投资情况：

| 操作 | 示例 |
|------|------|
| 添加好友 | "添加好友 张三"、"添加好友 小李 备注：同事" |
| 查看好友列表 | "好友列表"、"查看好友" |
| 导入好友持仓 | 粘贴持仓文本、上传截图/文件 |
| 分析好友持仓 | "分析好友 张三"、"朋友持仓分析" |

**MCP 工具**：
- `add_friend` — 添加好友
- `import_friend_holdings_text` — 从文本导入好友持仓
- `list_friends` — 列出所有好友
- `analyze_friend` — 分析好友持仓
- `generate_friend_report` — 生成好友报告

## 使用方式
```bash
# 实时行情
python3 scripts/stock_query.py 600519,000858

# 全维度分析
python3 scripts/full_analysis.py 600519

# 量化选股
python3 scripts/screening.py --pe-max 30 --roe-min 15

# 基金查询
python3 scripts/fund_query.py --code 000001

# 快速工具
python3 scripts/quick_tools.py quote 600519 000858   # 行情
python3 scripts/quick_tools.py score 600519          # 评分
python3 scripts/quick_tools.py compare 600519 000858 # 对比

# 自动报告
python3 scripts/auto_report.py --type daily --watchlist 600519 000858

# 工作流执行
python3 scripts/run_workflow.py list                  # 列出工作流
python3 scripts/run_workflow.py run stock-analysis    # 执行工作流
```

## 依赖安装（国内镜像）
```bash
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple akshare pandas numpy matplotlib flask requests empyrical arch playwright openpyxl python-docx
playwright install chromium
```

## 自动化工作流

### 工作流集合
详见 [.claude/workflows/](.claude/workflows/) 目录：

| 工作流 | 说明 | 触发词 |
|--------|------|--------|
| stock-analysis | 全维度股票分析 | `/stock-analysis` |
| stock-comparison | 股票对比分析 | `/stock-compare` |
| quant-screening | 量化选股 | `/quant-screen` |
| sector-analysis | 板块分析 | `/sector-analysis` |
| fund-research | 基金研究 | `/fund-research` |
| daily-report | 每日报告 | `/daily-report` |

### 快速命令
```bash
# 行情查询
python3 scripts/quick_tools.py quote 600519

# 综合评分
python3 scripts/quick_tools.py score 600519 000858

# 股票对比
python3 scripts/quick_tools.py compare 600519 000858 300750

# 价格提醒
python3 scripts/quick_tools.py alert 600519 1900 --below
```
