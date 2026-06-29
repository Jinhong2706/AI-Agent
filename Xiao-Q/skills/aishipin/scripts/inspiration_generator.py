#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI视频创作师 - 灵感裂变脚本
功能：将模糊灵感裂变为多个具体故事方向
支持：场景分析、情绪匹配、爆款指数计算

【命令行使用】
python scripts/inspiration_generator.py --idea "咖啡店的故事" --platform "抖音" --duration "30秒"
python scripts/inspiration_generator.py --idea "职场逆袭" --mood "燃" --count 5

【代码中使用】
from scripts.inspiration_generator import InspirationGenerator, StoryDirection

generator = InspirationGenerator()
directions = generator.generate_directions(
    idea="咖啡店的故事",
    mood="温馨",
    platform="抖音",
    duration=30
)
for direction in directions:
    print(direction.name, direction.viral_index)
"""

import random
import argparse
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from enum import Enum


class Mood(Enum):
    """情绪基调"""
    WARM = "温馨"
    MYSTERIOUS = "悬疑"
    FUNNY = "搞笑"
    HEALING = "治愈"
    HEARTBREAKING = "虐心"
    PASSIONATE = "燃"
    ROMANTIC = "浪漫"
    ANXIOUS = "焦虑"


class Platform(Enum):
    """目标平台"""
    DOUYIN = "抖音"
    XIAOHONGSHU = "小红书"
    BILIBILI = "B站"
    VIDEO_ACCOUNT = "视频号"
    ALL = "全平台"
    KUAISHOU = "快手"


class Duration(Enum):
    """时长偏好"""
    SHORT = "15秒"
    MEDIUM = "30秒"
    LONG = "1分钟"
    EXTRA_LONG = "3分钟"


@dataclass
class EmotionCurve:
    """情绪曲线"""
    stages: List[Dict[str, str]] = field(default_factory=list)
    
    def __str__(self):
        return " → ".join([f"{s['name']}({s['time']})" for s in self.stages])


@dataclass
class StoryDirection:
    """故事方向"""
    id: int
    name: str
    summary: str
    mood: str
    emotion_curve: EmotionCurve
    target_audience: str
    viral_index: int  # 1-5星
    viral_reasons: List[str]
    risks: List[str]
    recommendation: int  # 1-5星
    recommendation_for: str
    
    def to_markdown(self) -> str:
        """转换为Markdown格式"""
        viral_stars = "⭐" * self.viral_index
        rec_stars = "⭐" * self.recommendation
        
        curve_str = " → ".join([f"{s['name']}({s['time']})" for s in self.emotion_curve.stages])
        
        return f"""### 方向{self.id}：【{self.name}】{viral_stars}

**一句话梗概**：{self.summary}

**情绪曲线**：
{curve_str}

**目标受众**：{self.target_audience}

**爆款指数**：{viral_stars}
- 理由：{"；".join(self.viral_reasons)}
- 风险：{"；".join(self.risks)}

**推荐指数**：{rec_stars}（{self.recommendation_for}）
"""


class InspirationGenerator:
    """灵感裂变生成器"""
    
    # 故事类型模板库
    STORY_TEMPLATES = {
        "反转剧": {
            "structure": "铺垫→期待→反转→金句",
            "duration_range": [15, 30],
            "viral_potential": 5,
            "platforms": ["抖音", "快手"]
        },
        "共情剧": {
            "structure": "场景→情绪→金句→互动",
            "duration_range": [30, 60],
            "viral_potential": 4,
            "platforms": ["视频号", "小红书"]
        },
        "知识剧": {
            "structure": "提问→解答→案例→总结",
            "duration_range": [60, 180],
            "viral_potential": 4,
            "platforms": ["B站", "抖音"]
        },
        "种草剧": {
            "structure": "痛点→产品→效果→行动",
            "duration_range": [30, 60],
            "viral_potential": 4,
            "platforms": ["小红书", "抖音"]
        },
        "搞笑剧": {
            "structure": "铺垫→夸张→反转→意外",
            "duration_range": [15, 30],
            "viral_potential": 5,
            "platforms": ["抖音", "快手"]
        },
        "治愈剧": {
            "structure": "困境→温暖→治愈→希望",
            "duration_range": [30, 60],
            "viral_potential": 4,
            "platforms": ["小红书", "视频号"]
        }
    }
    
    # 场景元素库
    SCENE_ELEMENTS = {
        "咖啡店": ["窗边位置", "咖啡香气", "雨天", "阳光午后", "独自一人", "热闹人群"],
        "办公室": ["加班夜", "会议室", "打印机", "茶水间", "升职", "辞职"],
        "地铁": ["早高峰", "末班车", "错过", "相遇", "陌生人", "耳机"],
        "校园": ["图书馆", "操场", "食堂", "毕业", "暗恋", "友情"],
        "家里": ["深夜厨房", "阳台", "宠物陪伴", "独处", "家人来电"],
        "街头": ["雨天奔跑", "迷路", "街头艺人", "橱窗", "路灯"]
    }
    
    # 情绪曲线模板
    EMOTION_CURVES = {
        "温馨": [
            {"name": "好奇", "time": "0-3s"},
            {"name": "温暖", "time": "3-8s"},
            {"name": "感动", "time": "8-12s"},
            {"name": "甜蜜", "time": "12-15s"}
        ],
        "悬疑": [
            {"name": "平静", "time": "0-3s"},
            {"name": "紧张", "time": "3-8s"},
            {"name": "恐惧", "time": "8-12s"},
            {"name": "揭秘", "time": "12-15s"}
        ],
        "搞笑": [
            {"name": "正常", "time": "0-3s"},
            {"name": "尴尬", "time": "3-7s"},
            {"name": "爆笑", "time": "7-12s"},
            {"name": "反转", "time": "12-15s"}
        ],
        "治愈": [
            {"name": "孤独", "time": "0-3s"},
            {"name": "陪伴", "time": "3-8s"},
            {"name": "温暖", "time": "8-12s"},
            {"name": "治愈", "time": "12-15s"}
        ],
        "燃": [
            {"name": "低谷", "time": "0-3s"},
            {"name": "觉醒", "time": "3-8s"},
            {"name": "爆发", "time": "8-12s"},
            {"name": "高光", "time": "12-15s"}
        ]
    }
    
    def __init__(self):
        self.target_audiences = {
            "18-25岁女性": ["情感", "穿搭", "美妆", "生活"],
            "25-35岁职场人": ["职场", "成长", "效率", "理财"],
            "大学生": ["校园", "考研", "求职", "情感"],
            "新手妈妈": ["育儿", "家居", "美食", "自我成长"],
            "银发族": ["健康", "回忆", "家庭", "兴趣"]
        }
    
    def analyze_idea(self, idea: str) -> Dict:
        """分析输入灵感的核心元素"""
        keywords = {
            "咖啡": "咖啡店",
            "上班": "办公室", 
            "职场": "办公室",
            "地铁": "地铁",
            "校园": "校园",
            "毕业": "校园",
            "家": "家里",
            "街头": "街头",
            "城市": "街头"
        }
        
        scene = "街头"  # 默认场景
        for key, value in keywords.items():
            if key in idea:
                scene = value
                break
        
        elements = random.sample(self.SCENE_ELEMENTS.get(scene, ["日常"]), 2)
        
        return {
            "scene": scene,
            "elements": elements,
            "raw_idea": idea
        }
    
    def generate_directions(
        self, 
        idea: str, 
        mood: Optional[str] = None,
        platform: Optional[str] = None,
        duration: int = 30,
        count: int = 3
    ) -> List[StoryDirection]:
        """生成故事方向"""
        analysis = self.analyze_idea(idea)
        scene = analysis["scene"]
        
        # 根据时长筛选合适的模板
        available_templates = [
            name for name, template in self.STORY_TEMPLATES.items()
            if template["duration_range"][0] <= duration <= template["duration_range"][1]
        ]
        
        if not available_templates:
            available_templates = list(self.STORY_TEMPLATES.keys())
        
        # 生成指定数量的方向
        directions = []
        used_templates = set()
        
        for i in range(min(count, len(available_templates))):
            template_name = available_templates[i % len(available_templates)]
            if template_name in used_templates and len(available_templates) > 1:
                # 换一个模板
                alternatives = [t for t in available_templates if t not in used_templates]
                if alternatives:
                    template_name = random.choice(alternatives)
            
            used_templates.add(template_name)
            template = self.STORY_TEMPLATES[template_name]
            
            # 生成情绪曲线
            target_mood = mood or self._get_mood_for_template(template_name)
            emotion_curve = EmotionCurve(
                stages=self.EMOTION_CURVES.get(target_mood, self.EMOTION_CURVES["温馨"])
            )
            
            # 生成目标受众
            audience = random.choice(list(self.target_audiences.keys()))
            
            # 计算爆款指数
            viral_index = template["viral_potential"]
            if platform and platform in template["platforms"]:
                viral_index = min(5, viral_index + 1)
            
            # 生成方向
            direction = StoryDirection(
                id=i + 1,
                name=f"{scene}{template_name}",
                summary=self._generate_summary(scene, template_name, analysis["elements"]),
                mood=target_mood,
                emotion_curve=emotion_curve,
                target_audience=audience,
                viral_index=viral_index,
                viral_reasons=self._generate_viral_reasons(template_name, scene),
                risks=self._generate_risks(template_name),
                recommendation=random.randint(3, 5),
                recommendation_for=self._get_recommendation_for(template_name)
            )
            
            directions.append(direction)
        
        return directions
    
    def _get_mood_for_template(self, template_name: str) -> str:
        """获取模板对应的情绪"""
        mapping = {
            "反转剧": "搞笑",
            "共情剧": "治愈",
            "知识剧": "燃",
            "种草剧": "温馨",
            "搞笑剧": "搞笑",
            "治愈剧": "治愈"
        }
        return mapping.get(template_name, "温馨")
    
    def _generate_summary(self, scene: str, template: str, elements: List[str]) -> str:
        """生成故事梗概"""
        summaries = {
            "反转剧": f"在{scene}，看似平常的一天，却因为{elements[0]}发生了意想不到的反转...",
            "共情剧": f"{scene}里每个人都有故事，{elements[0]}让我想起了自己的{elements[1]}...",
            "知识剧": f"{scene}里藏着{elements[0]}的秘密，学会了你也能...",
            "种草剧": f"{elements[0]}改变了我在{scene}的体验，真的绝了！",
            "搞笑剧": f"{scene}里{elements[0]}引发的社死现场，笑到我肚子疼...",
            "治愈剧": f"在{scene}的{elements[0]}时刻，我被陌生人治愈了..."
        }
        return summaries.get(template, f"{scene}里发生了{elements[0]}...")
    
    def _generate_viral_reasons(self, template: str, scene: str) -> List[str]:
        """生成爆款理由"""
        base_reasons = [
            f"{scene}场景容易引发共鸣",
            "情绪起伏大，完播率高",
            "反转设计巧妙，易引发讨论"
        ]
        
        template_reasons = {
            "反转剧": ["反转出乎意料", "容易二创", "转发率高"],
            "共情剧": ["情感共鸣强", "评论互动高", "容易收藏"],
            "知识剧": ["实用价值高", "收藏率高", "转发学习"],
            "种草剧": ["种草属性强", "转化率高", "容易跟风"],
            "搞笑剧": ["传播性强", "娱乐性强", "易模仿"],
            "治愈剧": ["温暖治愈", "评论感人", "易传播正能量"]
        }
        
        return base_reasons + template_reasons.get(template, [])[:2]
    
    def _generate_risks(self, template: str) -> List[str]:
        """生成风险提示"""
        base_risks = [
            "开头3秒没有强钩子可能流失观众",
            "情绪铺垫太长会降低完播率"
        ]
        
        template_risks = {
            "反转剧": ["反转太刻意会显得尴尬", "观众可能猜到结局"],
            "共情剧": ["情绪过于沉重可能压抑", "需要真情实感"],
            "知识剧": ["内容不够硬核会被吐槽", "节奏把控难"],
            "种草剧": ["广告感太强会被反感", "需要真实体验"],
            "搞笑剧": ["笑点可能因人而异", "容易被复制"],
            "治愈剧": ["煽情过度会显得做作", "需要细节支撑"]
        }
        
        return base_risks + template_risks.get(template, [])[:1]
    
    def _get_recommendation_for(self, template: str) -> str:
        """获取推荐人群"""
        mapping = {
            "反转剧": "适合新手/博主",
            "共情剧": "适合专业创作者",
            "知识剧": "适合知识博主",
            "种草剧": "适合电商博主",
            "搞笑剧": "适合新手/全类型",
            "治愈剧": "适合情感博主"
        }
        return mapping.get(template, "适合新手")
    
    def to_markdown(self, directions: List[StoryDirection], raw_idea: str) -> str:
        """生成Markdown报告"""
        output = ["## 灵感裂变结果\n"]
        output.append(f"**原始灵感**：{raw_idea}\n")
        output.append(f"**生成方向数**：{len(directions)}\n")
        output.append("---\n")
        
        for direction in directions:
            output.append(direction.to_markdown())
            output.append("---\n")
        
        return "\n".join(output)


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(description="AI视频创作师 - 灵感裂变脚本")
    parser.add_argument("--idea", "-i", required=True, help="你的创作灵感")
    parser.add_argument("--mood", "-m", default=None, help="情绪基调：温馨/悬疑/搞笑/治愈/虐心/燃")
    parser.add_argument("--platform", "-p", default=None, help="目标平台：抖音/小红书/B站/视频号/全平台")
    parser.add_argument("--duration", "-d", type=int, default=30, help="时长偏好（秒）")
    parser.add_argument("--count", "-c", type=int, default=3, help="生成方向数量")
    parser.add_argument("--output", "-o", default=None, help="输出文件路径")
    
    args = parser.parse_args()
    
    # 生成灵感裂变
    generator = InspirationGenerator()
    directions = generator.generate_directions(
        idea=args.idea,
        mood=args.mood,
        platform=args.platform,
        duration=args.duration,
        count=args.count
    )
    
    # 生成报告
    report = generator.to_markdown(directions, args.idea)
    
    # 输出
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"报告已保存到：{args.output}")
    else:
        print(report)


if __name__ == "__main__":
    main()
