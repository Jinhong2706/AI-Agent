#!/usr/bin/env python3
"""一致性检查 — 读取 .consistency.yml 并执行规则

用法：
    python3 scripts/check_consistency.py

退出码：0 = 全部通过，1 = 有警告或错误
"""

import os
import re
import sys

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read_file(path):
    with open(os.path.join(SKILL_DIR, path), "r", encoding="utf-8") as f:
        return f.read()


def parse_yaml_simple(path):
    """解析 .consistency.yml（简单手写解析器，避免 PyYAML 依赖）
    
    按缩进层级解析 rules 列表中的每条规则。
    """
    with open(path) as f:
        lines = f.readlines()

    rules = []
    current = None
    in_exclude = False

    for line in lines:
        stripped = line.strip()
        # 跳过空行和注释
        if not stripped or stripped.startswith("#"):
            continue

        # 新规则开始
        if stripped.startswith("- id:"):
            if current:
                rules.append(current)
            current = {}
            in_exclude = False
            val = stripped.split("- id:", 1)[1].strip()
            current["id"] = val.strip('"').strip("'")
            continue

        if current is None:
            continue

        # exclude 数组项
        if stripped.startswith('- "'):
            if "exclude" not in current:
                current["exclude"] = []
            current["exclude"].append(stripped.strip('- "').rstrip('"'))
            continue

        # 普通 key: value
        if ":" in stripped:
            key, _, val = stripped.partition(":")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if not val:
                continue
            # 处理 exclude: ["item1", "item2"]
            if key == "exclude":
                items = re.findall(r'"([^"]+)"', val)
                current["exclude"] = items if items else [val]
            else:
                current[key] = val
            continue

        # 多行 exclude 数组项
        if stripped.startswith('- "'):
            if "exclude" not in current:
                current["exclude"] = []
            current["exclude"].append(stripped.strip('- "').rstrip('"'))
            continue

    if current:
        rules.append(current)

    return rules


def run_rule(rule):
    """执行单条规则"""
    rtype = rule.get("type", "")
    rid = rule.get("id", "?")

    # ── count_match ──
    if rtype == "count_match":
        directory = os.path.join(SKILL_DIR, rule.get("dir", ""))
        if not os.path.isdir(directory):
            return "❌", f"{rid}: 目录不存在 ({directory})"

        exclude = set(rule.get("exclude", []))
        glob_raw = rule.get("glob", "*.md")
        suffix = glob_raw.lstrip("*")
        files = [f for f in os.listdir(directory) if f.endswith(suffix) and f not in exclude]
        actual = len(files)

        target = read_file(rule.get("target_file", ""))
        tm = re.search(rule.get("target_pattern", ""), target)
        if not tm:
            return "❌", f"{rid}: 目标模式未匹配"

        declared = int(tm.group(1))
        if actual == declared:
            return "✅", f"{rid}: 一致（{actual}个）"
        else:
            return "❌", f"{rid}: 不一致（磁盘: {actual} ≠ 声明: {declared}）"

    # ── cross_reference ──
    if rtype == "cross_reference":
        source = read_file(rule.get("source_file", ""))
        target = read_file(rule.get("target_file", ""))
        sp = rule.get("source_pattern", "")
        tp = rule.get("target_pattern", "")

        # 源匹配（MULTILINE 让 ^ 匹配每行开头，不止字符串开头）
        sm = re.search(sp, source, re.MULTILINE)
        if not sm:
            return "❌", f"{rid}: 源模式未匹配"

        sg = int(rule.get("source_group", 1))
        try:
            sv = sm.group(sg)
        except IndexError:
            # 无捕获组时用完整匹配
            sv = sm.group(0)

        # 目标匹配
        tms = re.findall(tp, target, re.MULTILINE)
        if not tms:
            return "❌", f"{rid}: 目标模式未匹配"

        tg = int(rule.get("target_group", 1))
        first = tms[0]
        if isinstance(first, tuple):
            try:
                tv = str(first[tg - 1])
            except IndexError:
                tv = str(first[0])
        else:
            tv = str(first)

        if str(sv) == tv:
            return "✅", f"{rid}: 一致（{sv}）"
        else:
            return "❌", f"{rid}: 不一致（源: {sv} ≠ 目标: {tv}）"

    return "❌", f"{rid}: 未知规则类型 '{rtype}'"


def main():
    skill_name = os.path.basename(SKILL_DIR)
    print(f"一致性检查 — {skill_name}")
    print(f"目录：{SKILL_DIR}\n")

    yml_path = os.path.join(SKILL_DIR, ".consistency.yml")
    if not os.path.exists(yml_path):
        print("⚠️  .consistency.yml 不存在")
        sys.exit(0)

    rules = parse_yaml_simple(yml_path)
    if not rules:
        print("⚠️  无规则")
        sys.exit(0)

    passed = 0
    failed = 0
    for rule in rules:
        status, msg = run_rule(rule)
        print(f"  {status} {msg}")
        if status == "✅":
            passed += 1
        else:
            failed += 1

    print(f"\n结果：{passed} 通过 / {failed} 失败")
    sys.exit(1 if failed > 0 else 0)


if __name__ == "__main__":
    main()
