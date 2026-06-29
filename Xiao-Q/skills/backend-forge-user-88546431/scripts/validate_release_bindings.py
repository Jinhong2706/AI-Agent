#!/usr/bin/env python3
"""Validate Backend Forge release binding registry."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


def markers(path: Path) -> set[str]:
    if not path.exists():
        return set()
    return set(re.findall(r"\brelease_binding:\s*(RB-[A-Z0-9-]+)", path.read_text(encoding="utf-8")))


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    registry = json.loads((root / "references/release_bindings.json").read_text(encoding="utf-8"))
    errors: list[str] = []
    seen: set[str] = set()
    marker_ids: set[str] = set()

    for binding in registry.get("bindings", []):
        binding_id = binding.get("id")
        if not binding_id:
            errors.append("binding missing id")
            continue
        seen.add(binding_id)
        if binding.get("severity") not in {"P0", "P1"}:
            errors.append(f"{binding_id}: severity must be P0 or P1")
        for field in ("sources", "runtime", "positive_cases", "negative_cases"):
            values = binding.get(field)
            if not isinstance(values, list) or not values:
                errors.append(f"{binding_id}: missing {field}")
                continue
            if field in {"sources", "runtime"}:
                for value in values:
                    if not (root / value).exists():
                        errors.append(f"{binding_id}: missing path {value}")
                    if field == "sources":
                        marker_ids.update(markers(root / value))
        for check in binding.get("release_checks", []):
            check_file = root / check.get("file", "")
            if not check_file.exists():
                errors.append(f"{binding_id}: missing release check {check.get('file')}")
                continue
            text = check_file.read_text(encoding="utf-8")
            for needle in check.get("needles", []):
                if needle not in text:
                    errors.append(f"{binding_id}: missing needle {needle}")

    missing_markers = seen - marker_ids
    for binding_id in sorted(missing_markers):
        errors.append(f"{binding_id}: missing release_binding marker in source docs")

    if errors:
        for error in errors:
            print(f"FAIL {error}")
        return 1
    print(f"PASS {len(seen)} Backend Forge release bindings validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
