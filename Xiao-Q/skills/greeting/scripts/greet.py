#!/usr/bin/env python3
"""
Greeting Skill - 打招呼脚本
向用户热情地打招呼，说声"你好帅"！
"""

import argparse
import random


# 问候语模板
GREETINGS = {
    "basic": [
        "你好帅！👋",
        "嘿，你好帅！😄",
        "Hi～你好帅！🙌",
    ],
    "energetic": [
        "哇，你好帅啊！今天也是帅气的一天！✨",
        "天哪，你也太帅了吧！帅到发光！🌟",
        "你好帅！简直帅炸了！🔥",
    ],
    "formal": [
        "您好，非常高兴见到您！您真的好帅！🌟",
        "很荣幸与您交流，您真是太帅了！💎",
        "您好！容我夸赞一句——您真的很帅！👏",
    ],
}


def greet(name: str = None, style: str = "basic") -> str:
    """
    生成一条打招呼的问候语。

    Args:
        name: 用户的名字（可选）
        style: 问候风格，可选 'basic'、'energetic'、'formal'

    Returns:
        一条问候语字符串
    """
    if style not in GREETINGS:
        style = "basic"

    greeting = random.choice(GREETINGS[style])

    if name:
        # 在问候语前面加上名字
        greeting = f"嗨，{name}！{greeting}"

    return greeting


def main():
    parser = argparse.ArgumentParser(
        description="打招呼 Skill - 向用户说声'你好帅'！"
    )
    parser.add_argument(
        "--name",
        type=str,
        default=None,
        help="用户的名字，用于个性化问候",
    )
    parser.add_argument(
        "--style",
        type=str,
        choices=["basic", "energetic", "formal"],
        default="basic",
        help="问候风格：basic（基础）、energetic（元气）、formal（正式）",
    )

    args = parser.parse_args()
    message = greet(name=args.name, style=args.style)
    print(message)


if __name__ == "__main__":
    main()
