#!/usr/bin/env python3
"""Simulate color vision deficiency and detect chromostereopsis risk.

Usage:
    python simulate_cvd.py "#EF4444" "#22C55E"
    python simulate_cvd.py "#FF0000" "#0000FF"
    python simulate_cvd.py "#EF4444" "#22C55E" --json

Simulates how a color pair appears to people with:
  - Protanopia (no red cones, ~1% of males)
  - Deuteranopia (no green cones, ~6% of males)
  - Tritanopia (no blue cones, ~0.01%)

Also detects chromostereopsis risk (red-blue vibration illusion).

Uses Brettel 1997 simulation matrices (stdlib only, no dependencies).
"""

from __future__ import annotations

import argparse
import colorsys
import json
import math
import sys
from typing import TypedDict


class _ChromoResultRequired(TypedDict):
    risk: bool
    color1_hue: float
    color1_saturation: float
    color2_hue: float
    color2_saturation: float


class ChromoResult(_ChromoResultRequired, total=False):
    reason: str


class SimulationEntry(TypedDict):
    color1_simulated: str
    color2_simulated: str
    distance: float
    status: str


class AnalysisResult(TypedDict):
    color1: str
    color2: str
    chromostereopsis: ChromoResult
    simulations: dict[str, SimulationEntry]


# ── sRGB linearization ──────────────────────────────────────────────


def srgb_to_linear(c: float) -> float:
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def linear_to_srgb(c: float) -> float:
    c = max(0.0, min(1.0, c))
    return c * 12.92 if c <= 0.0031308 else 1.055 * (c ** (1 / 2.4)) - 0.055


def hex_to_linear(hex_color: str) -> tuple[float, float, float]:
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = h[0] * 2 + h[1] * 2 + h[2] * 2
    r = int(h[0:2], 16) / 255
    g = int(h[2:4], 16) / 255
    b = int(h[4:6], 16) / 255
    return srgb_to_linear(r), srgb_to_linear(g), srgb_to_linear(b)


def linear_to_hex(r: float, g: float, b: float) -> str:
    rs = int(round(linear_to_srgb(r) * 255))
    gs = int(round(linear_to_srgb(g) * 255))
    bs = int(round(linear_to_srgb(b) * 255))
    return f"#{rs:02X}{gs:02X}{bs:02X}"


# ── CVD simulation matrices (simplified Brettel/Viénot) ─────────────
# These 3x3 matrices transform linear RGB to simulated linear RGB.

CVD_MATRICES = {
    "protanopia": [
        [0.152286, 1.052583, -0.204868],
        [0.114503, 0.786281, 0.099216],
        [-0.003882, -0.048116, 1.051998],
    ],
    "deuteranopia": [
        [0.367322, 0.860646, -0.227968],
        [0.280085, 0.672501, 0.047413],
        [-0.011820, 0.042940, 0.968881],
    ],
    "tritanopia": [
        [1.255528, -0.076749, -0.178779],
        [-0.078411, 0.930809, 0.147602],
        [0.004733, 0.691367, 0.303900],
    ],
}


def apply_matrix(
    matrix: list[list[float]], r: float, g: float, b: float
) -> tuple[float, float, float]:
    """Apply a 3x3 color transformation matrix."""
    return (
        matrix[0][0] * r + matrix[0][1] * g + matrix[0][2] * b,
        matrix[1][0] * r + matrix[1][1] * g + matrix[1][2] * b,
        matrix[2][0] * r + matrix[2][1] * g + matrix[2][2] * b,
    )


def simulate_cvd(hex_color: str, cvd_type: str) -> str:
    """Simulate how a hex color appears with a given type of CVD."""
    r, g, b = hex_to_linear(hex_color)
    matrix = CVD_MATRICES[cvd_type]
    sr, sg, sb = apply_matrix(matrix, r, g, b)
    return linear_to_hex(sr, sg, sb)


# ── Perceptual distance ─────────────────────────────────────────────


def color_distance(hex1: str, hex2: str) -> float:
    """Approximate perceptual distance between two colors (Euclidean in linear RGB).

    Values < 0.05 are effectively indistinguishable.
    Values < 0.15 are difficult to distinguish.
    """
    r1, g1, b1 = hex_to_linear(hex1)
    r2, g2, b2 = hex_to_linear(hex2)
    return math.sqrt((r1 - r2) ** 2 + (g1 - g2) ** 2 + (b1 - b2) ** 2)


# ── Chromostereopsis detection ───────────────────────────────────────


def hex_to_hsl(hex_color: str) -> tuple[float, float, float]:
    """Convert hex to HSL (h: 0-360, s: 0-100, l: 0-100)."""
    h_str = hex_color.lstrip("#")
    if len(h_str) == 3:
        h_str = h_str[0] * 2 + h_str[1] * 2 + h_str[2] * 2
    r = int(h_str[0:2], 16) / 255
    g = int(h_str[2:4], 16) / 255
    b = int(h_str[4:6], 16) / 255
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    return h * 360, s * 100, l * 100


def check_chromostereopsis(hex1: str, hex2: str) -> ChromoResult:
    """Check if a color pair risks chromostereopsis.

    Chromostereopsis occurs when highly saturated colors at opposite ends
    of the visible spectrum (red ~0°/360° and blue ~240°) are placed
    adjacent. The eye cannot focus both wavelengths simultaneously,
    causing a depth/vibration illusion and eye strain.
    """
    h1, s1, _ = hex_to_hsl(hex1)
    h2, s2, _ = hex_to_hsl(hex2)

    # Check if one color is in the red range and the other in blue range
    def is_red(h: float) -> bool:
        return h <= 30 or h >= 330

    def is_blue(h: float) -> bool:
        return 210 <= h <= 270

    both_saturated = s1 >= 60 and s2 >= 60
    red_blue_pair = (is_red(h1) and is_blue(h2)) or (is_red(h2) and is_blue(h1))

    # Also check red+green at extreme saturation
    def is_green(h: float) -> bool:
        return 90 <= h <= 150

    red_green_extreme = (
        ((is_red(h1) and is_green(h2)) or (is_red(h2) and is_green(h1))) and s1 >= 80 and s2 >= 80
    )

    risk = (red_blue_pair and both_saturated) or red_green_extreme

    result = ChromoResult(
        risk=risk,
        color1_hue=round(h1, 1),
        color1_saturation=round(s1, 1),
        color2_hue=round(h2, 1),
        color2_saturation=round(s2, 1),
    )

    if risk:
        if red_blue_pair:
            result["reason"] = "High-saturation red + blue causes depth/vibration illusion."
        else:
            result["reason"] = (
                "Extreme-saturation red + green at screen boundaries causes vibration."
            )

    return result


# ── Main ─────────────────────────────────────────────────────────────


def analyze_pair(hex1: str, hex2: str) -> AnalysisResult:
    """Full analysis of a color pair for CVD safety and perceptual hazards."""
    simulations: dict[str, SimulationEntry] = {}

    for cvd_type in CVD_MATRICES:
        sim1 = simulate_cvd(hex1, cvd_type)
        sim2 = simulate_cvd(hex2, cvd_type)
        dist = color_distance(sim1, sim2)

        if dist < 0.05:
            status = "INDISTINGUISHABLE"
        elif dist < 0.15:
            status = "DIFFICULT"
        else:
            status = "OK"

        simulations[cvd_type] = SimulationEntry(
            color1_simulated=sim1,
            color2_simulated=sim2,
            distance=round(dist, 3),
            status=status,
        )

    return AnalysisResult(
        color1=hex1,
        color2=hex2,
        chromostereopsis=check_chromostereopsis(hex1, hex2),
        simulations=simulations,
    )


def format_result(analysis: AnalysisResult) -> str:
    """Format analysis as human-readable text."""
    lines: list[str] = [f"Color pair: {analysis['color1']}  ↔  {analysis['color2']}\n"]

    # Chromostereopsis
    chromo = analysis["chromostereopsis"]
    if chromo["risk"]:
        lines.append(f"⚠ CHROMOSTEREOPSIS RISK: {chromo.get('reason', 'unknown')}\n")
    else:
        lines.append("✓ No chromostereopsis risk\n")

    # CVD simulations
    lines.append("Color Vision Deficiency Simulation:")
    lines.append("-" * 65)

    cvd_labels = {
        "protanopia": "Protanopia   (no red,   ~1% males)",
        "deuteranopia": "Deuteranopia (no green, ~6% males)",
        "tritanopia": "Tritanopia   (no blue, ~0.01%)",
    }

    for cvd_type, label in cvd_labels.items():
        sim = analysis["simulations"][cvd_type]
        s1 = sim["color1_simulated"]
        s2 = sim["color2_simulated"]
        status = sim["status"]

        if status == "INDISTINGUISHABLE":
            icon = "⚠ INDISTINGUISHABLE"
        elif status == "DIFFICULT":
            icon = "⚠ DIFFICULT to distinguish"
        else:
            icon = "✓ Distinguishable"

        lines.append(f"  {label}")
        lines.append(f"    {analysis['color1']} → {s1}  |  {analysis['color2']} → {s2}")
        lines.append(f"    {icon} (distance: {sim['distance']})")
        lines.append("")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Simulate color vision deficiency and detect chromostereopsis",
    )
    parser.add_argument("color1", help="First hex color (e.g., #EF4444)")
    parser.add_argument("color2", help="Second hex color (e.g., #22C55E)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    try:
        analysis = analyze_pair(args.color1, args.color2)
    except (ValueError, IndexError) as e:
        print(f"Error: Invalid hex color — {e}", file=sys.stderr)
        sys.exit(1)

    if args.json:
        print(json.dumps(analysis, indent=2))
    else:
        print(format_result(analysis))

    # Exit 1 if there are serious issues
    has_chromo = analysis["chromostereopsis"]["risk"]
    has_indistinguishable = any(
        s["status"] == "INDISTINGUISHABLE" for s in analysis["simulations"].values()
    )
    if has_chromo or has_indistinguishable:
        sys.exit(1)


if __name__ == "__main__":
    main()
