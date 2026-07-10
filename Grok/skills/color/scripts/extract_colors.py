#!/usr/bin/env python3
"""Extract dominant colors from an image file.

Usage:
    python extract_colors.py screenshot.png
    python extract_colors.py screenshot.png --top 8
    python extract_colors.py screenshot.png --json
    python extract_colors.py screenshot.png --audit > palette.json
    python extract_colors.py screenshot.png --check

Extracts the most prominent colors by quantizing the image down to
a small palette and reporting each color with its pixel share.

Use --audit to generate a palette.json with every foreground/background
pair, ready to pipe into check_contrast.py --audit.

Use --check to extract colors AND run WCAG contrast checks on all
plausible pairs in a single command (no intermediate files needed).

Requires Pillow: pip install Pillow
"""

from __future__ import annotations

import argparse
import json
import sys
import warnings
from typing import TypedDict

try:
    from PIL import Image
except ImportError:
    print(
        "Error: Pillow is required for color extraction.\nInstall it with: pip install Pillow",
        file=sys.stderr,
    )
    sys.exit(1)


class ColorEntry(TypedDict):
    hex: str
    rgb: list[int]
    pixels: int
    share: float


class AuditPair(TypedDict):
    foreground: str
    background: str
    label: str


def _rgb_distance(c1: list[int], c2: list[int]) -> float:
    """Euclidean distance between two RGB colors (0-255 scale)."""
    return ((c1[0] - c2[0]) ** 2 + (c1[1] - c2[1]) ** 2 + (c1[2] - c2[2]) ** 2) ** 0.5


def _hue_from_rgb(r: int, g: int, b: int) -> float:
    """Return hue in degrees (0-360) from RGB 0-255. Returns -1 for achromatic."""
    import colorsys

    if r == g == b:
        return -1.0
    h, _, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
    if s < 0.08:  # nearly achromatic
        return -1.0
    return h * 360


def _hue_distance(h1: float, h2: float) -> float:
    """Circular hue distance in degrees. Returns 0 if either is achromatic (-1)."""
    if h1 < 0 or h2 < 0:
        return 0.0
    d = abs(h1 - h2)
    return min(d, 360 - d)


def _deduplicate(colors: list[ColorEntry], threshold: float = 35.0) -> list[ColorEntry]:
    """Merge colors that are perceptually close, summing their pixel counts.

    Iterates in frequency order; each new color is merged into the nearest
    existing cluster if within threshold, otherwise starts a new cluster.

    Hue-aware: two colors with hue distance > 40° are never merged, even if
    their RGB distance is small.  This preserves small accent colors (e.g. red
    text on a dark navy slide) that would otherwise be swallowed by a dominant
    background cluster.
    """
    merged: list[ColorEntry] = []
    for c in colors:
        c_hue = _hue_from_rgb(*c["rgb"])
        found = False
        for m in merged:
            m_hue = _hue_from_rgb(*m["rgb"])
            # Never merge chromatically distinct colors
            if _hue_distance(c_hue, m_hue) > 40:
                continue
            if _rgb_distance(c["rgb"], m["rgb"]) < threshold:
                m["pixels"] += c["pixels"]
                found = True
                break
        if not found:
            # Copy so we don't mutate the original
            merged.append(
                ColorEntry(
                    hex=c["hex"],
                    rgb=list(c["rgb"]),
                    pixels=c["pixels"],
                    share=0.0,
                )
            )

    # Recalculate shares after merging
    total = sum(m["pixels"] for m in merged)
    if total > 0:
        for m in merged:
            m["share"] = round(m["pixels"] / total * 100, 1)

    merged.sort(key=lambda x: x["pixels"], reverse=True)
    return merged


def _recover_accent_colors(
    image_path: str,
    existing: list[ColorEntry],
    min_share: float = 0.001,
) -> list[ColorEntry]:
    """Scan image for chromatically distinct accent colors missed by quantization.

    Finds pixel clusters whose hue differs from all existing colors by ≥40°.
    This catches small-but-important accent text (e.g. red numbers on a navy slide)
    that median-cut quantization merges into the dominant background.

    Uses NEAREST resampling at higher resolution to avoid LANCZOS blending
    small accent text into the surrounding background.
    """
    import collections

    # Only use hues from dominant colors (share > 0.5%) as the baseline.
    # Low-share colors from quantization may be LANCZOS blend artifacts
    # (e.g. red text blended into navy → dark maroon) whose hue would
    # wrongly prevent recovery of the true accent color.
    dominant = [c for c in existing if c["share"] > 0.5]
    existing_hues: list[float] = []
    for c in dominant:
        h = _hue_from_rgb(*c["rgb"])
        if h >= 0:
            existing_hues.append(h)

    # Higher res + NEAREST to preserve small accent regions accurately
    img = Image.open(image_path).convert("RGB")
    max_dim = 1000
    if max(img.size) > max_dim:
        ratio = max_dim / max(img.size)
        new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
        img = img.resize(new_size, Image.Resampling.NEAREST)

    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message="Image.Image.getdata")
        pixels: list[tuple[int, int, int]] = list(img.getdata())  # type: ignore[arg-type]
    total = len(pixels)
    if total == 0:
        return []

    # Collect pixels whose hue is far from all existing colors
    outlier_counts: dict[tuple[int, int, int], int] = collections.defaultdict(int)
    for r, g, b in pixels:
        h = _hue_from_rgb(r, g, b)
        if h < 0:
            continue  # achromatic, skip
        # Check if this hue is far from every existing color
        is_outlier = (
            all(_hue_distance(h, eh) > 40 for eh in existing_hues) if existing_hues else True
        )
        if is_outlier:
            # Light snap (nearest 2) preserves color fidelity
            snapped = ((r >> 1) << 1, (g >> 1) << 1, (b >> 1) << 1)
            outlier_counts[snapped] += 1

    if not outlier_counts:
        return []

    # Build ColorEntry list from outliers
    outlier_colors: list[ColorEntry] = []
    for (r, g, b), count in outlier_counts.items():
        share = count / total
        if share >= min_share:
            outlier_colors.append(
                ColorEntry(
                    hex=f"#{r:02X}{g:02X}{b:02X}",
                    rgb=[r, g, b],
                    pixels=count,
                    share=round(share * 100, 1),
                )
            )

    # Dedup outliers among themselves, then sort
    if outlier_colors:
        outlier_colors.sort(key=lambda x: x["pixels"], reverse=True)
        outlier_colors = _deduplicate(outlier_colors, threshold=30.0)

    return outlier_colors


def extract_colors(image_path: str, num_colors: int = 10) -> list[ColorEntry]:
    """Extract dominant colors from an image via quantization.

    Quantizes to 4× the requested count first, then deduplicates similar
    colors so that small-but-distinct elements (accent text, icons) aren't
    drowned out by large background regions.

    After initial extraction, runs an accent-recovery pass that scans for
    chromatically distinct minority colors (different hue region) that the
    quantizer may have merged into a dominant cluster.

    Returns a list of colors sorted by pixel count (most dominant first).
    """
    img = Image.open(image_path).convert("RGB")

    # Resize large images for speed (preserves color distribution)
    max_dim = 600  # slightly higher res to preserve small accent regions
    if max(img.size) > max_dim:
        ratio = max_dim / max(img.size)
        new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
        img = img.resize(new_size, Image.Resampling.LANCZOS)

    # Over-quantize to capture small accent colors, then dedup
    raw_count = min(num_colors * 8, 256)
    quantized = img.quantize(colors=raw_count, method=Image.Quantize.MEDIANCUT)
    palette_data = quantized.getpalette()
    if palette_data is None:
        return []

    # Count pixels per palette index using histogram (avoids deprecated getdata)
    histogram = quantized.histogram()
    total_pixels = sum(histogram[:raw_count])
    raw_colors: list[ColorEntry] = []

    for idx in range(raw_count):
        count = histogram[idx]
        if count == 0:
            continue
        r = palette_data[idx * 3]
        g = palette_data[idx * 3 + 1]
        b = palette_data[idx * 3 + 2]
        raw_colors.append(
            ColorEntry(
                hex=f"#{r:02X}{g:02X}{b:02X}",
                rgb=[r, g, b],
                pixels=count,
                share=round(count / total_pixels * 100, 1) if total_pixels else 0.0,
            )
        )

    # Sort by frequency before dedup (most common first = cluster anchors)
    raw_colors.sort(key=lambda x: x["pixels"], reverse=True)

    # Merge near-duplicates, then trim to requested count
    deduped = _deduplicate(raw_colors)
    main_colors = deduped[:num_colors]

    # Accent recovery: find chromatically distinct minority colors
    accents = _recover_accent_colors(image_path, main_colors)
    if accents:
        # Merge accents in, keeping total ≤ num_colors
        # Replace the least-significant main colors with accents
        combined = main_colors + accents
        # Re-sort but keep accents visible even if small
        combined.sort(key=lambda x: x["pixels"], reverse=True)
        # Deduplicate the combined list
        combined = _deduplicate(combined, threshold=30.0)
        return combined[:num_colors]

    return main_colors


def relative_luminance(r: int, g: int, b: int) -> float:
    """WCAG relative luminance from RGB 0-255."""
    rs = r / 255
    gs = g / 255
    bs = b / 255
    r_lin = rs / 12.92 if rs <= 0.03928 else ((rs + 0.055) / 1.055) ** 2.4
    g_lin = gs / 12.92 if gs <= 0.03928 else ((gs + 0.055) / 1.055) ** 2.4
    b_lin = bs / 12.92 if bs <= 0.03928 else ((bs + 0.055) / 1.055) ** 2.4
    return 0.2126 * r_lin + 0.7152 * g_lin + 0.0722 * b_lin


def contrast_ratio(hex1: str, hex2: str) -> float:
    """WCAG contrast ratio between two hex colors."""

    def _lum(hex_color: str) -> float:
        h = hex_color.lstrip("#")
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return relative_luminance(r, g, b)

    l1, l2 = _lum(hex1), _lum(hex2)
    lighter, darker = max(l1, l2), min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def build_audit_pairs(colors: list[ColorEntry]) -> list[AuditPair]:
    """Build foreground/background pairs for contrast auditing.

    Pairs each darker color (as foreground) with each lighter color
    (as background) based on luminance. Skips pairs where both colors
    are on the same side of the luminance spectrum since those are
    unlikely to be real text-on-background combinations.
    """
    # Compute luminance for each color
    with_lum: list[tuple[ColorEntry, float]] = []
    for c in colors:
        lum = relative_luminance(c["rgb"][0], c["rgb"][1], c["rgb"][2])
        with_lum.append((c, lum))

    pairs: list[AuditPair] = []
    for i, (c1, lum1) in enumerate(with_lum):
        for c2, lum2 in with_lum[i + 1 :]:
            # Only pair if there's meaningful luminance separation
            lighter = max(lum1, lum2)
            darker = min(lum1, lum2)
            ratio = (lighter + 0.05) / (darker + 0.05)
            if ratio < 1.5:
                continue  # Too similar, unlikely to be a real pair

            if lum1 < lum2:
                fg, bg = c1["hex"], c2["hex"]
            else:
                fg, bg = c2["hex"], c1["hex"]

            pairs.append(
                AuditPair(
                    foreground=fg,
                    background=bg,
                    label=f"{fg} on {bg}",
                )
            )

    return pairs


def format_table(colors: list[ColorEntry]) -> str:
    """Format extracted colors as a readable table."""
    lines: list[str] = ["  #   Hex       RGB              Share"]
    lines.append("  " + "-" * 42)
    for i, c in enumerate(colors, 1):
        r, g, b = c["rgb"]
        bar_len = int(c["share"] / 5)  # rough visual bar
        bar = "█" * bar_len
        lines.append(f"  {i:<3} {c['hex']}   ({r:>3}, {g:>3}, {b:>3})   {c['share']:>5.1f}%  {bar}")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract dominant colors from an image",
    )
    parser.add_argument("image", help="Path to image file (PNG, JPG, etc.)")
    parser.add_argument(
        "--top",
        type=int,
        default=10,
        metavar="N",
        help="Number of colors to extract (default: 10)",
    )
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument(
        "--audit",
        action="store_true",
        help="Output palette.json for use with check_contrast.py --audit",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Extract colors and run WCAG contrast checks on all pairs in one step",
    )
    args = parser.parse_args()

    try:
        colors = extract_colors(args.image, args.top)
    except FileNotFoundError:
        print(f"Error: File not found: {args.image}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: Could not read image: {e}", file=sys.stderr)
        sys.exit(1)

    if not colors:
        print("No colors extracted.", file=sys.stderr)
        sys.exit(1)

    if args.check:
        pairs = build_audit_pairs(colors)
        print(f"Dominant colors in {args.image}:\n")
        print(format_table(colors))
        print(f"\n  {len(colors)} colors extracted, {len(pairs)} pairs to check.\n")
        print("WCAG Contrast Audit:")
        print("-" * 70)
        failures = 0
        for p in pairs:
            ratio = contrast_ratio(p["foreground"], p["background"])
            pass_aa = ratio >= 4.5
            pass_ui = ratio >= 3.0
            if not pass_aa:
                failures += 1
            icon = "✓" if pass_aa else ("~" if pass_ui else "✗")
            grade = "AA" if pass_aa else ("UI-only" if pass_ui else "FAIL")
            print(f"  {icon} {ratio:>5.1f}:1  [{grade:<7}]  {p['label']}")
        print()
        passed = len(pairs) - failures
        print(f"  {passed}/{len(pairs)} pairs pass WCAG AA for normal text")
        if failures:
            print(f"  ⚠ {failures} pair(s) fail — review these for accessibility")
        sys.exit(1 if failures else 0)
    elif args.audit:
        pairs = build_audit_pairs(colors)
        print(json.dumps({"pairs": pairs}, indent=2))
    elif args.json:
        print(json.dumps(colors, indent=2))
    else:
        print(f"Dominant colors in {args.image}:\n")
        print(format_table(colors))
        print(f"\n  {len(colors)} colors extracted. Use --check to run contrast audit.")


if __name__ == "__main__":
    main()
