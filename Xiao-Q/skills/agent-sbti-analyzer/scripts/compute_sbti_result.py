#!/usr/bin/env python3
"""Compute SBTI result from answers.

This script is designed to be used by the agent while running the interactive test.
It is deterministic and reproduces the matching rules described in
`assets/data/sbti_test_data.json`.

Usage:
  python3 scripts/compute_sbti_result.py --answers '{"q1": 1, "q2": 3, ...}'

Notes:
- Do NOT pass or output any Base64 image strings.
- Image path in output is a relative path inside this Skill package.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple


DIM_ORDER: List[str] = [
    "S1",
    "S2",
    "S3",
    "E1",
    "E2",
    "E3",
    "A1",
    "A2",
    "A3",
    "Ac1",
    "Ac2",
    "Ac3",
    "So1",
    "So2",
    "So3",
]


def _skill_root() -> Path:
    return Path(__file__).resolve().parent.parent


def load_test_data() -> Dict[str, Any]:
    p = _skill_root() / "assets" / "data" / "sbti_test_data.json"
    return json.loads(p.read_text(encoding="utf-8"))


def load_image_map() -> Dict[str, str]:
    p = _skill_root() / "assets" / "personality_image_map.json"
    return json.loads(p.read_text(encoding="utf-8"))


def level_from_dim_sum(total: int) -> str:
    if total <= 3:
        return "L"
    if total == 4:
        return "M"
    return "H"


def level_to_num(level: str) -> int:
    return {"L": 1, "M": 2, "H": 3}[level]


def build_user_levels(answers: Dict[str, int], test_data: Dict[str, Any]) -> Dict[str, str]:
    # Sum each dimension by iterating question definitions.
    sums: Dict[str, int] = {d: 0 for d in DIM_ORDER}

    for q in test_data["questions"]:
        qid = q["id"]
        if q.get("special"):
            continue

        dim = q["dim"]
        if dim not in sums:
            continue

        if qid not in answers:
            raise ValueError(f"Missing answer for required question: {qid}")
        sums[dim] += int(answers[qid])

    return {dim: level_from_dim_sum(total) for dim, total in sums.items()}


def levels_to_pattern(levels: Dict[str, str]) -> str:
    letters = [levels[d] for d in DIM_ORDER]
    groups = ["".join(letters[i : i + 3]) for i in range(0, 15, 3)]
    return "-".join(groups)


@dataclass
class Match:
    code: str
    pattern: str
    distance: int
    exact: int
    similarity: int


def score_matches(user_levels: Dict[str, str], test_data: Dict[str, Any]) -> List[Match]:
    user_nums = [level_to_num(user_levels[d]) for d in DIM_ORDER]

    patterns_raw = test_data.get("patterns") or []
    patterns: Dict[str, str] = {}
    if isinstance(patterns_raw, list):
        for item in patterns_raw:
            patterns[item["code"]] = item["pattern"]
    else:
        patterns = patterns_raw

    matches: List[Match] = []

    for code, ptn in patterns.items():
        p_letters = [c for c in ptn.replace("-", "")]
        if len(p_letters) != 15:
            continue

        p_nums = [level_to_num(ch) for ch in p_letters]
        diffs = [abs(a - b) for a, b in zip(user_nums, p_nums)]
        total_distance = int(sum(diffs))
        exact = int(sum(1 for d in diffs if d == 0))
        similarity = max(0, int(round((1 - total_distance / 30) * 100)))

        matches.append(
            Match(
                code=code,
                pattern=ptn,
                distance=total_distance,
                exact=exact,
                similarity=similarity,
            )
        )

    # Sort rule: distance asc, exact desc, similarity desc
    matches.sort(key=lambda m: (m.distance, -m.exact, -m.similarity))
    return matches


def pick_final_code(answers: Dict[str, int], matches: List[Match]) -> Tuple[str, str]:
    """Return (final_code, reason)."""

    # Easter egg 1: DRUNK
    if int(answers.get("drink_gate_q2", 0)) == 2:
        return "DRUNK", "触发彩蛋：饮酒隐藏题 drink_gate_q2 选择了选项 2，结果强制判定为 DRUNK。"

    if not matches:
        return "HHHH", "无可用常规人格匹配模型，结果使用兜底人格 HHHH。"

    best = matches[0]

    # Easter egg 2: HHHH
    if best.similarity < 60:
        return "HHHH", (
            f"常规人格最高匹配度仅 {best.similarity}%（< 60%），触发兜底人格 HHHH。"
        )

    return best.code, (
        f"按 Distance 最小、Exact 最大、Similarity 最高排序，主类型人格为 {best.code}（Similarity={best.similarity}%）。"
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--answers",
        required=True,
        help="JSON string, e.g. '{\"q1\": 1, \"q2\": 3, ...}'",
    )
    args = ap.parse_args()

    answers: Dict[str, int] = {
        k: int(v) for k, v in json.loads(args.answers).items()  # type: ignore[arg-type]
    }

    test_data = load_test_data()
    image_map = load_image_map()

    user_levels = build_user_levels(answers=answers, test_data=test_data)
    user_pattern = levels_to_pattern(user_levels)

    matches = score_matches(user_levels=user_levels, test_data=test_data)
    final_code, reason = pick_final_code(answers=answers, matches=matches)

    result_def = (test_data.get("results_mapping") or {}).get(final_code) or {}

    out = {
        "final": {
            "code": final_code,
            "cn": result_def.get("cn"),
            "intro": result_def.get("intro"),
            "desc": result_def.get("desc"),
            "image": {
                "file_name": image_map.get(final_code),
                "relative_path": f"assets/images/{image_map.get(final_code)}" if image_map.get(final_code) else None,
            },
        },
        "reason": reason,
        "user": {
            "levels": user_levels,
            "pattern": user_pattern,
        },
        "best_match": (
            {
                "code": matches[0].code,
                "pattern": matches[0].pattern,
                "distance": matches[0].distance,
                "exact": matches[0].exact,
                "similarity": matches[0].similarity,
            }
            if matches
            else None
        ),
    }

    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
