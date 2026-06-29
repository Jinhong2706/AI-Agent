# AI股票研究员

> A股智能投研工具 — 技术分析 | 三维预测 | 多智能体 | 投资大师 | 量化模型 | 产业链 | GARCH波动率 | 因子评分 | 配对交易 | ML预测

## 功能一览

技术分析 · 三维预测 · 多智能体(7分析师) · 投资大师(巴菲特/格雷厄姆/林奇) · 产业链分析 · 持仓导入 · Web UI · MCP Server(27工具)

🆕 v2.1: GARCH波动率 · 多因子评分 · 配对交易 · ML预测 · 国内网络优化

## 快速开始

```bash
# 安装核心依赖
pip install requests pandas numpy scipy

# 安装量化分析依赖（v2.1.0新增）
pip install arch statsmodels scikit-learn

# 按需安装
pip install pytesseract Pillow python-pptx pdfplumber PyPDF2 selenium openpyxl  # 持仓导入
pip install reportlab   # PDF 报告
pip install langchain-core langchain-openai langchain-anthropic langgraph stockstats mootdx pydantic  # 多智能体

# 个股分析
python scripts/stock_researcher.py --codes 600519 --period short
# Web UI（http://localhost:5003）
python scripts/web_server.py
```

> 全部依赖在 `requirements.txt` 已激活（含 OCR/多智能体/报告导出/量化分析）。

## MCP 配置

```json
{
  "mcpServers": {
    "ai-stock-researcher": {
      "command": "python",
      "args": ["./mcp_server.py"]
    }
  }
}
```

## 文档

- [SKILL.md](SKILL.md) — 完整功能文档
- [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) — 常见问题与故障排查

## 数据源（国内网络直接可用 🇨🇳）

| 数据 | 来源 |
|------|------|
| A股实时行情 | 腾讯财经 qt.gtimg.cn |
| 历史K线 | mootdx (TCP) / 新浪财经备源 |
| 财务/估值数据 | 东方财富 / mootdx F10 |
| 股吧情绪 | 东方财富股吧 |
| 雪球讨论 | 雪球（需cookie） |
| 资金流向 | 东方财富 push2 |
| 一致预期EPS | 同花顺 10jqka |
| 财经新闻 | 财联社 / 东方财富 |
| 概念板块 | 百度股市通 |
| 北向资金 | 同花顺 hsgtApi |

> ⚠️ yfinance / Alpha Vantage 已移至可选依赖，国内网络不可用。

## 免责声明

本工具仅供投资参考，不构成投资建议。股票投资有风险，入市需谨慎。
