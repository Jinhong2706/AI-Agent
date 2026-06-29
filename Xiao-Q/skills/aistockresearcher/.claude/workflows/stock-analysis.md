# 股票全维度分析工作流

## 概述
7位AI分析师协作，对股票进行全维度分析评估。

## 触发词
- 股票分析
- 分析股票
- 全维度分析
- 综合评估

## 输入参数
| 参数 | 说明 | 示例 |
|------|------|------|
| code | 股票代码 | 600519 |

## 工作流步骤

### Phase 1: 获取实时行情
```python
from core.data_providers.stock_price import StockPriceProvider

provider = StockPriceProvider()
quote = provider.get("600519")

print(f"股票: {quote['name']}")
print(f"价格: {quote['price']}")
print(f"涨跌: {quote['change_pct']:+.2f}%")
```

### Phase 2: 7位分析师评估
```python
from core.agents import AnalystTeam

team = AnalystTeam()
analysis = team.analyze("600519")

print(f"综合评分: {analysis['overall_score']}/100")
print(f"投资建议: {analysis['recommendation']}")

for name, dim in analysis['dimensions'].items():
    print(f"  {name}: {dim['score']}/100")
```

### Phase 3: 技术指标计算
```python
import pandas as pd
import numpy as np

def calculate_indicators(df):
    # 均线
    df['MA5'] = df['close'].rolling(5).mean()
    df['MA10'] = df['close'].rolling(10).mean()
    df['MA20'] = df['close'].rolling(20).mean()

    # RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    # MACD
    exp1 = df['close'].ewm(span=12, adjust=False).mean()
    exp2 = df['close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()

    return df
```

### Phase 4: 生成分析报告
```python
def generate_report(code, quote, analysis):
    report = f"""
# {quote['name']}({code}) 投资分析报告

## 基本信息
- 当前价格: ¥{quote['price']}
- 涨跌幅: {quote['change_pct']:+.2f}%
- 成交量: {quote['volume']:,}

## 综合评估
- 综合评分: {analysis['overall_score']}/100
- 投资建议: {analysis['recommendation']}

## 分析师评分
"""

    for name, dim in analysis['dimensions'].items():
        score = dim['score']
        bar = "█" * (score // 5) + "░" * (20 - score // 5)
        report += f"- {name}: {bar} {score}/100\n"

    return report
```

## 输出格式
```
📊 股票分析报告 - 贵州茅台(600519)
================================

📈 实时行情:
- 当前价格: ¥1850.00
- 涨跌幅: +1.25%
- 成交量: 12,345,678

🤖 7位分析师评估:
- 综合评分: 72.5/100
- 投资建议: BUY

📊 分析师评分:
██████████████░░░░░░ 基本面: 75/100
████████████░░░░░░░░ 技术面: 65/100
██████████████░░░░░░ 风险面: 70/100
████████████░░░░░░░░ 情绪面: 60/100
███████████████░░░░░ 成长性: 78/100
███████████░░░░░░░░░ 宏观面: 55/100

💡 投资建议:
- 基本面优秀，估值合理
- 技术面呈上升趋势
- 建议适量配置
```

## 相关工作流
- `/stock-compare` - 股票对比
- `/quant-screen` - 量化选股
- `/fund-research` - 基金研究
