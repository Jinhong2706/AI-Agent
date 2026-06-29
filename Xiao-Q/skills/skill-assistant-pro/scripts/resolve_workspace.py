#!/usr/bin/env python3
"""resolve_workspace.py — 工作区路径解析 + 验证 CLI

防止"凭直觉建 workspace 路径"事故的唯一权威解析入口。
inspect / diagnose / batch_baseline / 加速器在 W.0 步骤必须调本脚本。

用法：
    # 标准用法：解析 sibling_of_skills_dir 布局
    python3 resolve_workspace.py --skill .cursor/skills/foo
    → 输出：.cursor/skills/skill-assistant-workspace/foo

    # 同时验证现有 sibling workspace 模板一致性
    python3 resolve_workspace.py --skill .cursor/skills/foo --check-existing

    # 自定义布局
    python3 resolve_workspace.py --skill .cursor/skills/foo --layout external
    python3 resolve_workspace.py --skill .cursor/skills/foo --layout project_local

    # 仅验证给定路径是否合法（不解析新路径）
    python3 resolve_workspace.py --validate .cursor/skills/foo-workspace
    → exit 1 + 报错（合法路径必须含 skill-assistant-workspace/）

Exit codes:
    0 — 解析或验证通过
    1 — 路径不合法（不在 skill-assistant-workspace/ 下）或 sibling 模板不一致
    2 — CLI 参数错误

设计动机：
    - SKILL.md NEVER 列表强约束：禁止凭直觉拼 <skill>-workspace 这种路径
    - manifest_io.write_manifest_atomic 在写之前会调 validate_workspace_path()
    - 多 module 共用同一段路径解析，避免漂移
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

WORKSPACE_CONTAINER_NAME = "skill-assistant-workspace"


def find_git_root(start: Path) -> Path | None:
    """向上找最近的 .git 目录，找不到返回 None。"""
    cur = start.resolve()
    for parent in [cur, *cur.parents]:
        if (parent / ".git").exists():
            return parent
    return None


def resolve_workspace_path(
    skill_path: Path,
    layout: str = "sibling_of_skills_dir",
    config: dict | None = None,
) -> Path:
    """根据布局策略解析 workspace 绝对路径。

    layout = "sibling_of_skills_dir": skill 父目录同级
    layout = "external":              ~/.skill-assistant/workspaces/<name>-workspace/
    layout = "project_local":         <repo_root>/.skill-doctor/<name>/

    与 references/workspace-layout.md 伪代码 1:1 对齐。
    """
    config = config or {}
    skill_path = Path(skill_path)
    skill_name = skill_path.name
    skills_container = skill_path.parent

    if layout == "sibling_of_skills_dir":
        return skills_container / WORKSPACE_CONTAINER_NAME / skill_name
    if layout == "external":
        root = Path(
            config.get("workspace_root", "~/.skill-assistant/workspaces")
        ).expanduser()
        return root / f"{skill_name}-workspace"
    if layout == "project_local":
        repo_root = find_git_root(skill_path) or Path.cwd()
        return repo_root / ".skill-doctor" / skill_name
    raise ValueError(f"未知 workspace.layout: {layout}（可选 sibling_of_skills_dir / external / project_local）")


def validate_workspace_path(
    path: Path | str,
    layout: str = "sibling_of_skills_dir",
) -> tuple[bool, str]:
    """验证给定路径是否符合 workspace 布局约定。

    返回 (合法?, 原因)。供 manifest_io 在写 manifest_root 前调用。

    sibling_of_skills_dir 模式核心规则：
        - 路径必须包含 `skill-assistant-workspace/` 容器目录（任意层级）
        - 容器目录的子目录名 = skill_name（不能是 <skill>-workspace 这种）

    external / project_local 模式只检查根前缀。
    """
    p = Path(path)
    parts = p.parts

    if layout == "sibling_of_skills_dir":
        if WORKSPACE_CONTAINER_NAME not in parts:
            return (
                False,
                f"路径 {p} 不含容器 `{WORKSPACE_CONTAINER_NAME}/`——可能被错拼成"
                f"`<skill>-workspace/` 之类的非法形式。请用 resolve_workspace.py "
                f"重新解析。",
            )
        idx = parts.index(WORKSPACE_CONTAINER_NAME)
        if idx == len(parts) - 1:
            return (
                False,
                f"路径 {p} 是 workspace 容器根本身，缺少 skill 子目录。"
                f"应为 `<...>/{WORKSPACE_CONTAINER_NAME}/<skill_name>/`。",
            )
        return True, f"OK · sibling_of_skills_dir · skill 子目录 = {parts[idx + 1]}"

    if layout == "external":
        if ".skill-assistant" not in parts and "workspaces" not in parts:
            return (
                False,
                f"external 布局应在 `~/.skill-assistant/workspaces/<name>-workspace/` 下，"
                f"实得 {p}",
            )
        return True, "OK · external"

    if layout == "project_local":
        if ".skill-doctor" not in parts:
            return (
                False,
                f"project_local 布局应在 `<repo_root>/.skill-doctor/<name>/` 下，实得 {p}",
            )
        return True, "OK · project_local"

    return False, f"未知 layout: {layout}"


def check_existing_siblings(workspace_path: Path) -> tuple[bool, str, list[str]]:
    """扫描容器目录下现有 sibling 子目录，确认路径模板一致。

    新建一个 skill 的 workspace 时，把它的"邻居"列出来给用户看，
    防止"我建在容器内，但容器名字拼错了/位置不对"这类错误。

    返回 (一致?, 描述, sibling 列表)。
    """
    container = workspace_path.parent
    if not container.exists():
        return True, f"容器 {container} 不存在（首次建立），无 sibling 可对照", []

    if container.name != WORKSPACE_CONTAINER_NAME:
        return (
            False,
            f"容器名 `{container.name}` 不等于约定 `{WORKSPACE_CONTAINER_NAME}`",
            [],
        )

    siblings = sorted(
        [d.name for d in container.iterdir() if d.is_dir() and not d.name.startswith(".")]
    )
    return True, f"容器 {container} 下现有 {len(siblings)} 个 sibling skill workspace", siblings


def _cli() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--skill", type=Path, help="被评测 skill 的目录路径（如 .cursor/skills/foo）")
    ap.add_argument(
        "--layout",
        choices=("sibling_of_skills_dir", "external", "project_local"),
        default="sibling_of_skills_dir",
        help="workspace 布局策略（默认 sibling_of_skills_dir）",
    )
    ap.add_argument(
        "--check-existing",
        action="store_true",
        help="同时扫现有 sibling workspace 验证路径模板",
    )
    ap.add_argument(
        "--validate",
        type=Path,
        help="仅验证给定路径是否合法（不解析新路径）",
    )
    args = ap.parse_args()

    if args.validate:
        ok, reason = validate_workspace_path(args.validate, args.layout)
        if ok:
            print(f"[resolve_workspace] ✓ {reason}", file=sys.stderr)
            print(args.validate)
            return 0
        print(f"[resolve_workspace] ✗ 路径不合法: {reason}", file=sys.stderr)
        return 1

    if not args.skill:
        ap.error("--skill 或 --validate 至少需要一个")
        return 2

    workspace = resolve_workspace_path(args.skill, args.layout)

    ok, reason = validate_workspace_path(workspace, args.layout)
    if not ok:
        print(
            f"[resolve_workspace] ✗ 解析结果路径不合法（脚本内部 bug 或异常 layout）: {reason}",
            file=sys.stderr,
        )
        return 1

    print(f"[resolve_workspace] ✓ {reason}", file=sys.stderr)

    if args.check_existing:
        consistent, desc, siblings = check_existing_siblings(workspace)
        print(f"[resolve_workspace] {desc}", file=sys.stderr)
        if siblings:
            print(
                f"[resolve_workspace]   邻居 sibling: {', '.join(siblings)}",
                file=sys.stderr,
            )
        if not consistent:
            return 1

    print(workspace)
    return 0


if __name__ == "__main__":
    sys.exit(_cli())
