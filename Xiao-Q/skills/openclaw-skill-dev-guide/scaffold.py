#!/usr/bin/env python3
"""Skill脚手架工具 — 一键生成完整Skill目录结构"""

import sys
import json
import argparse
import os


SKILL_MD_TEMPLATE = '''---
name: {name}
description: {description}
version: "1.0.0"
updated_at: "{date}"
category: ["开发工具"]
tags: [{tags}]
trigger: ["{trigger}"]
---

# {display_name}

> {description}

## 核心能力

1. **能力1** — 输入什么 → 输出什么
2. **能力2** — 输入什么 → 输出什么

## 交互流程

### 流程1：XXX

1. 用户提供XXX
2. 调用脚本：
   ```bash
   python scripts/main.py --input '{{"arg1": "value1"}}'
   ```
3. 输出结果

## 脚本说明

### scripts/main.py
- 输入：JSON格式参数
- 输出：JSON格式结果
- 逻辑：核心算法说明

## 设计原则
- 工具型>阅读型 — 有脚本、能运算、有输出
- 零依赖 — 纯Python标准库
- 可独立运行 — python scripts/main.py 直接跑
'''

MAIN_PY_TEMPLATE = '''#!/usr/bin/env python3
"""{display_name} — 主脚本"""

import sys
import json
import argparse


def main(args):
    """主逻辑"""
    if args.input:
        data = json.loads(args.input)
    else:
        data = {{}}

    result = process(data)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def process(data):
    """核心处理逻辑"""
    # TODO: 实现你的逻辑
    return {{"status": "ok", "data": data}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="{display_name}")
    parser.add_argument("--input", type=str, help="JSON格式输入参数")
    parser.add_argument("--output", type=str, help="输出文件路径（可选）")
    args = parser.parse_args()
    main(args)
'''

REFERENCES_README = '''# 参考文档

此目录存放技能的参考文档和API规范。

## 文档列表

（在此添加你的参考文档说明）
'''


def create_skill(name, display_name, description, output_dir="."):
    """创建Skill完整目录结构"""
    from datetime import date
    today = str(date.today())

    # 生成标签
    tags = ', '.join([f'"{t.strip()}"' for t in name.split('-')])
    trigger = name.replace('-', ' ')

    # 创建目录结构
    skill_dir = os.path.join(output_dir, name)
    scripts_dir = os.path.join(skill_dir, "scripts")
    refs_dir = os.path.join(skill_dir, "references")

    os.makedirs(scripts_dir, exist_ok=True)
    os.makedirs(refs_dir, exist_ok=True)

    # 写SKILL.md
    skill_md = SKILL_MD_TEMPLATE.format(
        name=name,
        display_name=display_name or name,
        description=description or "请填写技能描述",
        date=today,
        tags=tags,
        trigger=trigger
    )
    with open(os.path.join(skill_dir, "SKILL.md"), "w", encoding="utf-8") as f:
        f.write(skill_md)

    # 写scripts/main.py
    main_py = MAIN_PY_TEMPLATE.format(display_name=display_name or name)
    with open(os.path.join(scripts_dir, "main.py"), "w", encoding="utf-8") as f:
        f.write(main_py)

    # 写references/README.md
    with open(os.path.join(refs_dir, "README.md"), "w", encoding="utf-8") as f:
        f.write(REFERENCES_README)

    result = {
        "status": "ok",
        "message": f"Skill骨架已生成: {skill_dir}/",
        "structure": {
            skill_dir + "/SKILL.md": "技能定义文件",
            scripts_dir + "/main.py": "主脚本",
            refs_dir + "/README.md": "参考文档"
        },
        "next_steps": [
            "1. 编辑 SKILL.md — 填写核心能力和交互流程",
            "2. 编辑 scripts/main.py — 实现核心逻辑",
            "3. 运行 python scripts/validate.py --path ./" + name + " 验证结构",
            "4. 运行 python scripts/main.py --input '{\"test\": 1}' 测试脚本"
        ]
    }
    return result


def main():
    parser = argparse.ArgumentParser(description="Skill脚手架工具")
    parser.add_argument("--name", type=str, required=True, help="技能英文名（小写+短横线）")
    parser.add_argument("--display-name", type=str, default="", help="技能显示名称")
    parser.add_argument("--description", type=str, default="", help="技能描述（80字内）")
    parser.add_argument("--output", type=str, default=".", help="输出目录")
    args = parser.parse_args()

    # 验证name格式
    import re
    if not re.match(r'^[a-z0-9][a-z0-9-]*[a-z0-9]$', args.name):
        result = {"status": "error", "message": f"技能名格式错误: {args.name}，只允许小写英文+数字+短横线"}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(1)

    result = create_skill(args.name, args.display_name, args.description, args.output)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
