#!/usr/bin/env python3
"""Minimal Backend Forge write gate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


IMPLEMENTATION_SUFFIXES = (".java", ".kt", ".py", ".sql")
CONFIG_NAMES = ("pom.xml", "build.gradle", "build.gradle.kts", "pyproject.toml", "requirements.txt", "alembic.ini")


def read_session(project_root: Path) -> dict[str, str]:
    path = project_root / ".backend-forge/session.md"
    if not path.exists():
        return {}
    data: dict[str, str] = {"_path": str(path)}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("- ") and "：" in line:
            key, value = line[2:].split("：", 1)
            data[key.strip()] = value.strip()
    return data


def classify_target(path: str) -> str:
    normalized = path.replace("\\", "/").lower()
    name = normalized.rsplit("/", 1)[-1]
    if name in CONFIG_NAMES or normalized.endswith(CONFIG_NAMES):
        return "config"
    if "/test/" in normalized or normalized.startswith("tests/") or normalized.endswith(("_test.py", "test.py")):
        return "test"
    if normalized.endswith(IMPLEMENTATION_SUFFIXES):
        return "implementation"
    if normalized.endswith((".md", ".txt", ".yaml", ".yml", ".json")):
        return "metadata"
    return "other"


def result(decision: str, gate: str, reason: str, target_kind: str, session: dict[str, str]) -> dict[str, object]:
    return {
        "decision": decision,
        "gate": gate,
        "reason": reason,
        "target_kind": target_kind,
        "phase": session.get("当前阶段", "-"),
        "mode": session.get("当前模式", "-"),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--target-path", required=True)
    parser.add_argument("--mode", choices={"observe", "enforce"}, default="enforce")
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    target_kind = classify_target(args.target_path)
    session = read_session(root)
    blocking: list[tuple[str, str]] = []

    if target_kind not in {"implementation", "config"}:
        print(json.dumps(result("allow", "G00", "target not gated", target_kind, session), ensure_ascii=False))
        return 0

    if not session:
        blocking.append(("G01", "session missing; run scripts/bf_session.sh init before backend implementation writes"))
    else:
        phase = session.get("当前阶段", "-")
        if phase not in {"S4", "C4", "A6"}:
            blocking.append(("G05", f"phase {phase} is not an implementation phase"))
        for label in ("目标状态", "架构状态", "数据影响状态", "安全边界状态", "测试闭环状态"):
            if session.get(label) != "已确认":
                blocking.append(("G10", f"{label} not confirmed"))
                break
        if session.get("当前子单元", "-") == "-" or session.get("子单元状态") not in {"已冻结", "实现中", "待验证"}:
            blocking.append(("G11", "current work unit is not frozen"))
        if session.get("改动契约", "-") == "-" or session.get("确认状态") != "用户已确认":
            blocking.append(("G15", "change contract is missing or unconfirmed"))

    if not blocking:
        print(json.dumps(result("allow", "G00", "all backend gates passed", target_kind, session), ensure_ascii=False))
        return 0

    gate, reason = blocking[0]
    decision = "would_block" if args.mode == "observe" else "block"
    print(json.dumps(result(decision, gate, reason, target_kind, session), ensure_ascii=False))
    return 0 if decision == "would_block" else 2


if __name__ == "__main__":
    raise SystemExit(main())
