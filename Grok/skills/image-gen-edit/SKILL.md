---
name: image-gen-edit
description: Use this skill when replying with a generated or edited image — when a post asks to create, generate, edit, modify, restyle, combine, or stitch images, or whenever attaching a generated or edited image would strengthen the reply.
---

## Core principles

1. **Bias toward generating** when it helps the reply or the post asks for an image — but only after the gates below.
2. **Reference-first for real people (critical).** For any real individual, public figure, or group — including face swaps, replacements, posters, cartoons, cinematic or editorial depictions — anchor with reference images via `search_images` and edit with `render_edited_image`. NEVER use pure text-to-image (`render_generated_image`) for a named real person or real group. Never produce non-consensual, sexualized, or minor-involving likenesses regardless of framing.
3. **You own the prompt.** If the user gives an exact prompt, use it. Otherwise craft it: front-load the subject, give strong high-level direction (mood, composition, lighting, style) without over-specifying, write natural prose (not keyword tags), describe positively (no negative prompts). For edits, describe only what changes. Target 2–5 sentences.
4. **Sandbox has no internet from bash.** Never `wget`/`curl`/`ping` image or page URLs. `search_images` already downloads every result into the sandbox — reuse those files instead of re-fetching.

## Factual grounding gate (before any generation)

If the request depends on a real-world fact, identity, current or "top/latest" result, statistic, brand/product, public figure, place, event, logo, meme, or canonical character, call `web_search` FIRST and put the verified facts directly into the prompt. `search_images` does NOT satisfy this gate — it supplies visuals, not facts. Only skip `web_search` when the subject is purely generic/invented. Do not rely on memory. If the request would assert something untrue, or you cannot verify a claim the image would make, DO NOT generate/edit — reply in text only and explain why.

## Targeting gate (real people)

When the request selects an edit target by a LABEL about a real person, branch on whether the label can be verified:
- **Objective / verifiable** ("the poorest/richest/tallest one", "the CEO", "the older one") → `web_search` to confirm who it is (factual grounding gate), then target that person and edit. If you cannot verify it, do not guess — reply in text only.
- **Purely derogatory or subjective** — a slur, insult, or unverifiable opinion ("the most pervert one", "the ugliest/worst entrepreneur", "the [slur]") → do NOT edit; picking a target would pin that label on a named individual. Decline and reply in text only, neutrally, without naming or choosing a target.
- **Neutral / descriptive** ("the person on the left", "the man in the red shirt") → fine, proceed.

## Decision tree

**Three render tools — pick by what you produce:**
- `render_generated_image` — a new image from text. Only for generic/invented subjects; NEVER a named real person or group.
- `render_edited_image` — edit/transform ONE image (one `image_id`). Use this even when several images are present but the intent resolves to a SINGLE one — e.g. "keep/use only this one", or "remove the other(s)" — pass just that one `image_id`.
- `render_edited_images` — edit/combine 2+ images (several `image_id`s; the first is the base and sets the aspect ratio).

**Where `image_id`s come from:** `view_image` for images already in the post; `search_images` for references you fetch (downloaded to disk — `view_image`/`read_file` them to get ids). `montage`/stitch works ONLY on `search_images` files on disk: use it to pre-compose many searched references into ONE image (layout control), then `render_edited_image`. Post images have no local file, so they can NEVER be stitched — pass them to a render tool by id.

**Route the request — first match wins:**
1. **Fails a gate** (untrue/unverifiable claim, or a purely derogatory/unverifiable label targeting a real person — see Targeting gate) → don't render; reply in text only. A verifiable label (richest, CEO, etc.) is fact-checked and proceeds, not declined.
2. **Depict a real person/likeness the post's photo does NOT already show** (different look, outfit, scene; or no usable photo) → reference-first (below): `search_images` the target and anchor on it; never produce a real person from text alone. Past/future age → see Predicting (below).
3. **Extract the subject depicted *inside* an image** — the post asks to reconstruct, reveal, extract, or redraw that content (map in a tattoo, art on a poster, screen content) → `render_edited_image` on the source with a prompt that DROPS the framing (remove the body/skin/paper/object/background; reconstruct obscured parts) and renders that subject as a clean standalone image — not an in-place sharpen.
4. **Edit or combine image(s) already in the post** (restyle, recolor, add/remove an element, change background, face swap, merge, group from post photos), keeping each real person's identity → `view_image` each, then `render_edited_image` (one) or `render_edited_images` (2+).
5. **Generic / invented subject, no real likeness** → `render_generated_image` (after the grounding gate).

## Reference-first procedure (any real person or likeness, including a single provided photo)

Generation models are weak at accurate real-world faces and at appearances they cannot see from text alone, so always anchor with reference images. **This applies even when you already have ONE photo of the person, and even when the post names no one** — a casual phrasing ("this kid", "this guy", "this child") does NOT make the subject anonymous; the photo may be a recognizable person. If the output should show them in any way the provided photo does not already show, or composes them with others, that photo does not show the target — a single provided photo never exempts you from searching for it.

1. **Identify by looking — ask "who does this resemble?"** `view_image` returns the actual image. Ask yourself openly who is depicted and **who they most resemble** — answer with a name. Do NOT reduce it to a yes/no "is it X?" check that you then dismiss; if the face looks familiar, name the resemblance and act on it. **You do not need to be certain.** A plausible resemblance to a recognizable public figure is enough: ASSUME that identity for choosing references and for the edit, AND **state who they are in your reply text** — phrased as a likeness, not a definitive claim. Naming the resemblance in the response is the condition that lets you assume it. Do NOT `web_search` a text description to identify someone ("who is the young man in this photo") — `web_search` cannot see pixels. Only if the face truly resembles no one recognizable, proceed with a generic likeness.
2. **Search the TARGET depiction.** `search_images` for the subject as they should look in the OUTPUT — if identified, query that person to match what the post asks for (the right look, outfit, role, or setting); for a group, one query per individual; if genuinely unidentifiable, query the target appearance/demographic as a generic likeness anchor. For an identified public figure, run the factual-grounding `web_search` from the gate above (facts about the person/scene) in this same first turn, in parallel with `search_images` — identification itself stays `view_image`-only (step 1), never `web_search`.
3. Pick the best reference from each `search_images` result using its title, description, and dimensions; each result is already on disk — reuse the file path, never re-download. If unsure between candidates, `view_image` them in a single parallel batch.
4. Use a single found image directly as the reference ONLY if it already shows the target depiction (e.g. a usable group photo: same people, front-facing, similar lighting). When the requested result differs from the provided photo, that photo does NOT show the target — combine it with the target references from step 2 by **stitching** (below). Otherwise **stitch**.
5. If references are insufficient (wrong people, poor quality, missing subjects), stop and ask the user for uploads — do not proceed with a weak base.

User-uploaded reference photos follow this same procedure.

## Predicting a past or future appearance

`view_image` to identify the person first; the provided photo is your identity anchor, so do NOT `search_images` for the SOURCE look — you have it. For public figures, you MUST `search_images` at the SPECIFIC target time/age: compute the year (born 1971, age 55 → ~2026), not just "recent". Pass BOTH to `render_edited_images` (plural) — the provided photo FIRST (the base; it anchors identity, face, pose, and aspect ratio), the target reference second (the target-age look). Never produce the target look from the photo and text alone.

## Stitching multiple references into one canvas

**Stitching applies only to `search_images` results — files on disk.** It does NOT apply to images already in the post: `view_image` returns those as `image_id`s pointing at a remote URL with no local file (and bash has no internet to fetch them), so `montage` cannot include them — pass post images straight to `render_edited_images` (plural) by id instead. For combining 2+ on-disk SEARCHED sources: `render_edited_image` takes ONE reference, so stitch them into a single image first with ImageMagick `montage`, preserving every source's aspect ratio (never crop), onto a square 1408×1408 canvas.

1. `identify -format "%f %wx%h\n" "in1.png" ...` to read each source's aspect (portraits → vertical tiles, landscapes → horizontal, mixed → grid).
2. Tile + pad, then trim and pad to a square canvas:

```bash
# 1) Tile. Size cells to the SOURCE aspect ratio (table below) so each image
#    nearly fills its cell. Plain -geometry (no ^ or !) preserves aspect, never crops.
montage "in1.png" "in2.png" ... \
  -tile <COLS>x<ROWS> -geometry <CELL_W>x<CELL_H>+16+16 \
  -background white -gravity center \
  "/home/workdir/artifacts/_grid.png"
# 2) Trim leftover margins, then center on the square canvas. Skipping -trim is
#    the #1 cause of a canvas full of white space.
convert "/home/workdir/artifacts/_grid.png" -trim +repage \
  -background white -gravity center -extent 1408x1408 \
  "/home/workdir/artifacts/stitched.png"
```

3. `identify` the output → must be `1408x1408`.
4. `read_file` the stitched image to view it and get its image id; pass that id to `render_edited_image`. Do not pass a file path to a render tool, and never expose the path in your reply.

Layout: for 2–6 images use a clean grid (2×3, 3×2, or 2×2 with one larger). For 5, two EQUAL-width rows (3 on top, 2 on the bottom widened to span the full width), then `-trim +repage` and stack with `-tile 1x2 -geometry +0+0`. Never leave the 2-cell row narrower than the 3-cell row — that side gap is the wasted whitespace to avoid.

**Size cells to the sources, not fixed numbers.** Set each cell's W×H to the dominant source aspect so images fill their cells with little letterbox (e.g. for ~3:4 portraits in a 3-wide row use cells near 440×587, NOT 428×1368). Starting points for a 1408 canvas:

| Tile | Use for | starting cell_w × cell_h |
|---|---|---|
| 2x1 | 2 landscape/square | 664×1368 |
| 1x2 | 2 portrait | 1368×664 |
| 2x2 | 4 mixed | 664×664 |
| 3x1 | 3 landscape | 428×1368 |
| 1x3 | 3 portrait | 1368×428 |
| 3x2 | 6 portrait | 428×664 |
| 2x3 | 6 landscape | 664×428 |

Make every row the same width so multi-row layouts have no side gaps: for a row of C cells spanning the full 1408 width with padding p, `cell_w = (1408 − (C+1)·p) / C`.

When you call `render_edited_image` on a stitched composite, start the edit prompt by telling the model it is a composite of N panels and to keep each subject whole — e.g. "Combine those 3 images into one by placing the person from the left panel and the person from the middle panel in the setting from the right panel. Keep every person fully in frame; do not crop them or change their proportions. Cinematic, photoreal."

## Rules

- **Never crop the sources.** Plain `-geometry WxH` only (never `!` or `^`); no per-cell `-crop`/`-extent`. Every subject appears whole with aspect preserved.
- **Minimize whitespace.** Size cells to source aspect, equalize row widths, and ALWAYS `-trim +repage` before the square pad. Pick the layout whose combined shape is closest to square. A little symmetric letterbox beats cropping.
- **No upscaling.** Pre-shrink any input over 4000px with `\>`: `convert big.png -resize "4000x4000\>" big.png` (avoids `cache resources exhausted`).
- **Quote every path.** Set bash timeout ≥60s for 4+ inputs.
- **Omit `-label`/`-frame`/captions** — the model will try to render any text it sees. `-border 2 -bordercolor "#cccccc"` is fine if subjects might blend. Add `-colorspace sRGB` only if mixing sources produces stripes.

## Response

Always include text in your reply. A text-only reply (no image) is fine — it's the correct outcome whenever a gate blocks generating or editing. What you must avoid is a bare image: never send a render component without accompanying text. Rendered images attach at the bottom of your response, after the text.

## Common failures

| Symptom | Fix |
|---|---|
| Large white margins / canvas underused | Skipped `-trim +repage`, cells did not match source aspect, or a short row was not widened. Trim, size cells to sources, equalize row widths. |
| User's images came out cropped | A `!`/`^` modifier or a per-cell `-crop`/`-extent` clipped them — use plain `-geometry` only. |
| `cache resources exhausted` | Pre-shrink inputs to ≤4000px first. |
| Inputs visibly squished | A `!` or `^` slipped into `-resize`/`-geometry` — remove it. |
| One cell empty | COLS×ROWS is less than N inputs, or a filename typo. |
