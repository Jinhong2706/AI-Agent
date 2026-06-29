#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抖音对标账号工具 - 爆款视频分析脚本
功能：深度拆解爆款视频的内容规律、选题策略、呈现形式
"""

import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from collections import Counter


@dataclass
class ViralVideo:
    """爆款视频数据"""
    video_id: str = ""
    title: str = ""
    views: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    favorites: int = 0
    duration: int = 0
    publish_time: str = ""
    interaction_rate: float = 0.0
    completion_rate: float = 0.0
    categories: List[str] = field(default_factory=list)
    topics: List[str] = field(default_factory=list)


@dataclass
class VideoAnalysis:
    """视频分析结果"""
    video_id: str = ""
    hook_analysis: Dict[str, Any] = field(default_factory=dict)
    structure_analysis: Dict[str, Any] = field(default_factory=dict)
    content_patterns: List[str] = field(default_factory=list)
    success_factors: List[str] = field(default_factory=list)
    improvement_suggestions: List[str] = field(default_factory=list)


class ViralVideoAnalyzer:
    """爆款视频分析器"""
    
    # 爆款视频黄金公式库
    VIRAL_FORMULAS = {
        "知识类": {
            "hook_patterns": [
                "「你知道吗？{冷知识}」",
                "「99%的人都不知道的{技巧}」",
                "「{问题}的正确答案来了」"
            ],
            "structure": "痛点引入 → 知识讲解 → 实操演示 → 总结升华",
            "key_elements": ["实用干货", "案例展示", "效果对比"]
        },
        "情感类": {
            "hook_patterns": [
                "「{经历}的我，后来怎么样了」",
                "「{情绪词}！这{事情}太{形容词}了」",
                "「你有没有过{共鸣点}？」"
            ],
            "structure": "情绪触发 → 故事讲述 → 情感共鸣 → 引导评论",
            "key_elements": ["真实故事", "情感共鸣", "互动引导"]
        },
        "种草类": {
            "hook_patterns": [
                "「这个{产品}我要吹爆！」",
                "「{价位}以内的天花板被我找到了」",
                "「用了{时间}，{效果}绝了」"
            ],
            "structure": "痛点呈现 → 产品介绍 → 使用体验 → 效果对比 → 购买引导",
            "key_elements": ["真实体验", "效果对比", "限时优惠"]
        },
        "娱乐类": {
            "hook_patterns": [
                "「{反转}了家人们」",
                "「没想到{结果}会是这样」",
                "「这个{梗}我能笑一整年」"
            ],
            "structure": "悬念开场 → 过程发展 → 反转高潮 → 结尾互动",
            "key_elements": ["反转剧情", "幽默表达", "BGM配合"]
        },
        "教程类": {
            "hook_patterns": [
                "「{技能}只需{时间}，一看就会」",
                "「手把手教你{内容}」",
                "「学会这{数量}招，{效果}」"
            ],
            "structure": "成果展示 → 分步讲解 → 注意事项 → 总结回顾",
            "key_elements": ["成品展示", "步骤清晰", "难点提示"]
        }
    }
    
    # 爆款阈值标准
    VIRAL_THRESHOLDS = {
        "10万粉丝账号": {"views": 50000, "likes": 5000, "interaction_rate": 5},
        "50万粉丝账号": {"views": 200000, "likes": 20000, "interaction_rate": 5},
        "100万粉丝账号": {"views": 500000, "likes": 50000, "interaction_rate": 5},
        "500万粉丝账号": {"views": 2000000, "likes": 200000, "interaction_rate": 5},
        "1000万粉丝账号": {"views": 5000000, "likes": 500000, "interaction_rate": 5}
    }
    
    def __init__(self):
        self.analyzed_videos: Dict[str, VideoAnalysis] = {}
        self.pattern_cache: Dict[str, List[str]] = {}
    
    def identify_viral_videos(
        self, 
        videos: List[Dict], 
        follower_count: int = 100000
    ) -> List[ViralVideo]:
        """
        识别爆款视频
        
        Args:
            videos: 视频数据列表
            follower_count: 账号粉丝数
            
        Returns:
            List[ViralVideo]: 爆款视频列表
        """
        # 确定爆款阈值
        threshold = self._get_threshold(follower_count)
        
        viral_videos = []
        for video in videos:
            # 计算互动率
            views = video.get("views", 0)
            likes = video.get("likes", 0)
            comments = video.get("comments", 0)
            shares = video.get("shares", 0)
            favorites = video.get("favorites", 0)
            
            interaction_rate = 0
            if views > 0:
                interaction_rate = (likes + comments + shares + favorites) / views * 100
            
            # 判断是否为爆款
            if (views >= threshold["views"] or 
                likes >= threshold["likes"] or 
                interaction_rate >= threshold["interaction_rate"]):
                
                viral = ViralVideo(
                    video_id=video.get("video_id", ""),
                    title=video.get("title", ""),
                    views=views,
                    likes=likes,
                    comments=comments,
                    shares=shares,
                    favorites=favorites,
                    duration=video.get("duration", 0),
                    publish_time=video.get("publish_time", ""),
                    interaction_rate=round(interaction_rate, 2),
                    completion_rate=video.get("completion_rate", random.uniform(40, 80)),
                    topics=video.get("topics", [])
                )
                viral_videos.append(viral)
        
        # 按综合得分排序
        viral_videos.sort(key=lambda x: self._calculate_viral_score(x), reverse=True)
        
        return viral_videos
    
    def _get_threshold(self, follower_count: int) -> Dict[str, int]:
        """获取爆款阈值"""
        if follower_count >= 10000000:
            return self.VIRAL_THRESHOLDS["1000万粉丝账号"]
        elif follower_count >= 5000000:
            return self.VIRAL_THRESHOLDS["500万粉丝账号"]
        elif follower_count >= 1000000:
            return self.VIRAL_THRESHOLDS["100万粉丝账号"]
        elif follower_count >= 500000:
            return self.VIRAL_THRESHOLDS["50万粉丝账号"]
        else:
            return self.VIRAL_THRESHOLDS["10万粉丝账号"]
    
    def _calculate_viral_score(self, video: ViralVideo) -> float:
        """计算爆款综合得分"""
        # 播放量归一化（取对数）
        view_score = min(video.views / 100000, 100) * 0.3
        
        # 点赞率
        like_rate = video.likes / max(video.views, 1) * 100
        like_score = like_rate * 10 * 0.25
        
        # 评论率
        comment_rate = video.comments / max(video.views, 1) * 100
        comment_score = comment_rate * 20 * 0.2
        
        # 完播率
        completion_score = video.completion_rate * 0.25
        
        return view_score + like_score + comment_score + completion_score
    
    def analyze_video_structure(self, video: ViralVideo) -> VideoAnalysis:
        """
        分析视频结构
        
        Args:
            video: 爆款视频对象
            
        Returns:
            VideoAnalysis: 分析结果
        """
        analysis = VideoAnalysis(video_id=video.video_id)
        
        # 钩子分析
        analysis.hook_analysis = self._analyze_hook(video)
        
        # 结构分析
        analysis.structure_analysis = self._analyze_structure(video)
        
        # 内容规律
        analysis.content_patterns = self._extract_content_patterns(video)
        
        # 成功因素
        analysis.success_factors = self._identify_success_factors(video, analysis)
        
        # 改进建议
        analysis.improvement_suggestions = self._generate_improvements(video, analysis)
        
        self.analyzed_videos[video.video_id] = analysis
        return analysis
    
    def _analyze_hook(self, video: ViralVideo) -> Dict[str, Any]:
        """分析视频钩子（前3秒）"""
        hook_result = {
            "has_question": False,
            "has_number": False,
            "has_emotion": False,
            "has_contrast": False,
            "hook_type": "未知",
            "hook_strength": 0,
            "hook_text": ""
        }
        
        title = video.title
        
        # 检测钩子类型
        if "？" in title or "?" in title:
            hook_result["has_question"] = True
            hook_result["hook_type"] = "疑问型"
        
        # 数字检测
        if any(c.isdigit() for c in title):
            hook_result["has_number"] = True
            hook_result["hook_type"] = "数字型"
        
        # 情感词检测
        emotion_words = ["太", "绝了", "震惊", "感动", "笑死", "哭了"]
        if any(word in title for word in emotion_words):
            hook_result["has_emotion"] = True
            hook_result["hook_type"] = "情感型"
        
        # 对比检测
        if "却" in title or "但是" in title or "vs" in title.lower():
            hook_result["has_contrast"] = True
            hook_result["hook_type"] = "对比型"
        
        # 钩子强度评估
        hook_score = 0
        if hook_result["has_question"]:
            hook_score += 3
        if hook_result["has_number"]:
            hook_score += 2
        if hook_result["has_emotion"]:
            hook_score += 2
        if hook_result["has_contrast"]:
            hook_score += 3
        
        hook_result["hook_strength"] = min(hook_score, 10)
        hook_result["hook_text"] = self._extract_hook_text(title)
        
        return hook_result
    
    def _extract_hook_text(self, title: str) -> str:
        """提取钩子文本（前10个字）"""
        # 移除话题标签
        clean_title = title.split("#")[0].strip()
        return clean_title[:15] + "..." if len(clean_title) > 15 else clean_title
    
    def _analyze_structure(self, video: ViralVideo) -> Dict[str, Any]:
        """分析视频结构"""
        structure = {
            "duration_category": "",
            "structure_type": "",
            "pacing_score": 0,
            "highlights": []
        }
        
        # 时长分类
        if video.duration <= 15:
            structure["duration_category"] = "短视频（≤15秒）"
        elif video.duration <= 30:
            structure["duration_category"] = "短中视频（15-30秒）"
        elif video.duration <= 60:
            structure["duration_category"] = "中视频（30-60秒）"
        else:
            structure["duration_category"] = "长视频（>60秒）"
        
        # 推断结构类型
        if video.completion_rate >= 70:
            structure["structure_type"] = "紧凑型（高完播）"
            structure["pacing_score"] = 9
        elif video.completion_rate >= 50:
            structure["structure_type"] = "均衡型"
            structure["pacing_score"] = 7
        else:
            structure["structure_type"] = "松散型（低完播）"
            structure["pacing_score"] = 5
        
        # 内容亮点
        structure["highlights"] = self._extract_highlights(video)
        
        return structure
    
    def _extract_highlights(self, video: ViralVideo) -> List[str]:
        """提取内容亮点"""
        highlights = []
        
        # 基于数据推断亮点
        if video.comments / max(video.views, 1) > 0.02:
            highlights.append("评论引导性强")
        
        if video.shares / max(video.views, 1) > 0.01:
            highlights.append("传播性强（高分享）")
        
        if video.favorites / max(video.views, 1) > 0.05:
            highlights.append("收藏价值高")
        
        if video.likes / max(video.views, 1) > 0.1:
            highlights.append("内容认可度高")
        
        # 基于时长推断
        if video.duration <= 30:
            highlights.append("节奏快、信息密度高")
        else:
            highlights.append("内容深度足够")
        
        return highlights
    
    def _extract_content_patterns(self, video: ViralVideo) -> List[str]:
        """提取内容规律"""
        patterns = []
        
        # 分析话题标签
        for topic in video.topics[:3]:
            if "必看" in topic or "建议收藏" in topic:
                patterns.append("收藏型话题")
            elif "教程" in topic:
                patterns.append("教程型内容")
            elif "测评" in topic:
                patterns.append("测评型内容")
            elif "分享" in topic:
                patterns.append("分享型内容")
        
        # 分析时长偏好
        if video.duration <= 30:
            patterns.append("短视频形式")
        elif video.duration <= 60:
            patterns.append("中视频形式")
        else:
            patterns.append("长视频形式")
        
        # 基于互动数据推断
        if video.interaction_rate >= 10:
            patterns.append("高互动内容")
        elif video.interaction_rate >= 5:
            patterns.append("中等互动内容")
        
        return patterns
    
    def _identify_success_factors(
        self, 
        video: ViralVideo,
        analysis: VideoAnalysis
    ) -> List[str]:
        """识别成功因素"""
        factors = []
        
        # 钩子强度
        if analysis.hook_analysis["hook_strength"] >= 7:
            factors.append(f"强钩子：{analysis.hook_analysis['hook_type']}")
        
        # 结构优化
        if analysis.structure_analysis["pacing_score"] >= 7:
            factors.append("节奏把控好，完播率高")
        
        # 话题设置
        if video.topics:
            factors.append(f"话题标签精准：{', '.join(video.topics[:2])}")
        
        # 数据表现
        if video.interaction_rate >= 8:
            factors.append("高互动率，粉丝粘性强")
        
        if video.shares / max(video.views, 1) > 0.02:
            factors.append("高传播性，内容有传播价值")
        
        # 时机把握
        factors.append("发布时间与目标人群活跃时段匹配")
        
        return factors
    
    def _generate_improvements(
        self, 
        video: ViralVideo,
        analysis: VideoAnalysis
    ) -> List[str]:
        """生成改进建议"""
        suggestions = []
        
        # 钩子优化
        if analysis.hook_analysis["hook_strength"] < 7:
            suggestions.append("增强开头钩子，使用疑问句或数字开头")
            suggestions.append("前3秒必须出现核心看点或冲突")
        
        # 完播率优化
        if video.completion_rate < 50:
            suggestions.append("优化内容节奏，减少冗余信息")
            suggestions.append("重要内容前置，避免拖延")
        
        # 互动引导
        if video.comments / max(video.views, 1) < 0.01:
            suggestions.append("增加互动引导，如「评论区告诉我」")
            suggestions.append("设置话题讨论点，引导粉丝评论")
        
        # 分享引导
        if video.shares / max(video.views, 1) < 0.01:
            suggestions.append("增加转发激励话术，如「转给需要的朋友」")
        
        # 收藏引导
        if video.favorites / max(video.views, 1) < 0.03:
            suggestions.append("增加收藏引导，如「先收藏再学习」")
        
        return suggestions
    
    def compare_viral_patterns(
        self, 
        videos: List[ViralVideo]
    ) -> Dict[str, Any]:
        """
        爆款视频模式对比分析
        
        Args:
            videos: 爆款视频列表
            
        Returns:
            Dict: 模式分析结果
        """
        if not videos:
            return {}
        
        patterns = {
            "total_count": len(videos),
            "avg_duration": sum(v.duration for v in videos) / len(videos),
            "avg_interaction_rate": sum(v.interaction_rate for v in videos) / len(videos),
            "avg_completion_rate": sum(v.completion_rate for v in videos) / len(videos),
            "common_topics": self._extract_common_topics(videos),
            "duration_distribution": self._analyze_duration_dist(videos),
            "time_pattern": self._analyze_time_pattern(videos),
            "title_patterns": self._analyze_title_patterns(videos)
        }
        
        return patterns
    
    def _extract_common_topics(self, videos: List[ViralVideo]) -> List[str]:
        """提取共同话题"""
        all_topics = []
        for video in videos:
            all_topics.extend(video.topics)
        
        counter = Counter(all_topics)
        return [t[0] for t in counter.most_common(5)]
    
    def _analyze_duration_dist(self, videos: List[ViralVideo]) -> Dict[str, int]:
        """分析时长分布"""
        dist = {"≤15秒": 0, "16-30秒": 0, "31-60秒": 0, ">60秒": 0}
        
        for video in videos:
            if video.duration <= 15:
                dist["≤15秒"] += 1
            elif video.duration <= 30:
                dist["16-30秒"] += 1
            elif video.duration <= 60:
                dist["31-60秒"] += 1
            else:
                dist[">60秒"] += 1
        
        return dist
    
    def _analyze_time_pattern(self, videos: List[ViralVideo]) -> Dict[str, Any]:
        """分析发布时间模式"""
        hours = []
        for video in videos:
            try:
                dt = datetime.strptime(video.publish_time, "%Y-%m-%d %H:%M")
                hours.append(dt.hour)
            except:
                pass
        
        if hours:
            avg_hour = sum(hours) / len(hours)
            return {
                "avg_publish_hour": round(avg_hour, 1),
                "common_hours": list(set(hours))
            }
        return {}
    
    def _analyze_title_patterns(self, videos: List[ViralVideo]) -> List[str]:
        """分析标题模式"""
        patterns = []
        
        for video in videos:
            title = video.title
            
            if any(c.isdigit() for c in title):
                patterns.append("数字型标题")
            
            if "？" in title or "?" in title:
                patterns.append("疑问型标题")
            
            if any(word in title for word in ["太", "绝", "竟然", "没想到"]):
                patterns.append("情感型标题")
            
            if any(word in title for word in ["竟然", "但是", "却", "vs"]):
                patterns.append("对比型标题")
        
        # 返回最常见的模式
        counter = Counter(patterns)
        return [p[0] for p in counter.most_common(3)]
    
    def generate_viral_report(
        self, 
        videos: List[ViralVideo],
        patterns: Dict[str, Any]
    ) -> str:
        """
        生成爆款视频分析报告
        
        Args:
            videos: 爆款视频列表
            patterns: 模式分析结果
            
        Returns:
            str: 分析报告
        """
        report_lines = [
            "=" * 60,
            "🎬 爆款视频分析报告",
            "=" * 60,
            "",
            f"📊 分析视频数: {patterns.get('total_count', 0)} 条",
            "",
            "-" * 60,
            "一、爆款共性规律",
            "-" * 60,
            "",
            f"【平均时长】 {patterns.get('avg_duration', 0):.0f} 秒",
            f"【平均互动率】 {patterns.get('avg_interaction_rate', 0):.2f}%",
            f"【平均完播率】 {patterns.get('avg_completion_rate', 0):.1f}%",
            "",
            "【时长分布】",
        ]
        
        for duration, count in patterns.get("duration_distribution", {}).items():
            report_lines.append(f"  {duration}: {count} 条")
        
        report_lines.extend([
            "",
            "【高频话题】",
        ])
        
        for i, topic in enumerate(patterns.get("common_topics", [])[:5], 1):
            report_lines.append(f"  {i}. {topic}")
        
        report_lines.extend([
            "",
            "【标题模式】",
        ])
        
        for i, pattern in enumerate(patterns.get("title_patterns", [])[:3], 1):
            report_lines.append(f"  {i}. {pattern}")
        
        report_lines.extend([
            "",
            "-" * 60,
            "二、TOP10爆款视频",
            "-" * 60,
            "",
        ])
        
        for i, video in enumerate(videos[:10], 1):
            report_lines.extend([
                f"[{i}] {video.title}",
                f"    播放: {video.views:,} | 点赞: {video.likes:,} | 互动率: {video.interaction_rate}%",
                f"    时长: {video.duration}秒 | 完播率: {video.completion_rate:.1f}%",
                "",
            ])
        
        report_lines.extend([
            "-" * 60,
            "三、爆款打造建议",
            "-" * 60,
            "",
            "【选题方向】",
            f"  重点围绕: {', '.join(patterns.get('common_topics', [])[:3])}",
            "",
            "【时长建议】",
            f"  最佳时长: {self._get_optimal_duration(patterns)}",
            "",
            "【标题公式】",
            "  ✅ 数字型：学会这X招，快速搞定XX",
            "  ✅ 疑问型：为什么XX？XX了你就知道了",
            "  ✅ 情感型：太绝了！这XX我能用一周",
            "  ✅ 对比型：别人XX，我却XX",
            "",
            "【内容结构】",
            "  1. 黄金3秒：制造悬念/冲突/疑问",
            "  2. 内容展开：干货输出/情感共鸣/实用价值",
            "  3. 结尾引导：互动话术/关注引导/收藏激励",
            "",
            "=" * 60,
            f"报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "=" * 60,
        ])
        
        return "\n".join(report_lines)
    
    def _get_optimal_duration(self, patterns: Dict[str, Any]) -> str:
        """获取最佳时长建议"""
        avg_duration = patterns.get("avg_duration", 45)
        
        if avg_duration <= 20:
            return "15-30秒（节奏快、信息密集）"
        elif avg_duration <= 45:
            return "30-60秒（均衡型，适合大多数内容）"
        else:
            return "60秒以上（需要有足够的价值支撑）"


def main():
    """主函数 - 演示爆款视频分析"""
    print("=" * 60)
    print("抖音爆款视频分析工具")
    print("=" * 60)
    
    # 初始化分析器
    analyzer = ViralVideoAnalyzer()
    
    # 模拟视频数据
    sample_videos = [
        {
            "video_id": f"vid_{i}",
            "title": f"学会这{3+i}招，轻松搞定{['职场沟通', '时间管理', '人际交往'][i%3]}",
            "views": random.randint(50000, 500000),
            "likes": random.randint(5000, 50000),
            "comments": random.randint(500, 5000),
            "shares": random.randint(200, 2000),
            "favorites": random.randint(1000, 10000),
            "duration": random.choice([15, 30, 45, 60, 90]),
            "publish_time": (datetime.now() - timedelta(days=random.randint(1, 30))).strftime("%Y-%m-%d %H:%M"),
            "topics": random.sample(["#实用技巧", "#干货分享", "#必看", "#教程", "#建议收藏"], 3)
        }
        for i in range(20)
    ]
    
    # 识别爆款视频
    print("\n【1】识别爆款视频")
    follower_count = 100000
    viral_videos = analyzer.identify_viral_videos(sample_videos, follower_count)
    
    print(f"识别出 {len(viral_videos)} 条爆款视频（基于{follower_count:,}粉丝账号标准）")
    
    # 分析TOP3爆款
    print("\n【2】深度分析TOP3爆款")
    for i, video in enumerate(viral_videos[:3], 1):
        print(f"\n--- 爆款 #{i} ---")
        print(f"标题: {video.title}")
        print(f"数据: 播放{video.views:,} | 点赞{video.likes:,} | 互动率{video.interaction_rate}%")
        
        analysis = analyzer.analyze_video_structure(video)
        
        print(f"钩子类型: {analysis.hook_analysis['hook_type']}")
        print(f"钩子强度: {analysis.hook_analysis['hook_strength']}/10")
        print(f"结构类型: {analysis.structure_analysis['structure_type']}")
        print(f"内容亮点: {', '.join(analysis.structure_analysis['highlights'])}")
        
        if analysis.success_factors:
            print("成功因素:")
            for factor in analysis.success_factors[:3]:
                print(f"  ✅ {factor}")
        
        if analysis.improvement_suggestions:
            print("改进建议:")
            for suggestion in analysis.improvement_suggestions[:2]:
                print(f"  💡 {suggestion}")
    
    # 模式对比分析
    print("\n【3】爆款模式对比分析")
    patterns = analyzer.compare_viral_patterns(viral_videos)
    
    print(f"平均时长: {patterns['avg_duration']:.0f}秒")
    print(f"平均互动率: {patterns['avg_interaction_rate']:.2f}%")
    print(f"高频话题: {', '.join(patterns['common_topics'][:3])}")
    print(f"标题模式: {', '.join(patterns['title_patterns'])}")
    
    # 生成报告
    print("\n【4】生成分析报告")
    report = analyzer.generate_viral_report(viral_videos, patterns)
    print(report)
    
    print("\n" + "=" * 60)
    print("分析完成！")


if __name__ == "__main__":
    main()
