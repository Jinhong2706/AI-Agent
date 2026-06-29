#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抖音运营大师 - 核心工具集
一站式抖音运营工具，整合文案生成、选题灵感、视频创作、数据分析、直播运营五大模块

使用方法:
    python main.py --tool <工具名>
    
可用工具:
    trending      - 热门话题分析
    script        - 视频脚本生成
    title         - 标题与文案生成
    time          - 发布时间推荐
    analytics     - 数据分析报告
    competitor    - 竞品分析
    live          - 直播话术生成
    review        - 直播复盘

示例:
    python main.py --tool trending
    python main.py --tool script --theme "职场沟通技巧"
    python main.py --tool analytics --industry "美食"
"""

import argparse
import sys

# 导入各模块
from scripts.trending_topics import TrendingTopicsAnalyzer
from scripts.script_generator import VideoScriptGenerator
from scripts.title_generator import TitleGenerator
from scripts.optimal_time import OptimalTimeRecommender
from scripts.analytics_report import AnalyticsReporter
from scripts.competitor_analysis import CompetitorAnalyzer
from scripts.live_script import LiveStreamScriptGenerator
from scripts.live_review import LiveStreamReview


def show_banner():
    """显示横幅"""
    print("""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║     🎬 抖音运营大师 - 核心工具集 🎬                        ║
║                                                           ║
║     一站式抖音运营工具，100+核心功能                       ║
║     文案生成 | 选题灵感 | 视频创作 | 数据分析 | 直播运营    ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
    """)


def show_help():
    """显示帮助"""
    print("""
📚 使用方法

    python main.py --tool <工具名> [选项]

🎯 可用工具

    trending      热门话题分析
                  - 追踪热点选题
                  - 分析热度趋势
                  - 推荐蹭热点方式
                  
    script        视频脚本生成
                  - 生成口播稿/剧本
                  - 分镜脚本设计
                  - 内容结构规划
                  
    title         标题与文案生成
                  - 爆款标题生成
                  - 标题公式库
                  - AB测试标题
                  
    time          发布时间推荐
                  - 粉丝活跃分析
                  - 最佳时段推荐
                  - 发布日历生成
                  
    analytics     数据分析报告
                  - 播放量分析
                  - 互动率分析
                  - 完播率分析
                  
    competitor    竞品分析
                  - 竞品数据监控
                  - 差距分析
                  - SWOT分析
                  
    live          直播话术生成
                  - 开场话术
                  - 产品话术
                  - 促单话术
                  
    review        直播复盘
                  - 数据复盘
                  - 话术复盘
                  - 货品复盘

💡 示例

    # 热门话题分析
    python main.py --tool trending --industry "美食"
    
    # 视频脚本生成
    python main.py --tool script --theme "职场沟通技巧" --duration 60
    
    # 标题生成
    python main.py --tool title --topic "时间管理" --count 10
    
    # 发布时间推荐
    python main.py --tool time --industry "美食"
    
    # 数据分析
    python main.py --tool analytics --industry "美食"
    
    # 竞品分析
    python main.py --tool competitor
    
    # 直播话术
    python main.py --tool live --duration 120
    
    # 直播复盘
    python main.py --tool review

📖 详细文档

    查看 scripts/*.py 获取各工具详细文档
    查看 templates/templates.md 获取模板库
    查看 data/data_dict.md 获取数据字典
""")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="抖音运营大师 - 核心工具集")
    parser.add_argument("--tool", "-t", type=str, help="选择工具")
    parser.add_argument("--industry", "-i", type=str, default="通用", help="行业类型")
    parser.add_argument("--theme", type=str, default="", help="主题")
    parser.add_argument("--topic", type=str, default="", help="话题")
    parser.add_argument("--duration", type=int, default=60, help="时长(秒)")
    parser.add_argument("--count", type=int, default=5, help="数量")
    parser.add_argument("--show-help", action="store_true", help="显示帮助")
    
    args = parser.parse_args()
    
    if args.show_help or not args.tool:
        show_banner()
        show_help()
        return
    
    show_banner()
    
    # 根据工具选择执行
    tool_map = {
        "trending": run_trending,
        "script": run_script,
        "title": run_title,
        "time": run_time,
        "analytics": run_analytics,
        "competitor": run_competitor,
        "live": run_live,
        "review": run_review
    }
    
    tool_func = tool_map.get(args.tool)
    if tool_func:
        try:
            tool_func(args)
        except Exception as e:
            print(f"\n❌ 执行出错: {e}")
            import traceback
            traceback.print_exc()
    else:
        print(f"\n❌ 未知工具: {args.tool}")
        print("运行 --help 查看可用工具")


def run_trending(args):
    """运行热门话题分析"""
    analyzer = TrendingTopicsAnalyzer(industry=args.industry)
    
    print("\n📊 抖音热榜 TOP 10:")
    print("-" * 40)
    trending = analyzer.get_douyin_trending()
    for item in trending[:5]:
        print(f"  {item['rank']}. {item['topic']} (热度: {item['heat']:,})")
    
    print("\n💡 选题推荐:")
    print("-" * 40)
    recommendations = analyzer.recommend_topics(args.count)
    for i, rec in enumerate(recommendations, 1):
        print(f"  [{i}] {rec['类型']}: {rec['话题']}")
        print(f"      热度: {rec['热度']:,}")
        print(f"      建议: {rec['建议']}")


def run_script(args):
    """运行视频脚本生成"""
    generator = VideoScriptGenerator()
    theme = args.theme or "职场沟通技巧"
    
    print(f"\n📝 生成视频脚本: {theme}")
    print("-" * 40)
    
    script = generator.generate_script(
        theme=theme,
        duration=args.duration,
        script_type="口播分享",
        problem="说话没人听",
        method="沟通技巧"
    )
    
    print(f"主题: {script['基本信息']['主题']}")
    print(f"时长: {script['基本信息']['时长']}")
    print(f"\n【开场】")
    print(f"  {script['脚本内容']['开场']['内容']}")
    
    print("\n【分镜脚本】")
    table = generator.generate_script_table(theme, args.duration)
    print(f"{'镜号':<6}{'景别':<8}{'运镜':<8}{'时长':<6}")
    print("-" * 28)
    for row in table:
        print(f"{row['镜号']:<6}{row['景别']:<8}{row['运镜']:<8}{row['时长']:<6}")


def run_title(args):
    """运行标题生成"""
    generator = TitleGenerator()
    topic = args.topic or "高效工作"
    
    print(f"\n📝 生成标题: {topic}")
    print("-" * 40)
    
    # 生成各类型标题
    print("\n【各类型标题】")
    for formula in ["数字型", "疑问型", "感叹型", "悬念型"]:
        title = generator.generate_title(formula, topic)
        print(f"  [{formula}] {title}")
    
    # 批量生成
    print(f"\n【批量生成 {args.count} 个标题】")
    titles = generator.batch_generate_titles(topic, args.count)
    for i, title in enumerate(titles, 1):
        print(f"  {i}. {title}")


def run_time(args):
    """运行发布时间推荐"""
    recommender = OptimalTimeRecommender(industry=args.industry)
    
    print(f"\n⏰ 发布时间分析: {args.industry}")
    print("-" * 40)
    
    # 粉丝活跃分析
    fan_data = recommender.get_fan_active_hours()
    print(f"高峰日期: {', '.join(fan_data['高峰日期'])}")
    print(f"高峰时段: {', '.join(fan_data['高峰时段'])}")
    
    # 推荐时段
    print("\n【最佳发布时间推荐】")
    rec = recommender.recommend_optimal_time("通用", args.industry)
    print(f"行业: {rec['行业']}")
    print(f"最佳时段: {', '.join(rec['最佳时段'])}")
    print(f"原因: {rec['时段原因']}")


def run_analytics(args):
    """运行数据分析"""
    reporter = AnalyticsReporter(industry=args.industry)
    
    print(f"\n📊 数据分析报告: {args.industry}")
    print("-" * 40)
    
    # 生成数据
    videos = reporter.generate_sample_data(10)
    
    # 汇总报告
    summary = reporter.generate_summary_report(videos)
    print(f"分析周期: {summary['分析周期']}")
    print(f"分析视频数: {summary['分析视频数']}")
    print(f"总播放量: {summary['总体数据']['总播放量']:,}")
    print(f"平均播放量: {summary['平均值']['平均播放量']:,}")
    print(f"平均完播率: {summary['平均值']['平均完播率']}")
    print(f"平均互动率: {summary['平均值']['平均互动率']}")
    
    # TOP3
    print("\n【TOP3视频】")
    for i, v in enumerate(summary['TOP3视频'], 1):
        print(f"  {i}. {v['标题']}: {v['播放量']:,}播放")


def run_competitor(args):
    """运行竞品分析"""
    analyzer = CompetitorAnalyzer()
    
    print("\n🔍 竞品分析")
    print("-" * 40)
    
    # 添加竞品
    analyzer.add_competitor("竞品A", "@jingpinA", 500000, "美食教程")
    analyzer.add_competitor("竞品B", "@jingpinB", 300000, "美食日常")
    
    # 监控表
    print("【竞品监控表】")
    table = analyzer.generate_monitoring_table()
    print(f"{'账号':<12}{'粉丝数':<12}{'周涨粉':<10}{'平均播放':<12}")
    print("-" * 46)
    for row in table:
        print(f"{row['账号']:<12}{row['粉丝数']:<12}{row['周涨粉']:<10}{row['平均播放']:<12}")
    
    # SWOT分析
    print("\n【SWOT分析】")
    swot = analyzer.generate_swot_analysis({"名称": "我的账号"})
    for key, items in swot.items():
        print(f"  {key}:")
        for k, v in items.items():
            print(f"    - {k}: {v}")


def run_live(args):
    """运行直播话术生成"""
    generator = LiveStreamScriptGenerator()
    
    print("\n🎬 直播话术生成")
    print("-" * 40)
    
    # 开场话术
    print("【开场话术】")
    print(f"  {generator.generate_opening('暖场')}")
    print(f"  {generator.generate_opening('价值预告', product='美妆好物')}")
    
    # 促单话术
    print("\n【促单话术】")
    print(f"  {generator.generate_promote_script('紧迫感', count='20')}")
    print(f"  {generator.generate_promote_script('福利', gift1='化妆包', gift2='豪华礼包')}")
    
    # 完整脚本
    print("\n【完整直播脚本】")
    live_script = generator.generate_full_live_script(duration=args.duration)
    print(f"  直播时长: {live_script['基本信息']['直播时长']}")
    print(f"  产品数量: {live_script['基本信息']['产品数量']}")


def run_review(args):
    """运行直播复盘"""
    review = LiveStreamReview()
    
    print("\n📋 直播复盘")
    print("-" * 40)
    
    # 输入数据
    review.input_live_data({
        "日期": "2024-05-15",
        "时长": "2小时",
        "GMV目标": 50000,
        "实际GMV": 58000,
        "在线峰值": 850,
        "平均在线": 420,
        "观看人数": 12500,
        "下单人数": 380,
        "客单价": 152.63,
        "退货率": 8.5
    })
    
    # 数据复盘
    data_review = review.calculate_data_review()["数据复盘"]
    print(f"【GMV】")
    print(f"  目标: {data_review['GMV']['目标']}")
    print(f"  实际: {data_review['GMV']['实际']}")
    print(f"  完成率: {data_review['GMV']['完成率']} {data_review['GMV']['状态']}")
    
    print(f"\n【转化】")
    print(f"  观看人数: {data_review['转化']['观看人数']}")
    print(f"  下单人数: {data_review['转化']['下单人数']}")
    print(f"  转化率: {data_review['转化']['转化率']}")
    
    # 改进计划
    print("\n【下次改进计划】")
    improvement = review.generate_improvement_plan()["下次改进计划"]
    print("  话术调整:")
    for item in improvement["话术调整"][:2]:
        print(f"    - {item}")


if __name__ == "__main__":
    main()
