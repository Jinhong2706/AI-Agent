#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多渠道内容分发优化器 - 内容适配计算引擎

功能：
1. 解析输入内容，识别内容类型和核心信息点
2. 检测各平台格式要求
3. 计算适配参数（字数、结构、标签等）
4. 生成各平台适配建议

使用：python scripts/content-adapter.py <input_file>
输出：结构化的适配参数报告
"""

import json
import os
import re
import sys
from collections import Counter
from dataclasses import dataclass, field
from typing import Optional


# ============================================================
# 数据模型
# ============================================================

@dataclass
class PlatformSpec:
    """平台规格定义"""
    name: str
    name_cn: str
    min_chars: int
    max_chars: int
    ideal_chars: tuple  # (min, max) 理想字数范围
    hashtag_range: tuple  # (min, max) 标签数量范围
    hashtag_prefix: str  # 标签前缀
    title_style: str  # 标题风格描述
    content_features: list  # 内容特征要求
    optimal_times: list  # 最佳发布时间段
    priority: int  # 优先级（1最高）


@dataclass
class ContentProfile:
    """内容画像"""
    raw_text: str
    total_chars: int
    total_paragraphs: int
    content_type: str  # 科普/观点/教程/评测/故事
    tone: str  # 正式/轻松/专业/通俗
    has_data: bool
    has_images_reference: bool
    key_points: list = field(default_factory=list)
    core_theme: str = ""
    adaptation_score: int = 0


@dataclass
class AdaptationParams:
    """适配参数"""
    platform: str
    target_chars: int
    current_chars: int
    compression_ratio: float
    structure_type: str
    hashtag_count: int
    suggested_hashtags: list
    title_candidates: list
    estimated_engagement: str
    priority: int
    notes: list = field(default_factory=list)


# ============================================================
# 平台规格配置
# ============================================================

PLATFORMS = {
    "wechat": PlatformSpec(
        name="wechat",
        name_cn="微信公众号",
        min_chars=800,
        max_chars=5000,
        ideal_chars=(1500, 3000),
        hashtag_range=(0, 0),
        hashtag_prefix="",
        title_style="信息量丰富，18-30字，可使用分隔符",
        content_features=["深度分析", "结构化排版", "小标题分段", "封面图", "金句提炼"],
        optimal_times=["07:30-08:30", "12:00-13:00", "20:00-22:00"],
        priority=1
    ),
    "xiaohongshu": PlatformSpec(
        name="xiaohongshu",
        name_cn="小红书",
        min_chars=100,
        max_chars=1000,
        ideal_chars=(300, 800),
        hashtag_range=(5, 8),
        hashtag_prefix="#",
        title_style="吸睛短标题，15-25字，使用Emoji和符号",
        content_features=["视觉优先", "Emoji装饰", "要点列表", "前后对比", "标签吸睛"],
        optimal_times=["12:00-13:00", "18:00-20:00", "21:00-23:00"],
        priority=2
    ),
    "douyin": PlatformSpec(
        name="douyin",
        name_cn="抖音",
        min_chars=50,
        max_chars=500,
        ideal_chars=(100, 300),
        hashtag_range=(3, 5),
        hashtag_prefix="#",
        title_style="悬念式，10-20字，引发好奇心",
        content_features=["前3秒钩子", "节奏紧凑", "口语化", "互动引导", "BGM搭配"],
        optimal_times=["07:00-09:00", "12:00-13:00", "19:00-21:00", "21:00-23:00"],
        priority=3
    ),
    "bilibili": PlatformSpec(
        name="bilibili",
        name_cn="B站",
        min_chars=500,
        max_chars=5000,
        ideal_chars=(800, 2000),
        hashtag_range=(5, 10),
        hashtag_prefix="",
        title_style="知识性+趣味性，20-35字，可使用括号补充",
        content_features=["知识性强", "弹幕互动点", "分P结构", "参考文献", "UP主人设"],
        optimal_times=["17:00-19:00", "20:00-23:00", "周末全天"],
        priority=4
    ),
    "zhihu": PlatformSpec(
        name="zhihu",
        name_cn="知乎",
        min_chars=1000,
        max_chars=10000,
        ideal_chars=(2000, 5000),
        hashtag_range=(1, 3),
        hashtag_prefix="",
        title_style="问句式或陈述式，15-30字，体现专业性",
        content_features=["逻辑严密", "数据支撑", "引用标注", "分层论述", "学术规范"],
        optimal_times=["08:00-10:00", "12:00-14:00", "20:00-23:00"],
        priority=5
    ),
    "weibo": PlatformSpec(
        name="weibo",
        name_cn="微博",
        min_chars=50,
        max_chars=2000,
        ideal_chars=(100, 300),
        hashtag_range=(2, 3),
        hashtag_prefix="#",
        title_style="一句话观点，含话题标签，引发讨论",
        content_features=["话题标签", "热点结合", "传播性强", "反问互动", "短平快"],
        optimal_times=["07:00-09:00", "12:00-13:00", "17:00-19:00", "21:00-23:00"],
        priority=6
    )
}

# 内容类型关键词映射
CONTENT_TYPE_KEYWORDS = {
    "科普": ["科普", "原理", "机制", "为什么", "如何", "解释", "介绍", "了解", "认识"],
    "观点": ["认为", "观点", "看法", "思考", "反思", "趋势", "未来", "预测", "判断"],
    "教程": ["教程", "步骤", "方法", "指南", "实操", "技巧", "入门", "学会", "掌握"],
    "评测": ["评测", "对比", "测评", "体验", "优缺点", "推荐", "排名", "排行", "选择"],
    "故事": ["故事", "经历", "案例", "历程", "成长", "转变", "揭秘", "背后", "内幕"]
}

# 语气风格关键词
TONE_KEYWORDS = {
    "专业": ["数据", "研究", "报告", "分析", "统计", "指标", "模型", "框架", "方法论"],
    "轻松": ["哈哈", "嗯", "呗", "呢", "呀", "哇", "绝了", "真的", "太"],
    "正式": ["综上所述", "鉴于此", "值得注意的是", "研究表明", "数据显示", "由此可见"],
    "通俗": ["简单来说", "就是说", "相当于", "你可以理解为", "打个比方", "通俗讲"]
}


# ============================================================
# 内容分析引擎
# ============================================================

class ContentAnalyzer:
    """内容分析器：解析输入内容并生成画像"""

    def __init__(self, text: str):
        self.text = text.strip()
        self.paragraphs = [p.strip() for p in self.text.split("\n") if p.strip()]
        self.sentences = re.split(r'[。！？\n]', self.text)
        self.sentences = [s.strip() for s in self.sentences if s.strip()]

    def analyze(self) -> ContentProfile:
        """执行完整分析"""
        profile = ContentProfile(
            raw_text=self.text,
            total_chars=len(self.text),
            total_paragraphs=len(self.paragraphs),
            content_type="观点",
            tone="专业",
            has_data=False,
            has_images_reference=False
        )

        # 检测内容类型
        type_scores = {}
        for ctype, keywords in CONTENT_TYPE_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in self.text)
            type_scores[ctype] = score
        profile.content_type = max(type_scores, key=type_scores.get)

        # 检测语气风格
        tone_scores = {}
        for tone, keywords in TONE_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in self.text)
            tone_scores[tone] = score
        profile.tone = max(tone_scores, key=tone_scores.get)

        # 检测数据元素
        data_patterns = [
            r'\d+\.?\d*%', r'\d+亿', r'\d+万', r'\d+年',
            r'增长\d+', r'下降\d+', r'据统计', r'数据显示',
            r'\d+/\d+', r'\d+:\d+'
        ]
        profile.has_data = any(
            re.search(pattern, self.text) for pattern in data_patterns
        )

        # 检测图片引用
        image_patterns = [r'图\d', r'图片', r'配图', r'截图', r'示意图']
        profile.has_images_reference = any(
            re.search(pattern, self.text) for pattern in image_patterns
        )

        # 提取关键信息点
        profile.key_points = self._extract_key_points()
        profile.core_theme = self._extract_core_theme()
        profile.adaptation_score = self._calculate_adaptation_score(profile)

        return profile

    def _extract_key_points(self) -> list:
        """提取核心信息点"""
        key_points = []

        # 策略1：提取含序号的要点
        numbered = re.findall(r'(?:\d+[.、)）]|[一二三四五][.、)）])\s*(.{10,60})', self.text)
        if numbered:
            key_points.extend([p.strip() for p in numbered[:7]])

        # 策略2：提取段落首句作为要点
        if len(key_points) < 3:
            for para in self.paragraphs[:10]:
                first_sentence = re.split(r'[。！？]', para)[0].strip()
                if 10 < len(first_sentence) < 60 and first_sentence not in key_points:
                    key_points.append(first_sentence)

        # 策略3：提取含关键词的句子
        emphasis_patterns = [r'核心.*?是(.{5,30})', r'关键.*?在(.{5,30})', r'重点.*?是(.{5,30})']
        for pattern in emphasis_patterns:
            matches = re.findall(pattern, self.text)
            for m in matches[:2]:
                if m.strip() not in key_points:
                    key_points.append(m.strip())

        return key_points[:7] if key_points else [self.sentences[0][:50] if self.sentences else "内容主旨待确认"]

    def _extract_core_theme(self) -> str:
        """提取核心主题"""
        if not self.paragraphs:
            return "无法识别主题"

        # 使用第一段或含「主题」「关于」的句子
        first_para = self.paragraphs[0]
        theme_match = re.search(r'(?:关于|主题|探讨|讨论)(.{5,25})', first_para)
        if theme_match:
            return theme_match.group(1).strip()

        # 使用高频关键词构建主题
        all_text = " ".join(self.paragraphs[:5])
        words = re.findall(r'[\u4e00-\u9fff]{2,4}', all_text)
        word_freq = Counter(words)
        # 过滤停用词
        stopwords = {"这个", "那个", "我们", "他们", "可以", "已经", "因为", "所以", "但是", "然而",
                      "如果", "虽然", "以及", "对于", "通过", "进行", "目前", "同时", "不同", "一个"}
        top_words = [(w, c) for w, c in word_freq.most_common(10) if w not in stopwords]
        if top_words:
            theme = "、".join([w for w, _ in top_words[:3]])
            return theme[:30]

        return first_para[:30] if len(first_para) > 5 else "待确认主题"

    def _calculate_adaptation_score(self, profile: ContentProfile) -> int:
        """计算内容适配性评分（0-100）"""
        score = 50  # 基础分

        # 内容长度加分（适中最好）
        if 500 <= profile.total_chars <= 5000:
            score += 15
        elif 200 <= profile.total_chars:
            score += 10

        # 段落结构加分
        if profile.total_paragraphs >= 3:
            score += 10

        # 信息点丰富度加分
        if len(profile.key_points) >= 3:
            score += 10
        elif len(profile.key_points) >= 1:
            score += 5

        # 数据支撑加分
        if profile.has_data:
            score += 8

        # 图片引用加分
        if profile.has_images_reference:
            score += 7

        return min(score, 100)


# ============================================================
# 适配计算引擎
# ============================================================

class AdaptationEngine:
    """平台适配计算引擎"""

    def __init__(self, profile: ContentProfile):
        self.profile = profile

    def calculate_all(self) -> list:
        """计算所有平台的适配参数"""
        results = []
        for platform_id, spec in PLATFORMS.items():
            params = self._calculate_platform(platform_id, spec)
            results.append(params)
        return results

    def _calculate_platform(self, platform_id: str, spec: PlatformSpec) -> AdaptationParams:
        """计算单个平台的适配参数"""
        raw_chars = self.profile.total_chars
        ideal_min, ideal_max = spec.ideal_chars
        target_chars = min(max(raw_chars, ideal_min), ideal_max)

        # 计算压缩比
        if raw_chars > 0:
            compression_ratio = target_chars / raw_chars
        else:
            compression_ratio = 1.0

        # 确定结构类型
        structure_type = self._determine_structure(platform_id, compression_ratio)

        # 计算标签数量
        tag_min, tag_max = spec.hashtag_range
        hashtag_count = (tag_min + tag_max) // 2 if tag_max > 0 else 0

        # 生成建议标签
        suggested_hashtags = self._generate_hashtags(platform_id, spec)

        # 生成标题候选
        title_candidates = self._generate_titles(platform_id, spec)

        # 估算互动效果
        estimated_engagement = self._estimate_engagement(platform_id, spec)

        # 生成备注
        notes = self._generate_notes(platform_id, spec, compression_ratio)

        return AdaptationParams(
            platform=spec.name_cn,
            target_chars=target_chars,
            current_chars=raw_chars,
            compression_ratio=round(compression_ratio, 2),
            structure_type=structure_type,
            hashtag_count=hashtag_count,
            suggested_hashtags=suggested_hashtags,
            title_candidates=title_candidates,
            estimated_engagement=estimated_engagement,
            priority=spec.priority,
            notes=notes
        )

    def _determine_structure(self, platform_id: str, ratio: float) -> str:
        """确定内容结构类型"""
        structures = {
            "wechat": "引言-分论点展开-数据支撑-总结升华",
            "xiaohongshu": "钩子标题-要点列表-总结+互动引导",
            "douyin": "3秒钩子-核心观点展开-反转/惊喜-行动号召",
            "bilibili": "开场互动-知识点1-N-总结+互动引导（可分P）",
            "zhihu": "背景引入-问题分析-论据展开-结论建议",
            "weibo": "一句话观点+话题标签+互动反问"
        }
        base = structures.get(platform_id, "总分总")

        if ratio < 0.3:
            return f"高度精简版：{base}（需大幅压缩，仅保留核心观点）"
        elif ratio < 0.6:
            return f"精简版：{base}（需压缩次要内容，保留核心论据）"
        elif ratio > 1.2:
            return f"扩展版：{base}（需补充细节和案例以达到理想字数）"
        else:
            return f"标准版：{base}"

    def _generate_hashtags(self, platform_id: str, spec: PlatformSpec) -> list:
        """生成建议标签"""
        theme = self.profile.core_theme
        ctype = self.profile.content_type
        prefix = spec.hashtag_prefix

        # 从核心主题提取关键词
        keywords = re.findall(r'[\u4e00-\u9fff]{2,4}', theme)

        # 通用标签
        generic_tags = {
            "xiaohongshu": ["干货分享", "涨知识", "收藏备用", "自我提升"],
            "douyin": ["涨知识", "科普", "干货", "AI", "科技"],
            "bilibili": ["知识分享", "科技", "科普", "硬核", "深度解析"],
            "zhihu": [],
            "weibo": ["科技", "AI", "未来趋势"]
        }

        platform_tags = generic_tags.get(platform_id, [])
        all_tags = list(set(keywords + platform_tags))[:spec.hashtag_range[1]]

        if prefix:
            all_tags = [f"{prefix}{t}" for t in all_tags]

        return all_tags

    def _generate_titles(self, platform_id: str, spec: PlatformSpec) -> list:
        """生成标题候选"""
        theme = self.profile.core_theme
        ctype = self.profile.content_type
        candidates = []

        if platform_id == "wechat":
            candidates = [
                f"深度解读：{theme}，你了解多少？",
                f"一文讲透{theme}：核心要点与趋势分析",
                f"{theme}：从现状到未来的全景式解读"
            ]
        elif platform_id == "xiaohongshu":
            candidates = [
                f"🔥{ctype}干货｜{theme}精华版",
                f"建议收藏！{theme}必看指南✨",
                f"{theme}｜看完这篇就够了📝"
            ]
        elif platform_id == "douyin":
            candidates = [
                f"你知道{theme}吗？3分钟讲明白",
                f"{theme}，远比你想象的更震撼",
                f"这个{ctype}你知道吗？#干货"
            ]
        elif platform_id == "bilibili":
            candidates = [
                f"【{ctype}】{theme}（完整版）",
                f"{theme}：硬核解析来了！",
                f"深入浅出聊{theme}｜看完你就懂了"
            ]
        elif platform_id == "zhihu":
            candidates = [
                f"如何看待{theme}？",
                f"{theme}的核心逻辑是什么？",
                f"全面分析：{theme}的现状与未来"
            ]
        elif platform_id == "weibo":
            candidates = [
                f"{theme}，你怎么看？",
                f"聊一聊{theme} #科技#",
                f"关于{theme}，有几个关键点值得关注"
            ]

        return candidates[:3]

    def _estimate_engagement(self, platform_id: str, spec: PlatformSpec) -> str:
        """估算预期互动效果"""
        base_rates = {
            "wechat": {"read": "中高", "share": "中等", "like": "中等"},
            "xiaohongshu": {"save": "高", "like": "高", "comment": "中等"},
            "douyin": {"play": "高", "like": "中高", "share": "中高"},
            "bilibili": {"play": "中高", "coin": "中高", "favorite": "高"},
            "zhihu": {"read": "中高", "upvote": "中高", "collect": "高"},
            "weibo": {"read": "高", "repost": "高", "comment": "中等"}
        }
        rates = base_rates.get(platform_id, {})
        return "、".join([f"{k}({v})" for k, v in rates.items()])

    def _generate_notes(self, platform_id: str, spec: PlatformSpec,
                        ratio: float) -> list:
        """生成适配注意事项"""
        notes = []
        notes.append(f"目标字数范围：{spec.ideal_chars[0]}-{spec.ideal_chars[1]}字")
        notes.append(f"当前内容需要{'压缩' if ratio < 1 else '扩展'}至目标长度")

        if platform_id == "xiaohongshu":
            notes.append("建议使用3-5张高质量配图，首图为封面图")
            notes.append("正文适当使用Emoji分隔段落，增强视觉效果")
        elif platform_id == "douyin":
            notes.append("前3秒必须有强钩子，否则用户会划走")
            notes.append("脚本配合节奏明快的BGM，语速控制在200字/分钟以上")
        elif platform_id == "bilibili":
            notes.append("在知识点之间设置弹幕互动点（如提问、悬念）")
            notes.append("建议规划2-3个分P，每P时长8-15分钟")
        elif platform_id == "zhihu":
            notes.append("引用数据需标注来源，增强可信度")
            notes.append("回答开头可用「谢邀」或直接切入问题")
        elif platform_id == "wechat":
            notes.append("使用小标题分段，每段不超过200字")
            notes.append("文末添加公众号引导语，促进关注转化")

        if self.profile.has_data:
            notes.append("原文含数据元素，适配时请保留关键数据")
        if self.profile.has_images_reference:
            notes.append("原文含图片引用，适配时需根据平台要求调整图片尺寸和数量")

        return notes


# ============================================================
# 报告生成器
# ============================================================

class ReportGenerator:
    """适配报告生成器"""

    def __init__(self, profile: ContentProfile, adaptations: list):
        self.profile = profile
        self.adaptations = adaptations

    def generate(self) -> str:
        """生成完整适配报告"""
        lines = []
        lines.append("=" * 60)
        lines.append("  多渠道内容分发 - 适配参数报告")
        lines.append("=" * 60)
        lines.append("")

        # 内容画像
        lines.append("【内容画像】")
        lines.append(f"  核心主题：{self.profile.core_theme}")
        lines.append(f"  内容类型：{self.profile.content_type}")
        lines.append(f"  语气风格：{self.profile.tone}")
        lines.append(f"  原文字数：{self.profile.total_chars}字")
        lines.append(f"  段落数量：{self.profile.total_paragraphs}段")
        lines.append(f"  包含数据：{'是' if self.profile.has_data else '否'}")
        lines.append(f"  包含图片引用：{'是' if self.profile.has_images_reference else '否'}")
        lines.append(f"  适配评分：{self.profile.adaptation_score}/100")
        lines.append("")

        # 关键信息点
        lines.append("【核心信息点】")
        for i, point in enumerate(self.profile.key_points, 1):
            lines.append(f"  {i}. {point}")
        lines.append("")

        # 各平台适配参数
        lines.append("【平台适配参数】")
        lines.append("")

        # 按优先级排序
        sorted_adaptations = sorted(self.adaptations, key=lambda x: x.priority)

        for adap in sorted_adaptations:
            lines.append(f"--- {adap.platform}（优先级 P{adap.priority}）---")
            lines.append(f"  当前字数：{adap.current_chars}字")
            lines.append(f"  目标字数：{adap.target_chars}字")
            lines.append(f"  压缩比：{adap.compression_ratio}")
            lines.append(f"  内容结构：{adap.structure_type}")
            lines.append(f"  标签数量：{adap.hashtag_count}个")
            if adap.suggested_hashtags:
                lines.append(f"  建议标签：{' '.join(adap.suggested_hashtags)}")
            lines.append(f"  备选标题：")
            for i, title in enumerate(adap.title_candidates, 1):
                lines.append(f"    {i}. {title}")
            lines.append(f"  预期互动：{adap.estimated_engagement}")
            lines.append(f"  适配备注：")
            for note in adap.notes:
                lines.append(f"    - {note}")
            lines.append("")

        # 适配评分摘要
        lines.append("【适配评分摘要】")
        lines.append(f"  {'平台':<12} {'目标字数':<10} {'压缩比':<8} {'优先级':<6} {'预期互动'}")
        lines.append(f"  {'-'*12} {'-'*10} {'-'*8} {'-'*6} {'-'*20}")
        for adap in sorted_adaptations:
            lines.append(
                f"  {adap.platform:<12} {adap.target_chars:<10} "
                f"{adap.compression_ratio:<8} P{adap.priority:<5} {adap.estimated_engagement}"
            )
        lines.append("")

        # 适配建议
        lines.append("【适配建议】")
        if self.profile.adaptation_score >= 70:
            lines.append("  ✅ 内容适配性良好，可直接进行多平台分发")
        elif self.profile.adaptation_score >= 40:
            lines.append("  ⚠️ 内容适配性一般，建议补充数据和细节后分发")
        else:
            lines.append("  ❌ 内容适配性较低，建议调整素材后再进行分发")
        lines.append("")
        lines.append("  推荐发布顺序：")
        for i, adap in enumerate(sorted_adaptations, 1):
            spec = PLATFORMS[[k for k, v in PLATFORMS.items() if v.name_cn == adap.platform][0]]
            times = "、".join(spec.optimal_times[:2])
            lines.append(f"  第{i}步：{adap.platform}（建议时间：{times}）")

        lines.append("")
        lines.append("=" * 60)
        lines.append("  报告生成完毕")
        lines.append("=" * 60)

        return "\n".join(lines)


# ============================================================
# 主入口
# ============================================================

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python scripts/content-adapter.py <input_file>")
        print("      python scripts/content-adapter.py <input_file> --json")
        sys.exit(1)

    input_file = sys.argv[1]
    output_json = "--json" in sys.argv

    if not os.path.exists(input_file):
        print(f"错误：文件不存在 - {input_file}")
        sys.exit(1)

    with open(input_file, "r", encoding="utf-8") as f:
        text = f.read()

    if not text.strip():
        print("错误：文件内容为空")
        sys.exit(1)

    # 执行分析
    analyzer = ContentAnalyzer(text)
    profile = analyzer.analyze()

    # 计算适配参数
    engine = AdaptationEngine(profile)
    adaptations = engine.calculate_all()

    # 生成报告
    generator = ReportGenerator(profile, adaptations)

    if output_json:
        report_data = {
            "content_profile": {
                "core_theme": profile.core_theme,
                "content_type": profile.content_type,
                "tone": profile.tone,
                "total_chars": profile.total_chars,
                "total_paragraphs": profile.total_paragraphs,
                "has_data": profile.has_data,
                "has_images_reference": profile.has_images_reference,
                "key_points": profile.key_points,
                "adaptation_score": profile.adaptation_score
            },
            "adaptations": [
                {
                    "platform": a.platform,
                    "target_chars": a.target_chars,
                    "current_chars": a.current_chars,
                    "compression_ratio": a.compression_ratio,
                    "structure_type": a.structure_type,
                    "hashtag_count": a.hashtag_count,
                    "suggested_hashtags": a.suggested_hashtags,
                    "title_candidates": a.title_candidates,
                    "estimated_engagement": a.estimated_engagement,
                    "priority": a.priority,
                    "notes": a.notes
                }
                for a in sorted(adaptations, key=lambda x: x.priority)
            ]
        }
        print(json.dumps(report_data, ensure_ascii=False, indent=2))
    else:
        print(generator.generate())


if __name__ == "__main__":
    main()
