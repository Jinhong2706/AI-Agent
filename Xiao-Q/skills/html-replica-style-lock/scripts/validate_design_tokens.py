#!/usr/bin/env python3
"""Basic validator for design-tokens.json."""
from __future__ import annotations

import json
import sys
from pathlib import Path

REQUIRED_TOP_LEVEL = [
    "meta",
    "style_summary",
    "layout",
    "colors",
    "typography",
    "spacing",
    "sizing",
    "radius",
    "borders",
    "shadows",
    "effects",
    "motion",
    "components",
    "imagery",
    "responsive",
    "constraints",
    "expansion_rules",
]

REQUIRED_CONSTRAINT_KEYS = ["must_keep", "may_adapt", "must_not_do"]


def fail(msg: str) -> None:
    print(f"[FAIL] {msg}")
    sys.exit(1)


def main() -> None:
    if len(sys.argv) != 2:
        fail("Usage: validate_design_tokens.py <design-tokens.json>")

    path = Path(sys.argv[1])
    if not path.exists():
        fail(f"File not found: {path}")

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"Invalid JSON: {exc}")

    missing = [key for key in REQUIRED_TOP_LEVEL if key not in data]
    if missing:
        fail("Missing top-level keys: " + ", ".join(missing))

    if not isinstance(data["constraints"], dict):
        fail("constraints must be an object")

    missing_constraint_keys = [k for k in REQUIRED_CONSTRAINT_KEYS if k not in data["constraints"]]
    if missing_constraint_keys:
        fail("Missing constraints keys: " + ", ".join(missing_constraint_keys))

    if not isinstance(data.get("components"), dict) or not data["components"]:
        fail("components must be a non-empty object")

    print("[PASS] design-tokens.json passes basic checks.")


if __name__ == "__main__":
    main()
