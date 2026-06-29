#!/usr/bin/env python3
"""
📖 答案之书 — 随机翻书脚本

从 references/answers.md 答案库中随机抽取一条答案，模拟"翻开答案之书"的体验。

用法:
    python flip-book.py                        # 随机翻一页
    python flip-book.py --count 3              # 一次翻3页
    python flip-book.py --list                 # 列出所有答案
    python flip-book.py --json                 # JSON格式输出
    python flip-book.py --library 自定义路径.md  # 指定答案库文件
"""

import random
import argparse
import json
import sys
import os


# ========================================
# 答案库文件路径（默认相对于脚本所在目录）
# ========================================

DEFAULT_LIBRARY_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "references", "answers.md"
)


# ========================================
# Markdown 解析器
# ========================================

def parse_answers(filepath):
    """
    解析答案库 Markdown 文件，返回答案列表。

    格式：每行以 "- " 开头的就是一条答案。
    跳过标题行(#)、引用行(>)、分隔线(---)和空行。
    """
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    answers = []
    for line in lines:
        stripped = line.strip()

        # 跳过空行、标题、引用、分隔线
        if not stripped or stripped.startswith("#") or stripped.startswith(">") or stripped.startswith("---"):
            continue

        # 以 "- " 开头的是答案
        if stripped.startswith("- "):
            text = stripped[2:].strip()
            if text:
                answers.append(text)

    return answers


# ========================================
# 随机逻辑
# ========================================

def pick_random(answers, count=1):
    """随机选取答案。"""
    if not answers:
        return []
    return random.sample(answers, min(count, len(answers)))


def format_answer_card(text):
    """将答案格式化为卡片。"""
    return f"""
📖 答案之书

━━━━━━━━━━━━━━━━━━━━

✨ {text}

━━━━━━━━━━━━━━━━━━━━

🔄 要不要再翻一页？
"""


# ========================================
# 主入口
# ========================================

def main():
    parser = argparse.ArgumentParser(
        description="📖 答案之书 — 随机翻书脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python flip-book.py                          # 随机翻一页
  python flip-book.py --count 3                # 一次翻3页
  python flip-book.py --list                   # 列出所有答案
  python flip-book.py --library ./my-answers.md # 使用自定义答案库
        """
    )

    parser.add_argument("--count", type=int, default=1, help="翻几页（默认1页）")
    parser.add_argument("--list", action="store_true", help="列出所有答案")
    parser.add_argument("--json", action="store_true", help="以JSON格式输出")
    parser.add_argument("--library", default=DEFAULT_LIBRARY_PATH, help="答案库 Markdown 文件路径")

    args = parser.parse_args()

    # 解析答案库
    library_path = os.path.abspath(args.library)
    if not os.path.exists(library_path):
        print(f"❌ 找不到答案库文件：{library_path}")
        print("  请确认 references/answers.md 存在，或用 --library 指定路径。")
        sys.exit(1)

    answers = parse_answers(library_path)

    if not answers:
        print("😅 答案库是空的，没解析到任何答案。")
        print("  请检查 Markdown 文件的格式是否正确。")
        sys.exit(1)

    # 列出所有答案
    if args.list:
        print(f"\n📖 答案之书 — 共 {len(answers)} 条\n")
        for i, text in enumerate(answers, 1):
            display = text if len(text) <= 45 else text[:42] + "..."
            print(f"  {i:>2}. {display}")
        print()
        return

    # 随机选取
    picked = pick_random(answers, args.count)

    if args.json:
        output = [{"id": answers.index(a) + 1, "text": a} for a in picked]
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        for a in picked:
            print(format_answer_card(a))


if __name__ == "__main__":
    main()
