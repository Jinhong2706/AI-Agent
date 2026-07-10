#!/usr/bin/env python3
"""Generate an 11-shade color scale from a single brand hex color.

Usage:
    python generate_palette.py "#0D9488"
    python generate_palette.py "#7C3AED" --json
    python generate_palette.py "#0D9488" --check

Outputs hex values for shades 50–950 with consistent hue.
Use --check to also verify WCAG contrast for common pairs.
"""

from __future__ import annotations

import argparse
import colorsys
import json
import sys
from typing import TypedDict


class ContrastCheckResult(TypedDict):
    label: str
    foreground: str
    background: str
    ratio: float
    pass_aa: bool


# Shade definitions: (lightness%, saturation_multiplier)
SHADE_DEFS = {
    50: (97, 0.80),
    100: (94, 0.80),
    200: (87, 0.85),
    300: (75, 0.90),
    400: (62, 0.95),
    500: (48, 1.00),
    600: (40, 1.00),
    700: (33, 1.00),
    800: (27, 1.00),
    900: (20, 1.00),
    950: (10, 1.00),
}

USE_CASES = {
    50: "Subtle backgrounds",
    100: "Hover states",
    200: "Borders, dividers",
    300: "Disabled states",
    400: "Placeholder text",
    500: "Brand baseline",
    600: "Primary actions",
    700: "Hover on primary",
    800: "Active/pressed",
    900: "Text on light bg",
    950: "Dark mode bg",
}


def hex_to_hsl(hex_color: str) -> tuple[float, float, float]:
    """Convert hex to HSL (h: 0-360, s: 0-100, l: 0-100)."""
    h_str = hex_color.lstrip("#")
    if len(h_str) == 3:
        h_str = h_str[0] * 2 + h_str[1] * 2 + h_str[2] * 2
    r = int(h_str[0:2], 16) / 255
    g = int(h_str[2:4], 16) / 255
    b = int(h_str[4:6], 16) / 255

    h, l, s = colorsys.rgb_to_hls(r, g, b)
    return round(h * 360, 1), round(s * 100, 1), round(l * 100, 1)


def hsl_to_hex(h: float, s: float, l: float) -> str:
    """Convert HSL (h: 0-360, s: 0-100, l: 0-100) to hex."""
    r, g, b = colorsys.hls_to_rgb(h / 360, l / 100, s / 100)
    return f"#{int(round(r * 255)):02X}{int(round(g * 255)):02X}{int(round(b * 255)):02X}"


def generate_scale(hex_color: str) -> dict[int, str]:
    """Generate 11-shade scale from a single hex color."""
    hue, sat, _ = hex_to_hsl(hex_color)

    scale: dict[int, str] = {}
    for shade, (lightness, sat_mult) in SHADE_DEFS.items():
        adjusted_sat = min(100, sat * sat_mult)
        scale[shade] = hsl_to_hex(hue, adjusted_sat, lightness)

    return scale


def relative_luminance(hex_color: str) -> float:
    """WCAG relative luminance."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255
    r_lin = r / 12.92 if r <= 0.03928 else ((r + 0.055) / 1.055) ** 2.4
    g_lin = g / 12.92 if g <= 0.03928 else ((g + 0.055) / 1.055) ** 2.4
    b_lin = b / 12.92 if b <= 0.03928 else ((b + 0.055) / 1.055) ** 2.4
    return 0.2126 * r_lin + 0.7152 * g_lin + 0.0722 * b_lin


def contrast_ratio(c1: str, c2: str) -> float:
    """WCAG contrast ratio."""
    l1 = relative_luminance(c1)
    l2 = relative_luminance(c2)
    lighter, darker = max(l1, l2), min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def check_common_pairs(scale: dict[int, str]) -> list[ContrastCheckResult]:
    """Check WCAG contrast for common usage pairs."""
    white = "#FFFFFF"
    pairs = [
        (scale[950], white, "Body text (950 on white)"),
        (scale[900], white, "Card text (900 on white)"),
        (scale[600], white, "Primary button text (white on 600)"),
        (scale[500], white, "Brand color on white (500)"),
        (scale[50], scale[950], "Dark mode text (50 on 950)"),
        (scale[600], scale[50], "Muted text (600 on 50)"),
        (scale[400], scale[950], "Dark mode muted (400 on 950)"),
    ]

    results: list[ContrastCheckResult] = []
    for fg, bg, label in pairs:
        ratio = contrast_ratio(fg, bg)
        results.append(
            ContrastCheckResult(
                label=label,
                foreground=fg,
                background=bg,
                ratio=round(ratio, 2),
                pass_aa=ratio >= 4.5,
            )
        )
    return results


def format_table(scale: dict[int, str]) -> str:
    """Format shade scale as a readable table."""
    lines = ["Shade  Hex       Use Case"]
    lines.append("-" * 45)
    for shade in sorted(scale):
        hex_val = scale[shade]
        use = USE_CASES.get(shade, "")
        marker = " ◀ brand" if shade == 500 else ""
        lines.append(f"  {shade:>3}   {hex_val}   {use}{marker}")
    return "\n".join(lines)


def format_check(results: list[ContrastCheckResult]) -> str:
    """Format contrast check results."""
    lines: list[str] = ["\nContrast Checks (common pairs):"]
    lines.append("-" * 60)
    for r in results:
        status = "✓ PASS" if r["pass_aa"] else "✗ FAIL"
        lines.append(f"  {status}  {r['ratio']:>5}:1  {r['label']}")
    passes = sum(1 for r in results if r["pass_aa"])
    total = len(results)
    lines.append(f"\n  {passes}/{total} pairs pass WCAG AA for normal text")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate an 11-shade color scale from a brand hex",
    )
    parser.add_argument("hex_color", help="Brand hex color (e.g., #0D9488)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--check", action="store_true", help="Check WCAG contrast for common pairs")
    args = parser.parse_args()

    try:
        scale = generate_scale(args.hex_color)
    except (ValueError, IndexError):
        print(f"Error: Invalid hex color '{args.hex_color}'", file=sys.stderr)
        sys.exit(1)

    if args.json:
        output: dict[str, object] = {
            "input": args.hex_color,
            "scale": {str(k): v for k, v in scale.items()},
        }
        if args.check:
            output["contrast_checks"] = check_common_pairs(scale)
        print(json.dumps(output, indent=2))
    else:
        hue, sat, light = hex_to_hsl(args.hex_color)
        print(f"Input: {args.hex_color} → HSL({hue}°, {sat}%, {light}%)\n")
        print(format_table(scale))
        if args.check:
            print(format_check(check_common_pairs(scale)))


if __name__ == "__main__":
    main()
