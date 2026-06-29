#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抖音对标账号工具 - 内容策略拆解脚本
功能：深度拆解对标账号的内容策略、选题方向、人设定位
"""

import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from collections import Counter, defaultdict


@dataclass
class ContentStrategy:
    """内容策略"""
    account_id: str = ""
    content_matrix: Dict[str, float] = field(default_factory=dict)
    posting_schedule: Dict[str, Any] = field(default_factory=dict)
    content_themes: List[str] = field(default_factory=list)
    content_forms: List[str] = field(default_factory=list)
    style_tags: List[str] = field(default_factory=list)
    differentiation_points: List[str] = field(default_factory=list)


@dataclass
class PersonaProfile:
    """人设画像"""
    identity: str = ""
    personality: str = ""
    tone: str = ""
    values: List[str] = field(default_factory=list)
    visual_style: str = ""
    target_audience: str = ""


class ContentStrategyParser:
    """内容策略拆解器"""
    
    # 内容类型定义
    CONTENT_TYPES = {
        "引流型": {
            "purpose": "吸引新粉丝",
            "characteristics": ["爆点明确", "话题性强", "时效性高"],
            "frequency": "20%"
        },
        "固粉型": {
            "purpose": "维护老粉丝",
            "characteristics": ["价值输出", "粉丝互动", "情感连接"],
            "frequency": "40%"
        },
        "转化型": {
            "purpose": "商业变现",
            "characteristics": ["产品展示", "效果对比", "购买引导"],
            "frequency": "25%"
        },
        "人设型": {
            "purpose": "强化人设",
            "characteristics": ["个人生活", "观点表达", "态度展示"],
            "frequency": "15%"
        }
    }
    
    # 内容形式库
    CONTENT_FORMS = [
        "真人出镜口播",
        "剧情演绎",
        "图文轮播",
        "屏幕录制",
        "素材混剪",
        "沉浸式体验",
        "对比展示",
        "分屏解说"
    ]
    
    def __init__(self):
        self.parsed_strategies: Dict[str, ContentStrategy] = {}
        self.persona_cache: Dict[str, PersonaProfile] = {}
    
    def parse_content_strategy(
        self,
        account_data: Dict[str, Any],
        video_data: List[Dict[str, Any]],
        fan_data: Dict[str, Any]
    ) -> ContentStrategy:
        """
        解析内容策略
        
        Args:
            account_data: 账号基础数据
            video_data: 视频数据列表
            fan_data: 粉丝数据列表
            
        Returns:
            ContentStrategy: 内容策略对象
        """
        strategy = ContentStrategy(account_id=account_data.get("account_id", ""))
        
        # 1. 内容矩阵分析
        strategy.content_matrix = self._analyze_content_matrix(video_data)
        
        # 2. 发布节奏分析
        strategy.posting_schedule = self._analyze_posting_schedule(video_data)
        
        # 3. 内容主题分析
        strategy.content_themes = self._analyze_content_themes(video_data)
        
        # 4. 内容形式分析
        strategy.content_forms = self._analyze_content_forms(video_data)
        
        # 5. 风格标签
        strategy.style_tags = self._analyze_style_tags(video_data)
        
        # 6. 差异化特点
        strategy.differentiation_points = self._identify_differentiation(
            strategy, fan_data
        )
        
        self.parsed_strategies[strategy.account_id] = strategy
        return strategy
    
    def _analyze_content_matrix(self, videos: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        分析内容矩阵（内容类型占比）
        
        Returns:
            Dict: 各类型内容占比
        """
        matrix = {
            "引流型": 0.0,
            "固粉型": 0.0,
            "转化型": 0.0,
            "人设型": 0.0
        }
        
        if not videos:
            return matrix
        
        # 根据视频特征判断类型
        for video in videos:
            video_type = self._classify_video_type(video)
            matrix[video_type] += 1
        
        # 转换为百分比
        total = len(videos)
        for key in matrix:
            matrix[key] = round(matrix[key] / total * 100, 1)
        
        return matrix
    
    def _classify_video_type(self, video: Dict[str, Any]) -> str:
        """分类视频类型"""
        views = video.get("views", 0)
        likes = video.get("likes", 0)
        shares = video.get("shares", 0)
        comments = video.get("comments", 0)
        title = video.get("title", "")
        topics = video.get("topics", [])
        
        # 高分享率 → 引流型
        if views > 0 and shares / views > 0.02:
            return "引流型"
        
        # 高评论率 → 固粉型
        if views > 0 and comments / views > 0.02:
            return "固粉型"
        
        # 话题含"推荐/种草/测评" → 转化型
        topic_str = " ".join(topics)
        if any(word in topic_str for word in ["推荐", "种草", "测评", "好物"]):
            return "转化型"
        
        # 标题含"我/我的/生活" → 人设型
        if any(word in title for word in ["我", "我的", "生活", "日常", "今天"]):
            return "人设型"
        
        # 高互动 → 固粉型
        if views > 0 and (likes + comments) / views > 0.1:
            return "固粉型"
        
        # 默认：引流型
        return "引流型"
    
    def _analyze_posting_schedule(self, videos: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析发布节奏"""
        schedule = {
            "weekly_frequency": 0,
            "avg_posts_per_week": 0,
            "active_days": [],
            "active_hours": [],
            "pattern": ""
        }
        
        if not videos:
            return schedule
        
        # 统计发布时间
        hour_counter = Counter()
        date_counter = defaultdict(int)
        
        for video in videos:
            publish_time = video.get("publish_time", "")
            try:
                dt = datetime.strptime(publish_time, "%Y-%m-%d %H:%M")
                hour_counter[dt.hour] += 1
                date_counter[dt.strftime("%A")] += 1
            except:
                pass
        
        # 一周发布天数
        schedule["active_days"] = len(date_counter)
        
        # 计算平均每周发布数（假设视频跨度30天）
        schedule["avg_posts_per_week"] = round(len(videos) / 3, 1)
        
        # 高峰时段
        top_hours = hour_counter.most_common(3)
        schedule["active_hours"] = [h[0] for h in top_hours]
        
        # 最佳发布日
        top_days = Counter(date_counter).most_common(3)
        schedule["active_days"] = [d[0] for d in top_days]
        
        # 判断发布模式
        if schedule["avg_posts_per_week"] >= 7:
            schedule["pattern"] = "高频日更型"
        elif schedule["avg_posts_per_week"] >= 4:
            schedule["pattern"] = "稳定更新型"
        elif schedule["avg_posts_per_week"] >= 2:
            schedule["pattern"] = "精选内容型"
        else:
            schedule["pattern"] = "不定期更新型"
        
        return schedule
    
    def _analyze_content_themes(self, videos: List[Dict[str, Any]]) -> List[str]:
        """分析内容主题"""
        themes = []
        
        for video in videos:
            topics = video.get("topics", [])
            title = video.get("title", "")
            
            # 从话题中提取主题
            for topic in topics:
                topic = topic.replace("#", "")
                if len(topic) <= 10 and topic not in ["必看", "建议收藏", "干货", "分享"]:
                    themes.append(topic)
        
        # 统计高频主题
        theme_counter = Counter(themes)
        top_themes = [t[0] for t in theme_counter.most_common(8)]
        
        return top_themes
    
    def _analyze_content_forms(self, videos: List[Dict[str, Any]]) -> List[str]:
        """分析内容形式"""
        forms = []
        
        # 模拟形式判断（实际需要AI视觉分析）
        for video in videos:
            duration = video.get("duration", 0)
            views = video.get("views", 0)
            likes = video.get("likes", 0)
            
            # 根据数据特征推测形式
            if duration <= 20 and likes / max(views, 1) > 0.1:
                forms.append("快节奏口播")
            elif duration > 60 and views > 100000:
                forms.append("深度内容")
            elif random.random() > 0.5:
                forms.append("剧情演绎")
            else:
                forms.append("实用教程")
        
        # 返回最常见的3种形式
        form_counter = Counter(forms)
        return [f[0] for f in form_counter.most_common(3)]
    
    def _analyze_style_tags(self, videos: List[Dict[str, Any]]) -> List[str]:
        """分析风格标签"""
        tags = []
        
        for video in videos[:10]:
            title = video.get("title", "")
            views = video.get("views", 0)
            likes = video.get("likes", 0)
            
            # 标题风格判断
            if any(word in title for word in ["这招", "技巧", "方法", "学会"]):
                tags.append("干货实用")
            
            if any(word in title for word in ["测评", "对比", "测试"]):
                tags.append("专业测评")
            
            if any(word in title for word in ["太好笑了", "笑死", "搞笑"]):
                tags.append("幽默搞笑")
            
            if any(word in title for word in ["感动", "泪目", "太难了"]):
                tags.append("情感共鸣")
            
            if any(word in title for word in ["必看", "建议收藏", "收藏"]):
                tags.append("收藏价值")
            
            # 互动风格判断
            if views > 0 and likes / views > 0.1:
                tags.append("高互动")
        
        # 去重并返回
        unique_tags = list(set(tags))
        return unique_tags[:6]
    
    def _identify_differentiation(
        self, 
        strategy: ContentStrategy,
        fan_data: Dict[str, Any]
    ) -> List[str]:
        """识别差异化特点"""
        differentiation = []
        
        # 基于内容矩阵
        matrix = strategy.content_matrix
        if matrix.get("引流型", 0) > 30:
            differentiation.append("擅长制造爆款话题，引流能力强")
        if matrix.get("固粉型", 0) > 40:
            differentiation.append("注重粉丝运营，互动粘性高")
        if matrix.get("转化型", 0) > 25:
            differentiation.append("商业化内容占比高，变现能力强")
        
        # 基于内容主题
        themes = strategy.content_themes
        if themes:
            differentiation.append(f"专注{themes[0]}细分领域，定位清晰")
        
        # 基于风格标签
        style = strategy.style_tags
        if "干货实用" in style:
            differentiation.append("内容实用价值高，干货满满")
        if "收藏价值" in style:
            differentiation.append("内容具有长尾价值，易于传播")
        
        # 基于粉丝特征
        engagement = fan_data.get("engagement_rate", 0)
        if engagement > 6:
            differentiation.append("粉丝群体活跃度高，商业价值大")
        
        # 基于发布节奏
        pattern = strategy.posting_schedule.get("pattern", "")
        if "高频" in pattern:
            differentiation.append("保持高频更新，持续曝光")
        elif "精选" in pattern:
            differentiation.append("注重内容质量，宁缺毋滥")
        
        return differentiation[:5]
    
    def parse_persona(self, account_data: Dict[str, Any]) -> PersonaProfile:
        """
        解析人设画像
        
        Args:
            account_data: 账号数据
            
        Returns:
            PersonaProfile: 人设画像
        """
        persona = PersonaProfile()
        
        # 从账号信息推断
        category = account_data.get("category", "通用")
        bio = account_data.get("bio", "")
        nickname = account_data.get("nickname", "")
        
        # 身份定位
        persona.identity = self._infer_identity(category, nickname, bio)
        
        # 个性特征
        persona.personality = self._infer_personality(bio)
        
        # 语气风格
        persona.tone = self._infer_tone(bio)
        
        # 价值观
        persona.values = self._infer_values(bio)
        
        # 视觉风格
        persona.visual_style = self._infer_visual_style(account_data)
        
        # 目标受众
        persona.target_audience = self._infer_target_audience(category)
        
        self.persona_cache[account_data.get("account_id", "")] = persona
        return persona
    
    def _infer_identity(self, category: str, nickname: str, bio: str) -> str:
        """推断身份定位"""
        identities = {
            "美食": "美食博主/厨师",
            "美妆": "美妆博主/化妆师",
            "知识": "知识博主/专家",
            "职场": "职场导师/HR",
            "健身": "健身教练/运动博主",
            "穿搭": "时尚博主/穿搭师",
            "母婴": "育儿博主/妈妈",
            "家居": "家居博主/设计师"
        }
        
        # 检查是否有人设关键词
        if any(word in bio for word in ["年", "经验", "资深", "持证"]):
            return identities.get(category, "专业博主") + "（带专业背书）"
        elif any(word in bio for word in ["分享", "记录", "日常"]):
            return identities.get(category, "生活博主") + "（真实分享型）"
        else:
            return identities.get(category, "内容创作者")
    
    def _infer_personality(self, bio: str) -> str:
        """推断个性特征"""
        personalities = []
        
        if any(word in bio for word in ["认真", "专业", "严谨"]):
            personalities.append("专业严谨")
        if any(word in bio for word in ["幽默", "搞笑", "段子"]):
            personalities.append("幽默风趣")
        if any(word in bio for word in ["温暖", "治愈", "贴心"]):
            personalities.append("温暖治愈")
        if any(word in bio for word in ["犀利", "直接", "敢说"]):
            personalities.append("犀利直接")
        if any(word in bio for word in ["励志", "加油", "努力"]):
            personalities.append("积极励志")
        
        return personalities[0] if personalities else "真实自然"
    
    def _infer_tone(self, bio: str) -> str:
        """推断语气风格"""
        if any(word in bio for word in ["教你", "分享", "干货"]):
            return "教导型（传授知识）"
        elif any(word in bio for word in ["一起", "我们", "大家"]):
            return "朋友型（平等交流）"
        elif any(word in bio for word in ["必看", "建议", "强烈"]):
            return "权威型（专业推荐）"
        else:
            return "自然型（日常分享）"
    
    def _infer_values(self, bio: str) -> List[str]:
        """推断价值观"""
        values = []
        
        if any(word in bio for word in ["真实", "原创", "分享"]):
            values.append("真实分享")
        if any(word in bio for word in ["品质", "质量", "认真"]):
            values.append("品质优先")
        if any(word in bio for word in ["实用", "干货", "方法"]):
            values.append("实用主义")
        if any(word in bio for word in ["快乐", "开心", "享受"]):
            values.append("快乐生活")
        
        return values if values else ["热爱生活"]
    
    def _infer_visual_style(self, account_data: Dict[str, Any]) -> str:
        """推断视觉风格"""
        category = account_data.get("category", "通用")
        
        styles = {
            "美食": "暖色调、高食欲、干净整洁",
            "美妆": "精致、高级感、肤色真实",
            "知识": "简约、专业、留白适当",
            "职场": "商务、简洁、专业感",
            "健身": "活力、运动感、汗水感",
            "穿搭": "时尚、精致、场景多样",
            "母婴": "温馨、可爱、亲子感",
            "家居": "精致、温馨、场景化"
        }
        
        return styles.get(category, "统一风格、辨识度高")
    
    def _infer_target_audience(self, category: str) -> str:
        """推断目标受众"""
        audiences = {
            "美食": "25-35岁女性、热爱生活、注重生活品质",
            "美妆": "18-30岁女性、关注时尚、愿意尝试新品",
            "知识": "22-35岁职场人群、追求自我提升",
            "职场": "20-30岁职场新人、面临职业困惑",
            "健身": "20-35岁追求健康生活的人群",
            "穿搭": "18-30岁女性、关注时尚搭配",
            "母婴": "25-35岁新手父母、关注育儿知识",
            "家居": "25-40岁准备或已有家庭的人群"
        }
        
        return audiences.get(category, "18-35岁目标人群")
    
    def generate_strategy_report(
        self,
        strategy: ContentStrategy,
        persona: PersonaProfile
    ) -> str:
        """
        生成内容策略分析报告
        
        Args:
            strategy: 内容策略
            persona: 人设画像
            
        Returns:
            str: 分析报告
        """
        report_lines = [
            "=" * 60,
            "📋 内容策略拆解报告",
            "=" * 60,
            "",
            f"账号ID: {strategy.account_id}",
            "",
            "-" * 60,
            "一、人设定位",
            "-" * 60,
            "",
            f"【身份定位】 {persona.identity}",
            f"【个性特征】 {persona.personality}",
            f"【语气风格】 {persona.tone}",
            f"【视觉风格】 {persona.visual_style}",
            "",
            f"【核心价值观】 {', '.join(persona.values)}",
            f"【目标受众】 {persona.target_audience}",
            "",
            "-" * 60,
            "二、内容矩阵",
            "-" * 60,
            "",
            "【内容类型占比】",
        ]
        
        for content_type, percentage in strategy.content_matrix.items():
            type_info = self.CONTENT_TYPES.get(content_type, {})
            purpose = type_info.get("purpose", "")
            report_lines.append(f"  📊 {content_type}: {percentage}% ({purpose})")
        
        report_lines.extend([
            "",
            "【发布节奏】",
            f"  模式: {strategy.posting_schedule.get('pattern', '未知')}",
            f"  频率: 每周约{strategy.posting_schedule.get('avg_posts_per_week', 0)}条",
            f"  高峰时段: {', '.join(str(h)+':00' for h in strategy.posting_schedule.get('active_hours', []))}",
            "",
            "-" * 60,
            "三、内容主题",
            "-" * 60,
            "",
        ])
        
        for i, theme in enumerate(strategy.content_themes[:8], 1):
            report_lines.append(f"  {i}. {theme}")
        
        report_lines.extend([
            "",
            "-" * 60,
            "四、内容形式",
            "-" * 60,
            "",
        ])
        
        for i, form in enumerate(strategy.content_forms[:3], 1):
            report_lines.append(f"  {i}. {form}")
        
        report_lines.extend([
            "",
            "-" * 60,
            "五、风格标签",
            "-" * 60,
            "",
        ])
        
        style_str = " | ".join(strategy.style_tags[:6])
        report_lines.append(f"  {style_str}")
        
        report_lines.extend([
            "",
            "-" * 60,
            "六、差异化特点",
            "-" * 60,
            "",
        ])
        
        for i, point in enumerate(strategy.differentiation_points[:5], 1):
            report_lines.append(f"  {i}. {point}")
        
        report_lines.extend([
            "",
            "-" * 60,
            "七、策略启示",
            "-" * 60,
            "",
        ])
        
        suggestions = self._generate_strategy_suggestions(strategy, persona)
        for i, suggestion in enumerate(suggestions, 1):
            report_lines.append(f"  {i}. {suggestion}")
        
        report_lines.extend([
            "",
            "=" * 60,
            f"报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "=" * 60,
        ])
        
        return "\n".join(report_lines)
    
    def _generate_strategy_suggestions(
        self,
        strategy: ContentStrategy,
        persona: PersonaProfile
    ) -> List[str]:
        """生成策略建议"""
        suggestions = []
        
        # 基于内容矩阵建议
        matrix = strategy.content_matrix
        
        if matrix.get("引流型", 0) < 20:
            suggestions.append("可增加热点/话题类内容，提升引流能力")
        
        if matrix.get("固粉型", 0) < 30:
            suggestions.append("增加粉丝互动类内容，提升粉丝粘性")
        
        if matrix.get("人设型", 0) < 10:
            suggestions.append("适当增加个人生活/观点表达，强化人设")
        
        # 基于发布节奏建议
        pattern = strategy.posting_schedule.get("pattern", "")
        if "不定期" in pattern:
            suggestions.append("建议建立稳定的内容日历，保持规律更新")
        
        # 基于人设建议
        if persona.personality == "真实自然":
            suggestions.append("保持真实风格，内容要接地气")
        
        return suggestions


def main():
    """主函数 - 演示内容策略拆解"""
    print("=" * 60)
    print("抖音内容策略拆解工具")
    print("=" * 60)
    
    # 初始化拆解器
    parser = ContentStrategyParser()
    
    # 模拟账号数据
    sample_account = {
        "account_id": "test_account_001",
        "nickname": "美食侦探小分队",
        "category": "美食",
        "bio": "10年美食经验 | 分享地道美食 | 教你用普通食材做出餐厅级美味"
    }
    
    # 模拟视频数据
    sample_videos = [
        {
            "title": f"学会这{3+i%3}招，厨房小白变大厨",
            "views": random.randint(50000, 300000),
            "likes": random.randint(5000, 30000),
            "comments": random.randint(500, 3000),
            "shares": random.randint(200, 2000),
            "duration": random.choice([30, 45, 60]),
            "publish_time": (datetime.now() - timedelta(days=random.randint(1, 30))).strftime("%Y-%m-%d %H:%M"),
            "topics": random.sample(["#美食教程", "#家常菜", "#必看", "#干货", "#好物推荐"], 3)
        }
        for i in range(30)
    ]
    
    # 模拟粉丝数据
    sample_fan_data = {
        "engagement_rate": 6.5,
        "total_fans": 300000
    }
    
    # 解析内容策略
    print("\n【1】解析内容策略")
    strategy = parser.parse_content_strategy(sample_account, sample_videos, sample_fan_data)
    
    print(f"账号: {sample_account['nickname']}")
    print(f"\n内容矩阵:")
    for content_type, percentage in strategy.content_matrix.items():
        print(f"  {content_type}: {percentage}%")
    
    print(f"\n发布节奏: {strategy.posting_schedule.get('pattern', '未知')}")
    print(f"高峰时段: {strategy.posting_schedule.get('active_hours', [])}")
    
    print(f"\n内容主题TOP5:")
    for i, theme in enumerate(strategy.content_themes[:5], 1):
        print(f"  {i}. {theme}")
    
    print(f"\n差异化特点:")
    for point in strategy.differentiation_points[:3]:
        print(f"  ✅ {point}")
    
    # 解析人设画像
    print("\n【2】解析人设画像")
    persona = parser.parse_persona(sample_account)
    
    print(f"身份定位: {persona.identity}")
    print(f"个性特征: {persona.personality}")
    print(f"语气风格: {persona.tone}")
    print(f"视觉风格: {persona.visual_style}")
    print(f"目标受众: {persona.target_audience}")
    
    # 生成报告
    print("\n【3】生成策略分析报告")
    report = parser.generate_strategy_report(strategy, persona)
    print(report)
    
    print("\n" + "=" * 60)
    print("拆解完成！")


if __name__ == "__main__":
    main()
