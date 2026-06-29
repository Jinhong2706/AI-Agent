#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抖音对标账号工具 - 增长策略生成脚本
功能：基于对标分析结果，生成可落地的增长策略和执行方案
"""

import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class GrowthStrategy:
    """增长策略"""
    strategy_id: str = ""
    phase: str = ""  # startup/growth/mature
    focus_areas: List[str] = field(default_factory=list)
    tactics: List[Dict] = field(default_factory=list)
    kpis: List[Dict] = field(default_factory=list)
    timeline: Dict[str, str] = field(default_factory=dict)


@dataclass
class ContentPlan:
    """内容计划"""
    week_number: int = 0
    content_themes: List[str] = field(default_factory=list)
    content_matrix: Dict[str, int] = field(default_factory=dict)  # 类型: 数量
    posting_schedule: List[Dict] = field(default_factory=list)
    hot_topics: List[str] = field(default_factory=list)


class GrowthStrategyGenerator:
    """增长策略生成器"""
    
    # 增长阶段定义
    GROWTH_PHASES = {
        "startup": {
            "name": "冷启动期",
            "followers_range": (0, 10000),
            "focus": ["快速涨粉", "建立人设", "找到方向"],
            "timeline": "0-3个月"
        },
        "growth": {
            "name": "成长期",
            "followers_range": (10000, 100000),
            "focus": ["内容优化", "粉丝运营", "打造爆款"],
            "timeline": "3-12个月"
        },
        "mature": {
            "name": "成熟期",
            "followers_range": (100000, float("inf")),
            "focus": ["商业变现", "矩阵扩展", "品牌建设"],
            "timeline": "12个月以上"
        }
    }
    
    # 增长策略库
    GROWTH_TACTICS = {
        "content": [
            {
                "tactic": "爆款内容复制",
                "description": "研究对标账号爆款规律，制作类似结构内容",
                "expected_impact": "播放量提升50-100%",
                "difficulty": "medium"
            },
            {
                "tactic": "差异化定位",
                "description": "在对标基础上寻找差异化切入点",
                "expected_impact": "粉丝粘性提升30%",
                "difficulty": "high"
            },
            {
                "tactic": "固定更新时间",
                "description": "建立稳定的发布节奏，培养粉丝习惯",
                "expected_impact": "粉丝活跃度提升20%",
                "difficulty": "low"
            }
        ],
        "operation": [
            {
                "tactic": "评论区运营",
                "description": "主动回复评论，引导二次互动",
                "expected_impact": "互动率提升15%",
                "difficulty": "low"
            },
            {
                "tactic": "粉丝社群建设",
                "description": "建立粉丝群，培养核心粉丝",
                "expected_impact": "忠实粉丝增长50%",
                "difficulty": "medium"
            },
            {
                "tactic": "跨平台引流",
                "description": "在微信、小红书等平台导流",
                "expected_impact": "新粉来源增加30%",
                "difficulty": "medium"
            }
        ],
        "collaboration": [
            {
                "tactic": "达人互推",
                "description": "与同级别账号互相推荐",
                "expected_impact": "单次涨粉1000-5000",
                "difficulty": "medium"
            },
            {
                "tactic": "参与平台活动",
                "description": "抓住抖音官方活动流量",
                "expected_impact": "获得额外推荐流量",
                "difficulty": "low"
            },
            {
                "tactic": "热点蹭流量",
                "description": "及时跟进热门话题",
                "expected_impact": "爆款概率提升",
                "difficulty": "low"
            }
        ]
    }
    
    def __init__(self):
        self.generated_strategies: List[GrowthStrategy] = []
    
    def analyze_growth_phase(self, followers: int) -> str:
        """
        分析增长阶段
        
        Args:
            followers: 当前粉丝数
            
        Returns:
            str: 增长阶段
        """
        if followers < 10000:
            return "startup"
        elif followers < 100000:
            return "growth"
        else:
            return "mature"
    
    def generate_strategy(
        self,
        my_metrics: Dict[str, Any],
        benchmark_analysis: Dict[str, Any],
        target_metrics: Dict[str, Any]
    ) -> GrowthStrategy:
        """
        生成增长策略
        
        Args:
            my_metrics: 自身指标
            benchmark_analysis: 对标分析结果
            target_metrics: 目标指标
            
        Returns:
            GrowthStrategy: 增长策略
        """
        phase = self.analyze_growth_phase(my_metrics.get("followers", 0))
        phase_info = self.GROWTH_PHASES[phase]
        
        strategy = GrowthStrategy(
            strategy_id=f"strategy_{int(time.time())}",
            phase=phase,
            focus_areas=phase_info["focus"],
            timeline={"phase": phase_info["name"], "duration": phase_info["timeline"]}
        )
        
        # 基于分析结果生成战术
        strategy.tactics = self._generate_tactics(phase, benchmark_analysis)
        
        # 设置KPI
        strategy.kpis = self._generate_kpis(my_metrics, target_metrics)
        
        self.generated_strategies.append(strategy)
        return strategy
    
    def _generate_tactics(
        self,
        phase: str,
        benchmark_analysis: Dict[str, Any]
    ) -> List[Dict]:
        """生成战术列表"""
        tactics = []
        
        # 基础战术（所有阶段适用）
        tactics.append({
            "category": "content",
            "tactic": "固定更新节奏",
            "description": "每周发布3-5条内容，保持规律更新",
            "priority": "high"
        })
        
        tactics.append({
            "category": "operation",
            "description": "每天固定时间回复评论，与粉丝互动",
            "priority": "medium"
        })
        
        # 基于阶段添加战术
        if phase == "startup":
            tactics.extend([
                {
                    "category": "content",
                    "tactic": "快速试错",
                    "description": "尝试不同内容形式，找到适合自己的方向",
                    "priority": "high"
                },
                {
                    "category": "collaboration",
                    "tactic": "寻找同级别账号互推",
                    "description": "与粉丝量相近的账号合作，互相导流",
                    "priority": "medium"
                }
            ])
        
        elif phase == "growth":
            tactics.extend([
                {
                    "category": "content",
                    "tactic": "爆款复制与优化",
                    "description": "学习对标爆款的结构和形式，结合自身特点优化",
                    "priority": "high"
                },
                {
                    "category": "content",
                    "tactic": "建立内容矩阵",
                    "description": "形成稳定的内容类型组合，提升粉丝期待感",
                    "priority": "high"
                },
                {
                    "category": "operation",
                    "tactic": "粉丝社群运营",
                    "description": "建立粉丝群，培养核心粉丝群体",
                    "priority": "medium"
                }
            ])
        
        elif phase == "mature":
            tactics.extend([
                {
                    "category": "content",
                    "tactic": "内容品质升级",
                    "description": "提升内容制作质量，打造精品内容",
                    "priority": "high"
                },
                {
                    "category": "collaboration",
                    "tactic": "商业合作拓展",
                    "description": "承接品牌合作，实现商业变现",
                    "priority": "high"
                },
                {
                    "category": "operation",
                    "tactic": "矩阵号布局",
                    "description": "考虑开设子账号，扩大影响力",
                    "priority": "medium"
                }
            ])
        
        # 基于对标分析添加针对性战术
        if benchmark_analysis.get("content_insights"):
            insights = benchmark_analysis["content_insights"]
            
            if "weak_interaction" in insights:
                tactics.append({
                    "category": "operation",
                    "tactic": "强化互动引导",
                    "description": "在内容中增加互动话术，提升评论和分享",
                    "priority": "high"
                })
            
            if "weak_viral" in insights:
                tactics.append({
                    "category": "content",
                    "tactic": "话题型内容",
                    "description": "增加蹭热点和话题讨论类内容",
                    "priority": "high"
                })
        
        return tactics
    
    def _generate_kpis(
        self,
        my_metrics: Dict[str, Any],
        target_metrics: Dict[str, Any]
    ) -> List[Dict]:
        """生成KPI指标"""
        kpis = []
        
        # 粉丝增长
        current_followers = my_metrics.get("followers", 0)
        target_followers = target_metrics.get("followers", current_followers * 2)
        
        kpis.append({
            "metric": "粉丝数",
            "current": current_followers,
            "target": target_followers,
            "growth_rate": round((target_followers - current_followers) / current_followers * 100, 1) if current_followers > 0 else 0,
            "frequency": "weekly",
            "priority": "high"
        })
        
        # 互动率
        current_engagement = my_metrics.get("engagement_rate", 0)
        target_engagement = target_metrics.get("engagement_rate", current_engagement * 1.2)
        
        kpis.append({
            "metric": "互动率",
            "current": current_engagement,
            "target": target_engagement,
            "improvement": round(target_engagement - current_engagement, 2),
            "frequency": "weekly",
            "priority": "high"
        })
        
        # 播放量
        current_views = my_metrics.get("avg_views", 0)
        target_views = target_metrics.get("avg_views", current_views * 1.5)
        
        kpis.append({
            "metric": "平均播放",
            "current": current_views,
            "target": target_views,
            "improvement": round((target_views - current_views) / current_views * 100, 1) if current_views > 0 else 0,
            "frequency": "per_video",
            "priority": "medium"
        })
        
        # 爆款率
        kpis.append({
            "metric": "爆款率",
            "current": my_metrics.get("viral_rate", 0),
            "target": target_metrics.get("viral_rate", 15),
            "frequency": "monthly",
            "priority": "medium"
        })
        
        return kpis
    
    def generate_content_calendar(
        self,
        strategy: GrowthStrategy,
        weeks: int = 4,
        hot_topics: List[str] = None
    ) -> List[ContentPlan]:
        """
        生成内容日历
        
        Args:
            strategy: 增长策略
            weeks: 周数
            hot_topics: 热点话题
            
        Returns:
            List[ContentPlan]: 内容计划列表
        """
        if hot_topics is None:
            hot_topics = [
                "#职场干货", "#生活技巧", "#学习方法", 
                "#今日话题", "#热点讨论"
            ]
        
        plans = []
        
        # 内容矩阵配置
        matrix_config = {
            "startup": {"引流型": 3, "固粉型": 2, "人设型": 1},
            "growth": {"引流型": 2, "固粉型": 3, "人设型": 1},
            "mature": {"引流型": 1, "固粉型": 2, "转化型": 2, "人设型": 1}
        }
        
        matrix = matrix_config.get(strategy.phase, matrix_config["growth"])
        
        # 生成每周计划
        current_week = datetime.now().isocalendar()[1]
        
        for week_offset in range(weeks):
            week_num = current_week + week_offset
            
            # 分配内容类型
            weekly_matrix = {}
            remaining = 4  # 每周4条内容
            for content_type, ratio in matrix.items():
                count = min(remaining, int(ratio * 4 / sum(matrix.values())))
                weekly_matrix[content_type] = count
                remaining -= count
            
            # 确保总量为4
            while remaining > 0:
                for content_type in weekly_matrix:
                    weekly_matrix[content_type] += 1
                    remaining -= 1
                    if remaining <= 0:
                        break
            
            # 生成发布安排
            posting_schedule = []
            days = ["周一", "周三", "周五", "周日"]
            times = ["12:00", "20:00", "20:00", "21:00"]
            
            post_idx = 0
            for content_type, count in weekly_matrix.items():
                for _ in range(count):
                    posting_schedule.append({
                        "day": days[min(post_idx, len(days)-1)],
                        "time": times[min(post_idx, len(times)-1)],
                        "content_type": content_type,
                        "theme": self._generate_content_theme(content_type, hot_topics)
                    })
                    post_idx += 1
            
            # 排序
            posting_schedule.sort(key=lambda x: (days.index(x["day"]), x["time"]))
            
            plan = ContentPlan(
                week_number=week_num,
                content_themes=self._generate_weekly_themes(strategy.phase),
                content_matrix=weekly_matrix,
                posting_schedule=posting_schedule,
                hot_topics=random.sample(hot_topics, 3)
            )
            
            plans.append(plan)
        
        return plans
    
    def _generate_content_theme(self, content_type: str, hot_topics: List[str]) -> str:
        """生成内容主题"""
        themes = {
            "引流型": [
                "蹭热点话题",
                "争议性观点",
                "知识干货",
                "实用技巧"
            ],
            "固粉型": [
                "粉丝问答",
                "幕后花絮",
                "教程详解",
                "案例分析"
            ],
            "转化型": [
                "产品测评",
                "好物推荐",
                "效果展示",
                "选购指南"
            ],
            "人设型": [
                "个人生活",
                "观点分享",
                "成长故事",
                "日常记录"
            ]
        }
        
        return random.choice(themes.get(content_type, ["日常分享"]))
    
    def _generate_weekly_themes(self, phase: str) -> List[str]:
        """生成每周主题"""
        all_themes = [
            "本周重点：实用技巧分享",
            "本周重点：粉丝互动专题",
            "本周重点：热点话题跟进",
            "本周重点：案例深度解析",
            "本周重点：经验总结分享"
        ]
        
        return random.sample(all_themes, 2)
    
    def generate_action_checklist(
        self,
        strategy: GrowthStrategy,
        content_plan: ContentPlan
    ) -> Dict[str, Any]:
        """
        生成执行清单
        
        Args:
            strategy: 增长策略
            content_plan: 内容计划
            
        Returns:
            Dict: 执行清单
        """
        checklist = {
            "daily": [],
            "weekly": [],
            "monthly": []
        }
        
        # 每日任务
        checklist["daily"] = [
            "发布当天内容（按计划时间）",
            "回复所有评论（30分钟内）",
            "检查数据反馈",
            "查看对标账号动态"
        ]
        
        # 每周任务
        checklist["weekly"] = [
            "复盘本周数据表现",
            "分析对标账号爆款规律",
            "规划下周内容选题",
            "与粉丝群互动"
        ]
        
        if content_plan:
            checklist["weekly"].append(
                f"本周发布计划：{sum(content_plan.content_matrix.values())}条内容"
            )
        
        # 每月任务
        checklist["monthly"] = [
            "分析月度数据趋势",
            "评估KPI完成情况",
            "调整优化策略",
            "总结复盘"
        ]
        
        return checklist
    
    def generate_strategy_report(
        self,
        strategy: GrowthStrategy,
        content_plans: List[ContentPlan],
        action_checklist: Dict[str, Any]
    ) -> str:
        """
        生成增长策略报告
        
        Args:
            strategy: 增长策略
            content_plans: 内容计划列表
            action_checklist: 执行清单
            
        Returns:
            str: 策略报告
        """
        phase_info = self.GROWTH_PHASES.get(strategy.phase, {})
        
        report_lines = [
            "=" * 60,
            "🚀 抖音账号增长策略报告",
            "=" * 60,
            "",
            f"📌 当前阶段: {phase_info.get('name', '未知')}",
            f"📌 策略周期: {strategy.timeline.get('duration', '未知')}",
            "",
            "-" * 60,
            "一、增长策略概述",
            "-" * 60,
            "",
            f"【重点领域】: {', '.join(strategy.focus_areas)}",
            "",
        ]
        
        # 战术列表
        report_lines.extend([
            "",
            "二、执行战术",
            "-" * 60,
            "",
        ])
        
        # 按优先级分组
        high_priority = [t for t in strategy.tactics if t.get("priority") == "high"]
        medium_priority = [t for t in strategy.tactics if t.get("priority") == "medium"]
        
        if high_priority:
            report_lines.append("【高优先级】")
            for tactic in high_priority:
                desc = tactic.get("description", tactic.get("tactic", ""))
                report_lines.append(f"  🔴 {desc}")
            report_lines.append("")
        
        if medium_priority:
            report_lines.append("【中优先级】")
            for tactic in medium_priority:
                desc = tactic.get("description", tactic.get("tactic", ""))
                report_lines.append(f"  🟡 {desc}")
            report_lines.append("")
        
        # KPI指标
        report_lines.extend([
            "",
            "三、核心KPI",
            "-" * 60,
            "",
            f"{'指标':<12} {'当前':<15} {'目标':<15} {'频率':<10}",
            "-" * 60,
        ])
        
        for kpi in strategy.kpis:
            current = kpi.get("current", 0)
            target = kpi.get("target", 0)
            
            if "粉丝" in kpi["metric"]:
                current_str = f"{current:,}"
                target_str = f"{target:,}"
            elif isinstance(current, float):
                current_str = f"{current:.1f}%"
                target_str = f"{target:.1f}%"
            else:
                current_str = str(current)
                target_str = str(target)
            
            report_lines.append(
                f"{kpi['metric']:<12} {current_str:<15} {target_str:<15} {kpi.get('frequency', '-'):<10}"
            )
        
        # 内容日历
        if content_plans:
            report_lines.extend([
                "",
                "四、近期内容日历",
                "-" * 60,
                "",
            ])
            
            for plan in content_plans[:2]:
                report_lines.append(f"【第{plan.week_number}周】")
                report_lines.append(f"  内容矩阵: {plan.content_matrix}")
                report_lines.append(f"  热点话题: {', '.join(plan.hot_topics)}")
                report_lines.append("  发布安排:")
                
                for post in plan.posting_schedule[:4]:
                    report_lines.append(
                        f"    {post['day']} {post['time']} - {post['content_type']}: {post['theme']}"
                    )
                report_lines.append("")
        
        # 执行清单
        report_lines.extend([
            "",
            "五、日常执行清单",
            "-" * 60,
            "",
            "【每日必做】",
        ])
        
        for task in action_checklist.get("daily", []):
            report_lines.append(f"  ☐ {task}")
        
        report_lines.extend([
            "",
            "【每周必做】",
        ])
        
        for task in action_checklist.get("weekly", []):
            report_lines.append(f"  ☐ {task}")
        
        report_lines.extend([
            "",
            "=" * 60,
            "⚠️ 重要提醒",
            "-" * 60,
            "",
            "1. 坚持执行：策略效果需要时间积累，至少坚持4周再评估",
            "2. 数据驱动：根据实际数据反馈，及时调整策略",
            "3. 学习对标：持续关注对标账号动态，快速借鉴成功经验",
            "4. 内容为王：无论策略如何变化，优质内容永远是核心",
            "",
            "=" * 60,
            f"报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "=" * 60,
        ])
        
        return "\n".join(report_lines)


# 添加time引用
import time


def main():
    """主函数 - 演示增长策略生成"""
    print("=" * 60)
    print("抖音增长策略生成工具")
    print("=" * 60)
    
    # 初始化策略生成器
    generator = GrowthStrategyGenerator()
    
    # 模拟数据
    my_metrics = {
        "followers": 50000,
        "avg_views": 15000,
        "engagement_rate": 4.5,
        "completion_rate": 45,
        "viral_rate": 8,
        "commercial_value": 55
    }
    
    benchmark_analysis = {
        "followers": 500000,
        "avg_views": 80000,
        "engagement_rate": 6.5,
        "content_insights": ["weak_interaction", "weak_viral"]
    }
    
    target_metrics = {
        "followers": 100000,
        "avg_views": 50000,
        "engagement_rate": 6.0,
        "viral_rate": 15
    }
    
    # 分析增长阶段
    print("\n【1】分析增长阶段")
    phase = generator.analyze_growth_phase(my_metrics["followers"])
    phase_info = generator.GROWTH_PHASES[phase]
    
    print(f"当前阶段: {phase_info['name']}")
    print(f"重点领域: {', '.join(phase_info['focus'])}")
    
    # 生成增长策略
    print("\n【2】生成增长策略")
    strategy = generator.generate_strategy(my_metrics, benchmark_analysis, target_metrics)
    
    print(f"\n重点领域: {', '.join(strategy.focus_areas)}")
    print(f"\n执行战术({len(strategy.tactics)}项):")
    for tactic in strategy.tactics[:5]:
        priority_tag = {"high": "🔴", "medium": "🟡"}.get(tactic.get("priority", ""), "🟢")
        print(f"  {priority_tag} {tactic.get('description', tactic.get('tactic', ''))}")
    
    # 显示KPI
    print("\n【3】核心KPI目标")
    for kpi in strategy.kpis:
        if "粉丝" in kpi["metric"]:
            print(f"  {kpi['metric']}: {kpi['current']:,} → {kpi['target']:,} (增长{kpi['growth_rate']}%)")
        else:
            print(f"  {kpi['metric']}: {kpi['current']}% → {kpi['target']}%")
    
    # 生成内容日历
    print("\n【4】生成内容日历")
    hot_topics = ["#职场技巧", "#效率提升", "#学习方法", "#今日话题"]
    content_plans = generator.generate_content_calendar(strategy, weeks=2, hot_topics=hot_topics)
    
    for plan in content_plans[:1]:
        print(f"\n第{plan.week_number}周内容计划:")
        print(f"  内容矩阵: {plan.content_matrix}")
        print(f"  发布安排:")
        for post in plan.posting_schedule[:4]:
            print(f"    {post['day']} {post['time']} - {post['content_type']}")
    
    # 生成执行清单
    print("\n【5】生成执行清单")
    checklist = generator.generate_action_checklist(strategy, content_plans[0] if content_plans else None)
    
    print("  每日任务:")
    for task in checklist["daily"]:
        print(f"    ☐ {task}")
    
    # 生成完整报告
    print("\n【6】生成完整策略报告")
    report = generator.generate_strategy_report(strategy, content_plans, checklist)
    print(report)
    
    print("\n" + "=" * 60)
    print("策略生成完成！")


if __name__ == "__main__":
    main()
