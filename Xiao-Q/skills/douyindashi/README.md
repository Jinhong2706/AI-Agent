# 抖音运营大师 - Scripts 脚本目录

一站式抖音运营工具，整合文案生成、选题灵感、视频创作、数据分析、直播运营五大模块，共100+核心功能。

## 📁 目录结构

```
douyin_master/
├── SKILL.md                 # 技能说明文档
├── README.md                # 本文档
├── main.py                  # 主入口脚本
├── requirements.txt         # Python依赖
│
├── scripts/                 # 核心脚本目录
│   ├── trending_topics.py   # 热门话题分析
│   ├── script_generator.py  # 视频脚本生成
│   ├── title_generator.py   # 标题与文案生成
│   ├── optimal_time.py      # 发布时间推荐
│   ├── analytics_report.py  # 数据分析报告
│   ├── competitor_analysis.py # 竞品分析
│   ├── live_script.py       # 直播话术生成
│   └── live_review.py       # 直播复盘工具
│
├── templates/               # 模板目录
│   └── templates.md         # 脚本模板库
│
└── data/                    # 数据目录
    └── data_dict.md         # 数据字典
```

## 🚀 快速开始

### 安装依赖

```bash
pip install --no-deps -r requirements.txt
```

### 使用方法

```bash
# 查看帮助
python main.py --help

# 运行特定工具
python main.py --tool trending     # 热门话题分析
python main.py --tool script        # 视频脚本生成
python main.py --tool title        # 标题生成
python main.py --tool time         # 发布时间推荐
python main.py --tool analytics    # 数据分析
python main.py --tool competitor    # 竞品分析
python main.py --tool live         # 直播话术
python main.py --tool review       # 直播复盘
```

## 📜 核心脚本说明

### 1. trending_topics.py - 热门话题分析

**功能：**
- 获取抖音热榜话题
- 行业垂直热点追踪
- 热点蹭法指南
- 月度选题日历生成

**使用方法：**
```python
from scripts.trending_topics import TrendingTopicsAnalyzer

analyzer = TrendingTopicsAnalyzer(industry="美食")

# 获取热榜
trending = analyzer.get_douyin_trending()

# 获取行业热点
industry = analyzer.get_industry_trending("美食")

# 推荐选题
recommendations = analyzer.recommend_topics(5)

# 生成月度日历
calendar = analyzer.generate_monthly_calendar("5月")
```

### 2. script_generator.py - 视频脚本生成

**功能：**
- 口播稿生成
- 分镜脚本设计
- 内容结构规划
- 黄金开头/结尾生成

**使用方法：**
```python
from scripts.script_generator import VideoScriptGenerator

generator = VideoScriptGenerator()

# 生成完整脚本
script = generator.generate_script(
    theme="职场沟通技巧",
    duration=60,
    script_type="口播分享"
)

# 生成口播稿
oral_script = generator.generate_oral_script("时间管理", 60)

# 生成分镜表格
table = generator.generate_script_table("主题", 60)
```

### 3. title_generator.py - 标题与文案生成

**功能：**
- 爆款标题生成（10种公式）
- 标题优化
- 标题公式库
- AB测试标题

**使用方法：**
```python
from scripts.title_generator import TitleGenerator

generator = TitleGenerator()

# 生成标题
title = generator.generate_title("数字型", "时间管理")

# 优化标题
result = generator.optimize_title("如何做红烧肉")

# AB测试
ab_titles = generator.generate_ab_test_titles("职场沟通技巧", 4)

# 批量生成
titles = generator.batch_generate_titles("高效学习", 10)
```

### 4. optimal_time.py - 发布时间推荐

**功能：**
- 粉丝活跃时段分析
- 最佳发布时间推荐
- 发布日历生成
- 时段效果分析

**使用方法：**
```python
from scripts.optimal_time import OptimalTimeRecommender

recommender = OptimalTimeRecommender(industry="美食")

# 获取粉丝活跃时段
fan_data = recommender.get_fan_active_hours()

# 推荐最佳时间
rec = recommender.recommend_optimal_time("干货教程", "美食")

# 生成发布日历
calendar = recommender.generate_publishing_calendar(weeks=1)

# 生成报告
report = recommender.generate_time_report()
```

### 5. analytics_report.py - 数据分析报告

**功能：**
- 播放量分析
- 互动率分析
- 完播率分析
- 转化率分析
- 优化建议生成

**使用方法：**
```python
from scripts.analytics_report import AnalyticsReporter

reporter = AnalyticsReporter(industry="美食")

# 生成示例数据
videos = reporter.generate_sample_data(10)

# 分析单个视频
analysis = reporter.analyze_video(video)

# 生成汇总报告
summary = reporter.generate_summary_report(videos)

# 生成详细分析
detailed = reporter.generate_detailed_analysis(videos)

# 生成优化建议
suggestions = reporter.generate_optimization_suggestions(summary)
```

### 6. competitor_analysis.py - 竞品分析

**功能：**
- 竞品数据监控
- 差距分析
- SWOT分析
- 追赶策略

**使用方法：**
```python
from scripts.competitor_analysis import CompetitorAnalyzer

analyzer = CompetitorAnalyzer("我的账号")

# 添加竞品
analyzer.add_competitor("竞品A", "@jingpinA", 500000)

# 生成监控表
table = analyzer.generate_monitoring_table()

# 差距分析
gap = analyzer.analyze_gap(50000, 5000)

# SWOT分析
swot = analyzer.generate_swot_analysis(account_data)

# 追赶策略
strategy = analyzer.generate_catch_up_strategy(gap, swot)

# 内容规律分析
pattern = analyzer.analyze_content_patterns("竞品A")
```

### 7. live_script.py - 直播话术生成

**功能：**
- 开场话术
- 产品话术
- 促单话术
- 互动话术
- 完整直播脚本

**使用方法：**
```python
from scripts.live_script import LiveStreamScriptGenerator

generator = LiveStreamScriptGenerator()

# 生成开场
opening = generator.generate_opening("暖场", benefit="超多福利")

# 生成产品话术
product_script = generator.generate_product_script(product)

# 生成促单话术
promote = generator.generate_promote_script("紧迫感", count="20")

# 生成完整直播脚本
live_script = generator.generate_full_live_script(duration=120)

# 生成控场技巧
control = generator.generate_control_script()
```

### 8. live_review.py - 直播复盘

**功能：**
- 数据复盘
- 话术复盘
- 货品复盘
- 问题诊断
- 改进计划

**使用方法：**
```python
from scripts.live_review import LiveStreamReview

review = LiveStreamReview()

# 输入数据
review.input_live_data({
    "日期": "2024-05-15",
    "GMV目标": 50000,
    "实际GMV": 58000,
    ...
})

# 数据复盘
data_review = review.calculate_data_review()

# 货品复盘
product_review = review.calculate_product_review()

# 话术复盘
script_review = review.calculate_script_review()

# 问题诊断
diagnosis = review.generate_diagnosis()

# 改进计划
improvement = review.generate_improvement_plan()

# 完整报告
report = review.generate_full_review_report()
```

## 📊 行业基准数据

支持的行业：
- 美食
- 美妆
- 知识
- 职场
- 健身
- 穿搭
- 娱乐
- 母婴

各行业有不同的：
- 平均播放量基准
- 完播率基准
- 互动率基准
- 转粉率基准
- 最佳发布时间

## 🎯 使用示例

### 示例1：生成一周选题计划

```python
from scripts.trending_topics import TrendingTopicsAnalyzer

analyzer = TrendingTopicsAnalyzer(industry="美食")

# 获取热榜和行业热点
trending = analyzer.get_douyin_trending()
industry = analyzer.get_industry_trending()

# 生成月度日历
calendar = analyzer.generate_monthly_calendar("5月")

# 推荐选题
recommendations = analyzer.recommend_topics(7)
```

### 示例2：批量生成视频脚本

```python
from scripts.script_generator import VideoScriptGenerator

generator = VideoScriptGenerator()

topics = ["时间管理", "职场沟通", "高效学习"]
for topic in topics:
    script = generator.generate_script(topic, 60, "口播分享")
    # 保存脚本
```

### 示例3：竞品监控与分析

```python
from scripts.competitor_analysis import CompetitorAnalyzer

analyzer = CompetitorAnalyzer()

# 添加多个竞品
analyzer.add_competitor("竞品A", "@A", 500000)
analyzer.add_competitor("竞品B", "@B", 300000)

# 生成监控报告
my_account = {"名称": "我的账号", "粉丝数": 50000}
report = analyzer.generate_monitoring_report(my_account)
```

## 📝 模板使用

查看 `templates/templates.md` 获取：

- 视频脚本模板
- 直播脚本模板
- 封面文案模板
- 发布检查清单
- 复盘报告模板
- 话术模板库

## 🔧 扩展开发

### 添加新的标题公式

```python
from scripts.title_generator import TitleGenerator

generator = TitleGenerator()

# 添加自定义公式
generator.TITLE_FORMULAS["自定义型"] = [
    "你的{topic}，{result}",
    ...
]
```

### 添加新的话术模板

```python
from scripts.live_script import LiveStreamScriptGenerator

generator = LiveStreamScriptGenerator()

# 添加自定义开场
generator.OPENING_SCRIPTS["自定义"] = [
    "自定义话术...",
    ...
]
```

## 📚 数据来源

- 抖音热榜
- 微博热搜
- 百度指数
- 知乎热榜
- 创作者中心
- 蝉妈妈
- 飞瓜数据
- 新抖

## ⚠️ 注意事项

1. 数据为示例数据，实际使用时请接入真实API
2. 脚本中的基准数据仅供参考，需根据实际情况调整
3. 发布时间建议结合粉丝活跃数据进行调整
4. 话术模板需根据产品特性进行优化

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📧 联系方式

- 技能ID: 9d355da7-f143-473a-939a-074ec6d96cbf
- 版本: 1.0.2
- 平台: 虾评Skill
