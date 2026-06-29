#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI视频创作师 - 多平台适配脚本
功能：将一个剧本转换为各平台专用提示词

【命令行使用】
python scripts/multi_platform_adapter.py --script "咖啡店浪漫短片" --platforms "即梦,可灵,Sora"
python scripts/multi_platform_adapter.py --file "script.md" --platforms "即梦,Runway"

【代码中使用】
from scripts.multi_platform_adapter import MultiPlatformAdapter, PlatformConfig

adapter = MultiPlatformAdapter()
result = adapter.adapt(script_content, platforms=["即梦", "可灵", "Sora"])
print(result.to_markdown())
"""

import argparse
from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class PlatformConfig:
    """平台配置"""
    name: str
    language: str
    duration_range: str
    features: List[str]
    prompt_focus: List[str]
    example_prompt: str = ""


@dataclass
class AdaptedPrompt:
    """适配后的提示词"""
    platform: str
    original: str
    adapted: str
    tips: List[str]
    duration_note: str


@dataclass
class AdaptationResult:
    """适配结果"""
    original_script: str
    adaptations: List[AdaptedPrompt]
    comparison: Dict = field(default_factory=dict)
    
    def to_markdown(self) -> str:
        """转换为Markdown格式"""
        output = ["## 多平台提示词\n"]
        output.append(f"**原始剧本**：{self.original_script[:100]}...")
        output.append("")
        
        for adaptation in self.adaptations:
            output.append(f"### {adaptation.platform}（{adaptation.platform}）\n")
            output.append(f"**时长说明**：{adaptation.duration_note}")
            output.append("")
            output.append(f"**提示词**：\n```\n{adaptation.adapted}\n```")
            output.append("")
            output.append("**使用建议**：")
            for tip in adaptation.tips:
                output.append(f"- {tip}")
            output.append("")
            output.append("---\n")
        
        return "\n".join(output)


class MultiPlatformAdapter:
    """多平台适配器"""
    
    # 平台配置
    PLATFORMS = {
        "即梦": PlatformConfig(
            name="即梦",
            language="中文",
            duration_range="3秒-3分钟",
            features=["音画一体", "中文理解好", "性价比高"],
            prompt_focus=["画面描述", "音效设计", "环境音", "对白"],
            example_prompt=""
        ),
        "可灵": PlatformConfig(
            name="可灵",
            language="中文",
            duration_range="5秒-2分钟",
            features=["性价比高", "动作流畅", "中文支持好"],
            prompt_focus=["精简画面描述", "动作描述", "场景氛围"],
            example_prompt=""
        ),
        "Sora": PlatformConfig(
            name="Sora",
            language="英文",
            duration_range="3秒-1分钟",
            features=["叙事强", "画质顶级", "场景复杂"],
            prompt_focus=["完整故事结构", "镜头语言", "场景细节"],
            example_prompt=""
        ),
        "Pika": PlatformConfig(
            name="Pika",
            language="英文",
            duration_range="3秒-30秒",
            features=["风格化强", "操作简单", "创意空间大"],
            prompt_focus=["艺术风格", "视觉质感", "创意描述"],
            example_prompt=""
        ),
        "Runway": PlatformConfig(
            name="Runway",
            language="英文",
            duration_range="4秒-18秒",
            features=["专业级", "控制精准", "画质优秀"],
            prompt_focus=["专业参数", "镜头语言", "运动描述"],
            example_prompt=""
        ),
        "Vidu": PlatformConfig(
            name="Vidu",
            language="中文/英文",
            duration_range="4秒-30秒",
            features=["中国团队", "动漫风格", "性价比"],
            prompt_focus=["画面描述", "风格定位", "情感表达"],
            example_prompt=""
        )
    }
    
    # 中文提示词模板
    CHINESE_TEMPLATES = {
        "romantic": "{scene}，{lighting}，{character1}和{character2}{action}，{emotion}氛围，{style}，{duration}",
        "comedy": "{scene}，{character1}和{character2}{funny_action}，{comedy_element}，{style}，{duration}",
        "story": "{scene}开场，{character}进行{activity}，{conflict}，{resolution}，{style}，{duration}"
    }
    
    # 英文提示词模板
    ENGLISH_TEMPLATES = {
        "romantic": "A {scene} with {lighting}, {character1} and {character2} {action}. {emotion} atmosphere, {style}, {duration}. Cinematic, {camera_movement}",
        "narrative": "Scene 1: {scene}. {character} {activity}. {conflict}. Scene 2: {development}. Scene 3: {climax}. {style}, {duration}",
        "artistic": "{scene} in {art_style} style. {character} {action}. {mood}. {texture_details}. {duration}"
    }
    
    def __init__(self):
        self.scene_keywords = {
            "咖啡店": "温馨的日式咖啡店",
            "办公室": "现代简约的办公空间",
            "地铁": "繁忙的都市地铁站",
            "校园": "青春洋溢的校园",
            "家里": "温馨的家庭空间",
            "街头": "充满故事的街头"
        }
        
        self.lighting_keywords = {
            "温馨": "柔和的暖色调光线",
            "悬疑": "明暗对比强烈",
            "搞笑": "明亮的喜剧光线",
            "治愈": "温暖的午后阳光"
        }
        
        self.style_keywords = {
            "日系清新": "日系清新风格，暖黄色调，浅景深，电影感颗粒",
            "电影感": "电影质感，胶片色调，深景构图，戏剧性光线",
            "复古": "复古胶片风格，泛黄色调，柔焦，怀旧氛围",
            "现代": "现代简约风格，冷色调，高对比，极简构图"
        }
    
    def adapt(
        self, 
        script_content: str, 
        platforms: List[str],
        duration: int = 15
    ) -> AdaptationResult:
        """适配多平台"""
        adaptations = []
        
        for platform_name in platforms:
            if platform_name not in self.PLATFORMS:
                continue
            
            config = self.PLATFORMS[platform_name]
            adapted = self._adapt_to_platform(script_content, config, duration)
            tips = self._generate_tips(config, duration)
            duration_note = self._get_duration_note(config, duration)
            
            adaptations.append(AdaptedPrompt(
                platform=platform_name,
                original=script_content[:200],
                adapted=adapted,
                tips=tips,
                duration_note=duration_note
            ))
        
        return AdaptationResult(
            original_script=script_content,
            adaptations=adaptations
        )
    
    def _adapt_to_platform(
        self, 
        script_content: str, 
        config: PlatformConfig,
        duration: int
    ) -> str:
        """根据平台特点适配提示词"""
        # 解析原始剧本
        parsed = self._parse_script(script_content)
        
        # 根据平台生成提示词
        if config.name in ["即梦", "可灵", "Vidu"]:
            return self._generate_chinese_prompt(parsed, config, duration)
        else:
            return self._generate_english_prompt(parsed, config, duration)
    
    def _parse_script(self, content: str) -> Dict:
        """解析剧本内容"""
        # 提取关键信息（简化版）
        scene = self._extract_scene(content)
        emotion = self._extract_emotion(content)
        style = self._extract_style(content)
        
        return {
            "scene": scene,
            "emotion": emotion,
            "style": style,
            "raw_content": content
        }
    
    def _extract_scene(self, content: str) -> str:
        """提取场景"""
        scenes = ["咖啡店", "办公室", "地铁", "校园", "家里", "街头", "餐厅", "商场"]
        for scene in scenes:
            if scene in content:
                return scene
        return "咖啡店"
    
    def _extract_emotion(self, content: str) -> str:
        """提取情绪"""
        emotions = ["浪漫", "温馨", "搞笑", "悬疑", "治愈", "燃", "紧张"]
        for emotion in emotions:
            if emotion in content:
                return emotion
        return "温馨"
    
    def _extract_style(self, content: str) -> str:
        """提取风格"""
        styles = ["日系清新", "电影感", "复古", "现代", "唯美"]
        for style in styles:
            if style in content:
                return style
        return "日系清新"
    
    def _generate_chinese_prompt(
        self, 
        parsed: Dict, 
        config: PlatformConfig,
        duration: int
    ) -> str:
        """生成中文提示词"""
        scene_desc = self.scene_keywords.get(parsed["scene"], parsed["scene"])
        style_desc = self.style_keywords.get(parsed["style"], parsed["style"])
        
        # 即梦提示词（完整详细）
        if config.name == "即梦":
            prompt = f"""{scene_desc}，
下午柔和的阳光透过落地窗，
一个穿米色毛衣的短发女孩和一个穿黑色卫衣的男生
同时伸手拿桌上的咖啡杯，两人的手相遇，
镜头缓慢推近，女孩脸红，男生发现杯上的"缘分"二字，
镜头拉远，两人相视而笑。
{style_desc}，
{duration}秒短片。
环境音：咖啡店爵士乐、杯碟声，BGM：轻快吉他。"""
        
        # 可灵提示词（精简）
        elif config.name == "可灵":
            prompt = f"""{scene_desc}，
短发女孩和黑衣男生同时拿咖啡杯，手相遇，
尴尬又甜蜜的瞬间，
{style_desc}"""
        
        # Vidu提示词
        elif config.name == "Vidu":
            prompt = f"""{scene_desc}，
{parsed['emotion']}氛围，
{style_desc}，
两人相遇的美好瞬间，
细腻的情感表达"""
        
        else:
            prompt = f"""{scene_desc}，
{parsed['emotion']}情感，
{style_desc}"""
        
        return prompt
    
    def _generate_english_prompt(
        self, 
        parsed: Dict,
        config: PlatformConfig,
        duration: int
    ) -> str:
        """生成英文提示词"""
        scene_mapping = {
            "咖啡店": "cozy coffee shop",
            "办公室": "modern office",
            "地铁": "busy subway station",
            "校园": "vibrant campus",
            "家里": "cozy home",
            "街头": "charming street"
        }
        
        style_mapping = {
            "日系清新": "Japanese fresh style, warm tones, film grain",
            "电影感": "cinematic style, anamorphic lens, film grain",
            "复古": "vintage film style, nostalgic tones",
            "现代": "modern minimalist style, clean composition"
        }
        
        scene_en = scene_mapping.get(parsed["scene"], parsed["scene"])
        style_en = style_mapping.get(parsed["style"], "cinematic")
        
        # Sora提示词（完整叙事）
        if config.name == "Sora":
            prompt = f"""Story: A chance encounter at a coffee shop.

Scene 1: A cozy Japanese-style coffee shop with warm afternoon light streaming through large windows. A girl in beige sweater and a guy in black hoodie both reach for the same cup on the table.

Scene 2: Their hands meet above the cup. They freeze, surprised, faces inches apart.

Scene 3: The girl looks up, face flushed with embarrassment. The guy notices the characters "缘分" (fate) written on the cup and smiles.

Scene 4: Wide shot. They both laugh, sharing a warm moment as sunlight bathes the scene.

{style_en}, shallow depth of field, 35mm lens, warm color grading, {duration} seconds."""
        
        # Pika提示词（艺术风格）
        elif config.name == "Pika":
            prompt = f"""{scene_en}, anime illustration style.
A cute girl and handsome boy reaching for same coffee cup.
Surprise expression, blushing cheeks, warm atmosphere.
Beautiful lighting, soft colors, artistic rendering.
{style_en}, {duration} seconds."""
        
        # Runway提示词（专业参数）
        elif config.name == "Runway":
            prompt = f"""EXTERIOR/INTERIOR: {scene_en.upper()}
TIME: Late afternoon, golden hour
SUBJECT: Young couple, diverse ethnicities

Camera: Dolly in slowly, then push in on faces
Movement: Static wide, then handheld close-up

{style_en}
Lens: 35mm prime, f/2.8
Color: Warm tones, slight grain
Duration: {duration} seconds"""
        
        else:
            prompt = f"""{scene_en},
{parsed['emotion']} atmosphere,
{style_en},
{parsed['scene']} scene with romantic moment"""
        
        return prompt
    
    def _generate_tips(self, config: PlatformConfig, duration: int) -> List[str]:
        """生成使用建议"""
        tips = []
        
        if config.name == "即梦":
            tips = [
                "支持中文输入，直接使用中文提示词",
                "可以同时添加音效描述",
                "时长建议控制在2分钟以内效果更好",
                "画面不满意可以重新生成或调整种子"
            ]
        elif config.name == "可灵":
            tips = [
                "提示词尽量精简，不超过200字",
                "优先描述主体动作和场景",
                "对动作类内容生成效果较好",
                "支持首尾帧控制"
            ]
        elif config.name == "Sora":
            tips = [
                "建议使用英文提示词",
                "支持完整的场景描述",
                "可以添加相机运动描述",
                "生成时间较长，建议5分钟内视频"
            ]
        elif config.name == "Pika":
            tips = [
                "支持多种艺术风格",
                "适合创意类内容",
                "时长较短，适合短视频",
                "可以添加角色描述保持一致性"
            ]
        elif config.name == "Runway":
            tips = [
                "支持专业级控制",
                "可以使用相机运动指令",
                "Gen-2/Gen-3模型效果不同",
                "适合高质量商业内容"
            ]
        elif config.name == "Vidu":
            tips = [
                "中国团队开发，中文理解好",
                "动漫风格表现优秀",
                "性价比高",
                "支持镜头控制"
            ]
        
        return tips
    
    def _get_duration_note(self, config: PlatformConfig, original_duration: int) -> str:
        """获取时长说明"""
        if config.name == "即梦":
            return f"建议时长：{min(original_duration, 180)}秒"
        elif config.name == "可灵":
            return f"建议时长：{min(original_duration, 120)}秒"
        elif config.name == "Sora":
            return f"建议时长：{min(original_duration, 60)}秒"
        elif config.name == "Pika":
            return f"建议时长：{min(original_duration, 30)}秒"
        elif config.name == "Runway":
            return f"建议时长：{min(original_duration, 18)}秒"
        elif config.name == "Vidu":
            return f"建议时长：{min(original_duration, 30)}秒"
        return f"建议时长：{original_duration}秒"


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(description="AI视频创作师 - 多平台适配脚本")
    parser.add_argument("--script", "-s", help="剧本内容")
    parser.add_argument("--file", "-f", help="剧本文件路径")
    parser.add_argument("--platforms", "-p", default="即梦,可灵,Sora", help="目标平台（逗号分隔）")
    parser.add_argument("--duration", "-d", type=int, default=15, help="原始视频时长（秒）")
    parser.add_argument("--output", "-o", default=None, help="输出文件路径")
    
    args = parser.parse_args()
    
    # 读取剧本内容
    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            script_content = f.read()
    elif args.script:
        script_content = args.script
    else:
        print("请提供剧本内容或文件路径")
        return
    
    # 解析平台列表
    platforms = [p.strip() for p in args.platforms.split(",")]
    
    # 适配
    adapter = MultiPlatformAdapter()
    result = adapter.adapt(script_content, platforms, args.duration)
    
    # 输出
    output_content = result.to_markdown()
    
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_content)
        print(f"多平台提示词已保存到：{args.output}")
    else:
        print(output_content)


if __name__ == "__main__":
    main()
