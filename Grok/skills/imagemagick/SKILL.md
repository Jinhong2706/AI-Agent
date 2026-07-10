---
name: imagemagick
description: Use this skill for image processing with ImageMagick — resize, crop, convert format, add watermark/text, composite, annotate, adjust colors, create thumbnails, batch process, make montages/collages, merge images into a strip, and manipulate PNG/JPG/GIF/WebP/SVG images. Note that PDF/PS/EPS processing is disabled by sandbox policy. Triggers on 'merge images into one', 'combine images side by side', 'create image strip', 'image grid', 'resize image', 'crop image', 'convert png to jpg', 'add watermark', 'make thumbnail', 'image collage', 'montage', 'batch convert images', 'compress image', 'rotate image', 'overlay images', 'annotate image', 'adjust brightness', 'imagemagick'.
---

# ImageMagick Skill for Computer-Use Agents

Process static images with ImageMagick (`magick` / `identify`). This skill adds agent-specific safety rules and decision logic on top of ImageMagick knowledge the model already has.

For additional recipes (compositing, montages, batch processing, color adjustments, and more), see `references/recipes.md`.

---

## Safety Policy

### No-overwrite default

Do not overwrite input files. Always write to a new output path unless the user explicitly requests in-place modification.

### Verify output

After processing, verify the output exists and has reasonable dimensions:

```bash
magick identify -format "%f  %wx%h  %m  %b\n" "$OUTPUT"
```

### Other rules

- Quote all file paths.
- Do not delete the input file unless the user explicitly requests it.
- Only use local file paths. Do not pass user-supplied URLs directly to ImageMagick.
- Clean up temp files after successful operations.
- Use `-limit memory 256MiB -limit disk 512MiB` for large batch operations to prevent OOM in shared environments.

### Sandbox policy

The sandbox has an ImageMagick policy that restricts resource usage and disables risky coders (PS, EPS, PDF via Ghostscript). If a command fails with a policy error, do not try to bypass it -- inform the user.

---

## Inspect First

Always check image properties before complex operations:

```bash
# Human-readable summary
magick identify "$INPUT"

# Detailed info (format, dimensions, colorspace, depth, size)
magick identify -verbose "$INPUT" | head -30

# Quick dimensions
magick identify -format "%wx%h" "$INPUT"

# Quick format + dimensions + file size
magick identify -format "%m %wx%h %b" "$INPUT"
```

---

## Command Syntax

ImageMagick 7 uses the `magick` command. Common subcommands:

```bash
magick "$INPUT" [operations] "$OUTPUT"       # process single image
magick identify "$INPUT"                      # inspect image
magick composite overlay.png base.png out.png # composite images
magick montage *.jpg -geometry +2+2 out.png   # create montage
```

Key rule: **input comes first, operations in the middle, output last.**

---

## Core Recipes

### 1. Inspect image

```bash
magick identify -format "%f  %wx%h  %m  %[colorspace]  %b\n" "$INPUT"
```

### 2. Merge Images Into a Horizontal Strip

Use this when the user says "merge images", "combine images side by side", "create image strip", "make one long image", or "put images next to each other". This means arranging images in a single horizontal row -- not overlaying or blending them.

```bash
# Merge images into a horizontal strip, resize to uniform height, with spacing
magick montage image1.jpg image2.jpg image3.jpg \
  -resize x2048 \
  -geometry +20+0 \
  -tile x1 \
  -background none \
  "$OUTPUT"
```

- `-resize x2048`: normalize all images to the same height (adjust as needed)
- `-geometry +20+0`: 20px horizontal gap between images, no vertical gap
- `-tile x1`: single row (x1 = 1 row, unlimited columns)
- `-background none`: transparent gaps (use `white` or `black` if output is JPG)

For vertical strips, use `-tile 1x` instead of `-tile x1`.

### 3. Resize

```bash
# Resize to fit within 800x600, preserving aspect ratio
magick "$INPUT" -resize 800x600 "$OUTPUT"

# Resize to exact width, auto height
magick "$INPUT" -resize 800x "$OUTPUT"

# Resize to exact height, auto width
magick "$INPUT" -resize x600 "$OUTPUT"

# Force exact size (may distort)
magick "$INPUT" -resize 800x600! "$OUTPUT"

# Resize only if larger (shrink only)
magick "$INPUT" -resize 800x600\> "$OUTPUT"
```

### 4. Crop

```bash
# Crop to 400x300 from top-left corner
magick "$INPUT" -crop 400x300+0+0 +repage "$OUTPUT"

# Center crop to 1:1 square
magick "$INPUT" -gravity center -crop "%[fx:min(w,h)]x%[fx:min(w,h)]+0+0" +repage "$OUTPUT"

# Trim whitespace/transparent borders
magick "$INPUT" -trim +repage "$OUTPUT"
```

Always use `+repage` after crop to reset the virtual canvas.

### 5. Convert format

```bash
# PNG to JPG
magick "$INPUT" "$OUTPUT.jpg"

# JPG to PNG
magick "$INPUT" "$OUTPUT.png"

# Any format to WebP
magick "$INPUT" "$OUTPUT.webp"

# With quality control
magick "$INPUT" -quality 85 "$OUTPUT.jpg"
```

| Format | Quality range | Notes |
|--------|--------------|-------|
| JPEG | 1-100 (default 92) | Lossy; 85 is good balance |
| PNG | 0-9 compression level | Lossless; higher = smaller + slower |
| WebP | 1-100 | Lossy by default; `-define webp:lossless=true` for lossless |

### 6. Add text / watermark

```bash
# Add text at bottom center
magick "$INPUT" \
  -gravity south -pointsize 36 -fill white \
  -annotate +0+20 "Sample Text" \
  "$OUTPUT"

# Semi-transparent text watermark
magick "$INPUT" \
  -gravity center -pointsize 72 -fill "rgba(255,255,255,0.3)" \
  -annotate +0+0 "DRAFT" \
  "$OUTPUT"
```

For user-supplied text with special characters, write text to a temp file using `printf '%s'` (not `echo` with double quotes) and use `@filename`:

```bash
_tmpfile="$(mktemp)"
printf '%s' 'User supplied text here' > "$_tmpfile"
magick "$INPUT" -gravity south -pointsize 36 -fill white \
  -annotate +0+20 "@$_tmpfile" "$OUTPUT"
rm -f "$_tmpfile"
```

### 7. Composite / overlay

```bash
# Overlay a logo at top-right corner
magick "$INPUT" "$LOGO" \
  -gravity northeast -geometry +10+10 \
  -composite "$OUTPUT"

# Overlay with transparency
magick "$INPUT" \( "$OVERLAY" -alpha set -channel A -evaluate set 50% \) \
  -gravity center -composite "$OUTPUT"
```

### 8. Thumbnail

```bash
# Thumbnail preserving aspect ratio
magick "$INPUT" -thumbnail 200x200 "$OUTPUT"

# Thumbnail with center crop (exact size)
magick "$INPUT" -thumbnail 200x200^ -gravity center -extent 200x200 "$OUTPUT"
```

`-thumbnail` strips metadata and is faster than `-resize` for preview generation.

---

## Common Failure Modes

| Error | Fix |
|-------|-----|
| `not authorized` / policy error | Sandbox policy blocks this coder (e.g. PDF/PS). Inform user. |
| Output is 0 bytes | Check input exists; check format compatibility |
| Crop produces wrong region | Add `+repage` after `-crop` |
| Text renders as boxes | Font not available; use `-list font` to find available fonts |
| Colors look wrong after convert | Add `-colorspace sRGB` before output |
| Image too large, OOM | Add `-limit memory 256MiB -limit disk 512MiB` |
| Transparency lost in JPG output | JPG doesn't support alpha; use PNG/WebP or `-background white -flatten` |
| Special chars break `-annotate` | Write text to a file, use `@filename` |

---

## Command Construction Checklist

1. What is the input path? Inspect it if unknown.
2. What is the output path and format?
3. Does the operation change dimensions? Use `-resize` or `-crop`.
4. Does the operation change format? Specify output extension.
5. Is there a crop? Add `+repage`.
6. Is there text overlay? Escape special characters or use `@file`.
7. Is the output JPG? Handle transparency with `-flatten`.
8. Large batch? Add resource limits.
9. Verify output with `magick identify`.

---

## Agent Behavior Rules

1. Before constructing any command, identify: source format/dimensions, desired output format/dimensions, and quality requirements.
2. Inspect with `magick identify` if image properties are unknown.
3. Choose the simplest applicable command.
4. Never overwrite the input file unless explicitly asked.
5. Quote every path.
6. Use `@filename` for user-supplied text to avoid shell injection in `-annotate`.
7. Add `+repage` after any `-crop` operation.
8. When converting to JPG, flatten transparency first.
9. Verify output with `magick identify`.
10. If ImageMagick fails, read the error and adjust -- do not retry the same command.
11. If a policy error occurs, do not attempt to bypass it.
12. For compositing, montages, batch processing, and advanced operations, read `references/recipes.md`.

---

## References

- [ImageMagick documentation](https://imagemagick.org/script/command-line-processing.php)
- [Command-line options](https://imagemagick.org/script/command-line-options.php)
- [Image formats](https://imagemagick.org/script/formats.php)
