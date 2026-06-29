#!/usr/bin/env python3
"""Basic validator for replica HTML output."""
from __future__ import annotations

import re
import sys
from pathlib import Path


def fail(msg: str) -> None:
    print(f"[FAIL] {msg}")
    sys.exit(1)


def main() -> None:
    if len(sys.argv) != 2:
        fail("Usage: validate_html_output.py <index.html>")

    path = Path(sys.argv[1])
    if not path.exists():
        fail(f"File not found: {path}")

    text = path.read_text(encoding="utf-8", errors="ignore")

    checks = [
        ("<!DOCTYPE html" in text, "Missing doctype"),
        ("<style" in text, "Missing inline <style> block"),
        ("<body" in text, "Missing <body>"),
        (bool(re.search(r"<(main|section|header|article|nav)\b", text)), "Missing semantic layout tags"),
        (":root" in text, "Missing CSS variables in :root"),
    ]

    for ok, msg in checks:
        if not ok:
            fail(msg)

    print("[PASS] HTML output passes basic checks.")


if __name__ == "__main__":
    main()
