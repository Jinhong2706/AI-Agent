#!/usr/bin/env python3
"""
视频发布主脚本
支持多平台视频发布，自动生成标题和标签
"""

import argparse
import json
import os
import time
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class PlatformConfig:
    """平台配置"""
    name: str
    max_duration: int  # 秒
    aspect_ratio: str
    max_title_length: int
    tag_count: tuple  # (min, max)
    emoji_support: bool
    style: str


# 平台配置
PLATFORMS = {
    "xiaohongshu": PlatformConfig(
        name="小红书",
        max_duration=900,  # 15分钟
        aspect_ratio="9:16",
        max_title_length=20,
        tag_count=(3, 5),
        emoji_support=True,
        style="emotional"
    ),
    "douyin": PlatformConfig(
        name="抖音",
        max_duration=900,
        aspect_ratio="9:16",
        max_title_length=30,
        tag_count=(2, 3),
        emoji_support=True,
        style="concise"
    ),
    "shipinhao": PlatformConfig(
        name="视频号",
        max_duration=1800,
        aspect_ratio="16:9,9:16",
        max_title_length=40,
        tag_count=(2, 4),
        emoji_support=False,
        style="formal"
    ),
    "kuaishou": PlatformConfig(
        name="快手",
        max_duration=600,
        aspect_ratio="9:16",
        max_title_length=25,
        tag_count=(3, 5),
        emoji_support=True,
        style="casual"
    )
}

# 平台调性模板
STYLE_TEMPLATES = {
    "emotional": {
        "title_prefixes": ["震惊！", "必看！", "收藏！", "干货满满！", "太重要了！"],
        "title_suffixes": ["🔥", "💥", "⚠️", "📌", "✨"],
        "tag_styles": {
            "news": ["#热点追踪", "#最新消息", "#重磅新闻", "#今日热点"],
            "military": ["#军事动态", "#国际局势", "#国防军事"],
            "economy": ["#经济观察", "#财经热点", "#投资理财"],
            "tech": ["#科技前沿", "#黑科技", "#创新突破"],
            "lifestyle": ["#生活技巧", "#实用干货", "#好物推荐"]
        }
    },
    "concise": {
        "title_prefixes": ["最新！", "突发！", "快讯！"],
        "title_suffixes": [],
        "tag_styles": {
            "news": ["#热点", "#新闻", "#最新"],
            "military": ["#军事", "#国际"],
            "economy": ["#财经", "#经济"],
            "tech": ["#科技", "#创新"],
            "lifestyle": ["#生活", "#实用"]
        }
    },
    "formal": {
        "title_prefixes": [],
        "title_suffixes": [],
        "tag_styles": {
            "news": ["#国际新闻", "#时事热点"],
            "military": ["#军事新闻", "#国防动态"],
            "economy": ["#财经新闻", "#经济动态"],
            "tech": ["#科技新闻", "#创新前沿"],
            "lifestyle": ["#生活分享", "#实用知识"]
        }
    },
    "casual": {
        "title_prefixes": ["老铁们！", "家人们！", "兄弟们！"],
        "title_suffixes": ["👍", "💪", "🔥"],
        "tag_styles": {
            "news": ["#热点事件", "#大家都在看", "#今日热点"],
            "military": ["#军事那些事", "#国际大事"],
            "economy": ["#搞钱必看", "#财经热点"],
            "tech": ["#黑科技来了", "#科技好物"],
            "lifestyle": ["#生活小妙招", "#实用好物"]
        }
    }
}


def generate_title(topic: str, platform: str, category: str = "news") -> str:
    """
    根据平台调性生成标题
    
    Args:
        topic: 视频主题
        platform: 平台ID
        category: 内容类别
    
    Returns:
        生成的标题
    """
    config = PLATFORMS.get(platform)
    if not config:
        return topic
    
    style = STYLE_TEMPLATES.get(config.style, STYLE_TEMPLATES["concise"])
    
    # 选择前缀
    prefix = ""
    if style["title_prefixes"]:
        import random
        prefix = random.choice(style["title_prefixes"])
    
    # 选择后缀（emoji）
    suffix = ""
    if config.emoji_support and style["title_suffixes"]:
        import random
        suffix = random.choice(style["title_suffixes"])
    
    # 组合标题
    title = f"{prefix}{topic}{suffix}"
    
    # 截断到最大长度
    if len(title) > config.max_title_length:
        title = title[:config.max_title_length - 3] + "..."
    
    return title


def generate_tags(topic: str, platform: str, category: str = "news") -> List[str]:
    """
    根据平台调性生成标签
    
    Args:
        topic: 视频主题
        platform: 平台ID
        category: 内容类别
    
    Returns:
        标签列表
    """
    config = PLATFORMS.get(platform)
    if not config:
        return [f"#{topic}"]
    
    style = STYLE_TEMPLATES.get(config.style, STYLE_TEMPLATES["concise"])
    tag_styles = style.get("tag_styles", {})
    
    # 获取类别标签
    category_tags = tag_styles.get(category, [f"#{topic}"])
    
    # 确定标签数量
    min_tags, max_tags = config.tag_count
    import random
    tag_count = random.randint(min_tags, max_tags)
    
    # 选择标签
    tags = []
    if len(category_tags) >= tag_count:
        tags = random.sample(category_tags, tag_count)
    else:
        tags = category_tags.copy()
        # 添加通用标签
        general_tags = ["#原创", "#热门", "#推荐"]
        remaining = tag_count - len(tags)
        if remaining > 0:
            tags.extend(random.sample(general_tags, min(remaining, len(general_tags))))
    
    return tags[:max_tags]


def check_video(video_path: str, platform: str) -> Dict:
    """
    检查视频是否符合平台要求
    
    Returns:
        检查结果
    """
    config = PLATFORMS.get(platform)
    result = {
        "valid": True,
        "errors": [],
        "warnings": []
    }
    
    # 检查文件是否存在
    if not os.path.exists(video_path):
        result["valid"] = False
        result["errors"].append(f"视频文件不存在: {video_path}")
        return result
    
    # 检查文件大小
    file_size = os.path.getsize(video_path)
    if file_size > 500 * 1024 * 1024:  # 500MB
        result["warnings"].append(f"视频文件较大 ({file_size / 1024 / 1024:.1f}MB)，上传可能较慢")
    
    # TODO: 检查视频时长和分辨率
    # 需要使用 ffmpeg 或 moviepy
    
    return result


def publish_to_xiaohongshu(video_path: str, title: str, tags: List[str]) -> Dict:
    """
    发布到小红书
    
    Returns:
        发布结果
    """
    # TODO: 使用浏览器自动化
    # 可以调用 xiaohongshu-helper skill
    
    print(f"\n📱 发布到小红书")
    print(f"   标题: {title}")
    print(f"   标签: {' '.join(tags)}")
    print(f"   视频: {video_path}")
    
    # 模拟发布过程
    return {
        "platform": "xiaohongshu",
        "status": "pending_browser",
        "message": "需要打开浏览器完成发布"
    }


def publish_to_douyin(video_path: str, title: str, tags: List[str]) -> Dict:
    """
    发布到抖音
    """
    print(f"\n🎵 发布到抖音")
    print(f"   标题: {title}")
    print(f"   标签: {' '.join(tags)}")
    print(f"   视频: {video_path}")
    
    return {
        "platform": "douyin",
        "status": "pending_browser",
        "message": "需要打开浏览器完成发布"
    }


def publish_to_shipinhao(video_path: str, title: str, tags: List[str]) -> Dict:
    """
    发布到视频号
    """
    print(f"\n📹 发布到视频号")
    print(f"   标题: {title}")
    print(f"   标签: {' '.join(tags)}")
    print(f"   视频: {video_path}")
    
    return {
        "platform": "shipinhao",
        "status": "pending_browser",
        "message": "需要打开浏览器完成发布"
    }


def publish_to_kuaishou(video_path: str, title: str, tags: List[str]) -> Dict:
    """
    发布到快手
    """
    print(f"\n⚡ 发布到快手")
    print(f"   标题: {title}")
    print(f"   标签: {' '.join(tags)}")
    print(f"   视频: {video_path}")
    
    return {
        "platform": "kuaishou",
        "status": "pending_browser",
        "message": "需要打开浏览器完成发布"
    }


# 发布函数映射
PUBLISH_FUNCTIONS = {
    "xiaohongshu": publish_to_xiaohongshu,
    "douyin": publish_to_douyin,
    "shipinhao": publish_to_shipinhao,
    "kuaishou": publish_to_kuaishou
}


def main():
    parser = argparse.ArgumentParser(description="视频发布工具")
    parser.add_argument("--video", type=str, required=True, help="视频文件路径")
    parser.add_argument("--platforms", type=str, required=True, help="目标平台，逗号分隔")
    parser.add_argument("--topic", type=str, required=True, help="视频主题")
    parser.add_argument("--category", type=str, default="news", help="内容类别")
    parser.add_argument("--title", type=str, default="", help="自定义标题（可选）")
    parser.add_argument("--tags", type=str, default="", help="自定义标签，逗号分隔（可选）")
    parser.add_argument("--output", type=str, default="publish_report.json", help="报告输出文件")
    
    args = parser.parse_args()
    
    # 解析平台列表
    target_platforms = [p.strip() for p in args.platforms.split(",")]
    
    print("\n" + "="*60)
    print("🚀 视频发布工具")
    print("="*60)
    print(f"📹 视频: {args.video}")
    print(f"🎯 平台: {', '.join(target_platforms)}")
    print(f"📝 主题: {args.topic}")
    print(f"📂 类别: {args.category}")
    
    # 发布结果
    results = []
    
    for platform in target_platforms:
        if platform not in PLATFORMS:
            print(f"\n⚠️  不支持的平台: {platform}")
            continue
        
        # 检查视频
        check_result = check_video(args.video, platform)
        if not check_result["valid"]:
            print(f"\n❌ 视频检查失败: {check_result['errors']}")
            results.append({
                "platform": platform,
                "status": "failed",
                "errors": check_result["errors"]
            })
            continue
        
        # 生成或使用自定义标题
        if args.title:
            title = args.title
        else:
            title = generate_title(args.topic, platform, args.category)
        
        # 生成或使用自定义标签
        if args.tags:
            tags = [f"#{t.strip()}" for t in args.tags.split(",")]
        else:
            tags = generate_tags(args.topic, platform, args.category)
        
        # 执行发布
        publish_func = PUBLISH_FUNCTIONS.get(platform)
        if publish_func:
            result = publish_func(args.video, title, tags)
            results.append(result)
        else:
            print(f"\n⚠️  平台 {platform} 的发布功能尚未实现")
            results.append({
                "platform": platform,
                "status": "not_implemented"
            })
    
    # 保存报告
    report = {
        "timestamp": datetime.now().isoformat(),
        "video": args.video,
        "topic": args.topic,
        "category": args.category,
        "platforms": target_platforms,
        "results": results
    }
    
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print("\n" + "="*60)
    print(f"📋 发布报告已保存: {args.output}")
    print("="*60)


if __name__ == "__main__":
    main()
