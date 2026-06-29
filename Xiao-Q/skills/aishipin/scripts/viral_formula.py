#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI视频创作师 - 爆款公式脚本
功能：提供验证过的爆款模板和公式

【命令行使用】
python scripts/viral_formula.py --list
python scripts/viral_formula.py --formula "反转剧"
python scripts/viral_formula.py --scene "职场" --platform "抖音"

【代码中使用】
from scripts.viral_formula import ViralFormulaLibrary, FormulaTemplate

library = ViralFormulaLibrary()
formula = library.get_formula("反转剧")
print(formula.to_markdown())
"""

import argparse
from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class FormulaTemplate:
    """爆款公式模板"""
    id: str
    name: str
    platform: str
    structure: str
    duration_range: str
    applicable_scenes: List[str]
    shot_design: List[Dict[str, str]]
    emotion_flow: str
    tips: List[str]
    examples: List[str]
    
    def to_markdown(self) -> str:
        """转换为Markdown格式"""
        output = [f"## {self.name}公式（{self.platform} TOP1）\n"]
        output.append(f"**结构**：{self.structure}")
        output.append(f"**时长**：{self.duration_range}")
        output.append(f"**适用场景**：{', '.join(self.applicable_scenes)}")
        output.append("")
        output.append("**情绪流**：")
        output.append(self.emotion_flow)
        output.append("")
        output.append("**镜头设计**：")
        for shot in self.shot_design:
            output.append(f"- {shot['stage']}：{shot['description']}")
        output.append("")
        output.append("**注意事项**：")
        for tip in self.tips:
            if tip.startswith("✅"):
                output.append(f"- {tip}")
            elif tip.startswith("❌"):
                output.append(f"- {tip}")
            else:
                output.append(f"- {tip}")
        output.append("")
        output.append("**参考案例**：")
        for example in self.examples:
            output.append(f"- {example}")
        
        return "\n".join(output)


class ViralFormulaLibrary:
    """爆款公式库"""
    
    def __init__(self):
        self.formulas = self._init_formulas()
        self.categories = {
            "反转剧": "剧情/搞笑",
            "种草文": "产品推广",
            "知识点": "科普/教学",
            "情感共鸣": "情感/生活",
            "挑战赛": "互动/UGC",
            "产品展示": "电商/广告"
        }
    
    def _init_formulas(self) -> List[FormulaTemplate]:
        """初始化公式库"""
        return [
            FormulaTemplate(
                id="reversal",
                name="反转剧",
                platform="抖音",
                structure="铺垫(3-5s) → 期待建立(3-5s) → 反转(2-3s) → 金句(2-3s)",
                duration_range="15-30秒",
                applicable_scenes=["办公室", "商场", "家里", "餐厅", "街头"],
                shot_design=[
                    {"stage": "镜头1（铺垫）", "description": "展示看似正常的场景，建立预期"},
                    {"stage": "镜头2（期待）", "description": "角色做动作，暗示某种结果"},
                    {"stage": "镜头3（反转）", "description": "揭示完全不同的真相"},
                    {"stage": "镜头4（金句）", "description": "点睛之笔，升华主题"}
                ],
                emotion_flow="好奇 → 期待 → 惊讶 → 会心一笑",
                tips=[
                    "✅ 反转要在观众\"确信\"后才能出现",
                    "✅ 反转要合乎逻辑，不能硬转",
                    "❌ 不要反转太多次，容易混乱",
                    "✅ 金句要有记忆点，可以是台词或画面"
                ],
                examples=[
                    "\"以为是甲方爸爸，结果...\"",
                    "\"以为是普通朋友，结果...\"",
                    "\"以为是职场潜规则，结果...\""
                ]
            ),
            FormulaTemplate(
                id="planting",
                name="种草文",
                platform="小红书",
                structure="痛点(3-5s) → 产品(5-10s) → 效果(5-10s) → 行动(3-5s)",
                duration_range="30-60秒",
                applicable_scenes=["使用场景", "对比展示", "效果呈现"],
                shot_design=[
                    {"stage": "镜头1（痛点）", "description": "展示目标用户的痛点场景"},
                    {"stage": "镜头2（产品）", "description": "产品亮相，特点展示"},
                    {"stage": "镜头3（效果）", "description": "使用效果前后对比"},
                    {"stage": "镜头4（行动）", "description": "行动引导：购买/关注"}
                ],
                emotion_flow="焦虑 → 好奇 → 期待 → 信任",
                tips=[
                    "✅ 痛点要真实，能引起共鸣",
                    "✅ 产品展示要有代入感",
                    "✅ 效果展示要真实可信",
                    "❌ 不要过于广告感",
                    "✅ 行动引导要自然"
                ],
                examples=[
                    "\"敏感肌救星！用了之后...\"",
                    "\"上班族必备！每天省下2小时\"",
                    "\"租房党必备！小空间神器\""
                ]
            ),
            FormulaTemplate(
                id="knowledge",
                name="知识点",
                platform="B站",
                structure="提问(5s) → 解答(20-40s) → 案例(20-30s) → 总结(10s)",
                duration_range="60-180秒",
                applicable_scenes=["知识讲解", "技能教学", "经验分享"],
                shot_design=[
                    {"stage": "镜头1（提问）", "description": "设问引入，引发思考"},
                    {"stage": "镜头2（解答）", "description": "分点讲解要点"},
                    {"stage": "镜头3（案例）", "description": "实操演示或案例分析"},
                    {"stage": "镜头4（总结）", "description": "要点回顾，强化记忆"}
                ],
                emotion_flow="好奇 → 专注 → 恍然大悟 → 收获感",
                tips=[
                    "✅ 开头要抓住注意力",
                    "✅ 内容要硬核，有价值",
                    "✅ 案例要生动有趣",
                    "✅ 总结要有获得感",
                    "❌ 不要过于学术化"
                ],
                examples=[
                    "\"为什么你总是被割韭菜？\"",
                    "\"3分钟学会XXX\"",
                    "\"90%的人都做错了...\""
                ]
            ),
            FormulaTemplate(
                id="emotional",
                name="情感共鸣",
                platform="视频号",
                structure="场景(5-10s) → 情绪(10-20s) → 金句(5-10s) → 互动(3-5s)",
                duration_range="30-60秒",
                applicable_scenes=["生活场景", "情感故事", "人生感悟"],
                shot_design=[
                    {"stage": "镜头1（场景）", "description": "真实生活场景"},
                    {"stage": "镜头2（情绪）", "description": "情感积累和爆发"},
                    {"stage": "镜头3（金句）", "description": "触动人心的话"},
                    {"stage": "镜头4（互动）", "description": "引导评论和转发"}
                ],
                emotion_flow="代入 → 共情 → 感动 → 分享",
                tips=[
                    "✅ 场景要真实，有代入感",
                    "✅ 情绪要真挚，不做作",
                    "✅ 金句要戳心，引发共鸣",
                    "✅ 互动要引导讨论话题"
                ],
                examples=[
                    "\"成年人的崩溃就在一瞬间\"",
                    "\"你有多久没回家看父母了？\"",
                    "\"这就是我不想上班的原因\""
                ]
            ),
            FormulaTemplate(
                id="challenge",
                name="挑战赛",
                platform="快手",
                structure="规则(3s) → 示范(10-15s) → 邀请(3s)",
                duration_range="15-30秒",
                applicable_scenes=["趣味挑战", "技能展示", "互动参与"],
                shot_design=[
                    {"stage": "镜头1（规则）", "description": "简明扼要说明规则"},
                    {"stage": "镜头2（示范）", "description": "本人/达人示范"},
                    {"stage": "镜头3（邀请）", "description": "邀请参与，话术固定"}
                ],
                emotion_flow="好奇 → 跃跃欲试 → 参与冲动",
                tips=[
                    "✅ 规则要简单，一学就会",
                    "✅ 示范要有看点，好玩或厉害",
                    "✅ 邀请话术要固定，便于传播",
                    "✅ 要留有二次创作空间"
                ],
                examples=[
                    "\"挑战用一只手...\"",
                    "\"看看你能坚持几秒？\"",
                    "\"接住算你赢\""
                ]
            ),
            FormulaTemplate(
                id="product_showcase",
                name="产品展示",
                platform="全平台",
                structure="亮相(2-3s) → 功能(10-20s) → 细节(5-10s) → 品牌(3-5s)",
                duration_range="30-60秒",
                applicable_scenes=["电商", "广告", "品牌宣传"],
                shot_design=[
                    {"stage": "镜头1（亮相）", "description": "产品360度展示"},
                    {"stage": "镜头2（功能）", "description": "核心功能演示"},
                    {"stage": "镜头3（细节）", "description": "做工/材质特写"},
                    {"stage": "镜头4（品牌）", "description": "品牌Logo和口号"}
                ],
                emotion_flow="吸引 → 认可 → 信任 → 记忆",
                tips=[
                    "✅ 亮相要有冲击力",
                    "✅ 功能要可视化展示",
                    "✅ 细节要体现品质",
                    "✅ 品牌要自然融入"
                ],
                examples=[
                    "\"这就是传说中的...\"",
                    "\"用了3个月，忍不住分享\"",
                    "\"这个设计太绝了\""
                ]
            ),
            FormulaTemplate(
                id="before_after",
                name="前后对比",
                platform="全平台",
                structure="痛点展示(5s) → 改变过程(15-30s) → 完美呈现(5-10s)",
                duration_range="30-60秒",
                applicable_scenes=["改造", "变身", "逆袭", "修复"],
                shot_design=[
                    {"stage": "镜头1（痛点）", "description": "丑/乱/糟的状态展示"},
                    {"stage": "镜头2（过程）", "description": "转变过程（加速）"},
                    {"stage": "镜头3（完美）", "description": "完美呈现，惊艳亮相"}
                ],
                emotion_flow="嫌弃 → 期待 → 惊讶 → 羡慕",
                tips=[
                    "✅ 痛点要足够痛，对比才明显",
                    "✅ 过程要有节奏感，不能太冗长",
                    "✅ 完美呈现要有冲击力",
                    "✅ 配乐要配合节奏"
                ],
                examples=[
                    "\"改造前vs改造后\"",
                    "\"素颜vs妆后\"",
                    "\"乱房间vs整洁家\""
                ]
            ),
            FormulaTemplate(
                id="storytelling",
                name="故事叙述",
                platform="B站/视频号",
                structure="背景(5s) → 冲突(10-20s) → 高潮(10-15s) → 结局(5s)",
                duration_range="60-120秒",
                applicable_scenes=["真实故事", "人生经历", "创业故事"],
                shot_design=[
                    {"stage": "镜头1（背景）", "description": "交代时间、地点、人物"},
                    {"stage": "镜头2（冲突）", "description": "制造矛盾和困难"},
                    {"stage": "镜头3（高潮）", "description": "转折或突破"},
                    {"stage": "镜头4（结局）", "description": "圆满或开放式结尾"}
                ],
                emotion_flow="好奇 → 紧张 → 感动/激动 → 满足",
                tips=[
                    "✅ 故事要有代入感",
                    "✅ 冲突要真实可信",
                    "✅ 高潮要有爆点",
                    "✅ 结局要有回味"
                ],
                examples=[
                    "\"我是怎么从月薪3000到3万的\"",
                    "\"放弃百万年薪去创业\"",
                    "\"一个决定改变了我的人生\""
                ]
            )
        ]
    
    def get_all_formulas(self) -> List[FormulaTemplate]:
        """获取所有公式"""
        return self.formulas
    
    def get_formula(self, name: str) -> Optional[FormulaTemplate]:
        """获取指定公式"""
        for formula in self.formulas:
            if formula.name == name or formula.id == name:
                return formula
        return None
    
    def get_formulas_by_platform(self, platform: str) -> List[FormulaTemplate]:
        """按平台获取公式"""
        return [f for f in self.formulas if platform in f.platform or "全平台" in f.platform]
    
    def get_formulas_by_scene(self, scene: str) -> List[FormulaTemplate]:
        """按场景获取公式"""
        return [f for f in self.formulas if scene in f.applicable_scenes]
    
    def list_formulas(self) -> str:
        """列出所有公式"""
        output = ["## 爆款公式库\n"]
        output.append("| 公式名称 | 平台 | 结构 | 适用场景 |")
        output.append("|---------|------|------|----------|")
        
        for formula in self.formulas:
            scenes = "/".join(formula.applicable_scenes[:2])
            output.append(f"| {formula.name} | {formula.platform} | {formula.structure[:20]}... | {scenes} |")
        
        return "\n".join(output)
    
    def to_markdown(self) -> str:
        """生成完整公式库文档"""
        output = ["# 爆款公式库详解\n"]
        
        for formula in self.formulas:
            output.append(formula.to_markdown())
            output.append("---\n")
        
        return "\n".join(output)


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(description="AI视频创作师 - 爆款公式脚本")
    parser.add_argument("--list", "-l", action="store_true", help="列出所有公式")
    parser.add_argument("--formula", "-f", help="查看指定公式详情")
    parser.add_argument("--scene", "-s", help="按场景筛选公式")
    parser.add_argument("--platform", "-p", help="按平台筛选公式")
    parser.add_argument("--output", "-o", default=None, help="输出文件路径")
    
    args = parser.parse_args()
    
    library = ViralFormulaLibrary()
    
    if args.list:
        content = library.list_formulas()
    elif args.formula:
        formula = library.get_formula(args.formula)
        if formula:
            content = formula.to_markdown()
        else:
            content = f"未找到公式：{args.formula}"
    elif args.scene:
        formulas = library.get_formulas_by_scene(args.scene)
        if formulas:
            content = f"## 适用「{args.scene}」场景的公式\n\n"
            for f in formulas:
                content += f.to_markdown() + "\n---\n"
        else:
            content = f"未找到适用「{args.scene}」的公式"
    elif args.platform:
        formulas = library.get_formulas_by_platform(args.platform)
        if formulas:
            content = f"## 适用「{args.platform}」平台的公式\n\n"
            for f in formulas:
                content += f.to_markdown() + "\n---\n"
        else:
            content = f"未找到适用「{args.platform}」的公式"
    else:
        content = library.to_markdown()
    
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"公式库已保存到：{args.output}")
    else:
        print(content)


if __name__ == "__main__":
    main()
