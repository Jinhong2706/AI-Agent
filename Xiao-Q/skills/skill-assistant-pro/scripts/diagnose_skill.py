#!/usr/bin/env python3
"""
Skill Structure Probe — 结构探测工具

只采集 LLM 不擅长的事实数据（目录结构、文件清单、Token 估算），
不做任何语义判断。诊断判断全部交给 LLM。

Usage:
    diagnose_skill.py <skill-directory-path>
"""

import sys
import os
import re
import json
from pathlib import Path


def read_file_text(filepath: Path) -> str:
    """Read file content, return empty string on failure."""
    try:
        return filepath.read_text(encoding="utf-8")
    except Exception:
        return ""


def extract_frontmatter(content: str) -> dict:
    """Extract YAML frontmatter from SKILL.md."""
    match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return {}
    fm = {}
    for line in match.group(1).strip().split("\n"):
        if ":" in line:
            key, val = line.split(":", 1)
            fm[key.strip()] = val.strip()
    return fm


def extract_body(content: str) -> str:
    """Extract body (everything after frontmatter)."""
    match = re.match(r"^---\s*\n.*?\n---\s*\n(.*)", content, re.DOTALL)
    return match.group(1) if match else content


def count_tokens_approx(text: str) -> int:
    """Approximate token count (~4 chars/token English, ~2 chars/token Chinese)."""
    chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", text))
    other_chars = len(text) - chinese_chars
    return chinese_chars // 2 + other_chars // 4


def count_lines(text: str) -> int:
    return text.count("\n") + (1 if text and not text.endswith("\n") else 0)


def list_dir_files(directory: Path) -> list[dict]:
    """List files in a directory with basic stats."""
    if not directory.exists():
        return []
    files = []
    for f in sorted(directory.iterdir()):
        if f.is_file() and not f.name.startswith("."):
            content = read_file_text(f)
            files.append({
                "name": f.name,
                "lines": count_lines(content),
                "tokens": count_tokens_approx(content),
            })
    return files


def extract_headings(body: str) -> list[str]:
    """Extract markdown headings to show document structure."""
    return re.findall(r"^(#{1,4}\s+.+)$", body, re.MULTILINE)


def probe_skill(skill_dir_path: str) -> dict:
    """Probe a skill directory and return factual structure data."""
    skill_dir = Path(skill_dir_path).resolve()

    if not skill_dir.exists():
        return {"error": f"Directory not found: {skill_dir}"}

    # --- SKILL.md ---
    skill_md_path = skill_dir / "SKILL.md"
    skill_content = read_file_text(skill_md_path)
    if not skill_content:
        return {"error": "SKILL.md not found or empty"}

    frontmatter = extract_frontmatter(skill_content)
    body = extract_body(skill_content)

    # --- Directory structure ---
    scripts_files = list_dir_files(skill_dir / "scripts")
    references_files = list_dir_files(skill_dir / "references")
    assets_files = list_dir_files(skill_dir / "assets")

    # --- Token budget ---
    body_tokens = count_tokens_approx(body)
    total_prompt_tokens = body_tokens  # SKILL.md body
    for ref in references_files:
        total_prompt_tokens += ref["tokens"]

    return {
        "skill_name": frontmatter.get("name", os.path.basename(skill_dir)),
        "frontmatter": frontmatter,
        "skill_md": {
            "lines": count_lines(skill_content),
            "body_tokens": body_tokens,
            "headings": extract_headings(body),
        },
        "directories": {
            "scripts": scripts_files,
            "references": references_files,
            "assets": assets_files,
        },
        "token_budget": {
            "skill_md_body": body_tokens,
            "references_total": sum(r["tokens"] for r in references_files),
            "estimated_context_load": total_prompt_tokens,
        },
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: diagnose_skill.py <skill-directory-path>")
        print("  Probes a Skill directory and outputs structural facts as JSON.")
        print("  Does NOT make diagnosis judgments — that's the LLM's job.")
        sys.exit(1)

    result = probe_skill(sys.argv[1])
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
