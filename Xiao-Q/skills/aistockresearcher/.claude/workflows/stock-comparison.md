# 股票对比分析工作流

## 概述
对比多只股票的各项指标，帮助投资者做出选择。

## 触发词
- 股票对比
- 对比分析
- 哪个好
- 比较股票

## 输入参数
| 参数 | 说明 | 示例 |
|------|------|------|
| codes | 股票代码列表 | 600519,000858 |

## 工作流步骤

### Phase 1: 获取行情数据
```python
from core.data_providers.stock_price import StockPriceProvider

provider = StockPriceProvider()
codes = ["600519", "000858", "002304"]

quotes = {}
for code in codes:
    quote = provider.get(code)
    if quote.get('status') == 'success':
        quotes[code] = quote

print(f"获取到 {len(quotes)} 只股票行情")
```

### Phase 2: 多维度分析
```python
from core.agents import AnalystTeam

team = AnalystTeam()

analyses = {}
for code in codes:
    analysis = team.analyze(code)
    analyses[code] = analysis

print("多维度分析完成")
```

### Phase 3: 指标对比
```python
def compare_indicators(quotes, analyses):
    """对比各项指标"""
    comparison = {
        'basic': {},
        'valuation': {},
        'performance': {},
        'risk': {}
    }

    for code in codes:
        quote = quotes.get(code, {})
        analysis = analyses.get(code, {})

        # 基本信息
        comparison['basic'][code] = {
            'name': quote.get('name', ''),
            'price': quote.get('price', 0),
            'change_pct': quote.get('change_pct', 0)
        }

        # 估值指标
        comparison['valuation'][code] = {
            'pe': quote.get('pe', 0),
            'pb': quote.get('pb', 0),
            'ps': quote.get('ps', 0)
        }

        # 业绩指标
        comparison['performance'][code] = {
            'roe': quote.get('roe', 0),
            'revenue_growth': quote.get('revenue_growth', 0),
            'profit_growth': quote.get('profit_growth', 0)
        }

        # 风险指标
        comparison['risk'][code] = {
            'beta': quote.get('beta', 1),
            'volatility': quote.get('volatility', 0),
            'max_drawdown': quote.get('max_drawdown', 0)
        }

    return comparison
```

### Phase 4: 生成对比报告
```python
def generate_comparison_report(codes, quotes, analyses, comparison):
    report = f"""
# 股票对比分析报告

## 对比股票
"""

    for code in codes:
        quote = quotes.get(code, {})
        report += f"- {code} {quote.get('name', '')}\n"

    report += "\n## 基本信息对比\n\n"
    report += "| 指标 |"
    for code in codes:
        report += f" {code} |"
    report += "\n|------|"
    for _ in codes:
        report += "------|"
    report += "\n"

    # 价格对比
    report += "| 价格 |"
    for code in codes:
        price = comparison['basic'][code]['price']
        report += f" ¥{price:.2f} |"
    report += "\n"

    # 涨跌幅对比
    report += "| 涨跌幅 |"
    for code in codes:
        change = comparison['basic'][code]['change_pct']
        emoji = "🟢" if change >= 0 else "🔴"
        report += f" {emoji}{change:+.2f}% |"
    report += "\n"

    report += "\n## 估值指标对比\n\n"
    report += "| 指标 |"
    for code in codes:
        report += f" {code} |"
    report += "\n|------|"
    for _ in codes:
        report += "------|"
    report += "\n"

    # PE对比
    report += "| PE |"
    for code in codes:
        pe = comparison['valuation'][code]['pe']
        report += f" {pe:.1f} |"
    report += "\n"

    # PB对比
    report += "| PB |"
    for code in codes:
        pb = comparison['valuation'][code]['pb']
        report += f" {pb:.2f} |"
    report += "\n"

    report += "\n## 综合评分\n\n"
    report += "| 股票 | 评分 | 建议 |\n"
    report += "|------|------|------|\n"

    for code in codes:
        analysis = analyses.get(code, {})
        score = analysis.get('overall_score', 0)
        recommendation = analysis.get('recommendation', 'HOLD')
        name = quotes.get(code, {}).get('name', '')
        report += f"| {code} {name} | {score} | {recommendation} |\n"

    return report
```

## 输出格式
```
📊 股票对比分析报告
====================

🔍 对比股票:
- 600519 贵州茅台
- 000858 五粮液
- 002304 洋河股份

📈 基本信息对比:
┌────────┬──────────┬──────────┬──────────┐
│ 指标   │ 600519   │ 000858   │ 002304   │
├────────┼──────────┼──────────┼──────────┤
│ 价格   │ ¥1850.00 │ ¥168.50  │ ¥135.20  │
│ 涨跌幅 │ 🟢+1.25% │ 🔴-0.85% │ 🟢+0.45% │
└────────┴──────────┴──────────┴──────────┘

💰 估值指标对比:
┌────────┬──────────┬──────────┬──────────┐
│ 指标   │ 600519   │ 000858   │ 002304   │
├────────┼──────────┼──────────┼──────────┤
│ PE     │ 28.5     │ 22.3     │ 18.7     │
│ PB     │ 8.92     │ 6.15     │ 4.23     │
└────────┴──────────┴──────────┴──────────┘

🏆 综合评分:
┌──────────────┬──────┬──────┐
│ 股票         │ 评分 │ 建议 │
├──────────────┼──────┼──────┤
│ 600519 茅台  │ 75   │ BUY  │
│ 000858 五粮液│ 70   │ BUY  │
│ 002304 洋河  │ 65   │ HOLD │
└──────────────┴──────┴──────┘
```

## 相关工作流
- `/stock-analysis` - 单股分析
- `/quant-screen` - 量化选股
- `/sector-analysis` - 板块分析
