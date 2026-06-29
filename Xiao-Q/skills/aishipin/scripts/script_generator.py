#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI视频创作师 - 剧本生成脚本
功能：生成专业分镜脚本，包含角色卡、视觉风格、音效设计

【命令行使用】
python scripts/script_generator.py --scene "咖啡店" --type "浪漫" --duration 15 --platform "抖音"
python scripts/script_generator.py --scene "办公室" --type "搞笑" --duration 30 --output "script.md"

【代码中使用】
from scripts.script_generator import ScriptGenerator, Character, Storyboard

generator = ScriptGenerator()
script = generator.generate_script(
    scene="咖啡店",
    story_type="浪漫",
    duration=15,
    platform="抖音"
)
print(script.to_markdown())
"""

import random
import argparse
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from enum import Enum


class ShotType(Enum):
    """景别类型"""
    EXTREME_WIDE = "大远景"  #  establishing shot
    WIDE = "远景"           #  全景
    MEDIUM_WIDE = "中远景"   #  环境人像
    MEDIUM = "中景"          #  膝盖以上
    MEDIUM_CLOSE = "中近景"   #  腰部以上
    CLOSE = "近景"           #  胸部以上
    TIGHT = "特写"           #  局部特写
    EXTREME_TIGHT = "大特写" #  细节


class CameraMovement(Enum):
    """运镜方式"""
    STATIC = "固定"
    PAN = "摇镜"
    TILT = "俯仰"
    DOLLY = "推拉"
    TRACK = "移动"
    CRANE = "升降"
    HANDHELD = "手持"
    ZOOM = "变焦"


class VisualStyle(Enum):
    """视觉风格"""
    JAPANESE_FRESH = "日系清新"
    CINEMATIC = "电影感"
    RETRO = "复古"
    MODERN = "现代"
    NOSTALGIC = "怀旧"
    BRIGHT = "明亮"
    DARK = "暗调"
    PASTORAL = "田园"


@dataclass
class Character:
    """角色卡"""
    name: str
    age: int
    identity: str
    personality: str
    appearance: Dict[str, str] = field(default_factory=dict)
    signature_items: Dict[str, str] = field(default_factory=dict)
    signature_gestures: List[str] = field(default_factory=list)
    
    def to_markdown(self) -> str:
        """转换为Markdown格式"""
        output = [f"## 🎭 角色卡：{self.name}\n"]
        output.append("### 基本信息")
        output.append(f"- 年龄：{self.age}岁")
        output.append(f"- 身份：{self.identity}")
        output.append(f"- 性格：{self.personality}\n")
        
        output.append("### 外貌特征")
        output.append("| 部位 | 描述 | 提示词锚点 |")
        output.append("|------|------|-----------|")
        for part, desc in self.appearance.items():
            prompt = self._generate_prompt(part, desc)
            output.append(f"| {part} | {desc} | {prompt} |")
        
        output.append("\n### 标志性元素")
        output.append("| 元素 | 描述 | 提示词锚点 |")
        output.append("|------|------|-----------|")
        for item, desc in self.signature_items.items():
            prompt = self._generate_item_prompt(item, desc)
            output.append(f"| {item} | {desc} | {prompt} |")
        
        return "\n".join(output)
    
    def _generate_prompt(self, part: str, desc: str) -> str:
        """生成提示词锚点"""
        prompts = {
            "发型": "short black hair, shoulder length",
            "脸型": "oval face, fair skin",
            "眼睛": "bright eyes, gentle expression",
            "身材": "slim figure, approachable",
            "穿着": "casual style, earth tones"
        }
        return prompts.get(part, "natural appearance")
    
    def _generate_item_prompt(self, item: str, desc: str) -> str:
        """生成元素提示词"""
        return f"{item.lower()}, {desc.lower()}"


@dataclass
class Shot:
    """分镜"""
    number: int
    duration: int
    shot_type: str
    movement: str
    description: str
    dialogue: str = ""
    sound_effect: str = ""
    emotion: str = ""
    
    def to_markdown_row(self) -> str:
        """转换为Markdown表格行"""
        dialogue = self.dialogue if self.dialogue else "—"
        sound = self.sound_effect if self.sound_effect else "—"
        emotion = self.emotion if self.emotion else "—"
        return f"| {self.number} | {self.duration}s | {self.shot_type} | {self.movement} | {self.description} | {dialogue} | {sound} | {emotion} |"


@dataclass
class SoundDesign:
    """音效设计"""
    timeline: List[Dict] = field(default_factory=list)
    
    def to_markdown(self) -> str:
        """转换为Markdown格式"""
        output = ["## 🎵 音效设计\n"]
        output.append("| 时间 | 音效类型 | 描述 |")
        output.append("|------|---------|------|")
        for item in self.timeline:
            output.append(f"| {item['time']} | {item['type']} | {item['description']} |")
        return "\n".join(output)


@dataclass
class VideoScript:
    """完整视频脚本"""
    title: str
    script_type: str
    style: str
    duration: int
    platform: str
    bgm_suggestion: str
    characters: List[Character] = field(default_factory=list)
    shots: List[Shot] = field(default_factory=list)
    sound_design: Optional[SoundDesign] = None
    
    def to_markdown(self) -> str:
        """转换为完整Markdown脚本"""
        output = []
        
        # 基本信息
        output.append(f"## 🎬 分镜脚本：{self.title}\n")
        output.append("### 基本信息")
        output.append(f"- 类型：{self.script_type}")
        output.append(f"- 风格：{self.style}")
        output.append(f"- 时长：{self.duration}秒")
        output.append(f"- 平台适配：{self.platform}")
        output.append(f"- BGM建议：{self.bgm_suggestion}\n")
        
        # 角色卡
        for char in self.characters:
            output.append(char.to_markdown())
            output.append("")
        
        # 分镜脚本
        output.append("### 分镜详情")
        output.append("| 镜号 | 时长 | 景别 | 运镜 | 画面描述 | 台词/旁白 | 音效 | 情绪 |")
        output.append("|------|------|------|------|----------|-----------|------|------|")
        for shot in self.shots:
            output.append(shot.to_markdown_row())
        output.append("")
        
        # 视觉风格卡
        output.append(self._generate_visual_style_card())
        output.append("")
        
        # 音效设计
        if self.sound_design:
            output.append(self.sound_design.to_markdown())
        
        return "\n".join(output)
    
    def _generate_visual_style_card(self) -> str:
        """生成视觉风格卡"""
        style_descriptions = {
            "日系清新": {
                "整体风格": "日系清新",
                "色调": "暖黄、米白、浅棕",
                "光线": "下午自然光，侧逆光",
                "构图": "三分法，留白充足",
                "提示词": "Japanese fresh style, warm yellow tone, natural afternoon lighting, soft focus, shallow depth of field, film grain, 35mm lens"
            },
            "电影感": {
                "整体风格": "电影感",
                "色调": "低饱和、高对比",
                "光线": "戏剧性布光",
                "构图": "深景构图",
                "提示词": "cinematic style, anamorphic lens, shallow depth of field, film grain, dramatic lighting, color graded"
            },
            "复古": {
                "整体风格": "复古胶片",
                "色调": "泛黄、褪色",
                "光线": "柔和散射光",
                "构图": "居中构图",
                "提示词": "vintage film style, 35mm film grain, warm tones, nostalgic, slight vignette, retro aesthetic"
            },
            "现代": {
                "整体风格": "现代简约",
                "色调": "冷色调、高亮度",
                "光线": "自然光+补光",
                "构图": "极简构图",
                "提示词": "modern minimalist style, clean composition, bright natural light, contemporary aesthetic, 4K quality"
            }
        }
        
        style_info = style_descriptions.get(self.style, style_descriptions["现代"])
        
        output = ["## 🎨 视觉风格卡\n"]
        output.append(f"**整体风格**：{style_info['整体风格']}")
        output.append(f"**色调**：{style_info['色调']}")
        output.append(f"**光线**：{style_info['光线']}")
        output.append(f"**构图**：{style_info['构图']}")
        output.append("")
        output.append("**提示词风格描述**：")
        output.append(style_info['提示词'])
        
        return "\n".join(output)


class ScriptGenerator:
    """剧本生成器"""
    
    # 角色名字库
    MALE_NAMES = ["林浩", "陈阳", "张明", "李然", "王磊", "周宇", "吴晨", "郑凯", "刘洋", "赵晨"]
    FEMALE_NAMES = ["林小夏", "陈雨晴", "张思思", "李安然", "王雅婷", "周雨桐", "吴静怡", "郑诗涵", "刘晓晓", "赵晨曦"]
    
    # 场景描述库
    SCENE_SHOTS = {
        "咖啡店": [
            "暖黄色灯光洒落，咖啡香气弥漫",
            "窗边的阳光透过纱帘洒在桌面上",
            "咖啡杯冒着热气",
            "两人同时伸手拿杯子",
            "手指在杯子上方相遇",
            "女孩抬头，脸微红"
        ],
        "办公室": [
            "明亮的办公区域",
            "会议室的玻璃门",
            "办公桌上的绿植",
            "忙碌的键盘敲击声",
            "突然安静下来",
            "屏幕上跳动的消息"
        ],
        "地铁": [
            "人来人往的站台",
            "即将关闭的地铁门",
            "车厢内的对视",
            "窗外的城市夜景",
            "耳机线缠绕",
            "指尖的触碰"
        ],
        "校园": [
            "图书馆的落地窗",
            "操场边的长椅",
            "食堂的人潮",
            "教室走廊",
            "樱花树下",
            "夕阳下的校门"
        ],
        "家里": [
            "深夜的厨房灯光",
            "阳台上的植物",
            "窗边的猫",
            "沙发上的毛毯",
            "电视机的微光",
            "泡好的热茶"
        ]
    }
    
    # 台词模板库
    DIALOGUE_TEMPLATES = {
        "浪漫": [
            "那个...", "你好...", "这杯给你...", "谢谢...", "我们是不是见过？", "嗯，好像..."
        ],
        "搞笑": [
            "等等等等...", "什么情况？", "不是吧...", "这也太...", "救命啊...", "笑死我了..."
        ],
        "职场": [
            "这个方案...", "好的，没问题", "等等，我有个想法", "你确定吗？", "收到！", "马上处理"
        ],
        "治愈": [
            "没关系的", "我一直都在", "会好起来的", "谢谢你", "你做得很好", "我懂你的感受"
        ]
    }
    
    # BGM建议库
    BGM_SUGGESTIONS = {
        "浪漫": ["轻快吉他", "钢琴曲", "民谣", "轻音乐"],
        "搞笑": ["欢快配乐", "搞怪音效", "反转音乐"],
        "职场": ["商务配乐", "电子音乐", "节奏感强"],
        "治愈": ["温暖钢琴", "吉他轻弹", "自然音效"],
        "悬疑": ["紧张弦乐", "低沉音效", "悬疑配乐"],
        "燃": ["热血音乐", "高潮电子", "激昂配乐"]
    }
    
    def __init__(self):
        self.platform_configs = {
            "抖音": {"ratio": "9:16", "aspect": "vertical", "first_frame": True},
            "小红书": {"ratio": "3:4", "aspect": "square_vertical", "first_frame": True},
            "B站": {"ratio": "16:9", "aspect": "horizontal", "first_frame": False},
            "视频号": {"ratio": "9:16", "aspect": "vertical", "first_frame": True},
            "快手": {"ratio": "9:16", "aspect": "vertical", "first_frame": True}
        }
    
    def generate_character(self, gender: str = "female", age_range: tuple = (22, 30)) -> Character:
        """生成角色卡"""
        if gender == "female":
            name = random.choice(self.FEMALE_NAMES)
            age = random.randint(*age_range)
            identity = random.choice(["设计师", "文案编辑", "咖啡店常客", "公司职员", "自由职业"])
            personality = random.choice(["害羞、真诚、文艺", "开朗、活泼、直率", "温柔、细腻、善解人意"])
            appearance = {
                "发型": random.choice(["齐肩短发", "马尾辫", "披肩长发"]),
                "脸型": random.choice(["圆脸", "鹅蛋脸"]),
                "眼睛": random.choice(["杏眼", "圆眼"]),
                "穿着": random.choice(["米色毛衣", "白色衬衫", "浅色针织衫"])
            }
        else:
            name = random.choice(self.MALE_NAMES)
            age = random.randint(*age_range)
            identity = random.choice(["程序员", "咖啡师", "公司职员", "摄影师", "自由职业"])
            personality = random.choice(["内敛、沉稳", "阳光、幽默", "温柔、体贴"])
            appearance = {
                "发型": random.choice(["短发", "蓬松短发", "侧分"]),
                "脸型": random.choice(["方脸", "椭圆脸"]),
                "眼睛": random.choice(["单眼皮", "双眼皮"]),
                "穿着": random.choice(["黑色卫衣", "白T恤", "格子衬衫"])
            }
        
        signature_items = {
            "饰品": random.choice(["银色手链", "简约手表", "眼镜"]),
            "包": random.choice(["帆布包", "电脑包", "单肩包"])
        }
        
        signature_gestures = random.sample([
            "害羞时会抿嘴",
            "思考时会推眼镜",
            "微笑时会眯眼",
            "紧张时会摸耳朵"
        ], 2)
        
        return Character(
            name=name,
            age=age,
            identity=identity,
            personality=personality,
            appearance=appearance,
            signature_items=signature_items,
            signature_gestures=signature_gestures
        )
    
    def generate_shots(
        self, 
        scene: str, 
        story_type: str, 
        duration: int,
        has_characters: bool = True
    ) -> List[Shot]:
        """生成分镜"""
        shots = []
        scene_descriptions = self.SCENE_SHOTS.get(scene, self.SCENE_SHOTS["咖啡店"])
        dialogues = self.DIALOGUE_TEMPLATES.get(story_type, self.DIALOGUE_TEMPLATES["浪漫"])
        
        # 计算镜头数量（每镜2-4秒）
        num_shots = max(3, duration // 3)
        
        shot_sequence = [
            ("远景", "固定", "建立场景", "好奇"),
            ("中景", "固定", "角色入镜", "平静"),
            ("近景", "推近", "关键动作", "期待"),
            ("特写", "固定", "细节展示", "紧张"),
            ("中景", "拉远", "关系呈现", "高潮"),
            ("远景", "移动", "环境交代", "结束")
        ]
        
        emotions = ["好奇", "期待", "紧张", "心动", "甜蜜", "温暖", "意外"]
        
        for i in range(num_shots):
            shot_type, movement, action, emotion = shot_sequence[i % len(shot_sequence)]
            
            # 时长分配：开头短、中间适中、结尾稍长
            if i == 0:
                shot_duration = 2
            elif i == num_shots - 1:
                shot_duration = 4
            else:
                shot_duration = random.randint(2, 4)
            
            # 画面描述
            if i < len(scene_descriptions):
                description = scene_descriptions[i]
            else:
                description = f"{scene}内的{action}"
            
            # 台词（只在部分镜头出现）
            dialogue = random.choice(dialogues) if random.random() > 0.5 and i > 0 else ""
            
            # 音效
            sound_effects = ["咖啡店环境音", "心跳声", "背景音乐起", "轻声对话", "风声"]
            sound = random.choice(sound_effects) if random.random() > 0.5 else ""
            
            shots.append(Shot(
                number=i + 1,
                duration=shot_duration,
                shot_type=shot_type,
                movement=movement,
                description=description,
                dialogue=dialogue,
                sound_effect=sound,
                emotion=emotion if emotion else random.choice(emotions)
            ))
        
        return shots
    
    def generate_sound_design(
        self, 
        story_type: str, 
        duration: int
    ) -> SoundDesign:
        """生成音效设计"""
        timeline = []
        
        # 根据时长分配时间段
        segments = duration // 5
        sound_types = {
            "浪漫": ["环境音", "突然安静", "心跳声", "BGM"],
            "搞笑": ["欢快音乐", "突然安静", "搞笑音效", "BGM"],
            "职场": ["办公室环境音", "键盘声", "会议声", "BGM"],
            "治愈": ["轻柔音乐", "自然音效", "温暖BGM", "余音"]
        }
        
        sounds = sound_types.get(story_type, sound_types["浪漫"])
        
        for i in range(segments):
            start_time = i * 5
            end_time = min((i + 1) * 5, duration)
            
            if i == 0:
                sound_type = sounds[0]  # 环境音
                description = f"{scene_sounds(story_type, 'start')}"
            elif i == segments - 1:
                sound_type = sounds[-1]  # BGM
                description = f"{story_type}风格BGM，{get_bgm_mood(story_type)}"
            else:
                sound_type = sounds[i % (len(sounds) - 1)]
                description = get_sound_description(story_type, i)
            
            timeline.append({
                "time": f"{start_time}-{end_time}s",
                "type": sound_type,
                "description": description
            })
        
        return SoundDesign(timeline=timeline)
    
    def generate_script(
        self,
        scene: str,
        story_type: str = "浪漫",
        duration: int = 15,
        platform: str = "抖音",
        include_characters: bool = True,
        style: str = "日系清新"
    ) -> VideoScript:
        """生成完整视频脚本"""
        # 生成角色
        characters = []
        if include_characters:
            female_char = self.generate_character("female")
            male_char = self.generate_character("male")
            characters = [female_char, male_char]
        
        # 生成分镜
        shots = self.generate_shots(scene, story_type, duration)
        
        # 生成音效设计
        sound_design = self.generate_sound_design(story_type, duration)
        
        # BGM建议
        bgm_options = self.BGM_SUGGESTIONS.get(story_type, self.BGM_SUGGESTIONS["浪漫"])
        bgm = random.choice(bgm_options)
        
        # 平台信息
        platform_info = self.platform_configs.get(platform, self.platform_configs["抖音"])
        
        return VideoScript(
            title=f"{scene}{story_type}短片",
            script_type=f"剧情{story_type}",
            style=style,
            duration=duration,
            platform=f"{platform}（{platform_info['ratio']}竖屏）",
            bgm_suggestion=bgm,
            characters=characters,
            shots=shots,
            sound_design=sound_design
        )


def scene_sounds(story_type: str, moment: str) -> str:
    """获取场景音效"""
    sounds = {
        "浪漫": {"start": "咖啡店爵士乐、杯碟声", "middle": "心跳声渐强", "end": "甜蜜BGM"},
        "搞笑": {"start": "欢快背景音乐", "middle": "搞笑音效", "end": "反转音效"},
        "职场": {"start": "办公室环境音", "middle": "键盘敲击声", "end": "轻松BGM"},
        "治愈": {"start": "轻柔钢琴", "middle": "自然音效", "end": "温暖余音"}
    }
    return sounds.get(story_type, sounds["浪漫"]).get(moment, "")


def get_bgm_mood(story_type: str) -> str:
    """获取BGM情绪"""
    moods = {
        "浪漫": "甜蜜、温馨",
        "搞笑": "欢快、搞怪",
        "职场": "积极、向上",
        "治愈": "温暖、舒缓",
        "悬疑": "紧张、神秘",
        "燃": "激昂、热血"
    }
    return moods.get(story_type, "轻快")


def get_sound_description(story_type: str, index: int) -> str:
    """获取音效描述"""
    descriptions = {
        "浪漫": ["轻轻的心跳声", "突然安静", "两人呼吸声", "眼神交流"],
        "搞笑": ["突然安静", "尴尬音效", "众人笑声", "反转音效"],
        "职场": ["键盘声", "电话铃声", "打印机声", "会议讨论声"],
        "治愈": ["轻柔风铃声", "雨声", "猫咪叫声", "温暖的低语"]
    }
    sounds = descriptions.get(story_type, descriptions["浪漫"])
    return sounds[index % len(sounds)]


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(description="AI视频创作师 - 剧本生成脚本")
    parser.add_argument("--scene", "-s", required=True, help="核心场景：咖啡店/办公室/地铁/校园/家里/街头")
    parser.add_argument("--type", "-t", default="浪漫", help="故事类型：浪漫/搞笑/职场/治愈/悬疑/燃")
    parser.add_argument("--duration", "-d", type=int, default=15, help="视频时长（秒）")
    parser.add_argument("--platform", "-p", default="抖音", help="目标平台：抖音/小红书/B站/视频号/快手")
    parser.add_argument("--style", default="日系清新", help="视觉风格：日系清新/电影感/复古/现代")
    parser.add_argument("--no-character", action="store_true", help="不生成角色卡")
    parser.add_argument("--output", "-o", default=None, help="输出文件路径")
    
    args = parser.parse_args()
    
    # 生成剧本
    generator = ScriptGenerator()
    script = generator.generate_script(
        scene=args.scene,
        story_type=args.type,
        duration=args.duration,
        platform=args.platform,
        include_characters=not args.no_character,
        style=args.style
    )
    
    # 输出
    output_content = script.to_markdown()
    
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_content)
        print(f"剧本已保存到：{args.output}")
    else:
        print(output_content)


if __name__ == "__main__":
    main()
