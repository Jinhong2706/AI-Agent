#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抖音运营大师 - 数据分析报告脚本
功能：播放量分析、互动率分析、完播率分析、转化率分析
数据来源：创作者中心、蝉妈妈、飞瓜数据等
"""

import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional


class AnalyticsReporter:
    """数据分析报告生成器"""
    
    # 行业基准值
    INDUSTRY_BENCHMARKS = {
        "平均播放量": {
            "美食": 8500,
            "美妆": 12000,
            "知识": 6000,
            "职场": 7500,
            "娱乐": 15000,
            "穿搭": 10000,
            "健身": 8000,
            "通用": 8000
        },
        "完播率": {
            "30秒以内": {"优秀": 50, "良好": 40, "一般": 30},
            "1分钟": {"优秀": 45, "良好": 35, "一般": 25},
            "3分钟": {"优秀": 35, "良好": 25, "一般": 18},
            "5分钟以上": {"优秀": 25, "良好": 18, "一般": 12}
        },
        "互动率": {
            "优秀": 10,
            "良好": 5,
            "一般": 3
        },
        "转粉率": {
            "优秀": 3,
            "良好": 1.5,
            "一般": 0.5
        }
    }
    
    def __init__(self, industry: str = "通用"):
        self.industry = industry
    
    def generate_sample_data(self, video_count: int = 10) -> List[Dict]:
        """生成示例视频数据"""
        data = []
        base_views = self.INDUSTRY_BENCHMARKS["平均播放量"].get(self.industry, 8000)
        
        for i in range(video_count):
            views = int(base_views * random.uniform(0.3, 3.0))
            likes = int(views * random.uniform(0.03, 0.15))
            comments = int(views * random.uniform(0.005, 0.02))
            shares = int(views * random.uniform(0.003, 0.015))
            favorites = int(views * random.uniform(0.01, 0.05))
            followers = int(views * random.uniform(0.005, 0.02))
            avg_duration = random.randint(20, 50) if i % 3 != 0 else random.randint(40, 80)
            video_duration = 60 if i % 3 != 0 else 90
            
            data.append({
                "视频ID": f"V{1001+i}",
                "标题": f"视频标题_{i+1}",
                "发布时间": (datetime.now() - timedelta(days=i*2)).strftime("%Y-%m-%d"),
                "播放量": views,
                "点赞数": likes,
                "评论数": comments,
                "分享数": shares,
                "收藏数": favorites,
                "新增粉丝": followers,
                "平均观看时长": avg_duration,
                "视频时长": video_duration
            })
        
        return data
    
    def calculate_metrics(self, video: Dict) -> Dict:
        """计算视频指标"""
        views = video["播放量"]
        likes = video["点赞数"]
        comments = video["评论数"]
        shares = video["分享数"]
        favorites = video["收藏数"]
        followers = video["新增粉丝"]
        avg_duration = video["平均观看时长"]
        duration = video["视频时长"]
        
        # 完播率
        completion_rate = (avg_duration / duration) * 100 if duration > 0 else 0
        
        # 互动率 = (点赞+评论+分享+收藏) / 播放量 * 100%
        interaction_rate = ((likes + comments + shares + favorites) / views) * 100 if views > 0 else 0
        
        # 转粉率 = 新增粉丝 / 播放量 * 100%
        fan_rate = (followers / views) * 100 if views > 0 else 0
        
        return {
            "完播率": completion_rate,
            "互动率": interaction_rate,
            "转粉率": fan_rate,
            "点赞率": (likes / views) * 100 if views > 0 else 0,
            "评论率": (comments / views) * 100 if views > 0 else 0
        }
    
    def analyze_video(self, video: Dict) -> Dict:
        """分析单个视频"""
        metrics = self.calculate_metrics(video)
        video_duration = video["视频时长"]
        
        # 判断时长级别
        if video_duration <= 30:
            duration_level = "30秒以内"
        elif video_duration <= 60:
            duration_level = "1分钟"
        elif video_duration <= 180:
            duration_level = "3分钟"
        else:
            duration_level = "5分钟以上"
        
        benchmarks = self.INDUSTRY_BENCHMARKS["完播率"].get(duration_level, {"优秀": 40, "良好": 30, "一般": 20})
        
        # 评估等级
        completion_rating = self._get_rating(metrics["完播率"], benchmarks)
        interaction_rating = self._get_rating(metrics["互动率"], self.INDUSTRY_BENCHMARKS["互动率"])
        fan_rating = self._get_rating(metrics["转粉率"], self.INDUSTRY_BENCHMARKS["转粉率"])
        
        return {
            "视频ID": video["视频ID"],
            "播放量": video["播放量"],
            "核心指标": metrics,
            "评级": {
                "完播率": completion_rating,
                "互动率": interaction_rating,
                "转粉率": fan_rating
            },
            "诊断建议": self._generate_diagnosis(video, metrics)
        }
    
    def _get_rating(self, value: float, benchmarks: Dict) -> str:
        """获取评级"""
        if "优秀" in benchmarks and value >= benchmarks["优秀"]:
            return "⭐⭐⭐⭐⭐ 优秀"
        elif "良好" in benchmarks and value >= benchmarks["良好"]:
            return "⭐⭐⭐⭐ 良好"
        elif "一般" in benchmarks and value >= benchmarks["一般"]:
            return "⭐⭐⭐ 一般"
        else:
            return "⭐⭐ 待提升"
    
    def _generate_diagnosis(self, video: Dict, metrics: Dict) -> List[str]:
        """生成诊断建议"""
        suggestions = []
        
        # 播放量分析
        base_views = self.INDUSTRY_BENCHMARKS["平均播放量"].get(self.industry, 8000)
        if video["播放量"] > base_views * 2:
            suggestions.append("✅ 播放量表现优秀，是近期爆款")
        elif video["播放量"] < base_views * 0.5:
            suggestions.append("⚠️ 播放量偏低，建议优化封面和标题")
        
        # 完播率分析
        if metrics["完播率"] < 25:
            suggestions.append("⚠️ 完播率偏低，可能开头不够吸引或内容冗长")
        elif metrics["完播率"] > 45:
            suggestions.append("✅ 完播率优秀，内容结构紧凑")
        
        # 互动率分析
        if metrics["互动率"] > 8:
            suggestions.append("✅ 互动率高，粉丝活跃")
        elif metrics["互动率"] < 3:
            suggestions.append("⚠️ 互动率偏低，建议增加引导互动的话术")
        
        return suggestions
    
    def generate_summary_report(self, videos: List[Dict]) -> Dict:
        """生成汇总报告"""
        total_views = sum(v["播放量"] for v in videos)
        total_likes = sum(v["点赞数"] for v in videos)
        total_comments = sum(v["评论数"] for v in videos)
        total_shares = sum(v["分享数"] for v in videos)
        total_favorites = sum(v["收藏数"] for v in videos)
        total_followers = sum(v["新增粉丝"] for v in videos)
        
        video_count = len(videos)
        avg_views = total_views // video_count if video_count > 0 else 0
        
        # 计算平均指标
        all_metrics = [self.calculate_metrics(v) for v in videos]
        avg_completion = sum(m["完播率"] for m in all_metrics) / video_count if video_count > 0 else 0
        avg_interaction = sum(m["互动率"] for m in all_metrics) / video_count if video_count > 0 else 0
        avg_fan_rate = sum(m["转粉率"] for m in all_metrics) / video_count if video_count > 0 else 0
        
        # 找出TOP3和BOTTOM3
        sorted_videos = sorted(videos, key=lambda x: x["播放量"], reverse=True)
        top3 = sorted_videos[:3]
        bottom3 = sorted_videos[-3:] if len(sorted_videos) > 3 else []
        
        return {
            "报告时间": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "分析周期": f"近{len(videos)*2}天",
            "分析视频数": video_count,
            "总体数据": {
                "总播放量": total_views,
                "总点赞数": total_likes,
                "总评论数": total_comments,
                "总分享数": total_shares,
                "总收藏数": total_favorites,
                "总涨粉数": total_followers
            },
            "平均值": {
                "平均播放量": avg_views,
                "平均完播率": f"{avg_completion:.1f}%",
                "平均互动率": f"{avg_interaction:.2f}%",
                "平均转粉率": f"{avg_fan_rate:.2f}%"
            },
            "TOP3视频": [
                {"标题": v["标题"], "播放量": v["播放量"]} for v in top3
            ],
            "BOTTOM3视频": [
                {"标题": v["标题"], "播放量": v["播放量"]} for v in bottom3
            ],
            "对比基准": {
                "行业": self.industry,
                "行业平均播放": self.INDUSTRY_BENCHMARKS["平均播放量"].get(self.industry, 8000),
                "表现评估": "超越平均" if avg_views > self.INDUSTRY_BENCHMARKS["平均播放量"].get(self.industry, 8000) else "低于平均"
            }
        }
    
    def generate_detailed_analysis(self, videos: List[Dict]) -> Dict:
        """生成详细分析"""
        # 按内容类型分组（模拟）
        categories = {
            "教程类": [v for i, v in enumerate(videos) if i % 3 == 0],
            "测评类": [v for i, v in enumerate(videos) if i % 3 == 1],
            "剧情类": [v for i, v in enumerate(videos) if i % 3 == 2]
        }
        
        category_analysis = {}
        for cat, cat_videos in categories.items():
            if cat_videos:
                avg_views = sum(v["播放量"] for v in cat_videos) // len(cat_videos)
                avg_completion = sum(self.calculate_metrics(v)["完播率"] for v in cat_videos) / len(cat_videos)
                category_analysis[cat] = {
                    "视频数": len(cat_videos),
                    "平均播放": avg_views,
                    "平均完播率": f"{avg_completion:.1f}%"
                }
        
        return {
            "内容类型分析": category_analysis,
            "时间段分析": {
                "工作日发布": {"平均播放": 8500, "完播率": "38%"},
                "周末发布": {"平均播放": 10200, "完播率": "42%"}
            },
            "时长分析": {
                "15-30秒": {"平均播放": 12000, "完播率": "52%"},
                "1-3分钟": {"平均播放": 8000, "完播率": "38%"},
                "3分钟以上": {"平均播放": 5000, "完播率": "25%"}
            }
        }
    
    def generate_optimization_suggestions(self, report: Dict) -> List[str]:
        """生成优化建议"""
        suggestions = []
        
        # 基于表现生成建议
        avg_views = report["平均值"]["平均播放量"]
        industry_avg = report["对比基准"]["行业平均播放"]
        
        if avg_views < industry_avg:
            suggestions.append({
                "方向": "提升播放量",
                "建议": [
                    "优化封面：使用人脸+大字+高对比色",
                    "优化标题：使用数字型、疑问型标题公式",
                    "蹭热点：结合近期热点选题",
                    "提高更新频率：测试日更效果"
                ]
            })
        
        # 完播率建议
        completion = float(report["平均值"]["平均播放率"].replace("%", ""))
        if completion < 35:
            suggestions.append({
                "方向": "提升完播率",
                "建议": [
                    "优化开头3秒：使用痛点型/利益型开场",
                    "控制时长：精简内容，去除冗余",
                    "增加节奏感：快慢交替，制造起伏",
                    "设置悬念：让用户想看完"
                ]
            })
        
        # 互动率建议
        interaction = float(report["平均值"]["平均互动率"].replace("%", ""))
        if interaction < 5:
            suggestions.append({
                "方向": "提升互动率",
                "建议": [
                    "结尾引导互动：问问题、征求意见",
                    "评论区回复：及时回复粉丝评论",
                    "设置槽点：有争议性的话题引发讨论",
                    "福利互动：点赞/关注抽奖"
                ]
            })
        
        return suggestions


def main():
    """主函数"""
    print("=" * 60)
    print("📊 抖音运营大师 - 数据分析报告工具 📊")
    print("=" * 60)
    
    reporter = AnalyticsReporter(industry="美食")
    
    # 1. 生成示例数据
    print("\n📝 生成示例视频数据...")
    videos = reporter.generate_sample_data(10)
    
    # 2. 单视频分析
    print("\n🔍 单视频分析示例:")
    print("-" * 40)
    sample_video = videos[0]
    analysis = reporter.analyze_video(sample_video)
    
    print(f"  视频ID: {analysis['视频ID']}")
    print(f"  播放量: {analysis['播放量']:,}")
    print(f"  完播率: {analysis['核心指标']['完播率']:.1f}% {analysis['评级']['完播率']}")
    print(f"  互动率: {analysis['核心指标']['互动率']:.2f}% {analysis['评级']['互动率']}")
    print(f"  转粉率: {analysis['核心指标']['转粉率']:.2f}% {analysis['评级']['转粉率']}")
    print("  诊断建议:")
    for suggestion in analysis['诊断建议']:
        print(f"    {suggestion}")
    
    # 3. 汇总报告
    print("\n📋 汇总报告:")
    print("-" * 40)
    summary = reporter.generate_summary_report(videos)
    print(f"  分析周期: {summary['分析周期']}")
    print(f"  分析视频数: {summary['分析视频数']}")
    print(f"  总播放量: {summary['总体数据']['总播放量']:,}")
    print(f"  平均播放量: {summary['平均值']['平均播放量']:,}")
    print(f"  平均完播率: {summary['平均值']['平均完播率']}")
    print(f"  平均互动率: {summary['平均值']['平均互动率']}")
    print(f"  平均转粉率: {summary['平均值']['平均转粉率']}")
    print(f"  行业基准: {summary['对比基准']['行业']} - {summary['对比基准']['行业平均播放']:,}")
    print(f"  表现评估: {summary['对比基准']['表现评估']}")
    
    print("\n  TOP3视频:")
    for i, v in enumerate(summary['TOP3视频'], 1):
        print(f"    {i}. {v['标题']}: {v['播放量']:,}播放")
    
    # 4. 详细分析
    print("\n📈 内容类型分析:")
    print("-" * 40)
    detailed = reporter.generate_detailed_analysis(videos)
    for cat, data in detailed["内容类型分析"].items():
        print(f"  {cat}:")
        print(f"    视频数: {data['视频数']}")
        print(f"    平均播放: {data['平均播放']:,}")
        print(f"    平均完播率: {data['平均完播率']}")
    
    # 5. 优化建议
    print("\n💡 优化建议:")
    print("-" * 40)
    suggestions = reporter.generate_optimization_suggestions(summary)
    for group in suggestions:
        print(f"\n  【{group['方向']}】")
        for i, s in enumerate(group['建议'], 1):
            print(f"    {i}. {s}")
    
    print("\n" + "=" * 60)
    print("✅ 报告生成完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
