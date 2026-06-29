#!/usr/bin/env python3
"""Skill本地调试工具 — 模拟OpenClaw加载流程，本地测试Skill"""

import sys
import json
import argparse
import os
import subprocess


def debug_skill(path, input_data):
    """模拟OpenClaw加载并执行Skill"""
    results = []

    # 1. 解析SKILL.md
    skill_md_path = os.path.join(path, "SKILL.md")
    if not os.path.isfile(skill_md_path):
        return {"status": "error", "message": "SKILL.md不存在"}

    with open(skill_md_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 提取front matter
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            fm_text = parts[1]
            # 简单解析YAML front matter
            meta = {}
            for line in fm_text.strip().split("\n"):
                if ":" in line:
                    key, val = line.split(":", 1)
                    meta[key.strip()] = val.strip().strip('"')
            results.append({
                "step": "解析SKILL.md",
                "status": "ok",
                "meta": meta
            })

    # 2. 查找脚本
    scripts_dir = os.path.join(path, "scripts")
    if not os.path.isdir(scripts_dir):
        return {"status": "error", "message": "scripts/目录不存在"}

    py_files = [f for f in os.listdir(scripts_dir) if f.endswith(".py")]
    if not py_files:
        return {"status": "error", "message": "无Python脚本"}

    results.append({
        "step": "发现脚本",
        "status": "ok",
        "scripts": py_files
    })

    # 3. 执行主脚本
    main_script = os.path.join(scripts_dir, "main.py")
    if not os.path.isfile(main_script):
        # 用第一个py文件
        main_script = os.path.join(scripts_dir, py_files[0])

    cmd = ["python3", main_script]
    if input_data:
        cmd.extend(["--input", json.dumps(input_data, ensure_ascii=False)])

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=path
        )

        if proc.returncode == 0:
            # 尝试解析输出为JSON
            try:
                output_data = json.loads(proc.stdout)
            except json.JSONDecodeError:
                output_data = proc.stdout.strip()

            results.append({
                "step": "执行脚本",
                "status": "ok",
                "output": output_data
            })
        else:
            results.append({
                "step": "执行脚本",
                "status": "error",
                "returncode": proc.returncode,
                "stderr": proc.stderr.strip(),
                "stdout": proc.stdout.strip()[:500]
            })

    except subprocess.TimeoutExpired:
        results.append({
            "step": "执行脚本",
            "status": "error",
            "message": "执行超时（30秒）"
        })
    except Exception as e:
        results.append({
            "step": "执行脚本",
            "status": "error",
            "message": str(e)
        })

    # 4. 汇总
    has_error = any(r.get("status") == "error" for r in results)
    return {
        "status": "ok" if not has_error else "error",
        "skill_path": os.path.abspath(path),
        "input": input_data,
        "steps": results
    }


def main():
    parser = argparse.ArgumentParser(description="Skill本地调试工具")
    parser.add_argument("--path", type=str, required=True, help="Skill目录路径")
    parser.add_argument("--input", type=str, default="", help="JSON格式输入参数")
    args = parser.parse_args()

    input_data = {}
    if args.input:
        try:
            input_data = json.loads(args.input)
        except json.JSONDecodeError as e:
            print(json.dumps({"status": "error", "message": f"输入JSON格式错误: {e}"},
                             ensure_ascii=False, indent=2))
            sys.exit(1)

    result = debug_skill(args.path, input_data)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
