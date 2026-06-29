#!/usr/bin/env python3
"""Run deterministic Backend Forge routing checks."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    cases = json.loads((root / "tests/route_golden_cases.json").read_text(encoding="utf-8"))
    failed = False
    for case in cases:
        result = subprocess.run(
            ["bash", "scripts/classify_task.sh", case["prompt"]],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            print(f"FAIL {case['name']}: classify_task failed: {result.stderr.strip()}")
            failed = True
            continue
        actual = json.loads(result.stdout)
        if actual.get("mode") != case["expected_mode"] or actual.get("policy") != case["expected_policy"]:
            print(
                f"FAIL {case['name']}: expected {case['expected_mode']}/{case['expected_policy']}, "
                f"got {actual.get('mode')}/{actual.get('policy')}"
            )
            failed = True
        else:
            print(f"PASS {case['name']}: {actual.get('mode')}/{actual.get('policy')}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
