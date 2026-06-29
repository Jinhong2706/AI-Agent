---
name: fund-evaluation
description: 中国公募基金评价分析工具，支持获取基金基本信息、季度持仓数据、持仓变动对比、业绩分析等功能。使用场景包括：分析基金重仓股、对比季度持仓变化、导出基金数据、基金定期报告数据提取等。特别适用于需要通过天天基金网获取Wind API无法提供的基金持仓明细数据的场景。
---

# 基金评价分析工具

用于获取和分析中国公募基金数据的工具集，支持从天天基金网获取Wind API无法提供的基金持仓明细数据。

## 核心功能

- **基金基本信息查询**：基金名称、基金经理、成立日期、净值等
- **季度持仓数据获取**：前十大重仓股、占净值比、持股数量
- **持仓变动对比**：季度间持仓增减持分析
- **数据导出**：支持导出CSV格式

## 使用方法

### 获取基金最新季度持仓

```python
import sys
sys.path.insert(0, 'fund-evaluation/scripts')
from fund_evaluator import FundEvaluator

evaluator = FundEvaluator()
result = evaluator.get_holdings("519702")
evaluator.print_holdings(result)
```

### 对比季度持仓变化

```python
# 对比最近两个季度
evaluator.compare_quarters("519702")

# 对比指定季度
evaluator.compare_quarters("519702", "2025年4季度", "2025年3季度")
```

### 导出数据到CSV

```python
evaluator.export_to_csv(result, "output.csv")
```

## 数据来源

- **天天基金网** (fundf10.eastmoney.com)：基金持仓明细数据
- **Wind API**（可选）：基金基本信息、历史净值

## 命令行使用

```bash
# 获取基金持仓
python fund-evaluation/scripts/fund_evaluator.py 519702

# 对比季度变化
python fund-evaluation/scripts/fund_evaluator.py 519702 --compare

# 导出CSV
python fund-evaluation/scripts/fund_evaluator.py 519702 --export output.csv
```

## 输出示例

持仓数据表格包含：
- 排名
- 股票代码
- 股票名称
- 占净值比例
- 持股数量（万股）
- 持仓市值（万元）

季度对比显示：
- 新增持仓
- 清仓/减持至前10外的股票
- 仓位变化超过0.5%的股票
