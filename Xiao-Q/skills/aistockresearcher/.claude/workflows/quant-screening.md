# 量化选股工作流

## 概述
基于多因子模型的量化选股策略。

## 触发词
- 量化选股
- 选股策略
- 条件选股
- 因子选股

## 输入参数
| 参数 | 说明 | 默认值 |
|------|------|--------|
| pe-max | 市盈率上限 | 无 |
| roe-min | ROE下限 | 无 |
| pb-max | 市净率上限 | 无 |
| dy-min | 股息率下限 | 无 |
| industry | 行业筛选 | 无 |
| top | 返回数量 | 20 |

## 工作流步骤

### Phase 1: 获取股票池
```python
from core.data_providers.akshare_provider import AkShareProvider

provider = AkShareProvider()
stocks = provider.get_all_stocks()

print(f"股票池: {len(stocks)} 只")
```

### Phase 2: 多因子筛选
```python
def multi_factor_screen(stocks, conditions):
    """
    多因子筛选

    Args:
        stocks: 股票列表
        conditions: 筛选条件

    Returns:
        筛选结果
    """
    results = []

    for stock in stocks:
        score = 0
        factors = {}

        # PE因子
        if 'pe' in conditions:
            pe_min, pe_max = conditions['pe']
            if pe_min <= stock['pe'] <= pe_max:
                score += 20
                factors['pe'] = 'pass'

        # ROE因子
        if 'roe' in conditions:
            roe_min, roe_max = conditions['roe']
            if stock['roe'] >= roe_min:
                score += 25
                factors['roe'] = 'pass'

        # PB因子
        if 'pb' in conditions:
            pb_min, pb_max = conditions['pb']
            if pb_min <= stock['pb'] <= pb_max:
                score += 15
                factors['pb'] = 'pass'

        # 股息率因子
        if 'dy' in conditions:
            dy_min, dy_max = conditions['dy']
            if stock['dy'] >= dy_min:
                score += 10
                factors['dy'] = 'pass'

        if score >= 50:  # 至少通过50%的因子
            results.append({
                **stock,
                'score': score,
                'factors': factors
            })

    return sorted(results, key=lambda x: -x['score'])
```

### Phase 3: 行业分析
```python
def industry_analysis(stocks):
    """行业分布分析"""
    industry_stats = {}

    for stock in stocks:
        ind = stock.get('industry', '未知')
        if ind not in industry_stats:
            industry_stats[ind] = {
                'count': 0,
                'avg_pe': 0,
                'avg_roe': 0,
                'stocks': []
            }

        industry_stats[ind]['count'] += 1
        industry_stats[ind]['stocks'].append(stock['code'])

    # 计算平均值
    for ind, stats in industry_stats.items():
        ind_stocks = [s for s in stocks if s.get('industry') == ind]
        stats['avg_pe'] = sum(s['pe'] for s in ind_stocks) / len(ind_stocks)
        stats['avg_roe'] = sum(s['roe'] for s in ind_stocks) / len(ind_stocks)

    return industry_stats
```

### Phase 4: 生成选股报告
```python
def generate_screening_report(results, conditions):
    report = f"""
# 量化选股报告

## 筛选条件
"""

    for factor, (min_val, max_val) in conditions.items():
        report += f"- {factor}: {min_val} ~ {max_val}\n"

    report += f"""
## 筛选结果
共 {len(results)} 只股票符合条件

## TOP 10 推荐
| 排名 | 代码 | 名称 | PE | ROE | PB | 评分 |
|------|------|------|-----|------|-----|------|
"""

    for i, stock in enumerate(results[:10], 1):
        report += f"| {i} | {stock['code']} | {stock['name']} | "
        report += f"{stock['pe']:.1f} | {stock['roe']:.1f}% | "
        report += f"{stock['pb']:.2f} | {stock['score']} |\n"

    return report
```

## 输出格式
```
📊 量化选股报告
================

🎯 筛选条件:
- PE: 0 ~ 30
- ROE: 15% ~ 100%
- PB: 0 ~ 5

📈 筛选结果:
共 45 只股票符合条件

🏆 TOP 10 推荐:
┌────┬────────┬──────────┬───────┬───────┬──────┬──────┐
│排名│ 代码   │ 名称     │ PE    │ ROE   │ PB   │ 评分 │
├────┼────────┼──────────┼───────┼───────┼──────┼──────┤
│ 1  │ 600519 │ 贵州茅台 │ 28.5  │ 31.2% │ 8.92 │ 85   │
│ 2  │ 000858 │ 五粮液   │ 22.3  │ 25.8% │ 6.15 │ 80   │
│ 3  │ 002304 │ 洋河股份 │ 18.7  │ 20.1% │ 4.23 │ 75   │
└────┴────────┴──────────┴───────┴───────┴──────┴──────┘

📊 行业分布:
- 白酒: 5只
- 医药: 8只
- 科技: 12只
```

## 相关工作流
- `/stock-analysis` - 股票分析
- `/factor-strategy` - 因子策略
- `/stock-compare` - 股票对比
