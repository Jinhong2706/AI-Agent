---
name: ffmpeg
description: Use this skill for media processing with ffmpeg/ffprobe — inspect, convert, trim, resize, compress, extract frames/audio, replace audio, mute, make GIFs, add subtitles/overlays, and combine videos. Triggers on 'combine these videos', 'merge my clips', 'join these videos together', 'put them end to end', 'stitch the clips into one video', 'concatenate these files', 'make one long video from these parts', 'append the second video to the first', 'chain these videos', 'compress video', 'extract audio', 'resize video', 'make gif', 'remove audio', 'thumbnail', 'storyboard', 'slideshow', 'social-media crop', 'codec settings', 'crf', 'preset', 'stream mapping', 'ffmpeg troubleshooting'.
---

# FFmpeg Skill for Computer-Use Agents

Process media files with ffmpeg and ffprobe. This skill adds agent-specific safety rules and decision logic on top of ffmpeg knowledge the model already has.

For additional recipes (convert, remux, extract audio, replace audio, remove audio, GIF, subtitles, overlays, and more), see `references/recipes.md`.

---

## Safety Policy

### No-overwrite default

Use `-n` unless the user explicitly asks to overwrite.

```bash
ffmpeg -n -i "$INPUT" [output options] "$OUTPUT"
```

If overwriting is explicitly requested, use `-y`.

### Temp-file workflow

Write to a temporary file with the same extension as the intended output, verify, then rename:

```bash
# Derive temp path preserving the target extension
TMP_OUTPUT="${OUTPUT%.*}.tmp.${OUTPUT##*.}"

ffmpeg -n -i "$INPUT" [output options] "$TMP_OUTPUT" &&
ffprobe -v error "$TMP_OUTPUT" &&
mv "$TMP_OUTPUT" "$OUTPUT"
```

### Other rules

- Quote all file paths.
- Only use local file paths with `-i`. Do not pass user-supplied URLs directly to ffmpeg/ffprobe without validating the protocol (stick to `file://` or bare paths).
- Do not delete the input file unless the user explicitly requests it.
- After generating output, verify with `ffprobe`.
- Clean up temp directories after successful operations.

---

## Inspect First

Always probe unknown media before complex operations:

```bash
# Human-readable
ffprobe -hide_banner -i "$INPUT"

# Machine-readable JSON
ffprobe -v error -show_format -show_streams -of json "$INPUT"

# Quick queries
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$INPUT"          # duration
ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=s=x:p=0 "$INPUT"        # resolution
ffprobe -v error -show_entries stream=index,codec_type,codec_name -of table "$INPUT"                    # codecs
```

---

## Decision Tree: Copy vs Re-encode

### Use `-c copy` when

- Changing container only (e.g. `.mkv` to `.mp4`)
- Removing or extracting a stream
- Approximate keyframe-aligned trim
- Avoiding quality loss

```bash
ffmpeg -n -i "$INPUT" -c copy "$OUTPUT"
```

### Re-encode when

- Resizing, cropping, padding, rotating
- Applying any `-vf` or `-af` filter
- Changing codec, frame rate, or pixel format
- Frame-accurate trim required
- Web/browser compatibility required

### Audio codec decision

| Goal | Audio option |
|------|-------------|
| Preserve source audio exactly | `-c:a copy` (may not be compatible with all containers) |
| Web-compatible MP4 | `-c:a aac -b:a 128k` (always safe) |
| Audio for transcription | `-vn -acodec pcm_s16le -ar 16000 -ac 1` |

When the target is a web-compatible MP4, prefer `-c:a aac` over `-c:a copy` -- copied audio may retain a codec the browser cannot play.

---

## Web-Compatible MP4 Defaults

```bash
ffmpeg -n -i "$INPUT" \
  -c:v libx264 -crf 23 -preset medium -threads 4 \
  -c:a aac -b:a 128k \
  -pix_fmt yuv420p \
  -movflags +faststart \
  "$OUTPUT"
```

Always include `-threads 4` when re-encoding. Without it, ffmpeg uses all CPU cores, which causes severe contention when multiple agents run concurrently.

| Profile | Codec | CRF | Preset | Audio | Notes |
|---------|-------|-----|--------|-------|-------|
| General (default) | libx264 | 23 | medium | aac 128k | Best compatibility |
| High quality | libx264 | 18 | slow | aac 192k | Archival, mastering |
| Smaller file | libx264 | 28 | medium | aac 96k | |
| Minimum size | libx264 | 32 | slow | aac 64k | |
| Modern smaller MP4 | libx265 | 24 | medium | aac 128k | Add `-vtag hvc1`; less compatible, smaller files |
| WebM/VP9 | libvpx-vp9 | 15 | n/a | libopus | Add `-b:v 0`; web-native, slow encode |

When the user does not specify a codec, default to H.264 (libx264). Use H.265/VP9 only when the user asks for smaller files or specifies these codecs.

---

## Core Recipes

### 1. Inspect media

```bash
ffprobe -hide_banner -i "$INPUT"
```

### 2. Combine / Merge / Join / Stitch Videos End-to-End

Use this when the user says "combine", "merge", "join", "stitch", "put end to end", "make one long video", "append", or "chain" videos. These mean sequential concatenation -- playing clips one after another. If the user asks for side-by-side, overlay, grid, or picture-in-picture, see `references/recipes.md` instead.

**Same codec (fast, no re-encode):**

The concat demuxer file list uses single-quoted paths, which breaks on filenames containing single quotes. For reliable automation, symlink inputs into a temp directory with safe names (zero disk I/O, no file copies):

```bash
# Replace the list with the actual input files (any number of files)
INPUT_FILES=("video1.mp4" "video2.mp4" "video3.mp4")

_tmpd="$(mktemp -d)"
trap 'rm -rf "$_tmpd"' EXIT

i=0
for f in "${INPUT_FILES[@]}"; do
  safe="$_tmpd/clip_$(printf '%03d' $i).${f##*.}"
  ln -s "$(cd "$(dirname "$f")" && pwd)/$(basename "$f")" "$safe"
  printf "file '%s'\n" "$safe" >> "$_tmpd/concat_list.txt"
  i=$((i+1))
done

ffmpeg -n -f concat -safe 0 -i "$_tmpd/concat_list.txt" -c copy "$OUTPUT"
```

**Mixed codecs (re-encodes):**

All inputs must have audio streams. If any input lacks audio, add a silent track first (see `references/recipes.md` section "Handling Missing Audio Streams"). Adjust `-i` count and `concat=n=N` to match the actual number of inputs:

```bash
# Example with 3 inputs -- adjust n=, -i count, and stream labels for actual input count
ffmpeg -n \
  -i "$VIDEO1" \
  -i "$VIDEO2" \
  -i "$VIDEO3" \
  -filter_complex "[0:v:0][0:a:0][1:v:0][1:a:0][2:v:0][2:a:0]concat=n=3:v=1:a=1[v][a]" \
  -map "[v]" -map "[a]" \
  -c:v libx264 -crf 23 -preset medium -threads 4 -c:a aac \
  "$OUTPUT"
```

For video-only concat and more variants, see `references/recipes.md` section "Concatenate (Mixed Codecs)".

### 3. Trim

Fast (keyframe-aligned, not frame-accurate):

```bash
ffmpeg -n -ss "00:01:00" -i "$INPUT" -t "00:00:10" -c copy "$OUTPUT"
```

Accurate (re-encodes):

```bash
ffmpeg -n -i "$INPUT" \
  -ss "00:01:00" -t "00:00:10" \
  -c:v libx264 -c:a aac -pix_fmt yuv420p \
  "$OUTPUT"
```

**Trim semantics**: `-t` is duration from the seek point. `-to` is an absolute timestamp on the *output* timeline (not the source timeline) when `-ss` is on the output side. Use `-t duration` when the user specifies a clip length; use input-side `-ss` + `-to` when the user gives absolute source timestamps.

### 4. Fade In / Fade Out

Video fade (black to visible / visible to black):

```bash
# Fade in first 2 seconds, fade out last 2 seconds of a 30s video
ffmpeg -n -i "$INPUT" \
  -vf "fade=t=in:st=0:d=2,fade=t=out:st=28:d=2" \
  -c:v libx264 -crf 23 -preset medium -c:a aac \
  "$OUTPUT"
```

Audio fade:

```bash
# Fade in first 2 seconds, fade out last 2 seconds
ffmpeg -n -i "$INPUT" \
  -af "afade=t=in:st=0:d=2,afade=t=out:st=28:d=2" \
  -c:v copy -c:a aac \
  "$OUTPUT"
```

Combined video + audio fade:

```bash
ffmpeg -n -i "$INPUT" \
  -vf "fade=t=in:st=0:d=2,fade=t=out:st=28:d=2" \
  -af "afade=t=in:st=0:d=2,afade=t=out:st=28:d=2" \
  -c:v libx264 -crf 23 -preset medium -c:a aac \
  "$OUTPUT"
```

To calculate fade-out start: probe duration first, then `st = duration - fade_duration`. Video fade requires re-encoding video; audio fade requires re-encoding audio.

### 5. Resize

```bash
# By width (auto height, -2 ensures even dimensions)
ffmpeg -n -i "$INPUT" -vf "scale=1280:-2" \
  -c:v libx264 -crf 23 -preset medium -c:a aac -b:a 128k "$OUTPUT"

# By height
ffmpeg -n -i "$INPUT" -vf "scale=-2:720" \
  -c:v libx264 -crf 23 -preset medium -c:a aac -b:a 128k "$OUTPUT"
```

After any scale, pad, or crop, add `setsar=1` to the filter chain if the output aspect ratio looks wrong (non-square pixels).

### 6. Extract frames / single frame / thumbnail

```bash
# One frame per second
mkdir -p "$FRAME_DIR"
ffmpeg -n -i "$INPUT" -vf "fps=1" "$FRAME_DIR/frame_%06d.jpg"

# Single frame at timestamp (thumbnail)
ffmpeg -n -ss "00:00:01.500" -i "$INPUT" -frames:v 1 -q:v 2 "$OUTPUT"
```

For storyboard / contact sheet and slideshow recipes, see `references/recipes.md`.

---

## Common Failure Modes

| Error | Fix |
|-------|-----|
| Width not divisible by 2 | Add `-vf "scale=trunc(iw/2)*2:trunc(ih/2)*2"` |
| Output file already exists | Use different output path, or `-y` only if overwrite allowed |
| Codec not supported in container | Re-encode instead of `-c copy` |
| Output has no audio | Probe input; use `-map 0:a:0?` for optional audio |
| Output is huge | Increase CRF (`-crf 28`) or reduce resolution |
| Browser cannot play output | Use H.264 + AAC + yuv420p + faststart |
| MP4 not streamable / slow to start | Add `-movflags +faststart` |
| moov atom not found | Input file is incomplete or corrupt; re-download or recover source |
| Audio out of sync after speed change | Apply matching `atempo` filter to audio stream |
| Aspect ratio wrong after scale/pad/crop | Append `setsar=1` to the filter chain |
| `drawtext` breaks on special characters | Use `drawtext=textfile=input.txt` instead of inline `text=` for user-supplied text |

---

## Command Construction Checklist

1. What is the input path? Probe it if unknown.
2. What is the output path and extension?
3. Overwrite allowed? Default: `-n`.
4. Container-only change? `-c copy`.
5. Resizing/filtering? Re-encode video.
6. Multiple inputs? Use `-map`.
7. Audio might be absent? Use `0:a:0?`.
8. Web-compatible? H.264 + AAC + yuv420p + faststart.
9. Frame-accurate cut? Output-side `-ss`, re-encode.
10. Verify output with `ffprobe`.

---

## Agent Behavior Rules

1. Before constructing any command, identify: source format, desired output container/codec, target dimensions/duration, and whether the user prioritizes quality, speed, or file size.
2. Inspect with `ffprobe` if media details are unknown.
3. Choose the simplest applicable command.
4. Treat "combine/merge/join/stitch videos" as sequential concatenation unless the user explicitly asks for side-by-side, overlay, grid, or picture-in-picture.
5. Use `-c copy` only when not modifying media content.
6. Re-encode when applying any filter.
7. Quote every path. Keep filter graphs in double quotes; use single quotes inside for expressions like `enable='between(t,1,7)'`. Never interpolate untrusted text directly into filter strings -- use `textfile=` for user-supplied text.
8. Use `-n` unless overwrite was explicitly requested.
9. Save to a new output path.
10. Verify output with `ffprobe`.
11. If FFmpeg fails, read the error and adjust -- do not retry the same command.
12. For complex filter_complex, multi-input, or advanced tasks, read `references/recipes.md`.

---

## References

- [FFmpeg documentation](https://ffmpeg.org/ffmpeg.html)
- [FFprobe documentation](https://ffmpeg.org/ffprobe.html)
- [FFmpeg filters](https://ffmpeg.org/ffmpeg-filters.html)
- [H.264 encoding guide](https://trac.ffmpeg.org/wiki/Encode/H.264)
