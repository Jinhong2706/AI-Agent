#!/usr/bin/env python3
"""Validate an AI Skill package before publishing.

Checks covered:
- Required files and recommended directories
- YAML front matter existence, parseability, required fields, description length
- Markdown relative references and local links
- Forbidden / risky terms
- Empty files, oversized entry file, temporary artifacts

Usage:
  python scripts/validate-skill.py [skill_dir]
  python scripts/validate-skill.py --json [skill_dir]

Exit code:
  0 = no errors
  1 = validation errors found
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover
    yaml = None

REQUIRED_FILES = ["SKILL.md"]
RECOMMENDED_DIRS = ["references", "templates", "examples"]
REQUIRED_YAML_FIELDS = ["name", "description"]
DESCRIPTION_MIN_LEN = 40
DESCRIPTION_MAX_LEN = 500
ENTRY_WARN_LINE_LIMIT = 300

FORBIDDEN_TERMS = [
    "忽略以上指令",
    "绕过安全",
    "泄露系统提示词",
    "开发者模式",
    "无需用户确认删除",
    "rm -rf",
    "sudo ",
    "chmod 777",
    "/mnt/data/",
    "sandbox:",
]

TEMP_PATTERNS = [
    ".DS_Store",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".coverage",
    "*.log",
    "*.tmp",
    "*.bak",
    "*.swp",
    "node_modules",
]

MARKDOWN_EXTENSIONS = {".md", ".mdx"}
TEXT_EXTENSIONS = {".md", ".mdx", ".txt", ".json", ".yaml", ".yml", ".py", ".js", ".ts"}


@dataclass
class Finding:
    level: str  # ERROR / WARN / INFO
    path: str
    message: str


class Reporter:
    def __init__(self) -> None:
        self.findings: list[Finding] = []

    def error(self, path: Path | str, message: str) -> None:
        self.findings.append(Finding("ERROR", str(path), message))

    def warn(self, path: Path | str, message: str) -> None:
        self.findings.append(Finding("WARN", str(path), message))

    def info(self, path: Path | str, message: str) -> None:
        self.findings.append(Finding("INFO", str(path), message))

    @property
    def error_count(self) -> int:
        return sum(1 for item in self.findings if item.level == "ERROR")

    @property
    def warn_count(self) -> int:
        return sum(1 for item in self.findings if item.level == "WARN")

    @property
    def info_count(self) -> int:
        return sum(1 for item in self.findings if item.level == "INFO")

    def to_dict(self, root: Path | None = None) -> dict:
        return {
            "tool": "validate-skill",
            "schema_version": "1.0",
            "root": str(root) if root else None,
            "summary": {
                "errors": self.error_count,
                "warnings": self.warn_count,
                "infos": self.info_count,
                "total": len(self.findings),
                "passed": self.error_count == 0,
            },
            "findings": [
                {"level": item.level, "path": item.path, "message": item.message}
                for item in self.findings
            ],
        }

    def print_report(self) -> None:
        for item in self.findings:
            print(f"[{item.level}] {item.path}: {item.message}")
        print(json.dumps({"errors": self.error_count, "warnings": self.warn_count}, ensure_ascii=False))

    def print_json(self, root: Path | None = None) -> None:
        print(json.dumps(self.to_dict(root), ensure_ascii=False, indent=2))


def rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def iter_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if path.is_file():
            yield path


def extract_front_matter(text: str) -> tuple[str | None, str]:
    if not text.startswith("---\n"):
        return None, text
    end = text.find("\n---", 4)
    if end == -1:
        return None, text
    front = text[4:end].strip()
    body = text[end + len("\n---") :]
    return front, body


def validate_structure(root: Path, reporter: Reporter) -> None:
    for filename in REQUIRED_FILES:
        path = root / filename
        if not path.exists():
            reporter.error(filename, "缺少必需文件")
        elif path.stat().st_size == 0:
            reporter.error(filename, "文件为空")

    for dirname in RECOMMENDED_DIRS:
        path = root / dirname
        if not path.exists():
            reporter.warn(dirname, "建议补充该目录以支持渐进式加载和复用")
        elif not path.is_dir():
            reporter.error(dirname, "应为目录而不是文件")

    for pattern in TEMP_PATTERNS:
        for path in root.rglob(pattern):
            reporter.warn(rel(path, root), "发现运行态、缓存或临时产物，发布前建议移除")


def validate_front_matter(root: Path, reporter: Reporter) -> None:
    skill_path = root / "SKILL.md"
    if not skill_path.exists():
        return

    text = read_text(skill_path)
    front, _body = extract_front_matter(text)
    if front is None:
        reporter.error("SKILL.md", "缺少 YAML front matter 或未正确闭合")
        return
    if yaml is None:
        reporter.error("SKILL.md", "当前环境缺少 PyYAML，无法解析 YAML")
        return

    try:
        data = yaml.safe_load(front)
    except Exception as exc:  # noqa: BLE001
        reporter.error("SKILL.md", f"YAML 解析失败：{exc}")
        return

    if not isinstance(data, dict):
        reporter.error("SKILL.md", "YAML front matter 必须是对象结构")
        return

    for field in REQUIRED_YAML_FIELDS:
        value = data.get(field)
        if not isinstance(value, str) or not value.strip():
            reporter.error("SKILL.md", f"缺少必需 YAML 字段：{field}")

    name = data.get("name")
    if isinstance(name, str) and not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,62}[a-z0-9]", name):
        reporter.warn("SKILL.md", "name 建议使用小写字母、数字和连字符，长度 3-64")

    description = data.get("description")
    if isinstance(description, str):
        desc_len = len(description.strip())
        if desc_len < DESCRIPTION_MIN_LEN:
            reporter.warn("SKILL.md", f"description 偏短（{desc_len} 字），建议不少于 {DESCRIPTION_MIN_LEN} 字")
        if desc_len > DESCRIPTION_MAX_LEN:
            reporter.warn("SKILL.md", f"description 偏长（{desc_len} 字），建议不超过 {DESCRIPTION_MAX_LEN} 字")
        if ": " in description and not (front.find(f'description: "{description}"') >= 0 or front.find(f"description: '{description}'") >= 0):
            reporter.warn("SKILL.md", "description 含英文冒号加空格时建议加引号，避免 YAML 歧义")


def validate_markdown_links(root: Path, reporter: Reporter) -> None:
    link_pattern = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)|!\[[^\]]*\]\(([^)]+)\)")

    for path in iter_files(root):
        if path.suffix.lower() not in MARKDOWN_EXTENSIONS:
            continue
        text = read_text(path)
        for match in link_pattern.finditer(text):
            target = match.group(1) or match.group(2) or ""
            clean = target.strip().split("#", 1)[0].split("?", 1)[0]
            if not clean or re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", clean):
                continue
            if clean.startswith("/"):
                reporter.warn(rel(path, root), f"引用使用绝对路径：{target}")
                continue
            resolved = (path.parent / clean).resolve()
            try:
                resolved.relative_to(root.resolve())
            except ValueError:
                reporter.error(rel(path, root), f"引用路径越出技能包目录：{target}")
                continue
            if not resolved.exists():
                reporter.error(rel(path, root), f"引用文件不存在：{target}")


def validate_content(root: Path, reporter: Reporter) -> None:
    skill_path = root / "SKILL.md"
    if skill_path.exists():
        line_count = len(read_text(skill_path).splitlines())
        if line_count > ENTRY_WARN_LINE_LIMIT:
            reporter.warn("SKILL.md", f"入口文档 {line_count} 行，建议拆分到 references/examples 以支持渐进式加载")

    for path in iter_files(root):
        relative = rel(path, root)
        if path.stat().st_size == 0:
            reporter.warn(relative, "空文件，确认是否需要保留")
        if path.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        try:
            text = read_text(path)
        except UnicodeDecodeError:
            reporter.warn(relative, "文本文件无法按 UTF-8 读取")
            continue
        if relative == "scripts/validate-skill.py":
            continue
        for term in FORBIDDEN_TERMS:
            if term in text:
                reporter.error(relative, f"发现禁用词或高风险片段：{term}")


def validate_package(root: Path) -> Reporter:
    reporter = Reporter()
    if not root.exists():
        reporter.error(str(root), "技能目录不存在")
        return reporter
    if not root.is_dir():
        reporter.error(str(root), "目标路径不是目录")
        return reporter

    validate_structure(root, reporter)
    validate_front_matter(root, reporter)
    validate_markdown_links(root, reporter)
    validate_content(root, reporter)
    return reporter


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate an AI Skill package.")
    parser.add_argument("skill_dir", nargs="?", default=".", help="Skill package root directory")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON for CI or batch audit pipelines")
    args = parser.parse_args(argv)

    root = Path(args.skill_dir).resolve()
    reporter = validate_package(root)
    if args.json:
        reporter.print_json(root)
    else:
        reporter.print_report()
    return 1 if reporter.error_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
