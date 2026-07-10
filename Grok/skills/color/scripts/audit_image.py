#!/usr/bin/env python3
"""Full color accessibility audit of a screenshot in one command.

Usage:
    python audit_image.py screenshot.png
    python audit_image.py screenshot.png --json

Runs every check in a single pass:
  1. Extracts all colors (including small accent colors)
  2. Auto-classifies roles (background, text, accent, surface)
  3. Checks WCAG contrast for every meaningful pair
  4. Runs CVD simulation + chromostereopsis detection on failing/risky pairs
  5. Reports issues for review

Requires Pillow: pip install Pillow
"""

from __future__ import annotations

import argparse
import colorsys
import json
import math
import sys
import warnings
from typing import TypedDict

try:
    from PIL import Image
except ImportError:
    print(
        "Error: Pillow is required.\nInstall with: pip install Pillow",
        file=sys.stderr,
    )
    sys.exit(1)


# ── Types ────────────────────────────────────────────────────────────


class ExtractedColor(TypedDict):
    """Color entry returned by extract_colors_from_image."""

    hex: str
    rgb: list[int]
    pixels: int
    share: float


class ColorInfo(TypedDict):
    hex: str
    rgb: list[int]
    share: float
    role: str  # "background", "text", "accent", "surface", "unknown"


class PairResult(TypedDict):
    foreground: str
    background: str
    label: str
    ratio: float
    pass_aa: bool
    pass_aaa: bool
    pass_ui: bool


class CVDEntry(TypedDict):
    type: str
    fg_simulated: str
    bg_simulated: str
    distance: float
    status: str  # "OK", "DIFFICULT", "INDISTINGUISHABLE"


class HazardResult(TypedDict):
    pair: str
    chromostereopsis: bool
    chromo_reason: str
    cvd: list[CVDEntry]


class AuditReport(TypedDict):
    image: str
    colors: list[ColorInfo]
    contrast: list[PairResult]
    hazards: list[HazardResult]
    summary: dict[str, object]


# ── Color math ───────────────────────────────────────────────────────


def _srgb_to_linear(c: float) -> float:
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _linear_to_srgb(c: float) -> float:
    c = max(0.0, min(1.0, c))
    return c * 12.92 if c <= 0.0031308 else 1.055 * (c ** (1 / 2.4)) - 0.055


def hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    if len(h) == 3:
        h = h[0] * 2 + h[1] * 2 + h[2] * 2
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def relative_luminance(hex_color: str) -> float:
    r, g, b = hex_to_rgb(hex_color)
    rs, gs, bs = r / 255, g / 255, b / 255
    r_lin = _srgb_to_linear(rs)
    g_lin = _srgb_to_linear(gs)
    b_lin = _srgb_to_linear(bs)
    return 0.2126 * r_lin + 0.7152 * g_lin + 0.0722 * b_lin


def contrast_ratio(c1: str, c2: str) -> float:
    l1, l2 = relative_luminance(c1), relative_luminance(c2)
    lighter, darker = max(l1, l2), min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def hue_sat_light(hex_color: str) -> tuple[float, float, float]:
    """Returns (hue 0-360, saturation 0-100, lightness 0-100)."""
    r, g, b = hex_to_rgb(hex_color)
    h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
    return h * 360, s * 100, l * 100


def hsl_to_hex(h: float, s: float, l: float) -> str:
    r, g, b = colorsys.hls_to_rgb(h / 360, l / 100, s / 100)
    return f"#{int(round(r * 255)):02X}{int(round(g * 255)):02X}{int(round(b * 255)):02X}"


# ── CVD simulation (Brettel/Viénot matrices) ────────────────────────

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

CVD_LABELS = {
    "protanopia": "Protanopia   (no red,   ~1% males)",
    "deuteranopia": "Deuteranopia (no green, ~6% males)",
    "tritanopia": "Tritanopia   (no blue,  ~0.01%)",
}


def _simulate_cvd_hex(hex_color: str, cvd_type: str) -> str:
    r, g, b = hex_to_rgb(hex_color)
    rl, gl, bl = _srgb_to_linear(r / 255), _srgb_to_linear(g / 255), _srgb_to_linear(b / 255)
    m = CVD_MATRICES[cvd_type]
    sr = m[0][0] * rl + m[0][1] * gl + m[0][2] * bl
    sg = m[1][0] * rl + m[1][1] * gl + m[1][2] * bl
    sb = m[2][0] * rl + m[2][1] * gl + m[2][2] * bl
    ro = int(round(_linear_to_srgb(sr) * 255))
    go = int(round(_linear_to_srgb(sg) * 255))
    bo = int(round(_linear_to_srgb(sb) * 255))
    return f"#{ro:02X}{go:02X}{bo:02X}"


def _cvd_distance(hex1: str, hex2: str) -> float:
    r1, g1, b1 = hex_to_rgb(hex1)
    r2, g2, b2 = hex_to_rgb(hex2)
    rl1, gl1, bl1 = _srgb_to_linear(r1 / 255), _srgb_to_linear(g1 / 255), _srgb_to_linear(b1 / 255)
    rl2, gl2, bl2 = _srgb_to_linear(r2 / 255), _srgb_to_linear(g2 / 255), _srgb_to_linear(b2 / 255)
    return math.sqrt((rl1 - rl2) ** 2 + (gl1 - gl2) ** 2 + (bl1 - bl2) ** 2)


def check_chromostereopsis(hex1: str, hex2: str) -> tuple[bool, str]:
    h1, s1, _ = hue_sat_light(hex1)
    h2, s2, _ = hue_sat_light(hex2)

    def is_red(h: float) -> bool:
        return h <= 30 or h >= 330

    def is_blue(h: float) -> bool:
        return 210 <= h <= 270

    both_sat = s1 >= 60 and s2 >= 60
    red_blue = (is_red(h1) and is_blue(h2)) or (is_red(h2) and is_blue(h1))

    if red_blue and both_sat:
        return True, "High-saturation red + blue causes depth/vibration illusion"
    return False, ""


# ── Color extraction (using extract_colors module) ───────────────────


def _hue_from_rgb(r: int, g: int, b: int) -> float:
    if r == g == b:
        return -1.0
    h, _, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
    if s < 0.08:
        return -1.0
    return h * 360


def _hue_distance(h1: float, h2: float) -> float:
    if h1 < 0 or h2 < 0:
        return 0.0
    d = abs(h1 - h2)
    return min(d, 360 - d)


def _rgb_dist(c1: list[int], c2: list[int]) -> float:
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(c1, c2)))


def _point_to_segment_dist(
    point: list[float],
    a: list[float],
    b: list[float],
) -> tuple[float, float]:
    """Distance from *point* to line segment *a*–*b*.

    Returns ``(distance, t)`` where *t* is the projection parameter
    (0 → at *a*, 1 → at *b*).
    """
    ab = [b[k] - a[k] for k in range(3)]
    ap = [point[k] - a[k] for k in range(3)]
    ab_len_sq = sum(x * x for x in ab)
    if ab_len_sq < 1e-10:
        return math.sqrt(sum((point[k] - a[k]) ** 2 for k in range(3))), 0.0
    t = sum(ap[k] * ab[k] for k in range(3)) / ab_len_sq
    t_clamped = max(0.0, min(1.0, t))
    closest = [a[k] + t_clamped * ab[k] for k in range(3)]
    return math.sqrt(sum((point[k] - closest[k]) ** 2 for k in range(3))), t


def _filter_artifacts(colors: list[ExtractedColor]) -> list[ExtractedColor]:
    """Remove colours that are anti-aliasing blends or sub-pixel noise.

    Two independent checks (applied only to low-share colours so real
    accents are never discarded):

    1. **Interpolation** (share < 0.5 %): the colour sits on the RGB
       line segment between two higher-share colours — the classic
       sub-pixel blend at font / shape edges.
    2. **Near-duplicate** (share < 1.0 %): the colour is very close in
       RGB + hue to a dominant colour (≥ 2 % share, ≥ 10× this colour's
       share) — compression noise, dark vignettes, sub-pixel shifts.
    """
    if len(colors) < 3:
        return list(colors)

    kept: list[ExtractedColor] = []

    for color in colors:
        c_rgb = [float(x) for x in color["rgb"]]

        # ── check 1: interpolation artifact ──────────────────────
        if color["share"] < 0.5:
            higher = [o for o in colors if o["share"] > color["share"] and o is not color]
            is_interp = False
            for i, a_col in enumerate(higher):
                a = [float(x) for x in a_col["rgb"]]
                for b_col in higher[i + 1 :]:
                    b = [float(x) for x in b_col["rgb"]]
                    dist, t = _point_to_segment_dist(c_rgb, a, b)
                    if 0.0 <= t <= 1.0 and dist < 30.0:
                        is_interp = True
                        break
                if is_interp:
                    break
            if is_interp:
                continue

        # ── check 2: near-duplicate of a dominant colour ─────────
        if color["share"] < 1.0:
            c_hue = _hue_from_rgb(*color["rgb"])
            is_dup = False
            for dom in colors:
                if dom is color or dom["share"] < 2.0:
                    continue
                d_hue = _hue_from_rgb(*dom["rgb"])
                hue_ok = (c_hue < 0 and d_hue < 0) or (
                    c_hue >= 0 and d_hue >= 0 and _hue_distance(c_hue, d_hue) < 30
                )
                if not hue_ok:
                    continue
                if (
                    _rgb_dist(color["rgb"], dom["rgb"]) < 55
                    and dom["share"] / max(color["share"], 0.01) > 10
                ):
                    is_dup = True
                    break
            if is_dup:
                continue

        kept.append(color)

    # Recalculate shares after filtering.
    total = sum(c["pixels"] for c in kept)
    for c in kept:
        c["share"] = round(c["pixels"] / total * 100, 1) if total else 0.0
    kept.sort(key=lambda x: x["pixels"], reverse=True)
    return kept


def extract_colors_from_image(image_path: str, num_colors: int = 12) -> list[ExtractedColor]:
    """Extract colors with accent recovery.  Returns list of ExtractedColor dicts."""
    import collections

    img = Image.open(image_path).convert("RGB")

    # Resize for speed
    max_dim = 600
    if max(img.size) > max_dim:
        ratio = max_dim / max(img.size)
        new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
        img = img.resize(new_size, Image.Resampling.LANCZOS)

    # --- Phase 1: quantization for dominant colors ---
    raw_count = min(num_colors * 8, 256)
    quantized = img.quantize(colors=raw_count, method=Image.Quantize.MEDIANCUT)
    palette_data = quantized.getpalette()
    if palette_data is None:
        return []

    histogram = quantized.histogram()
    total_pixels = sum(histogram[:raw_count])
    raw_colors: list[ExtractedColor] = []
    for idx in range(raw_count):
        count = histogram[idx]
        if count == 0:
            continue
        r = palette_data[idx * 3]
        g = palette_data[idx * 3 + 1]
        b = palette_data[idx * 3 + 2]
        raw_colors.append(
            ExtractedColor(
                hex=f"#{r:02X}{g:02X}{b:02X}",
                rgb=[r, g, b],
                pixels=count,
                share=round(count / total_pixels * 100, 1) if total_pixels else 0.0,
            )
        )

    raw_colors.sort(key=lambda x: x["pixels"], reverse=True)

    # Hue-aware dedup
    merged: list[ExtractedColor] = []
    for c in raw_colors:
        c_hue = _hue_from_rgb(*c["rgb"])
        found = False
        for m in merged:
            m_hue = _hue_from_rgb(*m["rgb"])
            if _hue_distance(c_hue, m_hue) > 40:
                continue
            if _rgb_dist(c["rgb"], m["rgb"]) < 35:
                m["pixels"] += c["pixels"]
                found = True
                break
        if not found:
            merged.append(
                ExtractedColor(
                    hex=c["hex"], rgb=list(c["rgb"]), pixels=c["pixels"], share=c["share"]
                )
            )
    # Recalc shares
    total = sum(m["pixels"] for m in merged)
    for m in merged:
        m["share"] = round(m["pixels"] / total * 100, 1) if total else 0.0
    merged.sort(key=lambda x: x["pixels"], reverse=True)
    main_colors = merged[:num_colors]

    # --- Phase 2: accent recovery ---
    # Use a higher-res version with NEAREST sampling for accent detection.
    # LANCZOS blends small text into the background, producing muddy colors.
    accent_img = Image.open(image_path).convert("RGB")
    accent_max = 1000
    if max(accent_img.size) > accent_max:
        ratio = accent_max / max(accent_img.size)
        accent_size = (int(accent_img.size[0] * ratio), int(accent_img.size[1] * ratio))
        accent_img = accent_img.resize(accent_size, Image.Resampling.NEAREST)

    # Only use hues from dominant colors (share > 0.5%) as the baseline.
    # Low-share colors from quantization may be LANCZOS blend artifacts
    # (e.g. red text blended into navy → dark maroon) whose hue would
    # wrongly prevent recovery of the true accent color.
    dominant: list[ExtractedColor] = [c for c in main_colors if c["share"] > 0.5]
    existing_hues = [_hue_from_rgb(*c["rgb"]) for c in dominant if _hue_from_rgb(*c["rgb"]) >= 0]
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message="Image.Image.getdata")
        pixels: list[tuple[int, int, int]] = list(accent_img.getdata())  # type: ignore[arg-type]
    outlier_counts: dict[tuple[int, int, int], int] = collections.defaultdict(int)
    for r, g, b in pixels:
        h = _hue_from_rgb(r, g, b)
        if h < 0:
            continue
        if existing_hues and all(_hue_distance(h, eh) > 40 for eh in existing_hues):
            # Light snap (nearest 2) preserves color fidelity
            snapped = ((r >> 1) << 1, (g >> 1) << 1, (b >> 1) << 1)
            outlier_counts[snapped] += 1

    if outlier_counts:
        outlier_list: list[ExtractedColor] = []
        for (r, g, b), count in outlier_counts.items():
            share = count / len(pixels)
            if share >= 0.001:  # at least 0.1% of pixels
                outlier_list.append(
                    ExtractedColor(
                        hex=f"#{r:02X}{g:02X}{b:02X}",
                        rgb=[r, g, b],
                        pixels=count,
                        share=round(share * 100, 1),
                    )
                )
        if outlier_list:
            outlier_list.sort(key=lambda x: x["pixels"], reverse=True)
            # Dedup outliers
            deduped_outliers: list[ExtractedColor] = []
            for c in outlier_list:
                found = False
                for m in deduped_outliers:
                    if _rgb_dist(c["rgb"], m["rgb"]) < 30:
                        m["pixels"] += c["pixels"]
                        found = True
                        break
                if not found:
                    deduped_outliers.append(
                        ExtractedColor(
                            hex=c["hex"],
                            rgb=list(c["rgb"]),
                            pixels=c["pixels"],
                            share=c["share"],
                        )
                    )
            # Add top outliers to main colors
            for o in deduped_outliers[:3]:  # up to 3 accent colors
                main_colors.append(o)

    # Final dedup + sort
    total = sum(c["pixels"] for c in main_colors)
    for c in main_colors:
        c["share"] = round(c["pixels"] / total * 100, 1) if total else 0.0
    main_colors.sort(key=lambda x: x["pixels"], reverse=True)
    return main_colors[:num_colors]


# ── Role classification ──────────────────────────────────────────────


def classify_roles(colors: list[ExtractedColor]) -> list[ColorInfo]:
    """Auto-classify colors as background, text, accent, or surface."""
    if not colors:
        return []

    result: list[ColorInfo] = []

    # Largest share = background
    bg_hex = colors[0]["hex"]
    bg_lum = relative_luminance(bg_hex)

    for i, c in enumerate(colors):
        lum = relative_luminance(c["hex"])
        _, sat, _light = hue_sat_light(c["hex"])

        if i == 0:
            role = "background"
        elif c["share"] < 2.0 and sat > 25:
            # Small share + chromatic = accent
            role = "accent"
        elif abs(lum - bg_lum) > 0.3:
            # High luminance contrast to bg = likely text
            role = "text"
        elif c["share"] >= 2.0 and abs(lum - bg_lum) < 0.1:
            # Similar luminance, decent share = secondary surface
            role = "surface"
        else:
            role = "unknown"

        result.append(
            ColorInfo(
                hex=c["hex"],
                rgb=c["rgb"],
                share=c["share"],
                role=role,
            )
        )

    return result


# ── Build meaningful pairs ───────────────────────────────────────────


def build_pairs(colors: list[ColorInfo]) -> list[PairResult]:
    """Build foreground/background pairs based on classified roles."""
    pairs: list[PairResult] = []
    seen: set[tuple[str, str]] = set()

    # Find backgrounds/surfaces
    backgrounds: list[ColorInfo] = [c for c in colors if c["role"] in ("background", "surface")]
    foregrounds: list[ColorInfo] = [c for c in colors if c["role"] in ("text", "accent")]

    if not backgrounds:
        backgrounds = [colors[0]]  # fallback: largest = bg
    if not foregrounds:
        foregrounds = [c for c in colors[1:]]  # fallback: everything else

    for fg in foregrounds:
        for bg in backgrounds:
            if fg["hex"] == bg["hex"]:
                continue
            key = (fg["hex"], bg["hex"])
            if key in seen:
                continue
            seen.add(key)

            ratio = contrast_ratio(fg["hex"], bg["hex"])
            label = f"{fg['role']} ({fg['hex']}) on {bg['role']} ({bg['hex']})"
            pairs.append(
                PairResult(
                    foreground=fg["hex"],
                    background=bg["hex"],
                    label=label,
                    ratio=round(ratio, 2),
                    pass_aa=ratio >= 4.5,
                    pass_aaa=ratio >= 7.0,
                    pass_ui=ratio >= 3.0,
                )
            )

    # Also check surface-to-background boundary contrast
    bgs = [c for c in colors if c["role"] == "background"]
    surfaces = [c for c in colors if c["role"] == "surface"]
    for s in surfaces:
        for b in bgs:
            key = (s["hex"], b["hex"])
            if key in seen:
                continue
            seen.add(key)
            ratio = contrast_ratio(s["hex"], b["hex"])
            pairs.append(
                PairResult(
                    foreground=s["hex"],
                    background=b["hex"],
                    label=f"surface boundary ({s['hex']} vs {b['hex']})",
                    ratio=round(ratio, 2),
                    pass_aa=ratio >= 3.0,  # boundaries are UI components, not text (3:1)
                    pass_aaa=ratio >= 4.5,
                    pass_ui=ratio >= 3.0,
                )
            )

    # Sort: failures first, then by ratio ascending
    pairs.sort(key=lambda p: (p["pass_aa"], p["ratio"]))
    return pairs


# ── Hazard checks ────────────────────────────────────────────────────


def check_hazards(pairs: list[PairResult]) -> list[HazardResult]:
    """Run CVD + chromostereopsis on pairs that fail or involve chromatic colors."""
    results: list[HazardResult] = []

    for p in pairs:
        fg, bg = p["foreground"], p["background"]
        _, fg_sat, _ = hue_sat_light(fg)
        _, bg_sat, _ = hue_sat_light(bg)

        # Only check pairs that fail contrast OR involve saturated colors
        if p["pass_aa"] and fg_sat < 30 and bg_sat < 30:
            continue

        chromo_risk, chromo_reason = check_chromostereopsis(fg, bg)

        cvd_entries: list[CVDEntry] = []
        for cvd_type, label in CVD_LABELS.items():
            sim_fg = _simulate_cvd_hex(fg, cvd_type)
            sim_bg = _simulate_cvd_hex(bg, cvd_type)
            dist = _cvd_distance(sim_fg, sim_bg)

            if dist < 0.05:
                status = "INDISTINGUISHABLE"
            elif dist < 0.15:
                status = "DIFFICULT"
            else:
                status = "OK"

            cvd_entries.append(
                CVDEntry(
                    type=label,
                    fg_simulated=sim_fg,
                    bg_simulated=sim_bg,
                    distance=round(dist, 3),
                    status=status,
                )
            )

        has_issue = chromo_risk or any(e["status"] != "OK" for e in cvd_entries)
        if has_issue:
            results.append(
                HazardResult(
                    pair=f"{fg} on {bg}",
                    chromostereopsis=chromo_risk,
                    chromo_reason=chromo_reason,
                    cvd=cvd_entries,
                )
            )

    return results


# ── Report formatting ────────────────────────────────────────────────


def format_report(report: AuditReport) -> str:
    lines: list[str] = []

    lines.append(f"{'═' * 70}")
    lines.append(f"  COLOR ACCESSIBILITY AUDIT: {report['image']}")
    lines.append(f"{'═' * 70}\n")

    # ── Colors ──
    lines.append("COLORS DETECTED:")
    lines.append(f"  {'#':<4} {'Hex':<10} {'RGB':<18} {'Share':>6}  {'Role'}")
    lines.append(f"  {'-' * 58}")
    for i, c in enumerate(report["colors"], 1):
        r, g, b = c["rgb"]
        lines.append(
            f"  {i:<4} {c['hex']:<10} ({r:>3},{g:>3},{b:>3})      {c['share']:>5.1f}%  {c['role']}"
        )

    # ── Contrast ──
    lines.append(f"\n{'─' * 70}")
    lines.append("CONTRAST AUDIT:")
    failures = [p for p in report["contrast"] if not p["pass_aa"]]
    passes = [p for p in report["contrast"] if p["pass_aa"]]

    if failures:
        lines.append(f"\n  🚨 FAILURES ({len(failures)}):")
        for p in failures:
            is_boundary = "boundary" in p["label"]
            icon = "✗" if not p["pass_ui"] else "~"
            if is_boundary:
                grade = "WEAK" if not p["pass_ui"] else "OK"
            else:
                grade = "FAIL ALL" if not p["pass_ui"] else "UI-only"
            lines.append(f"    {icon} {p['ratio']:>5.1f}:1  [{grade:<8}]  {p['label']}")

    if passes:
        lines.append(f"\n  ✅ PASSING ({len(passes)}):")
        for p in passes:
            grade = "AAA" if p["pass_aaa"] else "AA"
            lines.append(f"    ✓ {p['ratio']:>5.1f}:1  [{grade:<8}]  {p['label']}")

    # ── Hazards ──
    if report["hazards"]:
        lines.append(f"\n{'─' * 70}")
        lines.append("PERCEPTUAL HAZARDS:")
        for h in report["hazards"]:
            lines.append(f"\n  Pair: {h['pair']}")
            if h["chromostereopsis"]:
                lines.append(f"    ⚠ CHROMOSTEREOPSIS: {h['chromo_reason']}")
            for cvd in h["cvd"]:
                if cvd["status"] != "OK":
                    icon = (
                        "⚠ INDISTINGUISHABLE"
                        if cvd["status"] == "INDISTINGUISHABLE"
                        else "⚠ DIFFICULT"
                    )
                    lines.append(f"    {icon} for {cvd['type']} (distance: {cvd['distance']})")

    # ── Summary ──
    lines.append(f"\n{'═' * 70}")
    s = report["summary"]
    lines.append("SUMMARY:")
    lines.append(f"  Colors detected:     {s['total_colors']}")
    lines.append(f"  Pairs checked:       {s['total_pairs']}")
    lines.append(f"  Passing AA:          {s['passing_aa']}")
    lines.append(f"  Failing:             {s['failing']}")
    lines.append(f"  Perceptual hazards:  {s['hazard_count']}")
    verdict = "✅ ALL CLEAR" if s["failing"] == 0 and s["hazard_count"] == 0 else "🚨 ISSUES FOUND"
    lines.append(f"  Verdict:             {verdict}")
    lines.append("")

    return "\n".join(lines)


# ── Main ─────────────────────────────────────────────────────────────


def audit(image_path: str) -> AuditReport:
    raw_colors = extract_colors_from_image(image_path)
    raw_colors = _filter_artifacts(raw_colors)
    colors = classify_roles(raw_colors)
    pairs = build_pairs(colors)
    hazards = check_hazards(pairs)

    return AuditReport(
        image=image_path,
        colors=colors,
        contrast=pairs,
        hazards=hazards,
        summary={
            "total_colors": len(colors),
            "total_pairs": len(pairs),
            "passing_aa": sum(1 for p in pairs if p["pass_aa"]),
            "failing": sum(1 for p in pairs if not p["pass_aa"]),
            "hazard_count": len(hazards),
        },
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Full color accessibility audit of a screenshot",
    )
    parser.add_argument("image", help="Path to image file (PNG, JPG, etc.)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    try:
        report = audit(args.image)
    except FileNotFoundError:
        print(f"Error: File not found: {args.image}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(format_report(report))

    sys.exit(1 if report["summary"]["failing"] or report["summary"]["hazard_count"] else 0)


if __name__ == "__main__":
    main()
