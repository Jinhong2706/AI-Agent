# ImageMagick Recipes

Extended command cookbook. Read this file when the core recipes in SKILL.md don't cover the task.

---

## Batch Convert Images

Always include `-limit memory 256MiB -limit disk 512MiB` in batch loops to prevent OOM in shared environments.

```bash
# Convert all PNGs in a directory to JPG
for f in "$DIR"/*.png; do
  magick "$f" -limit memory 256MiB -limit disk 512MiB -quality 85 "${f%.png}.jpg"
done

# Batch resize to max 1200px wide
for f in "$DIR"/*.jpg; do
  magick "$f" -limit memory 256MiB -limit disk 512MiB -resize 1200x\> "$DIR/resized_$(basename "$f")"
done
```

---

## Montage / Collage

Create a grid of images:

```bash
# 3-column grid with 5px gaps, white background
magick montage "$DIR"/*.jpg \
  -geometry 300x300+5+5 \
  -tile 3x \
  -background white \
  "$OUTPUT"

# 2x2 grid, specific images
magick montage img1.jpg img2.jpg img3.jpg img4.jpg \
  -geometry 400x400+2+2 \
  -tile 2x2 \
  "$OUTPUT"

# With labels
magick montage "$DIR"/*.jpg \
  -label "%f" \
  -geometry 200x200+5+5 \
  -tile 4x \
  -pointsize 12 \
  "$OUTPUT"
```

---

## Color Adjustments

```bash
# Adjust brightness/contrast
magick "$INPUT" -brightness-contrast 10x20 "$OUTPUT"

# Grayscale
magick "$INPUT" -colorspace Gray "$OUTPUT"

# Sepia tone
magick "$INPUT" -sepia-tone 80% "$OUTPUT"

# Negate / invert colors
magick "$INPUT" -negate "$OUTPUT"

# Auto-level (stretch histogram)
magick "$INPUT" -auto-level "$OUTPUT"

# Auto-gamma
magick "$INPUT" -auto-gamma "$OUTPUT"

# Adjust specific channel
magick "$INPUT" -channel Red -evaluate multiply 1.2 +channel "$OUTPUT"
```

---

## Borders and Frames

```bash
# Add solid border
magick "$INPUT" -bordercolor "#333333" -border 10x10 "$OUTPUT"

# Add rounded corners
magick "$INPUT" \
  \( +clone -alpha extract \
     -draw "fill black polygon 0,0 0,15 15,0 fill white circle 15,15 15,0" \
     \( +clone -flip \) -compose Multiply -composite \
     \( +clone -flop \) -compose Multiply -composite \
  \) -alpha off -compose CopyOpacity -composite "$OUTPUT"

# Drop shadow
magick "$INPUT" \
  \( +clone -background black -shadow 60x5+5+5 \) \
  +swap -background white -layers merge +repage "$OUTPUT"
```

---

## Rotate and Flip

```bash
# Rotate 90 degrees clockwise
magick "$INPUT" -rotate 90 "$OUTPUT"

# Rotate 90 degrees counterclockwise
magick "$INPUT" -rotate -90 "$OUTPUT"

# Rotate 180 degrees
magick "$INPUT" -rotate 180 "$OUTPUT"

# Rotate arbitrary angle (auto-expands canvas)
magick "$INPUT" -rotate 15 -background white "$OUTPUT"

# Flip vertical
magick "$INPUT" -flip "$OUTPUT"

# Flip horizontal
magick "$INPUT" -flop "$OUTPUT"
```

---

## Transparency

```bash
# Make white background transparent
magick "$INPUT" -fuzz 10% -transparent white "$OUTPUT"

# Make specific color transparent
magick "$INPUT" -fuzz 5% -transparent "#00FF00" "$OUTPUT"

# Flatten transparency to white background (for JPG output)
magick "$INPUT" -background white -flatten "$OUTPUT"

# Set global opacity
magick "$INPUT" -alpha set -channel A -evaluate set 50% "$OUTPUT"
```

---

## Blur and Sharpen

```bash
# Gaussian blur
magick "$INPUT" -blur 0x3 "$OUTPUT"

# Sharpen
magick "$INPUT" -sharpen 0x1 "$OUTPUT"

# Unsharp mask (common for web images)
magick "$INPUT" -unsharp 0x1+1+0.05 "$OUTPUT"

# Motion blur
magick "$INPUT" -motion-blur 0x10+45 "$OUTPUT"
```

---

## Create Images From Scratch

```bash
# Solid color
magick -size 800x600 xc:"#4A90D9" "$OUTPUT"

# Gradient
magick -size 800x600 gradient:"#4A90D9"-"#1A1A2E" "$OUTPUT"

# Transparent canvas
magick -size 800x600 xc:transparent "$OUTPUT"

# Checkerboard pattern
magick -size 800x600 pattern:checkerboard "$OUTPUT"
```

---

## Pad / Extend Canvas

```bash
# Pad to exact size with white background, centered
magick "$INPUT" \
  -gravity center \
  -background white \
  -extent 1920x1080 \
  "$OUTPUT"

# Pad to square
magick "$INPUT" \
  -gravity center \
  -background white \
  -extent "%[fx:max(w,h)]x%[fx:max(w,h)]" \
  "$OUTPUT"
```

---

## Strip Metadata

```bash
# Remove all EXIF/metadata
magick "$INPUT" -strip "$OUTPUT"
```

---

## Optimize File Size

```bash
# Optimize JPEG
magick "$INPUT" -strip -quality 80 -sampling-factor 4:2:0 "$OUTPUT"

# Optimize PNG
magick "$INPUT" -strip -define png:compression-level=9 "$OUTPUT"

# Optimize WebP
magick "$INPUT" -quality 80 -define webp:method=6 "$OUTPUT"
```

---

## Animated GIF Operations

```bash
# Resize animated GIF (preserving animation)
magick "$INPUT" -coalesce -resize 480x -deconstruct "$OUTPUT"

# Extract single frame from animated GIF
magick "$INPUT[0]" "$OUTPUT"

# Change animation speed (delay in 1/100s)
magick "$INPUT" -coalesce -set delay 10 -deconstruct "$OUTPUT"

# Reverse animation
magick "$INPUT" -coalesce -reverse -deconstruct "$OUTPUT"
```

Use `-coalesce` before and `-deconstruct` after modifying animated GIFs to preserve frame composition.

---

## Multi-page / Multi-layer

```bash
# Split multi-page TIFF into individual files
magick "$INPUT" "$OUTPUT_DIR/page_%03d.png"

# Combine images into multi-page TIFF
magick "$DIR"/*.png "$OUTPUT.tiff"

# Extract specific page
magick "$INPUT[2]" "$OUTPUT"
```

---

## Side-by-Side / Stack Images

```bash
# Horizontal (side by side)
magick "$IMG1" "$IMG2" +append "$OUTPUT"

# Vertical (stacked)
magick "$IMG1" "$IMG2" -append "$OUTPUT"

# With gap between images
magick "$IMG1" -splice 20x0 "$IMG2" +append "$OUTPUT"
```

---

## Social Media Sizes

```bash
# Instagram square (1080x1080)
magick "$INPUT" -thumbnail 1080x1080^ -gravity center -extent 1080x1080 "$OUTPUT"

# Instagram story (1080x1920)
magick "$INPUT" -thumbnail 1080x1920^ -gravity center -extent 1080x1920 "$OUTPUT"

# Twitter/X header (1500x500)
magick "$INPUT" -thumbnail 1500x500^ -gravity center -extent 1500x500 "$OUTPUT"

# Open Graph / social share (1200x630)
magick "$INPUT" -thumbnail 1200x630^ -gravity center -extent 1200x630 "$OUTPUT"
```
