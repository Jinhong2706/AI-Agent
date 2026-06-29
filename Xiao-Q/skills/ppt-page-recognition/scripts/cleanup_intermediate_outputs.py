#!/usr/bin/env python3

from __future__ import annotations

import argparse
import fnmatch
from pathlib import Path


DEFAULT_PATTERNS = [
    "vision_task_results.json",
    "*vision_task_results*.json",
    "*识别结果.json",
    "*识别结果_含vision_tasks*.json",
    "*audit*.json",
    "*审计报告*.json",
    "*diff*.json",
    "*对比*.json",
]


def should_remove(path: Path, keep_paths: set[Path], patterns: list[str]) -> bool:
    resolved = path.resolve()
    if resolved in keep_paths:
        return False
    if path.suffix.lower() != ".json":
        return False
    return any(fnmatch.fnmatch(path.name, pattern) for pattern in patterns)


def main() -> int:
    parser = argparse.ArgumentParser(description="Delete intermediate PPT recognition JSON files and keep only the final merged JSON.")
    parser.add_argument("--directory", type=Path, required=True, help="Directory to clean")
    parser.add_argument("--final-json", type=Path, action="append", default=[], help="Final JSON file(s) to preserve")
    parser.add_argument("--extra-keep", type=Path, action="append", default=[], help="Additional files to preserve")
    args = parser.parse_args()

    directory = args.directory.resolve()
    keep_paths = {path.resolve() for path in [*args.final_json, *args.extra_keep] if path}

    removed: list[str] = []
    for path in sorted(directory.iterdir()):
        if not path.is_file():
            continue
        if should_remove(path, keep_paths, DEFAULT_PATTERNS):
            path.unlink(missing_ok=True)
            removed.append(str(path))

    for item in removed:
        print(item)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
