#!/usr/bin/env python3
"""WCAG contrast ratio checker.

Usage:
    python check_contrast.py "#0D9488" "#FFFFFF"
    python check_contrast.py "#0D9488" "#FFFFFF" --json
    python check_contrast.py --audit palette.json

palette.json format for --audit:
    {
      "pairs": [
        {"foreground": "#042F2E", "background": "#FFFFFF", "label": "body text"},
        {"foreground": "#FFFFFF", "background": "#0D9488", "label": "primary button"}
      ]
    }
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import TypedDict


class GradeResult(TypedDict):
    ratio: float
    normal_text_aa: bool
    normal_text_aaa: bool
    large_text_aa: bool
    large_text_aaa: bool
    ui_components_aa: bool


class AuditEntry(TypedDict):
    foreground: str
    background: str
    label: str
    ratio: float
    normal_text_aa: bool
    normal_text_aaa: bool
    large_text_aa: bool
    large_text_aaa: bool
    ui_components_aa: bool


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert hex color string to RGB tuple."""
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = h[0] * 2 + h[1] * 2 + h[2] * 2
    if len(h) != 6:
        raise ValueError(f"Invalid hex color: {hex_color}")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def relative_luminance(hex_color: str) -> float:
    """Calculate relative luminance per WCAG 2.1.

    Returns a value between 0 (black) and 1 (white).
    """
    r, g, b = hex_to_rgb(hex_color)
    rs = r / 255
    gs = g / 255
    bs = b / 255

    r_lin = rs / 12.92 if rs <= 0.03928 else ((rs + 0.055) / 1.055) ** 2.4
    g_lin = gs / 12.92 if gs <= 0.03928 else ((gs + 0.055) / 1.055) ** 2.4
    b_lin = bs / 12.92 if bs <= 0.03928 else ((bs + 0.055) / 1.055) ** 2.4

    return 0.2126 * r_lin + 0.7152 * g_lin + 0.0722 * b_lin


def contrast_ratio(color1: str, color2: str) -> float:
    """Calculate WCAG contrast ratio between two hex colors.

    Returns a value between 1 (identical) and 21 (black on white).
    """
    lum1 = relative_luminance(color1)
    lum2 = relative_luminance(color2)
    lighter = max(lum1, lum2)
    darker = min(lum1, lum2)
    return (lighter + 0.05) / (darker + 0.05)


def grade(ratio: float) -> GradeResult:
    """Grade a contrast ratio against WCAG AA and AAA standards."""
    return GradeResult(
        ratio=round(ratio, 2),
        normal_text_aa=ratio >= 4.5,
        normal_text_aaa=ratio >= 7.0,
        large_text_aa=ratio >= 3.0,
        large_text_aaa=ratio >= 4.5,
        ui_components_aa=ratio >= 3.0,
    )


def format_result(fg: str, bg: str, result: GradeResult, label: str = "") -> str:
    """Format a contrast check result as human-readable text."""
    lines: list[str] = []
    prefix = f"[{label}] " if label else ""
    r = result["ratio"]
    lines.append(f"{prefix}{fg} on {bg} — Contrast ratio: {r}:1")

    def status(passed: bool) -> str:
        return "PASS ✓" if passed else "FAIL ✗"

    lines.append(
        f"  Normal text  AA: {status(result['normal_text_aa'])}    "
        f"AAA: {status(result['normal_text_aaa'])}"
    )
    lines.append(
        f"  Large text   AA: {status(result['large_text_aa'])}    "
        f"AAA: {status(result['large_text_aaa'])}"
    )
    lines.append(f"  UI elements  AA: {status(result['ui_components_aa'])}")

    return "\n".join(lines)


def audit_palette(palette_path: str, as_json: bool = False) -> int:
    """Audit all pairs in a palette JSON file. Returns count of failures."""
    with open(palette_path) as f:
        data = json.load(f)

    pairs = data.get("pairs", [])
    if not pairs:
        print("No pairs found in palette file.")
        return 0

    failures = 0
    results: list[AuditEntry] = []
    for pair in pairs:
        fg: str = pair["foreground"]
        bg: str = pair["background"]
        label: str = pair.get("label", "")
        ratio = contrast_ratio(fg, bg)
        result = grade(ratio)
        results.append(
            AuditEntry(
                foreground=fg,
                background=bg,
                label=label,
                **result,
            )
        )
        if not result["normal_text_aa"]:
            failures += 1

    if as_json:
        print(json.dumps(results, indent=2))
    else:
        for entry in results:
            entry_grade = GradeResult(
                ratio=entry["ratio"],
                normal_text_aa=entry["normal_text_aa"],
                normal_text_aaa=entry["normal_text_aaa"],
                large_text_aa=entry["large_text_aa"],
                large_text_aaa=entry["large_text_aaa"],
                ui_components_aa=entry["ui_components_aa"],
            )
            print(
                format_result(entry["foreground"], entry["background"], entry_grade, entry["label"])
            )
            print()

        total = len(results)
        passed = total - failures
        print(f"Summary: {passed}/{total} pairs pass AA for normal text")
        if failures:
            print(f"⚠ {failures} pair(s) FAIL AA for normal text")

    return failures


def main() -> None:
    parser = argparse.ArgumentParser(
        description="WCAG contrast ratio checker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            '  python check_contrast.py "#0D9488" "#FFFFFF"\n'
            '  python check_contrast.py "#0D9488" "#FFFFFF" --json\n'
            "  python check_contrast.py --audit palette.json\n"
        ),
    )
    parser.add_argument("foreground", nargs="?", help="Foreground hex color (e.g., #0D9488)")
    parser.add_argument("background", nargs="?", help="Background hex color (e.g., #FFFFFF)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--audit", metavar="FILE", help="Audit all pairs in a palette JSON file")
    args = parser.parse_args()

    if args.audit:
        failures = audit_palette(args.audit, args.json)
        sys.exit(1 if failures else 0)

    if not args.foreground or not args.background:
        parser.error("Provide foreground and background hex colors, or use --audit")

    ratio = contrast_ratio(args.foreground, args.background)
    result = grade(ratio)

    if args.json:
        print(
            json.dumps(
                {"foreground": args.foreground, "background": args.background, **result},
                indent=2,
            )
        )
    else:
        print(format_result(args.foreground, args.background, result))

    if not result["normal_text_aa"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
