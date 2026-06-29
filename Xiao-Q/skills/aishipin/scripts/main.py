#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI视频创作师 - 主脚本
整合所有功能模块，提供统一的命令行入口

【功能模块】
1. 灵感裂变 - 将模糊灵感裂变为多个具体故事方向
2. 剧本生成 - 生成专业分镜脚本
3. 剧本诊断 - 诊断已有剧本问题
4. 爆款公式 - 提供爆款模板和公式
5. 多平台适配 - 生成各平台专用提示词

【命令行使用】
python scripts/main.py --mode inspiration --idea "咖啡店的故事"
python scripts/main.py --mode script --scene "咖啡店" --type "浪漫"
python scripts/main.py --mode diagnosis --file "script.md"
python scripts/main.py --mode formula --formula "反转剧"
python scripts/main.py --mode adapt --file "script.md" --platforms "即梦,Sora"

【交互模式】
python scripts/main.py --mode interactive
"""

import argparse
import sys
import os
from typing import Optional

# 添加scripts目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入各模块
from inspiration_generator import InspirationGenerator
from script_generator import ScriptGenerator
from script_diagnosis import ScriptDiagnosis
from viral_formula import ViralFormulaLibrary
from multi_platform_adapter import MultiPlatformAdapter


class VideoCreationAssistant:
    """AI视频创作助手主类"""
    
    def __init__(self):
        self.inspiration_gen = InspirationGenerator()
        self.script_gen = ScriptGenerator()
        self.script_diag = ScriptDiagnosis()
        self.formula_lib = ViralFormulaLibrary()
        self.platform_adapter = MultiPlatformAdapter()
    
    def run_inspiration(
        self,
        idea: str,
        mood: Optional[str] = None,
        platform: Optional[str] = None,
        duration: int = 30,
        count: int = 3,
        output: Optional[str] = None
    ) -> str:
        """灵感裂变"""
        directions = self.inspiration_gen.generate_directions(
            idea=idea,
            mood=mood,
            platform=platform,
            duration=duration,
            count=count
        )
        
        report = self.inspiration_gen.to_markdown(directions, idea)
        
        if output:
            with open(output, "w", encoding="utf-8") as f:
                f.write(report)
            print(f"灵感裂变报告已保存到：{output}")
        
        return report
    
    def run_script_generation(
        self,
        scene: str,
        story_type: str = "浪漫",
        duration: int = 15,
        platform: str = "抖音",
        style: str = "日系清新",
        include_characters: bool = True,
        output: Optional[str] = None
    ) -> str:
        """剧本生成"""
        script = self.script_gen.generate_script(
            scene=scene,
            story_type=story_type,
            duration=duration,
            platform=platform,
            include_characters=include_characters,
            style=style
        )
        
        report = script.to_markdown()
        
        if output:
            with open(output, "w", encoding="utf-8") as f:
                f.write(report)
            print(f"剧本已保存到：{output}")
        
        return report
    
    def run_diagnosis(
        self,
        script_content: str,
        output: Optional[str] = None
    ) -> str:
        """剧本诊断"""
        report = self.script_diag.diagnose(script_content)
        
        output_content = report.to_markdown()
        
        if output:
            with open(output, "w", encoding="utf-8") as f:
                f.write(output_content)
            print(f"诊断报告已保存到：{output}")
        
        return output_content
    
    def run_formula(
        self,
        formula_name: Optional[str] = None,
        platform: Optional[str] = None,
        scene: Optional[str] = None,
        list_all: bool = False,
        output: Optional[str] = None
    ) -> str:
        """爆款公式"""
        if list_all:
            content = self.formula_lib.to_markdown()
        elif formula_name:
            formula = self.formula_lib.get_formula(formula_name)
            content = formula.to_markdown() if formula else f"未找到公式：{formula_name}"
        elif platform:
            formulas = self.formula_lib.get_formulas_by_platform(platform)
            content = f"## 适用「{platform}」平台的公式\n\n"
            for f in formulas:
                content += f.to_markdown() + "\n---\n"
        elif scene:
            formulas = self.formula_lib.get_formulas_by_scene(scene)
            content = f"## 适用「{scene}」场景的公式\n\n"
            for f in formulas:
                content += f.to_markdown() + "\n---\n"
        else:
            content = self.formula_lib.list_formulas()
        
        if output:
            with open(output, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"公式库已保存到：{output}")
        
        return content
    
    def run_adaptation(
        self,
        script_content: str,
        platforms: list,
        duration: int = 15,
        output: Optional[str] = None
    ) -> str:
        """多平台适配"""
        result = self.platform_adapter.adapt(script_content, platforms, duration)
        
        output_content = result.to_markdown()
        
        if output:
            with open(output, "w", encoding="utf-8") as f:
                f.write(output_content)
            print(f"多平台提示词已保存到：{output}")
        
        return output_content


def create_parser() -> argparse.ArgumentParser:
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        description="AI视频创作师 - 全流程AI视频创作助手",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
【使用示例】
  # 灵感裂变
  python scripts/main.py --mode inspiration --idea "咖啡店的故事"
  
  # 剧本生成
  python scripts/main.py --mode script --scene "咖啡店" --type "浪漫"
  
  # 剧本诊断
  python scripts/main.py --mode diagnosis --file "script.md"
  
  # 查看爆款公式
  python scripts/main.py --mode formula --list
  python scripts/main.py --mode formula --formula "反转剧"
  
  # 多平台适配
  python scripts/main.py --mode adapt --file "script.md" --platforms "即梦,Sora"
"""
    )
    
    parser.add_argument(
        "--mode", "-m",
        choices=["inspiration", "script", "diagnosis", "formula", "adapt", "interactive"],
        default="interactive",
        help="运行模式"
    )
    
    # 灵感裂变参数
    parser.add_argument("--idea", "-i", help="创作灵感")
    parser.add_argument("--mood", help="情绪基调")
    parser.add_argument("--count", type=int, default=3, help="生成方向数量")
    
    # 剧本生成参数
    parser.add_argument("--scene", "-s", help="核心场景")
    parser.add_argument("--type", "-t", default="浪漫", help="故事类型")
    parser.add_argument("--style", default="日系清新", help="视觉风格")
    parser.add_argument("--no-character", action="store_true", help="不生成角色卡")
    
    # 通用参数
    parser.add_argument("--duration", "-d", type=int, default=15, help="视频时长（秒）")
    parser.add_argument("--platform", "-p", help="目标平台")
    parser.add_argument("--platforms", help="目标平台列表（逗号分隔）")
    parser.add_argument("--file", "-f", help="输入文件路径")
    parser.add_argument("--formula", help="爆款公式名称")
    parser.add_argument("--list", action="store_true", help="列出所有")
    parser.add_argument("--output", "-o", help="输出文件路径")
    
    return parser


def interactive_mode():
    """交互模式"""
    print("\n" + "="*50)
    print("🎬 AI视频创作师 - 交互模式")
    print("="*50)
    
    assistant = VideoCreationAssistant()
    
    while True:
        print("\n请选择功能：")
        print("1. 灵感裂变 - 将模糊灵感裂变为多个故事方向")
        print("2. 剧本生成 - 生成专业分镜脚本")
        print("3. 剧本诊断 - 诊断已有剧本问题")
        print("4. 爆款公式 - 查看爆款模板")
        print("5. 多平台适配 - 生成各平台提示词")
        print("6. 退出")
        
        choice = input("\n请输入选项（1-6）：").strip()
        
        if choice == "6":
            print("\n感谢使用AI视频创作师！")
            break
        
        if choice == "1":
            idea = input("请输入你的创作灵感：").strip()
            if idea:
                mood = input("情绪基调（直接回车跳过）：").strip() or None
                platform = input("目标平台（直接回车跳过）：").strip() or None
                print("\n" + assistant.run_inspiration(idea, mood, platform))
        
        elif choice == "2":
            scene = input("请输入核心场景（咖啡店/办公室/地铁等）：").strip()
            if scene:
                story_type = input("故事类型（浪漫/搞笑/职场/治愈，直接回车默认浪漫）：").strip() or "浪漫"
                duration = int(input("视频时长（秒，直接回车默认15）：").strip() or "15")
                platform = input("目标平台（直接回车默认抖音）：").strip() or "抖音"
                print("\n" + assistant.run_script_generation(scene, story_type, duration, platform))
        
        elif choice == "3":
            file_path = input("请输入剧本文件路径：").strip()
            if file_path:
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    print("\n" + assistant.run_diagnosis(content))
                except FileNotFoundError:
                    print(f"文件不存在：{file_path}")
        
        elif choice == "4":
            formula_name = input("输入公式名称查看详情（直接回车列出所有）：").strip()
            if formula_name:
                print("\n" + assistant.run_formula(formula_name=formula_name))
            else:
                print("\n" + assistant.run_formula(list_all=True))
        
        elif choice == "5":
            file_path = input("请输入剧本文件路径：").strip()
            platforms = input("请输入目标平台（逗号分隔，如即梦,可灵,Sora）：").strip()
            if file_path and platforms:
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    platform_list = [p.strip() for p in platforms.split(",")]
                    print("\n" + assistant.run_adaptation(content, platform_list))
                except FileNotFoundError:
                    print(f"文件不存在：{file_path}")


def main():
    """主入口"""
    parser = create_parser()
    args = parser.parse_args()
    
    assistant = VideoCreationAssistant()
    
    # 交互模式
    if args.mode == "interactive":
        if len(sys.argv) == 1:
            interactive_mode()
        else:
            print("交互模式不支持其他参数，请使用 --mode 指定功能")
        return
    
    # 灵感裂变模式
    if args.mode == "inspiration":
        if not args.idea:
            print("错误：请提供 --idea 参数")
            return
        print(assistant.run_inspiration(
            idea=args.idea,
            mood=args.mood,
            platform=args.platform,
            duration=args.duration,
            count=args.count,
            output=args.output
        ))
    
    # 剧本生成模式
    elif args.mode == "script":
        if not args.scene:
            print("错误：请提供 --scene 参数")
            return
        print(assistant.run_script_generation(
            scene=args.scene,
            story_type=args.type,
            duration=args.duration,
            platform=args.platform or "抖音",
            style=args.style,
            include_characters=not args.no_character,
            output=args.output
        ))
    
    # 剧本诊断模式
    elif args.mode == "diagnosis":
        if not args.file:
            print("错误：请提供 --file 参数")
            return
        try:
            with open(args.file, "r", encoding="utf-8") as f:
                content = f.read()
            print(assistant.run_diagnosis(content, args.output))
        except FileNotFoundError:
            print(f"错误：文件不存在 {args.file}")
    
    # 爆款公式模式
    elif args.mode == "formula":
        print(assistant.run_formula(
            formula_name=args.formula,
            platform=args.platform,
            list_all=args.list,
            output=args.output
        ))
    
    # 多平台适配模式
    elif args.mode == "adapt":
        if not args.file or not args.platforms:
            print("错误：请提供 --file 和 --platforms 参数")
            return
        try:
            with open(args.file, "r", encoding="utf-8") as f:
                content = f.read()
            platform_list = [p.strip() for p in args.platforms.split(",")]
            print(assistant.run_adaptation(
                script_content=content,
                platforms=platform_list,
                duration=args.duration,
                output=args.output
            ))
        except FileNotFoundError:
            print(f"错误：文件不存在 {args.file}")


if __name__ == "__main__":
    main()
