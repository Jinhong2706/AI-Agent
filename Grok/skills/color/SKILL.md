---
name: color
description: Use this skill when the user needs help with color in any project — choosing palettes, checking accessibility/contrast, generating shade scales, avoiding perceptual pitfalls like chromostereopsis, reviewing color choices in designs, or auditing existing UIs.
---

# Color: Best Practices, Accessibility & Perceptual Safety

Practical guidance and sanity-check scripts for choosing, validating, and auditing color in any project.

## Quick Reference

| Task | Approach |
|------|----------|
| **Full audit (start here)** | `python scripts/audit_image.py screenshot.png` |
| Extract colors from image | `python scripts/extract_colors.py screenshot.png` |
| Check contrast ratio | `python scripts/check_contrast.py "#0D9488" "#FFFFFF"` |
| Generate shade scale | `python scripts/generate_palette.py "#0D9488"` |
| Simulate color blindness | `python scripts/simulate_cvd.py "#EF4444" "#22C55E"` |
| Audit all pairs in bulk | `python scripts/check_contrast.py --audit palette.json` |

---

## 1. How to Audit a Design

When reviewing color in an existing design, screenshot, or codebase, **run the full audit in one command**:

```bash
python scripts/audit_image.py screenshot.png
```

This single command does everything:
1. **Extracts every color** including small accent text (uses hue-aware clustering + accent recovery to catch minority colors like red numbers on a navy slide)
2. **Auto-classifies roles** — background, text, accent, surface
3. **Checks WCAG contrast** for every meaningful foreground/background pair
4. **Runs CVD simulation + chromostereopsis detection** on failing/risky pairs

Use `--json` for machine-readable output.

### When to use the individual scripts

The individual scripts are still useful for targeted checks:

```bash
# Check a specific pair you already know about
python scripts/check_contrast.py "#0D9488" "#FFFFFF"

# Simulate CVD for a specific pair
python scripts/simulate_cvd.py "#EF4444" "#22C55E"

# Extract colors without the full audit
python scripts/extract_colors.py screenshot.png --check

# Generate a shade scale from a brand color
python scripts/generate_palette.py "#0D9488" --check
```

### Manual review checklist

After running the audit, also verify these — the automated scan catches contrast and CVD issues, but these require human judgment:

1. **Colored accent text on a dark/colored background** — the #1 failure mode overall
2. **Muted/secondary text** — designers often make it too subtle
3. **Placeholder text in inputs** — commonly fails AA
4. **Disabled state text** — must still be readable if it carries content (WCAG permits lower contrast only for truly inactive controls)
5. **Links that rely on color alone** — must have underline or other non-color indicator
6. **Chart/graph colors** — especially red vs. green data series (CVD failure)
7. **Focus rings** — must hit 3:1 against both the background and the focused element
8. **Error messages** — red text on dark backgrounds often fails contrast

---

## 2. Color Strategy

### The 60-30-10 Rule

- **60% — Dominant** (neutrals/backgrounds): Sets tone without competing
- **30% — Secondary**: Supporting color for structure and variety
- **10% — Accent**: High-contrast moments for CTAs, alerts, key actions

**Choose 2-4 colors max** beyond neutrals. Strategic color beats saturation.

### Semantic Consistency

| Meaning | Typical Colors | Rule |
|---------|---------------|------|
| Success | Green (emerald, mint) | Same color = same meaning everywhere |
| Error | Red/pink (rose, crimson) | Never reuse error colors for decoration |
| Warning | Orange/amber | Must still pass contrast on its background |
| Info | Blue (sky, indigo) | Common for links — pair with underline |
| Neutral | Gray/slate | Add subtle warm/cool tint — avoid pure gray |

---

## 3. Generating Shade Scales

Convert a single hex into an 11-shade scale (50–950) by varying lightness while keeping hue constant. Lighter shades reduce saturation to prevent overly vibrant pastels.

```bash
python scripts/generate_palette.py "#0D9488"
python scripts/generate_palette.py "#0D9488" --check   # also runs WCAG contrast on common pairs
python scripts/generate_palette.py "#0D9488" --json     # machine-readable output
```

### Shade Roles

| Shade | Lightness | Typical Role |
|-------|-----------|-------------|
| 50–100 | 97–94% | Tinted backgrounds, hover states |
| 200–300 | 87–75% | Borders, dividers, disabled states |
| 400 | 62% | Muted/placeholder text (check contrast!) |
| **500** | 48% | **Brand baseline** |
| 600 | 40% | Primary actions, buttons |
| 700–800 | 33–27% | Hover/active states on primary |
| 900–950 | 20–10% | Text on light bg, dark mode backgrounds |

### OKLCH for Perceptual Uniformity

When the target environment supports it, prefer OKLCH over HSL — equal steps in lightness *look* equal to human eyes, making shade scales more visually consistent:

```css
background: oklch(97% 0.01 60);   /* warm tinted neutral */
background: oklch(97% 0.01 250);  /* cool tinted neutral */
```

---

## 4. Accessibility — WCAG Contrast

### Minimum Contrast Ratios

| Content Type | AA | AAA |
|--------------|-----|-----|
| Normal text (<18px) | 4.5:1 | 7:1 |
| Large text (≥18px or ≥14px bold) | 3:1 | 4.5:1 |
| UI components (buttons, icons, focus rings) | 3:1 | — |

**Target AA for all projects. Target AAA for healthcare, government, accessibility-focused apps.**

### Rules of Thumb

- On **light backgrounds**: use shade 600+ for text to pass AA, shade 700+ for AAA.
- On **dark backgrounds**: use shade 50–200 for text. Shade 400 often looks fine but check — it may fail AA on backgrounds darker than shade 900.
- A colored accent on a dark background **must still hit 3:1 minimum** or it's decorative noise. Run the script — don't eyeball it.
- **Two dark shades (both below 40% lightness) almost never pass.** Two light shades (both above 60%) almost never pass. You need colors on *opposite sides of the lightness spectrum*.

### Common Contrast Failure Patterns

**1. Decorative accent text that fails everything.** A colored accent (red, teal, brand color) used for headings, labels, or list markers on a dark background. It *looks* intentional but fails WCAG across the board. Example: red numbers `#CC3333` on navy `#2B3A67` = 2.15:1 — fails AA, AAA, and even UI component minimums. Fix: use a high-luminance accent (white, light gold, pale blue).

**2. Dark accent on dark background.** Two dark colors with different hues but similar luminance. Example: teal `#0D9488` on charcoal `#1F2937` = ~2.1:1. If both colors have lightness below 40%, they almost certainly fail.

**3. Light accent on light background.** Pastel or light brand colors as text on white. Example: light teal shade 300 on white = ~1.8:1. On white, text needs shade 600+ to pass.

**4. Colored text on colored background.** Brand-colored text on a tinted surface (e.g., primary-600 on primary-50). Looks cohesive but often lands in the contrast dead zone. Always run the check.

### Quick Contrast Reference by Lightness

Approximate ratios for lightness pairings (any hue):

| Light Color | Dark Color | Approx. Ratio | Pass AA Text? |
|-------------|------------|----------------|---------------|
| 97% (shade 50) | 10% (shade 950) | ~16:1 | ✅ AAA |
| 94% (shade 100) | 10% (shade 950) | ~14:1 | ✅ AAA |
| 62% (shade 400) | 10% (shade 950) | ~6:1 | ✅ AA |
| 48% (shade 500) | 100% (white) | ~3.5:1 | ❌ Borderline |
| 40% (shade 600) | 100% (white) | ~5.5:1 | ✅ AA |
| 33% (shade 700) | 100% (white) | ~8:1 | ✅ AAA |
| 40% (shade 600) | 20% (shade 900) | ~2.5:1 | ❌ Fail |
| 27% (shade 800) | 10% (shade 950) | ~2:1 | ❌ Fail |

### Checking Contrast

```bash
python scripts/check_contrast.py "#0D9488" "#FFFFFF"
# Contrast ratio: 3.74:1
# Normal text  AA: FAIL ✗    AAA: FAIL ✗
# Large text   AA: PASS ✓    AAA: FAIL ✗
# UI elements  AA: PASS ✓
```

### Bulk Audit

Create a JSON file listing every foreground/background pair, then check them all at once:

```json
{
  "pairs": [
    {"foreground": "#042F2E", "background": "#FFFFFF", "label": "body text"},
    {"foreground": "#FFFFFF", "background": "#0D9488", "label": "primary button"},
    {"foreground": "#CC3333", "background": "#2B3A67", "label": "red accent on navy"}
  ]
}
```

```bash
python scripts/check_contrast.py --audit palette.json
```

### Don't Rely on Color Alone

Color must never be the **only** indicator. Always pair with at least one redundant cue:
- **Icons** (✓ checkmark, ✗ error, ⚠ warning)
- **Text labels** ("Success", "Error")
- **Patterns or shapes** (striped bars, different marker shapes in charts)
- **Underlines** for links (don't rely solely on color to distinguish links from text)

---

## 5. Perceptual Hazards

### Chromostereopsis

**What**: Red and blue light focus at different depths on the retina. When highly saturated red and blue are placed adjacent — especially as text on background — the eye cannot focus both simultaneously, creating a depth/vibration illusion, "swimming" text, and eye strain.

**The spectrum of risk** (not just the extreme case):
- 🔴 **High risk**: Pure red (`#FF0000`) on pure blue (`#0000FF`) — immediately painful
- 🟠 **Moderate risk**: Saturated red/crimson (`#CC3333`) on dark navy (`#2B3A67`) — uncomfortable for extended reading, numbers/text appear to float
- 🟢 **Low risk**: Desaturated warm tone on a muted blue — acceptable if contrast ratio is met

**The key variables** are saturation and hue distance between the red and blue wavelengths. Even moderately saturated reds on dark blues cause discomfort that won't be caught by a pure contrast ratio check.

```bash
python scripts/simulate_cvd.py "#FF0000" "#0000FF"
# ⚠ CHROMOSTEREOPSIS RISK: High-saturation red + blue causes depth/vibration illusion.
```

**Fixes**:
- Desaturate one or both colors (reduce saturation below 60%)
- Separate them with a neutral gap (white, gray, or black border)
- Shift hues closer together (red → orange/coral, blue → teal)
- Add a large luminance gap (make one color much lighter)
- Best fix: use a different accent color entirely (gold, white, or light blue on navy)

### Simultaneous Contrast

Colors appear different depending on their surroundings. A medium gray on white looks darker than the same gray on black. A red next to green looks more vivid than the same red next to orange.

**Practical rule**: Always evaluate colors on their **actual background**, never in isolation. A color that looks fine in a swatch can fail in context.

### Halation

Light text on dark backgrounds can appear to "glow" or bleed, especially for users with astigmatism (~50% of people). The effect is worst with pure white on pure black.

**Fixes**:
- Use **off-white** text on dark backgrounds (e.g., shade 50 or `oklch(93% 0.01 250)`) instead of `#FFFFFF`
- Use **off-black** backgrounds (shade 950 or 900) instead of `#000000`
- Increase font weight slightly on dark backgrounds (text looks thinner against dark)
- Avoid thin/light font weights on dark mode entirely

### Vibrating Boundaries

Two colors with **similar luminance but different hue** create edges that "vibrate" visually. This is distinct from chromostereopsis — it happens with *any* hue pair at matched luminance, not just red/blue.

**Practical test**: Check that adjacent colored regions have a luminance contrast ratio ≥ 3:1:

```bash
python scripts/check_contrast.py "<region1>" "<region2>"
# If ratio is below 3:1, the boundary will shimmer
```

**Fix**: Separate with a neutral border, or adjust one region's lightness.

---

## 6. Color Blindness (CVD) Safety

~8% of males and ~0.5% of females have some form of color vision deficiency.

### Dangerous Pairs

| Type | Affected | Problem Pairs |
|------|----------|---------------|
| Protanopia (no red cones) | ~1% males | Red vs. green, red vs. brown, red on dark backgrounds (red darkens dramatically) |
| Deuteranopia (no green cones) | ~6% males | Green vs. red, green vs. brown, green vs. orange |
| Tritanopia (no blue cones) | ~0.01% | Blue vs. yellow, purple vs. blue |

**Protanopia deserves extra attention**: Red loses nearly all its brightness, collapsing to a dark olive/brown. A red accent on a dark background that's merely "low contrast" for typical vision may become **completely invisible** for protanopes.

### Safe Alternatives

Instead of red/green to show good/bad:
- ✅ **Blue vs. orange** — safe for all CVD types
- ✅ **Luminance differences** — dark vs. light of any hue
- ✅ **Redundant cues** — icons, patterns, labels, shapes alongside color

```bash
python scripts/simulate_cvd.py "#EF4444" "#22C55E"
# Shows simulated appearance for each CVD type
# Flags INDISTINGUISHABLE or DIFFICULT pairs
```

### CVD-Safe Palette Principles

1. Vary **luminance** as much as hue — if two colors have the same brightness, CVD users may not distinguish them
2. Never use red and green as the **only** two semantic colors — always add a third differentiator
3. Test warm colors (red/orange/yellow) against dark backgrounds with protanopia simulation — they darken dramatically
4. Blue is the safest anchor color — it's visible to all CVD types

---

## 7. Dark Mode Best Practices

### Key Principles

- **Swap lightness extremes** (50↔950), keep middle shades near 500
- **Never use pure black** (`#000000`) for backgrounds — it causes OLED smearing, kills elevation hierarchy, and worsens halation. Use shade 950 or 900.
- **Never use pure white** (`#FFFFFF`) for body text on dark — it causes halation. Use shade 50 or an off-white.
- **Brighten primary colors** one shade step (e.g., 600→500) for visibility on dark surfaces
- **Elevation = lightness**: Higher surfaces get lighter backgrounds (opposite of light mode's shadow-based elevation)
- **Every background must have a paired foreground** — if you change a surface color for dark mode, you must also update the text color on it. Unpaired changes break readability.

### Surface Lightness Hierarchy

Dark mode uses lightness (not shadow) to express elevation:

| Layer | Lightness | Shade |
|-------|-----------|-------|
| Lowest (page background) | 8–12% | 950 |
| Mid (cards, panels) | 16–22% | 900 |
| Highest (popovers, modals) | 24–30% | 800–850 |

Each step up should be perceptibly lighter. Aim for ≥5% lightness difference between adjacent layers.

### Text on Dark Surfaces

| Text Role | Recommended | Notes |
|-----------|------------|-------|
| Primary body text | Shade 50 (93–97%) | Off-white, not pure `#FFFFFF` |
| Secondary (captions) | Shade 400 (60–70%) | Check contrast — can be borderline on shade 950 |
| Disabled/placeholder | Shade 500–600 (40–50%) | Usually fails text AA — only acceptable for truly inactive controls |

### Accent Colors on Dark Surfaces

Accents chosen for contrast against white often fail on dark backgrounds. Always re-check:

| Accent | On White | On Shade 950 | Fix |
|--------|----------|-------------|-----|
| Shade 600 | ✅ ~5.7:1 | Often ❌ ~3:1 | Brighten to shade 400–500 |
| Red-600 | ✅ ~5.3:1 | Often ❌ ~2.8:1 | Brighten to red-400 |
| Deep purple | ✅ passes | Almost always ❌ | Lighter tint or switch hue |

### Borders on Dark Surfaces

- Aim for **10–15% lightness difference** from the surface
- Shade 800 border on shade 950 bg ≈ 17% difference ✓
- Shade 900 border on shade 950 bg ≈ 10% difference ✓ (subtle)
- Same shade as background = invisible border ✗

### Background-Foreground Pairing Checklist

Every surface that contains text must have an explicitly paired foreground. When switching to dark mode, both must change together:

- [ ] Page background → body text
- [ ] Card/panel background → card text
- [ ] Button background → button label
- [ ] Input background → input text + placeholder
- [ ] Tooltip/popover background → tooltip text
- [ ] Alert/banner background → alert text
- [ ] Muted/disabled surface → muted text (still must pass 4.5:1 if content is meaningful)

### Common Dark Mode Mistakes

| Mistake | Why It Fails | Fix |
|---------|-------------|-----|
| Pure black background | OLED smearing, no elevation, halation | Use shade 950 or 900 |
| Same primary shade as light mode | Too dark against dark surface, low contrast | Brighten one step (600→500) |
| Pure white text | Halation, eye strain | Use shade 50 or off-white |
| Accent color unchanged | May lose contrast on dark background | Re-check every accent against the dark surface |
| Changed background but not text | Text becomes invisible | Always pair background + foreground |

---

## 8. Anti-Patterns

**NEVER**:
- Use every color in the rainbow — pick 2-4 beyond neutrals
- Apply color randomly without semantic meaning
- Put gray text on colored backgrounds — it looks washed out; use a tint of the background color instead
- Use pure gray for neutrals — add a subtle warm or cool tint for sophistication
- Use pure black (`#000`) or pure white (`#fff`) for large areas
- Violate WCAG contrast requirements — always run the check script, don't eyeball
- Use color as the only indicator of state (accessibility failure)
- Use red text on blue/navy backgrounds (chromostereopsis + low contrast + CVD collapse)
- Use red/green as the only differentiator (color blindness failure)
- Assume a dark-on-dark accent "looks fine" — run the contrast check; the most common color failure is decorative accent text that fails everything below 3:1

---

## Scripts

| Script | Purpose |
|--------|---------|
| **`scripts/audit_image.py`** | **Full audit in one command** — extracts colors, classifies roles, checks contrast, runs CVD/chromostereopsis detection. Use `--json` for machine output. |
| `scripts/extract_colors.py` | Extract colors from a screenshot — `--check` runs contrast audit, `--audit` exports pairs JSON. Includes accent-recovery for small text colors. |
| `scripts/check_contrast.py` | WCAG contrast ratio checker — AA/AAA grading, bulk `--audit` mode |
| `scripts/generate_palette.py` | 11-shade scale generator from one hex — table, `--json`, `--check` for contrast |
| `scripts/simulate_cvd.py` | Color vision deficiency simulator + chromostereopsis detector |

All scripts use **Python 3 stdlib only** except `extract_colors.py` and `audit_image.py` which require **Pillow** (`pip install Pillow`).
