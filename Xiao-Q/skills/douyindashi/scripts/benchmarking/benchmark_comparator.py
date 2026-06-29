#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抖音对标账号工具 - 数据对比分析脚本
功能：多维度对比自身与对标账号的数据差异，量化追赶目标
"""

import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class AccountMetrics:
    """账号指标数据"""
    account_id: str = ""
    account_name: str = ""
    followers: int = 0
    following: int = 0
    total_likes: int = 0
    avg_views: float = 0.0
    avg_likes: float = 0.0
    avg_comments: float = 0.0
    avg_shares: float = 0.0
    engagement_rate: float = 0.0
    completion_rate: float = 0.0
    fan_value: float = 0.0
    viral_rate: float = 0.0  # 爆款率
    posting_frequency: float = 0.0  # 周均发布
    live_count: int = 0
    live_avg_viewers: int = 0
    commercial_value: float = 0.0


@dataclass
class MetricComparison:
    """指标对比结果"""
    metric_name: str = ""
    my_value: float = 0.0
    benchmark_value: float = 0.0
    difference: float = 0.0
    difference_rate: float = 0.0  # 百分比差异
    gap_score: float = 0.0  # 差距得分 (0-100)
    priority: str = "normal"  # high/medium/low


class BenchmarkComparator:
    """对标对比分析器"""
    
    # 指标权重配置
    METRIC_WEIGHTS = {
        "engagement_rate": 0.25,  # 互动率权重最高
        "fan_value": 0.20,
        "avg_views": 0.15,
        "completion_rate": 0.15,
        "viral_rate": 0.10,
        "commercial_value": 0.10,
        "posting_frequency": 0.05
    }
    
    # 差距等级定义
    GAP_LEVELS = {
        "excellent": {"max": 10, "label": "超越", "color": "🟢"},
        "good": {"max": 30, "label": "接近", "color": "🟡"},
        "fair": {"max": 50, "label": "一般", "color": "🟠"},
        "poor": {"max": 100, "label": "较大差距", "color": "🔴"}
    }
    
    def __init__(self):
        self.comparison_results: Dict[str, Dict] = {}
    
    def collect_my_account_metrics(
        self,
        account_data: Dict[str, Any],
        video_data: List[Dict[str, Any]],
        fan_data: Dict[str, Any]
    ) -> AccountMetrics:
        """
        收集自身账号指标
        
        Args:
            account_data: 账号数据
            video_data: 视频数据
            fan_data: 粉丝数据
            
        Returns:
            AccountMetrics: 账号指标
        """
        metrics = AccountMetrics(
            account_id=account_data.get("account_id", ""),
            account_name=account_data.get("nickname", "我的账号")
        )
        
        # 基础数据
        metrics.followers = account_data.get("followers", 0)
        metrics.following = account_data.get("following", 0)
        metrics.total_likes = account_data.get("likes", 0)
        
        # 计算视频平均数据
        if video_data:
            metrics.avg_views = sum(v.get("views", 0) for v in video_data) / len(video_data)
            metrics.avg_likes = sum(v.get("likes", 0) for v in video_data) / len(video_data)
            metrics.avg_comments = sum(v.get("comments", 0) for v in video_data) / len(video_data)
            metrics.avg_shares = sum(v.get("shares", 0) for v in video_data) / len(video_data)
            
            # 计算平均完播率
            completion_rates = [v.get("completion_rate", 0) for v in video_data]
            metrics.completion_rate = sum(completion_rates) / len(completion_rates)
            
            # 计算爆款率
            viral_count = sum(1 for v in video_data if v.get("views", 0) >= 100000)
            metrics.viral_rate = viral_count / len(video_data) * 100
        
        # 粉丝数据
        if fan_data:
            metrics.engagement_rate = fan_data.get("engagement_rate", 0)
            metrics.fan_value = fan_data.get("fans_quality_score", 0)
        
        # 计算综合互动率
        if metrics.avg_views > 0:
            total_interactions = metrics.avg_likes + metrics.avg_comments + metrics.avg_shares
            metrics.engagement_rate = total_interactions / metrics.avg_views * 100
        
        # 粉丝价值
        if metrics.followers > 0:
            metrics.fan_value = metrics.total_likes / metrics.followers
        
        # 商业价值
        metrics.commercial_value = self._calculate_commercial_value(metrics)
        
        return metrics
    
    def _calculate_commercial_value(self, metrics: AccountMetrics) -> float:
        """计算商业价值"""
        score = 50
        
        # 粉丝量
        if metrics.followers >= 1000000:
            score += 20
        elif metrics.followers >= 100000:
            score += 15
        elif metrics.followers >= 10000:
            score += 10
        
        # 互动率
        if metrics.engagement_rate >= 8:
            score += 15
        elif metrics.engagement_rate >= 5:
            score += 10
        elif metrics.engagement_rate >= 3:
            score += 5
        
        # 爆款率
        if metrics.viral_rate >= 20:
            score += 10
        elif metrics.viral_rate >= 10:
            score += 5
        
        return min(score, 100)
    
    def collect_benchmark_metrics(
        self,
        account_data: Dict[str, Any],
        video_data: List[Dict[str, Any]],
        fan_data: Dict[str, Any]
    ) -> AccountMetrics:
        """收集对标账号指标"""
        # 使用相同的方法收集指标
        return self.collect_my_account_metrics(account_data, video_data, fan_data)
    
    def compare_metrics(
        self,
        my_metrics: AccountMetrics,
        benchmark_metrics: AccountMetrics
    ) -> List[MetricComparison]:
        """
        对比指标差异
        
        Args:
            my_metrics: 自身指标
            benchmark_metrics: 对标指标
            
        Returns:
            List[MetricComparison]: 对比结果列表
        """
        comparisons = []
        
        # 定义需要对比的指标
        metric_definitions = [
            ("粉丝数", "followers", "high"),
            ("平均播放", "avg_views", "high"),
            ("平均点赞", "avg_likes", "medium"),
            ("平均评论", "avg_comments", "medium"),
            ("平均分享", "avg_shares", "medium"),
            ("互动率", "engagement_rate", "high"),
            ("完播率", "completion_rate", "high"),
            ("粉丝价值", "fan_value", "medium"),
            ("爆款率", "viral_rate", "medium"),
            ("商业价值", "commercial_value", "medium")
        ]
        
        for metric_name, metric_key, priority in metric_definitions:
            my_value = getattr(my_metrics, metric_key, 0)
            bench_value = getattr(benchmark_metrics, metric_key, 0)
            
            comparison = self._compare_single_metric(
                metric_name, my_value, bench_value, priority
            )
            comparisons.append(comparison)
        
        # 按优先级和差距排序
        comparisons.sort(key=lambda x: (
            0 if x.priority == "high" else 1,
            -x.gap_score
        ))
        
        return comparisons
    
    def _compare_single_metric(
        self,
        metric_name: str,
        my_value: float,
        benchmark_value: float,
        priority: str
    ) -> MetricComparison:
        """对比单个指标"""
        comparison = MetricComparison(
            metric_name=metric_name,
            my_value=my_value,
            benchmark_value=benchmark_value,
            priority=priority
        )
        
        # 计算差异
        if benchmark_value > 0:
            comparison.difference = benchmark_value - my_value
            comparison.difference_rate = (comparison.difference / benchmark_value) * 100
        else:
            comparison.difference = my_value
            comparison.difference_rate = 100 if my_value > 0 else 0
        
        # 计算差距得分
        if benchmark_value > 0:
            # 差异越小，得分越高
            ratio = min(my_value / benchmark_value, 1.5)
            comparison.gap_score = round(ratio * 100, 1)
        else:
            comparison.gap_score = 100 if my_value > 0 else 0
        
        return comparison
    
    def calculate_overall_gap(self, comparisons: List[MetricComparison]) -> Dict[str, Any]:
        """
        计算整体差距
        
        Args:
            comparisons: 指标对比列表
            
        Returns:
            Dict: 整体差距分析
        """
        total_weighted_gap = 0
        weighted_sum = 0
        
        high_priority_gaps = []
        medium_priority_gaps = []
        
        for comp in comparisons:
            weight = self.METRIC_WEIGHTS.get(comp.metric_name.lower().replace("平均", "").replace("率", "_rate"), 0.1)
            
            # 差距率（对数处理，避免极端值影响）
            if comp.benchmark_value > 0:
                gap_ratio = comp.difference / comp.benchmark_value
            else:
                gap_ratio = 0
            
            weighted_gap = gap_ratio * weight
            total_weighted_gap += weighted_gap
            weighted_sum += weight
            
            # 分类差距
            if comp.priority == "high":
                high_priority_gaps.append(comp)
            elif comp.priority == "medium":
                medium_priority_gaps.append(comp)
        
        # 标准化
        if weighted_sum > 0:
            overall_gap = total_weighted_gap / weighted_sum * 100
        else:
            overall_gap = 0
        
        # 确定差距等级
        gap_level = "excellent"
        for level, info in self.GAP_LEVELS.items():
            if overall_gap <= info["max"]:
                gap_level = level
                break
        
        return {
            "overall_gap": round(overall_gap, 1),
            "gap_level": gap_level,
            "gap_label": self.GAP_LEVELS[gap_level]["label"],
            "gap_color": self.GAP_LEVELS[gap_level]["color"],
            "high_priority_gaps": high_priority_gaps,
            "medium_priority_gaps": medium_priority_gaps,
            "weighted_gaps": {comp.metric_name: comp.difference_rate for comp in comparisons}
        }
    
    def estimate_catch_up_time(
        self,
        my_metrics: AccountMetrics,
        benchmark_metrics: AccountMetrics,
        growth_rates: Dict[str, float] = None
    ) -> Dict[str, Any]:
        """
        估算追赶时间
        
        Args:
            my_metrics: 自身指标
            benchmark_metrics: 对标指标
            growth_rates: 各指标增长率（周），
            
        Returns:
            Dict: 追赶时间估算
        """
        if growth_rates is None:
            # 默认增长率（基于行业平均）
            growth_rates = {
                "followers": 3.0,  # 粉丝周增长率
                "avg_views": 5.0,
                "engagement_rate": 2.0,
                "viral_rate": 10.0
            }
        
        estimates = []
        
        # 粉丝追赶时间
        follower_gap = benchmark_metrics.followers - my_metrics.followers
        if follower_gap > 0 and growth_rates.get("followers", 0) > 0:
            weekly_growth = my_metrics.followers * (growth_rates["followers"] / 100)
            if weekly_growth > 0:
                weeks_needed = follower_gap / weekly_growth
                estimates.append({
                    "metric": "粉丝数",
                    "gap": follower_gap,
                    "weekly_growth": round(weekly_growth),
                    "weeks_needed": round(weeks_needed, 1),
                    "months_needed": round(weeks_needed / 4, 1)
                })
        
        # 互动率追赶时间
        engagement_gap = benchmark_metrics.engagement_rate - my_metrics.engagement_rate
        if engagement_gap > 0 and growth_rates.get("engagement_rate", 0) > 0:
            weekly_improvement = growth_rates["engagement_rate"] / 100
            if weekly_improvement > 0:
                weeks_needed = engagement_gap / weekly_improvement
                estimates.append({
                    "metric": "互动率",
                    "gap": round(engagement_gap, 2),
                    "weekly_improvement": round(weekly_improvement, 2),
                    "weeks_needed": round(weeks_needed, 1),
                    "months_needed": round(weeks_needed / 4, 1)
                })
        
        return {
            "estimates": estimates,
            "fastest_catch_up": estimates[0] if estimates else None,
            "recommended_focus": self._recommend_catch_up_focus(estimates)
        }
    
    def _recommend_catch_up_focus(self, estimates: List[Dict]) -> str:
        """推荐追赶重点"""
        if not estimates:
            return "全面提升"
        
        # 优先推荐追赶时间最短的
        fastest = min(estimates, key=lambda x: x.get("weeks_needed", 999))
        
        if fastest.get("weeks_needed", 999) <= 8:
            return f"优先追赶「{fastest['metric']}」，预计{fastonest['months_needed']}个月达成"
        else:
            return f"「{fastest['metric']}」差距较大，建议重点提升"
    
    def generate_comparison_report(
        self,
        my_metrics: AccountMetrics,
        benchmark_metrics: AccountMetrics,
        comparisons: List[MetricComparison],
        overall_gap: Dict[str, Any],
        catch_up_plan: Dict[str, Any]
    ) -> str:
        """
        生成对比分析报告
        
        Args:
            my_metrics: 自身指标
            benchmark_metrics: 对标指标
            comparisons: 指标对比列表
            overall_gap: 整体差距
            catch_up_plan: 追赶计划
            
        Returns:
            str: 对比分析报告
        """
        report_lines = [
            "=" * 60,
            "📊 账号对比分析报告",
            "=" * 60,
            "",
            "一、账号基本信息对比",
            "-" * 60,
            "",
            f"{'指标':<15} {'我的账号':<15} {'对标账号':<15} {'差异':<15}",
            "-" * 60,
            f"{'账号名称':<15} {my_metrics.account_name:<15} {benchmark_metrics.account_name:<15} {'-':<15}",
            f"{'粉丝数':<15} {my_metrics.followers:>12,} {benchmark_metrics.followers:>12,} {benchmark_metrics.followers - my_metrics.followers:>+12,}",
            f"{'总获赞':<15} {my_metrics.total_likes:>12,} {benchmark_metrics.total_likes:>12,} {benchmark_metrics.total_likes - my_metrics.total_likes:>+12,}",
            f"{'商业价值':<15} {my_metrics.commercial_value:>12.0f} {benchmark_metrics.commercial_value:>12.0f} {benchmark_metrics.commercial_value - my_metrics.commercial_value:>+12.0f}",
            "",
            "二、核心数据对比",
            "-" * 60,
            "",
            f"{'指标':<15} {'我的账号':<15} {'对标账号':<15} {'差距率':<15} {'优先级':<10}",
            "-" * 60,
        ]
        
        for comp in comparisons:
            priority_tag = {"high": "🔴高", "medium": "🟡中", "normal": "🟢低"}.get(comp.priority, "")
            report_lines.append(
                f"{comp.metric_name:<15} "
                f"{comp.my_value:>12,.1f} "
                f"{comp.benchmark_value:>12,.1f} "
                f"{comp.difference_rate:>+11.1f}% "
                f"{priority_tag:<10}"
            )
        
        report_lines.extend([
            "",
            "三、差距等级评估",
            "-" * 60,
            "",
        ])
        
        # 差距等级可视化
        gap_bar = self._generate_gap_bar(overall_gap["overall_gap"])
        gap_color = overall_gap["gap_color"]
        gap_label = overall_gap["gap_label"]
        
        report_lines.extend([
            f"综合差距: {gap_color} {gap_label} ({overall_gap['overall_gap']}%)",
            f"进度条: {gap_bar}",
            "",
        ])
        
        # 重点差距项
        report_lines.extend([
            "重点差距项（高优先级）:",
        ])
        
        for comp in overall_gap.get("high_priority_gaps", [])[:3]:
            report_lines.append(f"  ⚠️ {comp.metric_name}: 差距 {comp.difference_rate:.1f}%")
        
        report_lines.extend([
            "",
            "四、追赶时间预估",
            "-" * 60,
            "",
        ])
        
        for estimate in catch_up_plan.get("estimates", []):
            report_lines.append(
                f"  📌 {estimate['metric']}: "
                f"差距 {estimate.get('gap', 0):,.0f}, "
                f"预计 {estimate.get('months_needed', 0):.1f} 个月"
            )
        
        report_lines.extend([
            "",
            f"💡 {catch_up_plan.get('recommended_focus', '')}",
            "",
            "=" * 60,
            f"报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "=" * 60,
        ])
        
        return "\n".join(report_lines)
    
    def _generate_gap_bar(self, gap_percentage: float, length: int = 20) -> str:
        """生成差距可视化进度条"""
        filled = int((1 - min(gap_percentage, 100) / 100) * length)
        empty = length - filled
        
        bar = "█" * filled + "░" * empty
        percentage = f"{100 - gap_percentage:.0f}%"
        
        return f"[{bar}] {percentage}"
    
    def generate_improvement_plan(
        self,
        comparisons: List[MetricComparison],
        overall_gap: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        生成改进计划
        
        Args:
            comparisons: 指标对比
            overall_gap: 整体差距
            
        Returns:
            Dict: 改进计划
        """
        plan = {
            "immediate_actions": [],  # 立即执行
            "short_term_goals": [],   # 短期目标（1个月）
            "medium_term_goals": [],   # 中期目标（3个月）
            "key_metrics_to_improve": []
        }
        
        # 根据差距生成建议
        for comp in comparisons:
            if comp.priority == "high" and comp.difference_rate > 20:
                # 立即行动
                action = self._generate_action_for_metric(comp)
                plan["immediate_actions"].append(action)
                plan["key_metrics_to_improve"].append(comp.metric_name)
        
        # 短期目标
        plan["short_term_goals"] = [
            "建立稳定的内容更新节奏",
            "优化视频开头3秒钩子设计",
            "提升粉丝互动率至对标账号80%水平",
            "每周分析1次对标账号爆款规律"
        ]
        
        # 中期目标
        plan["medium_term_goals"] = [
            "粉丝量达到对标账号50%",
            "爆款率提升至15%以上",
            "形成稳定的内容矩阵",
            "建立粉丝社群运营体系"
        ]
        
        return plan
    
    def _generate_action_for_metric(self, comp: MetricComparison) -> Dict[str, str]:
        """为指标生成具体行动"""
        actions = {
            "粉丝数": {
                "action": "增加引流型内容投放，蹭热点话题",
                "kpi": "周涨粉增速提升50%"
            },
            "平均播放": {
                "action": "优化选题和封面，提升推荐流量",
                "kpi": "单视频平均播放提升30%"
            },
            "互动率": {
                "action": "增加互动引导话术，引导评论和收藏",
                "kpi": "互动率提升至5%以上"
            },
            "完播率": {
                "action": "优化内容节奏，重要信息前置",
                "kpi": "完播率提升至50%以上"
            },
            "爆款率": {
                "action": "学习爆款规律，多尝试热门话题",
                "kpi": "月度爆款数量翻倍"
            }
        }
        
        return actions.get(
            comp.metric_name, 
            {"action": f"重点提升{comp.metric_name}", "kpi": "提升至对标80%"}
        )


def main():
    """主函数 - 演示数据对比分析"""
    print("=" * 60)
    print("抖音账号对比分析工具")
    print("=" * 60)
    
    # 初始化对比器
    comparator = BenchmarkComparator()
    
    # 模拟我的账号数据
    my_account = {
        "account_id": "my_account",
        "nickname": "我的账号",
        "followers": 50000,
        "following": 200,
        "likes": 500000
    }
    
    my_videos = [
        {
            "views": random.randint(5000, 50000),
            "likes": random.randint(500, 5000),
            "comments": random.randint(50, 500),
            "shares": random.randint(20, 200),
            "completion_rate": random.uniform(35, 55)
        }
        for _ in range(30)
    ]
    
    my_fans = {
        "engagement_rate": 5.2,
        "fans_quality_score": 65
    }
    
    # 模拟对标账号数据
    benchmark_account = {
        "account_id": "benchmark_account",
        "nickname": "行业标杆",
        "followers": 500000,
        "following": 500,
        "likes": 5000000
    }
    
    benchmark_videos = [
        {
            "views": random.randint(50000, 500000),
            "likes": random.randint(5000, 50000),
            "comments": random.randint(500, 5000),
            "shares": random.randint(200, 2000),
            "completion_rate": random.uniform(45, 65)
        }
        for _ in range(30)
    ]
    
    benchmark_fans = {
        "engagement_rate": 7.5,
        "fans_quality_score": 85
    }
    
    # 收集指标
    print("\n【1】收集账号指标")
    my_metrics = comparator.collect_my_account_metrics(my_account, my_videos, my_fans)
    benchmark_metrics = comparator.collect_benchmark_metrics(
        benchmark_account, benchmark_videos, benchmark_fans
    )
    
    print(f"我的账号粉丝: {my_metrics.followers:,}")
    print(f"对标账号粉丝: {benchmark_metrics.followers:,}")
    print(f"我的互动率: {my_metrics.engagement_rate:.2f}%")
    print(f"对标互动率: {benchmark_metrics.engagement_rate:.2f}%")
    
    # 对比分析
    print("\n【2】多维度对比分析")
    comparisons = comparator.compare_metrics(my_metrics, benchmark_metrics)
    
    print("\n核心差距:")
    for comp in comparisons[:5]:
        print(f"  {comp.metric_name}: 差距 {comp.difference_rate:.1f}% [{comp.priority}]")
    
    # 整体差距评估
    print("\n【3】整体差距评估")
    overall_gap = comparator.calculate_overall_gap(comparisons)
    
    gap_bar = comparator._generate_gap_bar(overall_gap["overall_gap"])
    print(f"综合差距: {overall_gap['gap_color']} {overall_gap['gap_label']}")
    print(f"进度条: {gap_bar}")
    
    # 追赶时间预估
    print("\n【4】追赶时间预估")
    catch_up_plan = comparator.estimate_catch_up_time(my_metrics, benchmark_metrics)
    
    for estimate in catch_up_plan.get("estimates", []):
        print(f"  {estimate['metric']}: 预计 {estimate['months_needed']:.1f} 个月追上")
    
    print(f"\n💡 {catch_up_plan.get('recommended_focus', '')}")
    
    # 生成改进计划
    print("\n【5】生成改进计划")
    improvement_plan = comparator.generate_improvement_plan(comparisons, overall_gap)
    
    print("\n立即行动:")
    for action in improvement_plan.get("immediate_actions", [])[:3]:
        print(f"  🔴 {action['action']}")
    
    print("\n短期目标:")
    for goal in improvement_plan.get("short_term_goals", [])[:3]:
        print(f"  🟡 {goal}")
    
    # 生成完整报告
    print("\n【6】生成完整对比报告")
    report = comparator.generate_comparison_report(
        my_metrics, benchmark_metrics, comparisons, overall_gap, catch_up_plan
    )
    print(report)
    
    print("\n" + "=" * 60)
    print("对比分析完成！")


if __name__ == "__main__":
    main()
