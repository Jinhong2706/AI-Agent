#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抖音对标账号工具 - 粉丝画像分析脚本
功能：深度分析对标账号的粉丝特征、行为习惯、商业价值
"""

import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from collections import Counter


@dataclass
class FanProfile:
    """粉丝画像"""
    account_id: str = ""
    fan_count: int = 0
    gender_ratio: Dict[str, float] = field(default_factory=dict)
    age_distribution: Dict[str, float] = field(default_factory=dict)
    region_distribution: Dict[str, float] = field(default_factory=dict)
    interest_tags: List[str] = field(default_factory=list)
    device_distribution: Dict[str, float] = field(default_factory=dict)
    active_hours: List[int] = field(default_factory=list)
    engagement_rate: float = 0.0
    loyalty_score: float = 0.0
    commercial_value: float = 0.0


@dataclass
class ContentPreference:
    """内容偏好"""
    category: str = ""
    style: str = ""
    duration_preference: str = ""
    interaction_style: str = ""


class FanProfileAnalyzer:
    """粉丝画像分析器"""
    
    # 行业粉丝特征基准
    INDUSTRY_BENCHMARKS = {
        "美食": {
            "target_age": ["25-34", "18-24"],
            "target_gender": "female",
            "peak_hours": [11, 12, 17, 18, 20, 21],
            "avg_engagement": 5.5,
            "consumption_level": "medium-high"
        },
        "美妆": {
            "target_age": ["18-24", "25-34"],
            "target_gender": "female",
            "peak_hours": [12, 13, 20, 21, 22],
            "avg_engagement": 6.8,
            "consumption_level": "high"
        },
        "知识": {
            "target_age": ["25-34", "35-44"],
            "target_gender": "neutral",
            "peak_hours": [12, 13, 20, 21],
            "avg_engagement": 4.2,
            "consumption_level": "medium"
        },
        "职场": {
            "target_age": ["25-34", "18-24"],
            "target_gender": "neutral",
            "peak_hours": [8, 9, 12, 13, 20, 21],
            "avg_engagement": 4.5,
            "consumption_level": "medium"
        },
        "健身": {
            "target_age": ["18-24", "25-34"],
            "target_gender": "neutral",
            "peak_hours": [6, 7, 19, 20, 21],
            "avg_engagement": 5.8,
            "consumption_level": "high"
        },
        "穿搭": {
            "target_age": ["18-24", "25-34"],
            "target_gender": "female",
            "peak_hours": [12, 13, 20, 21, 22],
            "avg_engagement": 6.2,
            "consumption_level": "high"
        },
        "母婴": {
            "target_age": ["25-34", "35-44"],
            "target_gender": "female",
            "peak_hours": [10, 11, 14, 15, 21, 22],
            "avg_engagement": 7.5,
            "consumption_level": "very-high"
        },
        "家居": {
            "target_age": ["25-34", "35-44"],
            "target_gender": "female",
            "peak_hours": [12, 13, 20, 21, 22],
            "avg_engagement": 5.0,
            "consumption_level": "high"
        }
    }
    
    def __init__(self):
        self.analyzed_profiles: Dict[str, FanProfile] = {}
        self.comparison_cache: Dict[str, Any] = {}
    
    def analyze_fan_profile(
        self, 
        fan_data: Dict[str, Any],
        category: str = "通用"
    ) -> FanProfile:
        """分析粉丝画像"""
        profile = FanProfile(
            account_id=fan_data.get("account_id", ""),
            fan_count=fan_data.get("total_fans", 0),
            gender_ratio=fan_data.get("gender_distribution", {}),
            age_distribution=fan_data.get("age_distribution", {}),
            region_distribution=fan_data.get("region_distribution", {}),
            interest_tags=fan_data.get("interest_tags", []),
            engagement_rate=fan_data.get("engagement_rate", 0),
            loyalty_score=fan_data.get("fans_quality_score", 0) / 100
        )
        
        profile.device_distribution = self._generate_device_distribution()
        profile.active_hours = fan_data.get("active_hours", [12, 20, 21])
        profile.commercial_value = self._calculate_commercial_value(profile, category)
        
        self.analyzed_profiles[profile.account_id] = profile
        return profile
    
    def _generate_device_distribution(self) -> Dict[str, float]:
        """生成设备分布"""
        return {
            "iOS": round(random.uniform(30, 55), 1),
            "Android": round(random.uniform(45, 70), 1)
        }
    
    def _calculate_commercial_value(self, profile: FanProfile, category: str) -> float:
        """计算商业价值"""
        score = 50
        
        if profile.fan_count >= 1000000:
            score += 20
        elif profile.fan_count >= 100000:
            score += 15
        elif profile.fan_count >= 10000:
            score += 10
        
        if profile.engagement_rate >= 8:
            score += 15
        elif profile.engagement_rate >= 5:
            score += 10
        elif profile.engagement_rate >= 3:
            score += 5
        
        score += profile.loyalty_score * 10
        
        female_ratio = profile.gender_ratio.get("female", 50)
        if female_ratio >= 70:
            score += 5
        
        return min(score, 100)
    
    def compare_with_benchmark(
        self, 
        profile: FanProfile, 
        category: str = "通用"
    ) -> Dict[str, Any]:
        """与行业基准对比"""
        benchmark = self.INDUSTRY_BENCHMARKS.get(category, self._get_default_benchmark())
        
        comparison = {
            "category": category,
            "benchmark": benchmark,
            "gaps": {},
            "advantages": {},
            "suggestions": []
        }
        
        female_ratio = profile.gender_ratio.get("female", 50)
        if female_ratio >= 60:
            comparison["advantages"]["gender"] = f"女性占比{female_ratio}%，高于行业均值"
        else:
            comparison["gaps"]["gender"] = f"女性占比{female_ratio}%，低于同类账号"
        
        top_age = max(profile.age_distribution.items(), key=lambda x: x[1])
        if top_age[0] in benchmark["target_age"]:
            comparison["advantages"]["age"] = f"核心年龄段为{top_age[0]}，精准触达目标人群"
        else:
            comparison["gaps"]["age"] = f"核心年龄段为{top_age[0]}，与行业偏好有偏差"
        
        if profile.engagement_rate >= benchmark["avg_engagement"]:
            comparison["advantages"]["engagement"] = f"互动率{profile.engagement_rate}%，高于行业均值"
        else:
            comparison["gaps"]["engagement"] = f"互动率{profile.engagement_rate}%，低于行业均值"
            comparison["suggestions"].append("建议提升内容互动性，增加引导评论的话术")
        
        common_hours = set(profile.active_hours) & set(benchmark["peak_hours"])
        if len(common_hours) >= 3:
            comparison["advantages"]["timing"] = "发布时段与粉丝活跃时段匹配度较高"
        else:
            comparison["suggestions"].append("建议调整发布时间至粉丝活跃时段")
        
        comparison["suggestions"].extend(self._generate_improvement_suggestions(comparison))
        
        return comparison
    
    def _get_default_benchmark(self) -> Dict[str, Any]:
        """获取默认基准"""
        return {
            "target_age": ["18-24", "25-34"],
            "target_gender": "neutral",
            "peak_hours": [12, 20, 21],
            "avg_engagement": 4.5,
            "consumption_level": "medium"
        }
    
    def _generate_improvement_suggestions(self, comparison: Dict) -> List[str]:
        """生成改进建议"""
        suggestions = []
        
        if "engagement" in comparison["gaps"]:
            suggestions.append("增强内容互动性：结尾引导评论、设置话题讨论")
            suggestions.append("提升粉丝粘性：增加粉丝专属福利、互动活动")
        
        if "gender" in comparison["gaps"]:
            suggestions.append("调整内容方向，增加目标人群关注的内容类型")
        
        return suggestions
    
    def analyze_content_preference(
        self, 
        fan_data: Dict[str, Any],
        video_data: List[Dict]
    ) -> ContentPreference:
        """分析粉丝内容偏好"""
        preference = ContentPreference()
        
        high_interaction_videos = [
            v for v in video_data 
            if (v.get("likes", 0) + v.get("comments", 0)) / max(v.get("views", 1), 1) > 0.05
        ]
        
        if high_interaction_videos:
            durations = [v.get("duration", 0) for v in high_interaction_videos]
            avg_duration = sum(durations) / len(durations)
            
            if avg_duration <= 20:
                preference.duration_preference = "短视频（15-30秒）"
            elif avg_duration <= 60:
                preference.duration_preference = "中视频（30-60秒）"
            else:
                preference.duration_preference = "长视频（60秒以上）"
            
            all_topics = []
            for v in high_interaction_videos:
                all_topics.extend(v.get("topics", []))
            
            topic_counter = Counter(all_topics)
            top_topics = [t[0] for t in topic_counter.most_common(3)]
            preference.category = "、".join(top_topics)
            preference.style = self._analyze_content_style(high_interaction_videos)
        
        preference.interaction_style = self._analyze_interaction_style(fan_data)
        
        return preference
    
    def _analyze_content_style(self, videos: List[Dict]) -> str:
        """分析内容风格"""
        styles = []
        
        for video in videos[:10]:
            views = video.get("views", 0)
            likes = video.get("likes", 0)
            comments = video.get("comments", 0)
            
            if views > 0 and comments / views > 0.02:
                styles.append("话题讨论型")
            
            if views > 0 and likes / views > 0.05:
                styles.append("情感共鸣型")
        
        return styles[0] if styles else "实用干货型"
    
    def _analyze_interaction_style(self, fan_data: Dict) -> str:
        """分析互动风格偏好"""
        engagement = fan_data.get("engagement_rate", 0)
        
        if engagement >= 8:
            return "高互动型粉丝，偏好深度参与内容"
        elif engagement >= 5:
            return "中等互动型粉丝，喜欢点赞收藏"
        else:
            return "低互动型粉丝，主要作为纯观众"
    
    def generate_fan_report(
        self, 
        profile: FanProfile,
        comparison: Dict[str, Any],
        preference: ContentPreference
    ) -> str:
        """生成粉丝画像分析报告"""
        report_lines = [
            "=" * 60,
            "📊 粉丝画像分析报告",
            "=" * 60,
            "",
            f"📌 账号ID: {profile.account_id}",
            f"📌 粉丝总量: {profile.fan_count:,}",
            f"📌 商业价值评分: {profile.commercial_value}/100",
            "",
            "-" * 60,
            "一、粉丝基础画像",
            "-" * 60,
            "",
            "【性别分布】",
            f"  女性: {profile.gender_ratio.get('female', 0)}%",
            f"  男性: {profile.gender_ratio.get('male', 0)}%",
            "",
            "【年龄分布】",
        ]
        
        for age, ratio in profile.age_distribution.items():
            report_lines.append(f"  {age}: {ratio}%")
        
        report_lines.extend([
            "",
            "【地域分布TOP5】",
        ])
        
        sorted_regions = sorted(
            profile.region_distribution.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:5]
        for i, (region, ratio) in enumerate(sorted_regions, 1):
            report_lines.append(f"  {i}. {region}: {ratio}%")
        
        report_lines.extend([
            "",
            "【活跃时段】",
            f"  高活跃时段: {', '.join(str(h)+':00' for h in profile.active_hours)}",
            "",
            "-" * 60,
            "二、粉丝质量分析",
            "-" * 60,
            "",
            f"【互动率】 {profile.engagement_rate}%",
            f"【忠诚度】 {profile.loyalty_score * 100:.0f}%",
            "",
        ])
        
        if comparison.get("advantages"):
            report_lines.append("【优势亮点】")
            for key, value in comparison["advantages"].items():
                report_lines.append(f"  ✅ {value}")
            report_lines.append("")
        
        if comparison.get("gaps"):
            report_lines.append("【待优化项】")
            for key, value in comparison["gaps"].items():
                report_lines.append(f"  ⚠️ {value}")
            report_lines.append("")
        
        report_lines.extend([
            "-" * 60,
            "三、内容偏好洞察",
            "-" * 60,
            "",
            f"【偏好时长】 {preference.duration_preference}",
            f"【内容风格】 {preference.style}",
            f"【互动类型】 {preference.interaction_style}",
            "",
            "-" * 60,
            "四、优化建议",
            "-" * 60,
            "",
        ])
        
        for i, suggestion in enumerate(comparison.get("suggestions", []), 1):
            report_lines.append(f"  {i}. {suggestion}")
        
        report_lines.extend([
            "",
            "=" * 60,
            f"报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "=" * 60,
        ])
        
        return "\n".join(report_lines)
    
    def batch_analyze(
        self, 
        fan_data_list: List[Dict[str, Any]],
        categories: List[str]
    ) -> List[Dict[str, Any]]:
        """批量分析多个账号粉丝画像"""
        results = []
        
        for fan_data, category in zip(fan_data_list, categories):
            profile = self.analyze_fan_profile(fan_data, category)
            comparison = self.compare_with_benchmark(profile, category)
            
            results.append({
                "account_id": fan_data.get("account_id"),
                "profile": profile,
                "comparison": comparison,
                "commercial_value": profile.commercial_value
            })
        
        results.sort(key=lambda x: x["commercial_value"], reverse=True)
        return results


def main():
    """主函数 - 演示粉丝画像分析"""
    print("=" * 60)
    print("抖音粉丝画像分析工具")
    print("=" * 60)
    
    analyzer = FanProfileAnalyzer()
    
    sample_fan_data = {
        "account_id": "test_account_001",
        "total_fans": 500000,
        "gender_distribution": {"female": 72, "male": 28},
        "age_distribution": {
            "18-24": 35, 
            "25-34": 40, 
            "35-44": 18, 
            "45+": 7
        },
        "region_distribution": {
            "广东": 18.5, "江苏": 10.2, "浙江": 9.8, 
            "山东": 7.5, "河南": 6.8, "四川": 6.2, "其他": 41.0
        },
        "interest_tags": ["美食", "时尚", "美妆", "旅游", "健身", "家居"],
        "active_hours": [12, 13, 20, 21, 22],
        "engagement_rate": 6.8,
        "fans_quality_score": 85
    }
    
    print("\n【1】分析粉丝画像")
    profile = analyzer.analyze_fan_profile(sample_fan_data, category="美妆")
    
    print(f"粉丝总量: {profile.fan_count:,}")
    print(f"女性占比: {profile.gender_ratio.get('female', 0)}%")
    print(f"商业价值: {profile.commercial_value}")
    
    print("\n【2】与行业基准对比")
    comparison = analyzer.compare_with_benchmark(profile, category="美妆")
    
    if comparison["advantages"]:
        print("\n✅ 优势亮点:")
        for key, value in comparison["advantages"].items():
            print(f"   {value}")
    
    if comparison["suggestions"]:
        print("\n📋 优化建议:")
        for i, suggestion in enumerate(comparison["suggestions"], 1):
            print(f"   {i}. {suggestion}")
    
    print("\n【3】生成分析报告")
    preference = ContentPreference(
        duration_preference="中视频（30-60秒）",
        style="实用干货型",
        interaction_style="中等互动型粉丝，喜欢点赞收藏"
    )
    report = analyzer.generate_fan_report(profile, comparison, preference)
    print(report)
    
    print("\n" + "=" * 60)
    print("分析完成！")


if __name__ == "__main__":
    main()
