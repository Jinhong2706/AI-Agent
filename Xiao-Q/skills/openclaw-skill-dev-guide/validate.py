#!/usr/bin/env python3
"""Skill结构验证工具 — 检查Skill目录是否符合OpenClaw规范"""

import sys
import json
import argparse
import os
import re


def validate_skill(path):
    """验证Skill结构，返回检查结果列表"""
    results = []

    # 1. 检查目录存在
    if not os.path.isdir(path):
        return [{"check": "目录存在", "status": "fail", "message": f"目录不存在: {path}"}]

    # 2. 检查SKILL.md
    skill_md_path = os.path.join(path, "SKILL.md")
    if not os.path.isfile(skill_md_path):
        results.append({"check": "SKILL.md存在", "status": "fail", "message": "缺少SKILL.md文件"})
    else:
        results.append({"check": "SKILL.md存在", "status": "pass"})
        # 检查front matter
        with open(skill_md_path, "r", encoding="utf-8") as f:
            content = f.read()

        if not content.startswith("---"):
            results.append({"check": "Front Matter格式", "status": "fail", "message": "SKILL.md缺少front matter (---)"})
        else:
            # 提取front matter
            parts = content.split("---", 2)
            if len(parts) < 3:
                results.append({"check": "Front Matter格式", "status": "fail", "message": "front matter未正确关闭"})
            else:
                fm = parts[1]
                # 检查必填字段
                required_fields = ["name", "description", "version"]
                for field in required_fields:
                    if f"{field}:" in fm:
                        results.append({"check": f"必填字段: {field}", "status": "pass"})
                    else:
                        results.append({"check": f"必填字段: {field}", "status": "fail", "message": f"缺少必填字段: {field}"})

                # 检查name格式
                name_match = re.search(r'name:\s*(.+)', fm)
                if name_match:
                    name = name_match.group(1).strip().strip('"')
                    if re.match(r'^[a-z0-9][a-z0-9-]*[a-z0-9]$', name):
                        results.append({"check": "name格式", "status": "pass", "message": name})
                    else:
                        results.append({"check": "name格式", "status": "warn", "message": f"{name} 不符合小写+短横线规范"})

        # 检查是否有脚本调用（区分阅读型vs工具型）
        if "scripts/" in content or "python" in content:
            results.append({"check": "工具型Skill", "status": "pass", "message": "包含脚本调用"})
        else:
            results.append({"check": "工具型Skill", "status": "fail", "message": "无脚本调用，属于阅读型Skill（0分）"})

    # 3. 检查scripts目录
    scripts_dir = os.path.join(path, "scripts")
    if not os.path.isdir(scripts_dir):
        results.append({"check": "scripts/目录", "status": "fail", "message": "缺少scripts/目录"})
    else:
        py_files = [f for f in os.listdir(scripts_dir) if f.endswith(".py")]
        if py_files:
            results.append({"check": "scripts/目录", "status": "pass", "message": f"{len(py_files)}个Python脚本"})
        else:
            results.append({"check": "scripts/目录", "status": "fail", "message": "scripts/目录为空，无Python脚本"})

    # 4. 检查敏感信息
    all_files = []
    for root, dirs, files in os.walk(path):
        for f in files:
            all_files.append(os.path.join(root, f))

    sensitive_patterns = [
        (r'sk_[a-zA-Z0-9]{20,}', 'API Key硬编码'),
        (r'password\s*[:=]\s*["\'][^"\']+["\']', '密码硬编码'),
        (r'token\s*[:=]\s*["\'][^"\']+["\']', 'Token硬编码'),
    ]

    for fpath in all_files:
        try:
            with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            for pattern, desc in sensitive_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    results.append({
                        "check": f"敏感信息: {desc}",
                        "status": "fail",
                        "message": f"在 {os.path.relpath(fpath, path)} 中发现{desc}"
                    })
        except:
            pass

    # 5. 检查文件大小
    total_size = 0
    for fpath in all_files:
        size = os.path.getsize(fpath)
        total_size += size
        if size > 50 * 1024:
            results.append({
                "check": "文件大小",
                "status": "warn",
                "message": f"{os.path.relpath(fpath, path)} 超过50KB ({size//1024}KB)"
            })

    if total_size > 5 * 1024 * 1024:
        results.append({
            "check": "总包大小",
            "status": "fail",
            "message": f"总大小{total_size//1024//1024}MB，超过5MB限制"
        })
    else:
        results.append({"check": "总包大小", "status": "pass", "message": f"{total_size//1024}KB"})

    return results


def main():
    parser = argparse.ArgumentParser(description="Skill结构验证工具")
    parser.add_argument("--path", type=str, required=True, help="Skill目录路径")
    args = parser.parse_args()

    results = validate_skill(args.path)

    pass_count = sum(1 for r in results if r["status"] == "pass")
    fail_count = sum(1 for r in results if r["status"] == "fail")
    warn_count = sum(1 for r in results if r["status"] == "warn")

    output = {
        "status": "ok" if fail_count == 0 else "fail",
        "summary": {
            "pass": pass_count,
            "fail": fail_count,
            "warn": warn_count,
            "total": len(results)
        },
        "results": results
    }

    print(json.dumps(output, ensure_ascii=False, indent=2))
    if fail_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
