# 抖音对标账号工具 - Scripts 脚本目录

本目录包含抖音对标账号分析工具的核心 Python 脚本集合，提供完整的对标账号分析功能。

## 📁 目录结构

```
benchmarking/
├── __init__.py                  # 模块初始化
├── README.md                    # 本文档
├── account_collector.py         # 对标账号信息采集
├── fan_profile_analyzer.py      # 粉丝画像分析
├── viral_video_analyzer.py      # 爆款视频分析
├── content_strategy_parser.py   # 内容策略拆解
├── competitor_monitor.py        # 竞品动态监控
├── benchmark_comparator.py      # 数据对比分析
└── growth_strategy_generator.py  # 增长策略生成
```

## 🔧 功能模块

### 1. account_collector.py - 对标账号采集器

**功能**：批量采集对标账号的基础信息、作品数据、粉丝数据

**主要类**：
- `AccountCollector` - 采集器主类
- `AccountInfo` - 账号基础信息数据类
- `VideoInfo` - 视频作品信息数据类
- `LiveInfo` - 直播信息数据类

**核心方法**：
```python
from account_collector import AccountCollector

collector = AccountCollector(source="chanmama")

# 采集单个账号
account = collector.collect_account_info("https://www.douyin.com/user/xxx")

# 采集作品列表
videos = collector.collect_account_videos(account_id, limit=30, min_likes=1000)

# 采集粉丝数据
fan_data = collector.collect_fan_data(account_id)

# 批量采集
results = collector.batch_collect(["url1", "url2", "url3"])

# 导出数据
json_data = collector.export_data(format="json")
```

---

### 2. fan_profile_analyzer.py - 粉丝画像分析器

**功能**：深度分析对标账号的粉丝特征、行为习惯、商业价值

**主要类**：
- `FanProfileAnalyzer` - 分析器主类
- `FanProfile` - 粉丝画像数据类
- `ContentPreference` - 内容偏好数据类

**核心方法**：
```python
from fan_profile_analyzer import FanProfileAnalyzer

analyzer = FanProfileAnalyzer()

# 分析粉丝画像
profile = analyzer.analyze_fan_profile(fan_data, category="美妆")

# 与行业基准对比
comparison = analyzer.compare_with_benchmark(profile, category="美妆")

# 分析内容偏好
preference = analyzer.analyze_content_preference(fan_data, video_data)

# 生成分析报告
report = analyzer.generate_fan_report(profile, comparison, preference)
```

---

### 3. viral_video_analyzer.py - 爆款视频分析器

**功能**：深度拆解爆款视频的内容规律、选题策略、呈现形式

**主要类**：
- `ViralVideoAnalyzer` - 分析器主类
- `ViralVideo` - 爆款视频数据类
- `VideoAnalysis` - 视频分析结果数据类

**核心方法**：
```python
from viral_video_analyzer import ViralVideoAnalyzer

analyzer = ViralVideoAnalyzer()

# 识别爆款视频
viral_videos = analyzer.identify_viral_videos(videos, follower_count=100000)

# 深度分析单个视频
analysis = analyzer.analyze_video_structure(video)

# 爆款模式对比分析
patterns = analyzer.compare_viral_patterns(viral_videos)

# 生成爆款报告
report = analyzer.generate_viral_report(viral_videos, patterns)
```

---

### 4. content_strategy_parser.py - 内容策略拆解器

**功能**：深度拆解对标账号的内容策略、选题方向、人设定位

**主要类**：
- `ContentStrategyParser` - 拆解器主类
- `ContentStrategy` - 内容策略数据类
- `PersonaProfile` - 人设画像数据类

**核心方法**：
```python
from content_strategy_parser import ContentStrategyParser

parser = ContentStrategyParser()

# 解析内容策略
strategy = parser.parse_content_strategy(account_data, video_data, fan_data)

# 解析人设画像
persona = parser.parse_persona(account_data)

# 生成策略报告
report = parser.generate_strategy_report(strategy, persona)
```

---

### 5. competitor_monitor.py - 竞品动态监控器

**功能**：实时监控对标账号的更新、爆款、直播等动态变化

**主要类**：
- `CompetitorMonitor` - 监控器主类
- `CompetitorUpdate` - 竞品动态数据类
- `MonitoringTask` - 监控任务数据类

**核心方法**：
```python
from competitor_monitor import CompetitorMonitor

monitor = CompetitorMonitor()

# 创建监控任务
task = monitor.create_monitoring_task(
    account_ids=["acc1", "acc2"],
    monitor_types=["video", "follower", "viral", "live"],
    frequency="daily"
)

# 设置基准数据
monitor.set_baseline("acc1", baseline_data)

# 执行监控
results = monitor.execute_monitoring(task.task_id, accounts_data)

# 获取监控汇总
summary = monitor.get_monitoring_summary()

# 生成告警报告
report = monitor.generate_alert_report(results["alerts"])
```

---

### 6. benchmark_comparator.py - 对标对比分析器

**功能**：多维度对比自身与对标账号的数据差异，量化追赶目标

**主要类**：
- `BenchmarkComparator` - 对比器主类
- `AccountMetrics` - 账号指标数据类
- `MetricComparison` - 指标对比结果数据类

**核心方法**：
```python
from benchmark_comparator import BenchmarkComparator

comparator = BenchmarkComparator()

# 收集自身指标
my_metrics = comparator.collect_my_account_metrics(account_data, video_data, fan_data)

# 收集对标指标
benchmark_metrics = comparator.collect_benchmark_metrics(benchmark_data, ...)

# 对比指标差异
comparisons = comparator.compare_metrics(my_metrics, benchmark_metrics)

# 计算整体差距
overall_gap = comparator.calculate_overall_gap(comparisons)

# 估算追赶时间
catch_up_plan = comparator.estimate_catch_up_time(my_metrics, benchmark_metrics)

# 生成对比报告
report = comparator.generate_comparison_report(my_metrics, benchmark_metrics, ...)
```

---

### 7. growth_strategy_generator.py - 增长策略生成器

**功能**：基于对标分析结果，生成可落地的增长策略和执行方案

**主要类**：
- `GrowthStrategyGenerator` - 生成器主类
- `GrowthStrategy` - 增长策略数据类
- `ContentPlan` - 内容计划数据类

**核心方法**：
```python
from growth_strategy_generator import GrowthStrategyGenerator

generator = GrowthStrategyGenerator()

# 分析增长阶段
phase = generator.analyze_growth_phase(followers=50000)

# 生成增长策略
strategy = generator.generate_strategy(my_metrics, benchmark_analysis, target_metrics)

# 生成内容日历
content_plans = generator.generate_content_calendar(strategy, weeks=4)

# 生成执行清单
checklist = generator.generate_action_checklist(strategy, content_plan)

# 生成策略报告
report = generator.generate_strategy_report(strategy, content_plans, checklist)
```

---

## 📊 数据流程

```
┌─────────────────┐
│  1. 数据采集    │  account_collector.py
│  (账号/作品/粉丝)│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  2. 粉丝分析     │  fan_profile_analyzer.py
│  (画像/偏好)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  3. 爆款分析     │  viral_video_analyzer.py
│  (规律/结构)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  4. 策略拆解     │  content_strategy_parser.py
│  (内容/人设)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  5. 竞品监控     │  competitor_monitor.py
│  (动态/告警)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  6. 数据对比     │  benchmark_comparator.py
│  (差距/KPI)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  7. 策略生成     │  growth_strategy_generator.py
│  (方案/执行)     │
└─────────────────┘
```

## 🚀 快速使用

### 完整分析流程示例

```python
from benchmarking import (
    AccountCollector,
    FanProfileAnalyzer,
    ViralVideoAnalyzer,
    ContentStrategyParser,
    CompetitorMonitor,
    BenchmarkComparator,
    GrowthStrategyGenerator
)

# Step 1: 采集数据
collector = AccountCollector()
accounts = collector.batch_collect(["url1", "url2", "url3"])

# Step 2: 粉丝分析
fan_analyzer = FanProfileAnalyzer()
for acc in accounts["success"]:
    profile = fan_analyzer.analyze_fan_profile(acc["data"]["fans"])

# Step 3: 爆款分析
video_analyzer = ViralVideoAnalyzer()
viral_videos = video_analyzer.identify_viral_videos(acc["data"]["videos"])

# Step 4: 策略拆解
strategy_parser = ContentStrategyParser()
strategy = strategy_parser.parse_content_strategy(
    acc["data"]["account"], 
    acc["data"]["videos"], 
    acc["data"]["fans"]
)

# Step 5: 竞品监控
monitor = CompetitorMonitor()
task = monitor.create_monitoring_task([acc["account_id"] for acc in accounts["success"]])

# Step 6: 数据对比
comparator = BenchmarkComparator()
my_metrics = comparator.collect_my_account_metrics(my_data, my_videos, my_fans)
bench_metrics = comparator.collect_benchmark_metrics(acc_data, acc_videos, acc_fans)
comparisons = comparator.compare_metrics(my_metrics, bench_metrics)

# Step 7: 策略生成
strategy_gen = GrowthStrategyGenerator()
growth_strategy = strategy_gen.generate_strategy(my_metrics, {}, target_metrics)
content_plan = strategy_gen.generate_content_calendar(growth_strategy)

# 导出完整报告
report = strategy_gen.generate_strategy_report(growth_strategy, content_plan, {})
print(report)
```

## 📋 依赖要求

- Python 3.7+
- 无需额外依赖（使用标准库）

## 📝 注意事项

1. **数据来源**：实际使用时需要接入真实数据源（如蝉妈妈API、飞瓜数据等）
2. **模拟数据**：当前脚本中的数据为模拟数据，用于演示功能
3. **API配置**：使用真实API需要在各脚本中配置相应的API密钥和端点

## 🔄 版本历史

- v1.0.0 (2024) - 初始版本，包含7个核心分析模块

## 📧 联系方式

如有问题或建议，请联系开发团队。
