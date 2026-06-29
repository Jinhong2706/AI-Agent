# AI-Stock-Researcher 工作流集合

## 📋 工作流列表

### 股票分析
| 工作流 | 说明 | 触发词 |
|--------|------|--------|
| [stock-analysis](stock-analysis.md) | 全维度股票分析 | `/stock-analysis` |
| [stock-comparison](stock-comparison.md) | 股票对比分析 | `/stock-compare` |
| [sector-analysis](sector-analysis.md) | 板块分析 | `/sector-analysis` |

### 量化选股
| 工作流 | 说明 | 触发词 |
|--------|------|--------|
| [quant-screening](quant-screening.md) | 量化选股 | `/quant-screen` |
| [factor-strategy](factor-strategy.md) | 因子策略 | `/factor-strategy` |

### 基金研究
| 工作流 | 说明 | 触发词 |
|--------|------|--------|
| [fund-research](fund-research.md) | 基金研究 | `/fund-research` |
| [fund-comparison](fund-comparison.md) | 基金对比 | `/fund-compare` |

### 数据管理
| 工作流 | 说明 | 触发词 |
|--------|------|--------|
| [data-update](data-update.md) | 数据更新 | `/data-update` |
| [daily-report](daily-report.md) | 每日报告 | `/daily-report` |

## 🚀 快速开始

### 手动执行工作流
```bash
# 股票分析
/workflow stock-analysis 600519

# 量化选股
/workflow quant-screen --pe-max 30 --roe-min 15

# 基金研究
/workflow fund-research 000001
```

### 命令行工具
```bash
# 实时行情
python scripts/stock_query.py 600519,000858

# 全维度分析
python scripts/full_analysis.py 600519

# 量化选股
python scripts/screening.py --pe-max 30 --roe-min 15

# 基金查询
python scripts/fund_query.py --code 000001
```

## 📊 功能模块

### 7位AI分析师
| 分析师 | 维度 | 权重 |
|--------|------|------|
| 基本面分析师 | 价值 | 25% |
| 技术分析师 | 动量 | 15% |
| 风险分析师 | 风险 | 15% |
| 情绪分析师 | 情绪 | 15% |
| 成长分析师 | 成长 | 20% |
| 宏观分析师 | 宏观 | 10% |
| 综合分析师 | 汇总 | - |

### 数据源
- 新浪财经（主）
- 腾讯财经（备用）
- AkShare（历史数据）
- 东方财富（新闻）

## 🔧 配置说明

### 环境变量
```bash
# LLM配置
LLM_API_KEY=your_api_key
LLM_BASE_URL=https://api.deepseek.com

# 缓存配置
CACHE_TTL=300
CACHE_DIR=.cache
```

### 依赖安装
```bash
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple \
    akshare pandas numpy matplotlib flask requests \
    empyrical arch playwright openpyxl python-docx
```

## 📈 使用示例

### 股票分析
```bash
# 单只股票分析
python scripts/full_analysis.py 600519

# 批量查询
python scripts/stock_query.py 600519,000858,300750
```

### 量化选股
```bash
# 条件选股
python scripts/screening.py --pe-max 30 --roe-min 15 --pb-max 5

# 表达式选股
python scripts/screening.py --expr "pe<30 and roe>15 and pb<5"
```

### 板块分析
```bash
# 板块预测
python scripts/sector_forecast.py 半导体

# 基金新闻
python scripts/news_crawler.py --limit 50
```

## 🐛 故障排除

### 常见问题
1. **行情获取失败**
   - 检查网络连接
   - 尝试其他数据源

2. **选股无结果**
   - 放宽筛选条件
   - 检查数据完整性

3. **分析报错**
   - 检查股票代码格式
   - 查看日志文件

### 日志位置
- 分析日志: `logs/analysis.log`
- 错误日志: `logs/error.log`
- 缓存目录: `.cache/`

## 🔗 相关资源
- [SKILL.md](../../SKILL.md) - Skill主文档
- [README.md](../../README.md) - 项目说明
- [核心代码](../../core/) - 核心模块
