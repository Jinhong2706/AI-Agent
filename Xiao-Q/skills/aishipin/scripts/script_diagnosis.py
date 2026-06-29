#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI视频创作师 - 剧本诊断脚本
功能：诊断已有剧本问题，提供修复方案

【命令行使用】
python scripts/script_diagnosis.py --file "script.md"
python scripts/script_diagnosis.py --content "第1镜：开场，咖啡店环境..."

【代码中使用】
from scripts.script_diagnosis import ScriptDiagnosis, DiagnosisReport

diagnoser = ScriptDiagnosis()
report = diagnoser.diagnose(script_content)
print(report.to_markdown())
"""

import argparse
import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class DimensionScore:
    """维度评分"""
    name: str
    score: int
    max_score: int = 100
    grade: str = ""
    
    def __post_init__(self):
        percentage = (self.score / self.max_score) * 100
        if percentage >= 90:
            self.grade = "A+"
        elif percentage >= 80:
            self.grade = "A"
        elif percentage >= 75:
            self.grade = "A-"
        elif percentage >= 70:
            self.grade = "B+"
        elif percentage >= 60:
            self.grade = "B"
        elif percentage >= 55:
            self.grade = "B-"
        elif percentage >= 50:
            self.grade = "C+"
        elif percentage >= 40:
            self.grade = "C"
        elif percentage >= 30:
            self.grade = "D"
        else:
            self.grade = "F"


@dataclass
class Issue:
    """问题项"""
    severity: str  # "高" / "中" / "低"
    location: str
    problem: str
    current: str
    suggestion: str
    priority: int  # 1-3, 1最高


@dataclass
class GoodPractice:
    """做得好的地方"""
    aspect: str
    description: str


@dataclass
class DiagnosisReport:
    """诊断报告"""
    structure_score: DimensionScore
    emotion_score: DimensionScore
    shot_score: DimensionScore
    dialogue_score: DimensionScore
    sound_score: DimensionScore
    platform_score: DimensionScore
    must_fix: List[Issue] = field(default_factory=list)
    suggestions: List[Issue] = field(default_factory=list)
    good_practices: List[GoodPractice] = field(default_factory=list)
    
    def get_total_score(self) -> int:
        """计算总分"""
        scores = [
            self.structure_score.score,
            self.emotion_score.score,
            self.shot_score.score,
            self.dialogue_score.score,
            self.sound_score.score,
            self.platform_score.score
        ]
        return sum(scores) // len(scores)
    
    def get_overall_grade(self) -> str:
        """获取综合等级"""
        total = self.get_total_score()
        if total >= 90:
            return "A+"
        elif total >= 80:
            return "A"
        elif total >= 70:
            return "B+"
        elif total >= 60:
            return "B"
        elif total >= 50:
            return "C"
        else:
            return "D"
    
    def to_markdown(self) -> str:
        """转换为Markdown格式"""
        output = ["## 📋 剧本诊断报告\n"]
        
        # 评分总览
        output.append("### 📊 评分总览")
        output.append("| 维度 | 得分 | 等级 |")
        output.append("|------|------|------|")
        output.append(f"| 结构 | {self.structure_score.score}/100 | {self.structure_score.grade} |")
        output.append(f"| 情绪 | {self.emotion_score.score}/100 | {self.emotion_score.grade} |")
        output.append(f"| 镜头 | {self.shot_score.score}/100 | {self.shot_score.grade} |")
        output.append(f"| 台词 | {self.dialogue_score.score}/100 | {self.dialogue_score.grade} |")
        output.append(f"| 音效 | {self.sound_score.score}/100 | {self.sound_score.grade} |")
        output.append(f"| **综合** | **{self.get_total_score()}/100** | **{self.get_overall_grade()}** |")
        output.append("")
        
        # 必须修复的问题
        if self.must_fix:
            output.append("### ❌ 必须修复")
            for i, issue in enumerate(self.must_fix, 1):
                severity_icon = "🔴" if issue.severity == "高" else "🟡"
                output.append(f"#### 问题{i}：{issue.location}")
                output.append(f"**严重程度**：{severity_icon} {issue.severity}")
                output.append(f"**问题**：{issue.problem}")
                output.append(f"**现状**：{issue.current}")
                output.append(f"**修复建议**：{issue.suggestion}")
                output.append("")
        
        # 建议优化
        if self.suggestions:
            output.append("### ⚠️ 建议优化")
            for i, suggestion in enumerate(self.suggestions, 1):
                output.append(f"#### 建议{i}：{suggestion.location}")
                output.append(f"**现状**：{suggestion.current}")
                output.append(f"**建议**：{suggestion.suggestion}")
                output.append("")
        
        # 做得好的地方
        if self.good_practices:
            output.append("### ✅ 做得好的地方")
            for practice in self.good_practices:
                output.append(f"1. **{practice.aspect}**：{practice.description}")
            output.append("")
        
        return "\n".join(output)


class ScriptDiagnosis:
    """剧本诊断器"""
    
    # 诊断规则配置
    STRUCTURE_RULES = {
        "opening_hook": {
            "check": "开头3秒是否有钩子",
            "good": "有强吸引力的开头",
            "bad": "平淡开场，无信息量"
        },
        "conflict_middle": {
            "check": "中段是否有冲突/转折",
            "good": "有明显的冲突或转折",
            "bad": "平铺直叙，缺乏张力"
        },
        "ending": {
            "check": "结尾是否完整或有反转",
            "good": "有反转或点睛之笔",
            "bad": "结尾仓促或烂尾"
        }
    }
    
    EMOTION_RULES = {
        "curve": {
            "check": "情绪曲线是否起伏",
            "good": "有明显的情绪起伏",
            "bad": "情绪平淡，缺乏变化"
        },
        "climax": {
            "check": "高潮是否在合适位置",
            "good": "高潮在视频的2/3处左右",
            "bad": "高潮太早或太晚"
        },
        "target_emotion": {
            "check": "目标情绪是否明确",
            "good": "有清晰的情感定位",
            "bad": "情绪混乱，不统一"
        }
    }
    
    SHOT_RULES = {
        "variety": {
            "check": "景别是否有变化",
            "good": "景别丰富，有特写/中景/远景",
            "bad": "景别单一，缺乏变化"
        },
        "rhythm": {
            "check": "镜头节奏是否合理",
            "good": "节奏有张有弛",
            "bad": "节奏单调或混乱"
        },
        "duration": {
            "check": "镜头时长是否合适",
            "good": "时长分配合理，重点镜头有足够时长",
            "bad": "镜头时长平均分配，重点不突出"
        }
    }
    
    DIALOGUE_RULES = {
        "density": {
            "check": "台词密度是否适中",
            "good": "台词精炼，不冗余",
            "bad": "台词太多或太少"
        },
        "style": {
            "check": "台词风格是否统一",
            "good": "台词风格符合整体调性",
            "bad": "台词风格跳跃"
        },
        "memory_point": {
            "check": "是否有记忆点台词",
            "good": "有金句或记忆点",
            "bad": "缺乏让人记住的台词"
        }
    }
    
    SOUND_RULES = {
        "bgm": {
            "check": "BGM设计是否合理",
            "good": "BGM与内容匹配，有节奏变化",
            "bad": "BGM缺失或不匹配"
        },
        "sound_effects": {
            "check": "音效是否到位",
            "good": "关键节点有音效加持",
            "bad": "音效缺失或过多"
        },
        "silence": {
            "check": "静音处理是否恰当",
            "good": "有适当的静音处理",
            "bad": "全程嘈杂或全程静音"
        }
    }
    
    def __init__(self):
        self.rules = {
            "structure": self.STRUCTURE_RULES,
            "emotion": self.EMOTION_RULES,
            "shot": self.SHOT_RULES,
            "dialogue": self.DIALOGUE_RULES,
            "sound": self.SOUND_RULES
        }
    
    def parse_script(self, content: str) -> Dict:
        """解析剧本内容"""
        # 提取镜头信息
        shots = []
        shot_pattern = r'\|\s*(\d+)\s*\|\s*(\d+)s?\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|'
        matches = re.findall(shot_pattern, content)
        
        for match in matches:
            shots.append({
                "number": int(match[0]),
                "duration": int(match[1]),
                "shot_type": match[2].strip(),
                "movement": match[3].strip(),
                "description": match[4].strip()
            })
        
        # 提取时长信息
        duration_match = re.search(r'时长[：:]\s*(\d+)秒', content)
        duration = int(duration_match.group(1)) if duration_match else 0
        
        return {
            "shots": shots,
            "duration": duration,
            "has_character": "角色卡" in content,
            "has_sound": "音效设计" in content,
            "has_visual_style": "视觉风格" in content
        }
    
    def diagnose(self, script_content: str) -> DiagnosisReport:
        """诊断剧本"""
        parsed = self.parse_script(script_content)
        shots = parsed["shots"]
        duration = parsed["duration"]
        
        # 诊断各维度
        structure_score = self._diagnose_structure(shots, duration)
        emotion_score = self._diagnose_emotion(shots, duration)
        shot_score = self._diagnose_shots(shots)
        dialogue_score = self._diagnose_dialogue(script_content)
        sound_score = self._diagnose_sound(parsed)
        platform_score = self._diagnose_platform(script_content)
        
        # 生成问题列表
        must_fix = []
        suggestions = []
        good_practices = []
        
        # 结构问题
        if structure_score.score < 60:
            must_fix.append(Issue(
                severity="高",
                location="整体结构",
                problem="结构不完整",
                current="剧本缺少必要的起承转合",
                suggestion="按照'开头钩子-中段冲突-结尾反转'的结构重新组织",
                priority=1
            ))
        elif structure_score.score < 75:
            suggestions.append(Issue(
                severity="中",
                location="整体结构",
                problem="结构可优化",
                current="结构基本完整但不够紧凑",
                suggestion="精简开头，加快节奏",
                priority=2
            ))
        else:
            good_practices.append(GoodPractice(
                aspect="结构设计",
                description="剧本有清晰的开头、中段和结尾"
            ))
        
        # 镜头问题
        shot_types = [s["shot_type"] for s in shots]
        if len(set(shot_types)) < 3:
            must_fix.append(Issue(
                severity="高",
                location="第1镜",
                problem="景别单一",
                current="全片景别变化少，缺乏视觉层次",
                suggestion="增加特写、远景等景别变化",
                priority=2
            ))
        else:
            good_practices.append(GoodPractice(
                aspect="景别设计",
                description="镜头景别有丰富变化"
            ))
        
        # 台词问题
        if "台词" not in script_content and "对白" not in script_content:
            suggestions.append(Issue(
                severity="中",
                location="台词设计",
                problem="台词设计缺失",
                current="剧本缺少台词设计",
                suggestion="适当添加台词或旁白增加信息量",
                priority=2
            ))
        
        # 音效问题
        if not parsed["has_sound"]:
            must_fix.append(Issue(
                severity="高",
                location="音效设计",
                problem="音效缺失",
                current="剧本缺少音效设计",
                suggestion="添加BGM、环境音、心跳声等音效设计",
                priority=3
            ))
        else:
            good_practices.append(GoodPractice(
                aspect="音效设计",
                description="有完整的音效设计方案"
            ))
        
        return DiagnosisReport(
            structure_score=structure_score,
            emotion_score=emotion_score,
            shot_score=shot_score,
            dialogue_score=dialogue_score,
            sound_score=sound_score,
            platform_score=platform_score,
            must_fix=must_fix,
            suggestions=suggestions,
            good_practices=good_practices
        )
    
    def _diagnose_structure(self, shots: List[Dict], duration: int) -> DimensionScore:
        """诊断结构"""
        score = 70
        
        # 检查开头钩子
        if len(shots) > 0:
            first_shot_desc = shots[0].get("description", "")
            if any(word in first_shot_desc for word in ["对视", "悬念", "突发", "意外"]):
                score += 15
            elif any(word in first_shot_desc for word in ["环境", "开场", "平静"]):
                score -= 10
        
        # 检查冲突
        if any("冲突" in s.get("description", "") or "转折" in s.get("description", "") for s in shots):
            score += 10
        
        # 检查结尾
        if len(shots) >= 3:
            last_shot_desc = shots[-1].get("description", "")
            if any(word in last_shot_desc for word in ["反转", "金句", "点睛", "高光"]):
                score += 10
        
        return DimensionScore(name="结构", score=min(100, max(0, score)))
    
    def _diagnose_emotion(self, shots: List[Dict], duration: int) -> DimensionScore:
        """诊断情绪"""
        score = 65
        
        # 检查情绪标注
        emotions = [s.get("emotion", "") for s in shots if s.get("emotion")]
        if len(emotions) > 3:
            score += 10
        
        # 检查情绪变化
        if len(set(emotions)) >= 3:
            score += 10
        
        # 检查高潮位置
        climax_shots = [s for s in shots if "高潮" in s.get("emotion", "") or "心动" in s.get("emotion", "")]
        if climax_shots:
            # 简单检查：在中后段有高潮
            climax_position = climax_shots[0]["number"] / len(shots) if shots else 0
            if 0.4 <= climax_position <= 0.8:
                score += 10
        
        return DimensionScore(name="情绪", score=min(100, max(0, score)))
    
    def _diagnose_shots(self, shots: List[Dict]) -> DimensionScore:
        """诊断镜头"""
        score = 75
        
        if not shots:
            return DimensionScore(name="镜头", score=0)
        
        # 检查景别变化
        shot_types = [s.get("shot_type", "") for s in shots]
        unique_types = set(shot_types)
        
        if len(unique_types) < 3:
            score -= 15
        elif len(unique_types) >= 5:
            score += 10
        
        # 检查运镜变化
        movements = [s.get("movement", "") for s in shots]
        if len(set(movements)) >= 3:
            score += 10
        
        # 检查时长分布
        durations = [s.get("duration", 0) for s in shots]
        if durations:
            avg_duration = sum(durations) / len(durations)
            if max(durations) > avg_duration * 1.5:
                score += 5  # 有重点镜头
        
        return DimensionScore(name="镜头", score=min(100, max(0, score)))
    
    def _diagnose_dialogue(self, content: str) -> DimensionScore:
        """诊断台词"""
        score = 60
        
        # 提取台词
        dialogue_pattern = r'\|[^|]*\|[^|]*\|[^|]*\|[^|]*\|([^|]+)\|'
        dialogues = re.findall(dialogue_pattern, content)
        non_dash = [d.strip() for d in dialogues if d.strip() and d.strip() != "—"]
        
        if len(non_dash) > 2:
            score += 15
        
        if len(non_dash) > 5:
            score += 10
        
        # 检查金句
        if any(word in content for word in ["金句", "点睛", "记忆点"]):
            score += 10
        
        return DimensionScore(name="台词", score=min(100, max(0, score)))
    
    def _diagnose_sound(self, parsed: Dict) -> DimensionScore:
        """诊断音效"""
        score = 60
        
        if parsed["has_sound"]:
            score += 25
        
        return DimensionScore(name="音效", score=min(100, max(0, score)))
    
    def _diagnose_platform(self, content: str) -> DimensionScore:
        """诊断平台适配"""
        score = 70
        
        # 检查平台标注
        platforms = ["抖音", "小红书", "B站", "视频号", "快手", "Sora", "可灵", "即梦"]
        if any(p in content for p in platforms):
            score += 15
        
        # 检查比例标注
        ratios = ["9:16", "16:9", "3:4", "4:3", "1:1"]
        if any(r in content for r in ratios):
            score += 10
        
        return DimensionScore(name="平台适配", score=min(100, max(0, score)))


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(description="AI视频创作师 - 剧本诊断脚本")
    parser.add_argument("--file", "-f", help="剧本文件路径")
    parser.add_argument("--content", "-c", help="剧本内容（直接传入）")
    parser.add_argument("--output", "-o", default=None, help="输出文件路径")
    
    args = parser.parse_args()
    
    # 读取剧本内容
    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            script_content = f.read()
    elif args.content:
        script_content = args.content
    else:
        print("请提供剧本文件路径或内容")
        return
    
    # 诊断
    diagnoser = ScriptDiagnosis()
    report = diagnoser.diagnose(script_content)
    
    # 输出
    output_content = report.to_markdown()
    
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_content)
        print(f"诊断报告已保存到：{args.output}")
    else:
        print(output_content)


if __name__ == "__main__":
    main()
