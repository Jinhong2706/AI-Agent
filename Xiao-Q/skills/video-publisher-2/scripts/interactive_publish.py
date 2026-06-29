#!/usr/bin/env python3
"""
交互式视频发布工具
引导用户提供必要信息
"""

import argparse
import json
import os
from datetime import datetime
from typing import Dict, List


def interactive_guide():
    """交互式引导"""
    print("\n" + "="*60)
    print("🎬 视频发布向导")
    print("="*60)
    
    # Step 1: 视频文件
    print("\n📹 Step 1: 视频文件")
    print("   请提供视频文件路径")
    video_path = input("   路径: ").strip()
    
    if not os.path.exists(video_path):
        print(f"   ❌ 文件不存在: {video_path}")
        return
    
    # Step 2: 目标平台
    print("\n🎯 Step 2: 目标平台")
    print("   支持的平台:")
    print("   1. 小红书 (xiaohongshu)")
    print("   2. 抖音 (douyin)")
    print("   3. 视频号 (shipinhao)")
    print("   4. 快手 (kuaishou)")
    print("   可多选，用逗号分隔，如: 1,2,3")
    
    platform_input = input("   选择: ").strip()
    
    platform_map = {
        "1": "xiaohongshu",
        "2": "douyin",
        "3": "shipinhao",
        "4": "kuaishou"
    }
    
    platforms = []
    for p in platform_input.split(","):
        p = p.strip()
        if p in platform_map:
            platforms.append(platform_map[p])
        elif p in platform_map.values():
            platforms.append(p)
    
    if not platforms:
        print("   ❌ 未选择有效平台")
        return
    
    print(f"   ✅ 已选择: {', '.join(platforms)}")
    
    # Step 3: 视频主题
    print("\n📝 Step 3: 视频主题")
    print("   请简述视频内容（用于生成标题和标签）")
    topic = input("   主题: ").strip()
    
    if not topic:
        print("   ❌ 主题不能为空")
        return
    
    # Step 4: 内容类别
    print("\n📂 Step 4: 内容类别")
    print("   选择内容类别:")
    print("   1. 新闻资讯 (news)")
    print("   2. 军事国际 (military)")
    print("   3. 经济财经 (economy)")
    print("   4. 科技创新 (tech)")
    print("   5. 生活方式 (lifestyle)")
    
    category_input = input("   选择 (默认1): ").strip() or "1"
    
    category_map = {
        "1": "news",
        "2": "military",
        "3": "economy",
        "4": "tech",
        "5": "lifestyle"
    }
    
    category = category_map.get(category_input, "news")
    print(f"   ✅ 类别: {category}")
    
    # Step 5: 生成标题和标签预览
    print("\n🎨 Step 5: 标题和标签预览")
    print("   正在根据平台调性生成...")
    
    # 导入生成函数
    from publish import generate_title, generate_tags, PLATFORMS
    
    preview = {}
    for platform in platforms:
        config = PLATFORMS.get(platform)
        if not config:
            continue
        
        title = generate_title(topic, platform, category)
        tags = generate_tags(topic, platform, category)
        
        preview[platform] = {
            "platform_name": config.name,
            "title": title,
            "tags": tags
        }
        
        print(f"\n   【{config.name}】")
        print(f"   标题: {title}")
        print(f"   标签: {' '.join(tags)}")
    
    # Step 6: 确认发布
    print("\n✅ Step 6: 确认发布")
    print("   选项:")
    print("   1. 直接发布")
    print("   2. 修改标题/标签后发布")
    print("   3. 取消发布")
    
    choice = input("   选择: ").strip()
    
    if choice == "1":
        # 执行发布
        print("\n🚀 开始发布...")
        
        # 调用发布脚本
        import subprocess
        
        platforms_str = ",".join(platforms)
        cmd = [
            "python3", "publish.py",
            "--video", video_path,
            "--platforms", platforms_str,
            "--topic", topic,
            "--category", category
        ]
        
        subprocess.run(cmd)
        
    elif choice == "2":
        # 修改模式
        print("\n   ✏️  自定义模式")
        custom_title = input("   输入自定义标题（留空使用自动生成）: ").strip()
        custom_tags = input("   输入自定义标签（逗号分隔，留空使用自动生成）: ").strip()
        
        # 使用自定义内容发布
        cmd = [
            "python3", "publish.py",
            "--video", video_path,
            "--platforms", ",".join(platforms),
            "--topic", topic,
            "--category", category
        ]
        
        if custom_title:
            cmd.extend(["--title", custom_title])
        if custom_tags:
            cmd.extend(["--tags", custom_tags])
        
        subprocess.run(cmd)
        
    else:
        print("\n   ❌ 已取消发布")
        return
    
    print("\n" + "="*60)
    print("✅ 发布流程完成")
    print("="*60)


def main():
    parser = argparse.ArgumentParser(description="交互式视频发布")
    parser.add_argument("--auto", action="store_true", help="自动模式（使用默认值）")
    
    args = parser.parse_args()
    
    if args.auto:
        # 自动模式：从配置文件读取
        print("🤖 自动模式")
        # TODO: 从配置文件读取参数
    else:
        interactive_guide()


if __name__ == "__main__":
    main()
