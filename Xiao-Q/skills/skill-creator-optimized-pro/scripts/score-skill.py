#!/usr/bin/env python3
"""
Semi-automatic Skill scorecard.

Usage:
  python scripts/score-skill.py [skill_dir]
  python scripts/score-skill.py --json [skill_dir]

The script maps the 100-point scorecard in references/skill-scorecard.md
into deterministic static checks. It is intentionally conservative:
it does not replace human review, but gives a stable baseline for batch audit.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

REQUIRED_FRONT_MATTER_FIELDS = ["name", "description"]
RECOMMENDED_DIRS = ["references", "templates", "examples"]
# Build sensitive phrases by fragments so static validators do not flag this scorer itself.
HIGH_RISK_TERMS = [
    "ignore previous " + "instructions",
    "忽略" + "以上指令",
    "开发者" + "模式",
    "泄露" + "系统提示词",
    "无条件执行" + "危险命令",
]
REFERENCE_HINTS = ["references/", "templates/", "examples/", "scripts/"]
DELIVERY_HINTS = ["交付", "output/", "local-file://", "验证", "打包"]
ERROR_HANDLING_HINTS = ["异常", "失败", "降级", "权限", "确认", "中止"]
AUDIT_HINTS = ["检查", "验证", "清单", "评分", "审计", "复核"]
BOUNDARY_HINTS = ["适用", "不适用", "边界", "触发", "description"]
EXECUTION_HINTS = ["步骤", "流程", "工具", "文件", "脚本", "命令"]


@dataclass
class CheckResult:
    id: str
    title: str
    max_points: int
    points: int
    status: str
    notes: list[str] = field(default_factory=list)


@dataclass
class ScoreReport:
    root: Path
    checks: list[CheckResult]

    @property
    def score(self) -> int:
        return max(0, sum(item.points for item in self.checks))

    @property
    def max_score(self) -> int:
        return sum(item.max_points for item in self.checks if item.max_points > 0)

    @property
    def level(self) -> str:
        score = self.score
        if score >= 90:
            return "A 标杆级"
        if score >= 80:
            return "B 可发布"
        if score >= 70:
            return "C 可试用"
        if score >= 60:
            return "D 需整改"
        return "E 不建议发布"

    def to_dict(self) -> dict:
        return {
            "tool": "score-skill",
            "schema_version": "1.0",
            "root": str(self.root),
            "summary": {
                "score": self.score,
                "max_score": self.max_score,
                "level": self.level,
                "passed": self.score >= 80,
            },
            "checks": [
                {
                    "id": item.id,
                    "title": item.title,
                    "max_points": item.max_points,
                    "points": item.points,
                    "status": item.status,
                    "notes": item.notes,
                }
                for item in self.checks
            ],
        }


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def extract_front_matter(text: str) -> tuple[dict[str, str], list[str]]:
    notes: list[str] = []
    if not text.startswith("---\n"):
        return {}, ["SKILL.md 缺少 YAML front matter"]
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, ["YAML front matter 未正确闭合"]
    block = parts[1]
    data: dict[str, str] = {}
    for line in block.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            notes.append(f"无法解析的元数据行：{line}")
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip('"\'')
    return data, notes


def markdown_files(root: Path) -> list[Path]:
    return sorted(
        p for p in root.rglob("*.md")
        if ".git" not in p.parts and "node_modules" not in p.parts
    )


def all_markdown_text(root: Path) -> str:
    chunks = []
    for path in markdown_files(root):
        chunks.append(read_text(path))
    return "\n".join(chunks)


def points_by_ratio(max_points: int, hits: int, target: int) -> int:
    if target <= 0:
        return max_points
    return min(max_points, round(max_points * min(hits, target) / target))


def make_check(check_id: str, title: str, max_points: int, points: int, notes: list[str]) -> CheckResult:
    points = max(0, min(max_points, points))
    if points == max_points:
        status = "pass"
    elif points >= round(max_points * 0.6):
        status = "partial"
    else:
        status = "fail"
    return CheckResult(check_id, title, max_points, points, status, notes)


def score_trigger_and_boundary(root: Path, skill_text: str, corpus: str, meta: dict[str, str]) -> CheckResult:
    points = 0
    notes = []
    description = meta.get("description", "")
    if description and 20 <= len(description) <= 300:
        points += 6
    else:
        notes.append("description 建议控制在 20-300 字符，并清楚描述触发场景")
    hits = sum(1 for word in BOUNDARY_HINTS if word in corpus)
    p = points_by_ratio(14, hits, 5)
    points += p
    if p < 14:
        notes.append("建议补足适用/不适用边界、触发条件和意图识别说明")
    return make_check("trigger_boundary", "触发与适用边界", 20, points, notes)


def score_structure(root: Path, skill_text: str, meta: dict[str, str], fm_notes: list[str]) -> CheckResult:
    points = 0
    notes = []
    if (root / "SKILL.md").exists():
        points += 3
    else:
        notes.append("缺少 SKILL.md")
    missing = [field for field in REQUIRED_FRONT_MATTER_FIELDS if not meta.get(field)]
    if not missing and not fm_notes:
        points += 7
    else:
        notes.extend(fm_notes or [])
        if missing:
            notes.append("缺少必填元数据字段：" + ", ".join(missing))
    dir_hits = sum(1 for name in RECOMMENDED_DIRS if (root / name).is_dir())
    points += points_by_ratio(5, dir_hits, len(RECOMMENDED_DIRS))
    if dir_hits < len(RECOMMENDED_DIRS):
        notes.append("建议包含 references/、templates/、examples/ 等渐进式资源目录")
    return make_check("structure_metadata", "结构与注册元数据", 15, points, notes)


def score_progressive_loading(root: Path, skill_text: str, corpus: str) -> CheckResult:
    hits = sum(1 for hint in REFERENCE_HINTS if hint in corpus)
    points = points_by_ratio(15, hits, 4)
    notes = [] if points == 15 else ["建议明确何时加载 references/templates/examples/scripts 中的辅助材料"]
    if len(skill_text) > 12000:
        points = max(0, points - 3)
        notes.append("SKILL.md 偏长，建议进一步拆分到 references/ 以降低入口负担")
    return make_check("progressive_loading", "渐进式加载", 15, points, notes)


def score_executability(root: Path, corpus: str) -> CheckResult:
    points = 0
    notes = []
    hits = sum(1 for hint in EXECUTION_HINTS if hint in corpus)
    points += points_by_ratio(10, hits, 5)
    if (root / "scripts").is_dir():
        points += 3
    else:
        notes.append("建议提供 scripts/ 中的可执行辅助脚本")
    if (root / "templates").is_dir():
        points += 2
    else:
        notes.append("建议提供 templates/ 供用户直接复用")
    if points < 15:
        notes.append("建议补足输入、处理、输出、验证的可执行步骤")
    return make_check("executability", "可执行性", 15, points, notes)


def score_auditability(root: Path, corpus: str) -> CheckResult:
    points = 0
    notes = []
    hits = sum(1 for hint in AUDIT_HINTS if hint in corpus)
    points += points_by_ratio(8, hits, 4)
    if (root / "scripts" / "validate-skill.py").exists():
        points += 4
    else:
        notes.append("建议提供 validate-skill.py 或等价校验脚本")
    if (root / "references" / "skill-scorecard.md").exists():
        points += 3
    else:
        notes.append("建议提供 skill-scorecard.md 或等价评分表")
    return make_check("auditability", "可审计性", 15, points, notes)


def score_error_handling(root: Path, corpus: str) -> CheckResult:
    hits = sum(1 for hint in ERROR_HANDLING_HINTS if hint in corpus)
    points = points_by_ratio(10, hits, 5)
    notes = [] if points == 10 else ["建议补足权限失败、文件缺失、工具失败、信息不足、降级交付等异常分支"]
    return make_check("error_handling", "异常处理", 10, points, notes)


def score_delivery_contract(root: Path, corpus: str) -> CheckResult:
    points = points_by_ratio(10, sum(1 for hint in DELIVERY_HINTS if hint in corpus), 5)
    notes = [] if points == 10 else ["建议明确交付物路径、引用格式、验证结果和打包规则"]
    return make_check("delivery_contract", "交付契约", 10, points, notes)


def score_risk_terms(root: Path, corpus: str) -> CheckResult:
    found = [term for term in HIGH_RISK_TERMS if term.lower() in corpus.lower()]
    points = 10 if not found else max(0, 10 - 3 * len(found))
    notes = [] if not found else ["发现高风险片段：" + ", ".join(found)]
    return make_check("safety_risk", "安全与高风险片段", 10, points, notes)


def score_package(root: Path) -> ScoreReport:
    skill_path = root / "SKILL.md"
    skill_text = read_text(skill_path) if skill_path.exists() else ""
    corpus = all_markdown_text(root)
    meta, fm_notes = extract_front_matter(skill_text)
    checks = [
        score_trigger_and_boundary(root, skill_text, corpus, meta),
        score_structure(root, skill_text, meta, fm_notes),
        score_progressive_loading(root, skill_text, corpus),
        score_executability(root, corpus),
        score_auditability(root, corpus),
        score_error_handling(root, corpus),
        score_delivery_contract(root, corpus),
    ]
    risk = score_risk_terms(root, corpus)
    if risk.points < risk.max_points:
        penalty = risk.max_points - risk.points
        checks.append(CheckResult(
            "safety_penalty",
            "安全与高风险片段扣分",
            0,
            -penalty,
            "fail",
            risk.notes,
        ))
    return ScoreReport(root=root, checks=checks)


def print_text(report: ScoreReport) -> None:
    print(f"Skill score: {report.score}/{report.max_score} - {report.level}")
    for item in report.checks:
        print(f"[{item.status}] {item.id}: {item.points}/{item.max_points} {item.title}")
        for note in item.notes:
            print(f"  - {note}")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Semi-automatic Skill scorecard")
    parser.add_argument("skill_dir", nargs="?", default=".", help="Skill package root directory")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")
    args = parser.parse_args(argv)
    root = Path(args.skill_dir).resolve()
    report = score_package(root)
    if args.json:
        print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
    else:
        print_text(report)
    return 0 if report.score >= 80 else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
