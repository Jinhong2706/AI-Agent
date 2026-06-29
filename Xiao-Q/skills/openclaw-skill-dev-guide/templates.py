#!/usr/bin/env python3
"""Skill代码模板库 — 常见功能的即用模板"""

import sys
import json
import argparse
import os


TEMPLATES = {
    "file-io": {
        "name": "文件读写工具",
        "description": "读取/写入/追加文件内容",
        "code": '''#!/usr/bin/env python3
"""文件读写工具"""

import sys
import json
import argparse
import os


def read_file(path, encoding="utf-8"):
    """读取文件内容"""
    with open(path, "r", encoding=encoding) as f:
        return f.read()


def write_file(path, content, encoding="utf-8"):
    """写入文件（覆盖）"""
    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
    with open(path, "w", encoding=encoding) as f:
        f.write(content)


def append_file(path, content, encoding="utf-8"):
    """追加文件"""
    with open(path, "a", encoding=encoding) as f:
        f.write(content)


def main():
    parser = argparse.ArgumentParser(description="文件读写工具")
    parser.add_argument("--action", choices=["read", "write", "append"], required=True)
    parser.add_argument("--path", type=str, required=True, help="文件路径")
    parser.add_argument("--content", type=str, default="", help="写入内容")
    args = parser.parse_args()

    if args.action == "read":
        result = {"status": "ok", "content": read_file(args.path)}
    elif args.action == "write":
        write_file(args.path, args.content)
        result = {"status": "ok", "message": f"已写入: {args.path}"}
    elif args.action == "append":
        append_file(args.path, args.content)
        result = {"status": "ok", "message": f"已追加: {args.path}"}

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
'''
    },

    "http-request": {
        "name": "HTTP请求工具",
        "description": "GET/POST请求（web_fetch风格）",
        "code": '''#!/usr/bin/env python3
"""HTTP请求工具（web_fetch风格）"""

import sys
import json
import argparse
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode


def http_request(url, method="GET", headers=None, data=None, timeout=30):
    """发送HTTP请求"""
    req_headers = headers or {}
    req_data = None

    if data and method == "POST":
        if isinstance(data, dict):
            req_data = json.dumps(data).encode("utf-8")
            req_headers.setdefault("Content-Type", "application/json")
        else:
            req_data = data.encode("utf-8") if isinstance(data, str) else data

    req = Request(url, data=req_data, headers=req_headers, method=method)
    try:
        with urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return {
                "status": "ok",
                "status_code": resp.status,
                "headers": dict(resp.headers),
                "body": body[:50000]  # 限制输出大小
            }
    except HTTPError as e:
        return {"status": "error", "status_code": e.code, "message": str(e)}
    except URLError as e:
        return {"status": "error", "message": f"连接失败: {e.reason}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def main():
    parser = argparse.ArgumentParser(description="HTTP请求工具")
    parser.add_argument("--url", type=str, required=True, help="请求URL")
    parser.add_argument("--method", type=str, default="GET", help="请求方法")
    parser.add_argument("--headers", type=str, default="{}", help="请求头JSON")
    parser.add_argument("--data", type=str, default="", help="请求体")
    args = parser.parse_args()

    headers = json.loads(args.headers) if args.headers else {}
    data = json.loads(args.data) if args.data else None

    result = http_request(args.url, args.method, headers, data)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
'''
    },

    "data-process": {
        "name": "数据清洗/转换工具",
        "description": "JSON数据清洗、格式转换、字段提取",
        "code": '''#!/usr/bin/env python3
"""数据清洗/转换工具"""

import sys
import json
import argparse
import re


def clean_data(data, rules):
    """根据规则清洗数据"""
    if isinstance(data, list):
        return [clean_item(item, rules) for item in data]
    elif isinstance(data, dict):
        return clean_item(data, rules)
    return data


def clean_item(item, rules):
    """清洗单条数据"""
    result = {}

    # 字段提取
    if "pick" in rules:
        for field in rules["pick"]:
            if field in item:
                result[field] = item[field]
    else:
        result = dict(item)

    # 字段重命名
    if "rename" in rules:
        for old_name, new_name in rules["rename"].items():
            if old_name in result:
                result[new_name] = result.pop(old_name)

    # 字段过滤（移除空值）
    if rules.get("drop_null"):
        result = {k: v for k, v in result.items() if v is not None and v != ""}

    # 字符串清洗
    if rules.get("strip_strings"):
        for k, v in result.items():
            if isinstance(v, str):
                result[k] = v.strip()

    return result


def main():
    parser = argparse.ArgumentParser(description="数据清洗/转换工具")
    parser.add_argument("--input", type=str, required=True, help="输入数据JSON")
    parser.add_argument("--rules", type=str, default="{}", help="清洗规则JSON")
    args = parser.parse_args()

    data = json.loads(args.input)
    rules = json.loads(args.rules)

    result = {
        "status": "ok",
        "input_count": len(data) if isinstance(data, list) else 1,
        "output": clean_data(data, rules)
    }

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
'''
    },

    "report-gen": {
        "name": "报告生成工具",
        "description": "Markdown格式报告生成",
        "code": '''#!/usr/bin/env python3
"""报告生成工具（Markdown输出）"""

import sys
import json
import argparse
from datetime import date


def generate_report(title, sections, output_path=None):
    """生成Markdown格式报告"""
    lines = []
    lines.append(f"# {title}")
    lines.append(f"\n> 生成日期: {date.today()}\n")

    for section in sections:
        heading = section.get("heading", "")
        level = section.get("level", 2)
        prefix = "#" * level
        lines.append(f"\n{prefix} {heading}\n")

        content = section.get("content", "")
        if isinstance(content, str):
            lines.append(content)
        elif isinstance(content, list):
            # 表格
            if content and isinstance(content[0], dict):
                headers = list(content[0].keys())
                lines.append("| " + " | ".join(headers) + " |")
                lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
                for row in content:
                    lines.append("| " + " | ".join(str(row.get(h, "")) for h in headers) + " |")
            else:
                for item in content:
                    lines.append(f"- {item}")

        lines.append("")

    report = "\n".join(lines)

    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report)
        return {"status": "ok", "message": f"报告已生成: {output_path}", "length": len(report)}
    else:
        return {"status": "ok", "report": report, "length": len(report)}


def main():
    parser = argparse.ArgumentParser(description="报告生成工具")
    parser.add_argument("--input", type=str, required=True, help="报告数据JSON")
    parser.add_argument("--output", type=str, default="", help="输出文件路径")
    args = parser.parse_args()

    data = json.loads(args.input)
    title = data.get("title", "报告")
    sections = data.get("sections", [])

    result = generate_report(title, sections, args.output or None)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
'''
    },

    "cli-parser": {
        "name": "命令行参数解析工具",
        "description": "标准化的CLI参数解析模板",
        "code": '''#!/usr/bin/env python3
"""命令行参数解析工具 — 标准模板"""

import sys
import json
import argparse


def parse_and_execute(args):
    """解析参数并执行逻辑"""
    result = {
        "status": "ok",
        "command": args.command,
        "params": {
            k: v for k, v in vars(args).items()
            if k != "command" and v is not None
        }
    }

    # 根据command分发
    if args.command == "run":
        result["output"] = execute_run(args)
    elif args.command == "check":
        result["output"] = execute_check(args)
    elif args.command == "list":
        result["output"] = execute_list(args)
    else:
        result["status"] = "error"
        result["message"] = f"未知命令: {args.command}"

    return result


def execute_run(args):
    """执行run命令"""
    return {"message": "执行完成", "input": args.input}


def execute_check(args):
    """执行check命令"""
    return {"message": "检查完成", "target": args.target}


def execute_list(args):
    """执行list命令"""
    return {"message": "列表完成", "items": []}


def main():
    parser = argparse.ArgumentParser(description="命令行工具模板")
    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # run子命令
    run_parser = subparsers.add_parser("run", help="执行")
    run_parser.add_argument("--input", type=str, help="输入JSON")

    # check子命令
    check_parser = subparsers.add_parser("check", help="检查")
    check_parser.add_argument("--target", type=str, help="检查目标")

    # list子命令
    list_parser = subparsers.add_parser("list", help="列表")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    result = parse_and_execute(args)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
'''
    }
}


def main():
    parser = argparse.ArgumentParser(description="Skill代码模板库")
    parser.add_argument("--list", action="store_true", help="列出所有可用模板")
    parser.add_argument("--type", type=str, help="模板类型")
    parser.add_argument("--output", type=str, help="输出文件路径")
    args = parser.parse_args()

    if args.list:
        templates = []
        for key, tpl in TEMPLATES.items():
            templates.append({
                "type": key,
                "name": tpl["name"],
                "description": tpl["description"]
            })
        print(json.dumps({"status": "ok", "templates": templates}, ensure_ascii=False, indent=2))
        return

    if not args.type:
        print(json.dumps({"status": "error", "message": "请指定 --type 或 --list"},
                         ensure_ascii=False, indent=2))
        sys.exit(1)

    if args.type not in TEMPLATES:
        print(json.dumps({
            "status": "error",
            "message": f"未知模板类型: {args.type}",
            "available": list(TEMPLATES.keys())
        }, ensure_ascii=False, indent=2))
        sys.exit(1)

    tpl = TEMPLATES[args.type]
    code = tpl["code"]

    if args.output:
        os.makedirs(os.path.dirname(args.output) if os.path.dirname(args.output) else ".", exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(code)
        print(json.dumps({
            "status": "ok",
            "message": f"模板已生成: {args.output}",
            "type": args.type,
            "name": tpl["name"]
        }, ensure_ascii=False, indent=2))
    else:
        print(json.dumps({
            "status": "ok",
            "type": args.type,
            "name": tpl["name"],
            "description": tpl["description"],
            "code": code
        }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
