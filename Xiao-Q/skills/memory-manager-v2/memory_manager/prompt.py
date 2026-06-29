# -*- coding: utf-8 -*-
"""
记忆管家 V3.0 - Prompt 模板管理（轻量方案）
V3.0+ 新增：支持在 .workbuddy/memory/ 中以 PROMPT_ 前缀管理 Prompt 模板

模板文件格式（Markdown + front-matter）:
    ---
    tags: [代码审查, 重构]
    version: 2
    description: "代码审查提示词模板"
    ---
    # 代码审查 Prompt
    请对以下代码进行审查...
"""

import json
from datetime import datetime
from pathlib import Path

from .config import (
    VERSION, _, get_colors,
    is_symlink, safe_file_read, get_file_info, parse_front_matter,
    iter_memory_files,
)


PROMPT_PREFIX = "PROMPT_"
PROMPT_INDEX_FILE = "prompt_index.json"


def _is_prompt_file(md_file):
    """判断是否为 Prompt 模板文件"""
    return md_file.name.startswith(PROMPT_PREFIX) and md_file.suffix == ".md"


def list_prompts(workspace_path, tag=None):
    """列出所有 Prompt 模板

    Args:
        workspace_path: 工作空间路径
        tag: 可选标签过滤

    Returns:
        dict: {prompts: [{name, tags, version, description, modified, size_kb}], total}
    """
    base_path = Path(workspace_path).resolve()
    memory_path = base_path / ".workbuddy" / "memory"

    result = {
        "version": VERSION,
        "timestamp": datetime.now().isoformat(),
        "prompts": [],
        "total": 0
    }

    if not memory_path.exists():
        result["error"] = _("memory_dir_not_exist")
        return result

    for md_file, mtime, size_kb, rel_path in iter_memory_files(
            memory_path, skip_memory_md=True):
        if not _is_prompt_file(md_file):
            continue

        content, _ = safe_file_read(md_file)
        fm = parse_front_matter(content) if content else {}

        file_tags = fm.get("tags", [])

        # 标签过滤
        if tag and not any(t.lower() == tag.lower() for t in file_tags):
            continue

        prompt_info = {
            "name": md_file.stem,  # PROMPT_xxx
            "file": md_file.name,
            "path": rel_path,
            "tags": file_tags,
            "version": fm.get("version", 1),
            "description": fm.get("description", ""),
            "category": fm.get("category", ""),
            "modified": mtime.strftime("%Y-%m-%d"),
            "size_kb": round(size_kb, 2),
        }

        result["prompts"].append(prompt_info)
        result["total"] += 1

    result["prompts"].sort(key=lambda x: x["modified"], reverse=True)
    return result


def get_prompt(workspace_path, name):
    """获取 Prompt 模板内容

    Args:
        workspace_path: 工作空间路径
        name: 模板名称（不含 PROMPT_ 前缀也可）

    Returns:
        dict: {name, content, tags, version, description}
    """
    base_path = Path(workspace_path).resolve()
    memory_path = base_path / ".workbuddy" / "memory"

    # 自动补全 PROMPT_ 前缀
    if not name.startswith(PROMPT_PREFIX):
        name = PROMPT_PREFIX + name

    result = {
        "version": VERSION,
        "name": name,
        "found": False,
    }

    # 在 memory/ 及子目录中查找
    target_file = None
    if memory_path.exists():
        for md_file, mtime, size_kb, rel_path in iter_memory_files(
                memory_path, skip_memory_md=True):
            if md_file.stem == name or md_file.name == f"{name}.md":
                target_file = md_file
                break

    if target_file is None:
        result["error"] = _("file_not_exist").format(name=name)
        return result

    content, _ = safe_file_read(target_file)
    if content is None:
        result["error"] = _("read_failed").format(name=name)
        return result

    fm = parse_front_matter(content)

    # 去除 front-matter 部分，返回纯 Prompt 内容
    body = content
    if content.startswith("---"):
        try:
            end = content.index("---", 3)
            body = content[end + 3:].strip()
        except ValueError:
            pass

    result["found"] = True
    result["content"] = body
    result["tags"] = fm.get("tags", [])
    result["version"] = fm.get("version", 1)
    result["description"] = fm.get("description", "")
    result["category"] = fm.get("category", "")
    result["file"] = target_file.name
    result["path"] = str(target_file.relative_to(memory_path)) if target_file.is_relative_to(memory_path) else target_file.name

    return result


def save_prompt(workspace_path, name, content, tags=None, description="", category=""):
    """保存 Prompt 模板

    Args:
        workspace_path: 工作空间路径
        name: 模板名称（不含 PROMPT_ 前缀也可）
        content: Prompt 内容
        tags: 标签列表
        description: 描述
        category: 分类

    Returns:
        dict: {name, file, saved, version}
    """
    base_path = Path(workspace_path).resolve()
    memory_path = base_path / ".workbuddy" / "memory"

    # 自动补全 PROMPT_ 前缀
    if not name.startswith(PROMPT_PREFIX):
        name = PROMPT_PREFIX + name

    memory_path.mkdir(parents=True, exist_ok=True)

    # 子目录支持：category 作为子目录
    target_dir = memory_path
    if category:
        target_dir = memory_path / category
        target_dir.mkdir(parents=True, exist_ok=True)

    target_file = target_dir / f"{name}.md"

    # 检查是否已存在 → 版本递增
    version = 1
    if target_file.exists():
        old_content, _ = safe_file_read(target_file)
        if old_content:
            old_fm = parse_front_matter(old_content)
            version = int(old_fm.get("version", 1)) + 1

    # 构建 front-matter
    fm_lines = ["---"]
    if tags:
        fm_lines.append(f"tags: [{', '.join(tags)}]")
    if description:
        fm_lines.append(f'description: "{description}"')
    if category:
        fm_lines.append(f"category: {category}")
    fm_lines.append(f"version: {version}")
    fm_lines.append("---")

    full_content = "\n".join(fm_lines) + "\n\n" + content

    try:
        target_file.write_text(full_content, encoding="utf-8")
    except (OSError, IOError, PermissionError) as e:
        return {"error": str(e), "saved": False}

    return {
        "name": name,
        "file": target_file.name,
        "saved": True,
        "version": version,
        "tags": tags or [],
        "description": description,
        "category": category,
    }


def search_prompts(workspace_path, keyword=None, tag=None):
    """搜索 Prompt 模板（关键词 + 标签）

    Args:
        workspace_path: 工作空间路径
        keyword: 可选关键词搜索
        tag: 可选标签过滤

    Returns:
        dict: {prompts: [...], total}
    """
    base_path = Path(workspace_path).resolve()
    memory_path = base_path / ".workbuddy" / "memory"

    result = {
        "version": VERSION,
        "timestamp": datetime.now().isoformat(),
        "keyword": keyword,
        "tag": tag,
        "prompts": [],
        "total": 0
    }

    if not memory_path.exists():
        result["error"] = _("memory_dir_not_exist")
        return result

    keyword_lower = keyword.lower() if keyword else ""

    for md_file, mtime, size_kb, rel_path in iter_memory_files(
            memory_path, skip_memory_md=True):
        if not _is_prompt_file(md_file):
            continue

        content, _ = safe_file_read(md_file)
        fm = parse_front_matter(content) if content else {}
        file_tags = fm.get("tags", [])

        # 标签过滤
        if tag and not any(t.lower() == tag.lower() for t in file_tags):
            continue

        # 关键词搜索
        score = 0
        if keyword_lower:
            name_lower = md_file.name.lower()
            desc = fm.get("description", "").lower()
            content_lower = (content or "").lower()

            if keyword_lower in name_lower:
                score += 20
            if keyword_lower in desc:
                score += 15
            if keyword_lower in " ".join(file_tags).lower():
                score += 25
            if keyword_lower in content_lower:
                score += 5

            if score == 0:
                continue

        result["prompts"].append({
            "name": md_file.stem,
            "file": md_file.name,
            "path": rel_path,
            "tags": file_tags,
            "version": fm.get("version", 1),
            "description": fm.get("description", ""),
            "category": fm.get("category", ""),
            "score": score,
            "modified": mtime.strftime("%Y-%m-%d"),
            "size_kb": round(size_kb, 2),
        })

    result["prompts"].sort(key=lambda x: x.get("score", 0), reverse=True)
    result["total"] = len(result["prompts"])
    return result
