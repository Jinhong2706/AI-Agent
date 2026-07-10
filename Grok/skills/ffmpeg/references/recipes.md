# FFmpeg Recipes

Extended command cookbook. Read this file when the core recipes in SKILL.md don't cover the task, or when dealing with complex filter_complex, multi-input, or advanced stream mapping.

---

## Handling Missing Audio Streams

Some inputs have no audio. Commands that map audio streams (`-map 0:a`, `-filter_complex "[0:a]..."`) will fail on audio-less inputs.

**Rules:**

- When mapping audio, use optional syntax: `-map 0:a:0?`
- When the task involves audio mixing, speed change, or concat with audio, probe first to confirm audio exists.
- If any input lacks audio, use the video-only variant or add a silent audio track:

```bash
# Add silent audio (useful before concat with audio-bearing files)
ffmpeg -n -i "$INPUT" \
  -f lavfi -i anullsrc=r=44100:cl=stereo \
  -map 0:v:0 -map 1:a:0 \
  -c:v copy -c:a aac \
  -shortest \
  "$OUTPUT"
```

---

## Convert to Web-Compatible MP4

```bash
ffmpeg -n -i "$INPUT" \
  -c:v libx264 -crf 23 -preset medium \
  -c:a aac -b:a 128k \
  -pix_fmt yuv420p \
  -movflags +faststart \
  "$OUTPUT"
```

Lower crf = higher quality + larger file. Range: 18-28.

## Remux (Container Change, No Re-encode)

```bash
ffmpeg -n -i "$INPUT" -c copy "$OUTPUT"
```

If this fails, the input codecs are not compatible with the output container -- re-encode.

---

## Make an Existing MP4/MOV/M4A Streamable

```bash
ffmpeg -n -i "$INPUT" -c copy -movflags +faststart "$OUTPUT"
```

Works for any container that stores the moov atom (MP4, MOV, M4A).

---

## Fit Into a Canvas With Padding

Horizontal 1920x1080:

```bash
ffmpeg -n -i "$INPUT" \
  -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1" \
  -c:v libx264 -crf 23 -preset medium \
  -c:a aac -b:a 128k -pix_fmt yuv420p \
  "$OUTPUT"
```

Vertical 1080x1920 (Shorts/Reels/TikTok):

```bash
ffmpeg -n -i "$INPUT" \
  -vf "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1" \
  -c:v libx264 -crf 23 -preset medium \
  -c:a aac -b:a 128k -pix_fmt yuv420p \
  "$OUTPUT"
```

---

## Crop

Center crop to 1:1 square:

```bash
ffmpeg -n -i "$INPUT" \
  -vf "crop='min(iw,ih)':'min(iw,ih)'" \
  -c:v libx264 -crf 23 -preset medium -c:a aac -b:a 128k \
  "$OUTPUT"
```

Center crop to 16:9:

```bash
ffmpeg -n -i "$INPUT" \
  -vf "crop='if(gt(iw/ih,16/9),ih*16/9,iw)':'if(gt(iw/ih,16/9),ih,iw*9/16)'" \
  -c:v libx264 -crf 23 -preset medium -c:a aac -b:a 128k \
  "$OUTPUT"
```

---

## Force Exact Size (May Distort)

Only use if the user explicitly wants exact dimensions:

```bash
ffmpeg -n -i "$INPUT" \
  -vf "scale=1280:720" \
  -c:v libx264 -crf 23 -preset medium -c:a aac -b:a 128k \
  "$OUTPUT"
```

---

## Create Video From Image Sequence

```bash
ffmpeg -n -framerate 30 \
  -i "$FRAME_DIR/frame_%06d.jpg" \
  -c:v libx264 -pix_fmt yuv420p \
  "$OUTPUT"
```

If images have odd dimensions:

```bash
ffmpeg -n -framerate 30 \
  -i "$FRAME_DIR/frame_%06d.png" \
  -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" \
  -c:v libx264 -pix_fmt yuv420p \
  "$OUTPUT"
```

---

## Mix Background Music With Original Audio

Requires both inputs to have audio streams. Probe first.

```bash
ffmpeg -n \
  -i "$VIDEO_INPUT" \
  -i "$MUSIC_INPUT" \
  -filter_complex "[1:a]volume=0.20[music];[0:a][music]amix=inputs=2:duration=shortest[aout]" \
  -map 0:v:0 -map "[aout]" \
  -c:v copy -c:a aac \
  -shortest \
  "$OUTPUT"
```

If video stream copy fails, re-encode with `-c:v libx264 -crf 23 -preset medium`.

---

## Change Volume

```bash
# Quieter
ffmpeg -n -i "$INPUT" -filter:a "volume=0.5" "$OUTPUT"

# Louder
ffmpeg -n -i "$INPUT" -filter:a "volume=2.0" "$OUTPUT"
```

---

## Extract Audio

```bash
# MP3
ffmpeg -n -i "$INPUT" -vn -c:a libmp3lame -q:a 2 "$OUTPUT"

# WAV for transcription
ffmpeg -n -i "$INPUT" -vn -acodec pcm_s16le -ar 16000 -ac 1 "$OUTPUT"

# Copy without re-encoding
ffmpeg -n -i "$INPUT" -map 0:a:0 -c:a copy "$OUTPUT"
```

---

## Remove Audio (Mute)

```bash
ffmpeg -n -i "$INPUT" -an -c:v copy "$OUTPUT"
```

---

## Replace Audio

Requires both inputs to have the expected streams.

```bash
ffmpeg -n \
  -i "$VIDEO_INPUT" \
  -i "$AUDIO_INPUT" \
  -map 0:v:0 -map 1:a:0 \
  -c:v copy -c:a aac \
  -shortest \
  "$OUTPUT"
```

---

## Create GIF

Use a temp palette in a temp directory to avoid clobbering user files:

```bash
_tmpd="$(mktemp -d)"
trap 'rm -rf "$_tmpd"' EXIT

ffmpeg -n -ss "00:00:00" -t "00:00:03" -i "$INPUT" \
  -vf "fps=12,scale=480:-1:flags=lanczos,palettegen" "$_tmpd/palette.png"

ffmpeg -n -ss "00:00:00" -t "00:00:03" -i "$INPUT" \
  -i "$_tmpd/palette.png" \
  -filter_complex "fps=12,scale=480:-1:flags=lanczos[x];[x][1:v]paletteuse" \
  "$OUTPUT"
```

---

## Subtitles

Burn-in (hardcode, requires re-encode):

```bash
ffmpeg -n -i "$INPUT" \
  -vf "subtitles=subs.srt" \
  -c:v libx264 -crf 23 -preset medium -c:a aac \
  "$OUTPUT"
```

Soft subtitle track (stream copy, no re-encode):

```bash
# MKV container (supports srt/ass natively)
ffmpeg -n -i "$INPUT" -i subs.srt \
  -c copy -c:s srt \
  "$OUTPUT"

# MP4 container (requires mov_text codec)
ffmpeg -n -i "$INPUT" -i subs.srt \
  -c copy -c:s mov_text \
  "$OUTPUT"
```

---

## Concatenate (Mixed Codecs)

Re-encodes everything. All inputs must have audio; if any lacks audio, add a silent track first (see "Handling Missing Audio Streams" above).

Two files:

```bash
ffmpeg -n \
  -i "$VIDEO1" \
  -i "$VIDEO2" \
  -filter_complex "[0:v:0][0:a:0][1:v:0][1:a:0]concat=n=2:v=1:a=1[v][a]" \
  -map "[v]" -map "[a]" \
  -c:v libx264 -crf 23 -preset medium -c:a aac \
  "$OUTPUT"
```

Video-only (no audio in any input):

```bash
ffmpeg -n \
  -i "$VIDEO1" \
  -i "$VIDEO2" \
  -filter_complex "[0:v:0][1:v:0]concat=n=2:v=1:a=0[v]" \
  -map "[v]" \
  -c:v libx264 -crf 23 -preset medium -pix_fmt yuv420p \
  "$OUTPUT"
```

---

## Change Frame Rate

```bash
ffmpeg -n -i "$INPUT" \
  -vf "fps=30" \
  -c:v libx264 -crf 23 -preset medium -c:a aac \
  "$OUTPUT"
```

---

## Speed Up / Slow Down

2x speed (requires audio):

```bash
ffmpeg -n -i "$INPUT" \
  -filter_complex "[0:v]setpts=0.5*PTS[v];[0:a]atempo=2.0[a]" \
  -map "[v]" -map "[a]" \
  "$OUTPUT"
```

0.5x speed (requires audio):

```bash
ffmpeg -n -i "$INPUT" \
  -filter_complex "[0:v]setpts=2.0*PTS[v];[0:a]atempo=0.5[a]" \
  -map "[v]" -map "[a]" \
  "$OUTPUT"
```

Video-only (no audio):

```bash
ffmpeg -n -i "$INPUT" \
  -vf "setpts=0.5*PTS" \
  -an \
  "$OUTPUT"
```

For video: lower setpts = faster. For audio: higher atempo = faster. `atempo` supports 0.5-100.0; for extreme changes chain multiple filters (e.g. `atempo=2.0,atempo=2.0` for 4x).

---

## Add Text Overlay

```bash
ffmpeg -n -i "$INPUT" \
  -vf "drawtext=text='Hello':fontcolor=white:fontsize=48:x=(w-text_w)/2:y=h-100" \
  -c:v libx264 -crf 23 -preset medium -c:a aac -b:a 128k \
  "$OUTPUT"
```

If font errors occur, specify a font file with `fontfile=/path/to/font.ttf`. For user-supplied text, use `drawtext=textfile=input.txt` instead of inline `text=` to avoid escaping issues with quotes, colons, and special characters.

---

## Add Image Overlay / Logo

Top-left corner:

```bash
ffmpeg -n \
  -i "$INPUT" -i "$IMAGE" \
  -filter_complex "[0:v][1:v]overlay=10:10" \
  -c:v libx264 -crf 23 -preset medium -c:a aac -b:a 128k \
  "$OUTPUT"
```

Center:

```bash
ffmpeg -n \
  -i "$INPUT" -i "$IMAGE" \
  -filter_complex "[0:v][1:v]overlay=(main_w-overlay_w)/2:(main_h-overlay_h)/2" \
  -c:v libx264 -crf 23 -preset medium -c:a aac -b:a 128k \
  "$OUTPUT"
```

---

## Fix Odd Width / Height for H.264

```bash
ffmpeg -n -i "$INPUT" \
  -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" \
  -c:v libx264 -crf 23 -preset medium -c:a copy \
  "$OUTPUT"
```

---

## Rotate Video

90 CW: `-vf "transpose=1"`. 90 CCW: `-vf "transpose=2"`. 180: `-vf "transpose=1,transpose=1"`.

```bash
ffmpeg -n -i "$INPUT" \
  -vf "transpose=1" \
  -c:v libx264 -crf 23 -preset medium -c:a aac -b:a 128k \
  "$OUTPUT"
```

---

## Normalize Audio Loudness

```bash
ffmpeg -n -i "$INPUT" \
  -af "loudnorm" \
  -c:v copy -c:a aac \
  "$OUTPUT"
```

If video stream copy fails, re-encode with `-c:v libx264 -crf 23 -preset medium`.

---

## Generate Thumbnail Contact Sheet

Samples one frame every 10 seconds, creates a 3x3 grid:

```bash
ffmpeg -n -i "$INPUT" \
  -vf "fps=1/10,scale=320:-1,tile=3x3" \
  -frames:v 1 \
  "$OUTPUT"
```

---

## Remove Metadata

```bash
ffmpeg -n -i "$INPUT" -map_metadata -1 -c copy "$OUTPUT"
```

If stream copy fails, re-encode.

---

## Keep Only First Video and First Audio Stream

```bash
ffmpeg -n -i "$INPUT" \
  -map 0:v:0 -map 0:a:0? \
  -c:v libx264 -crf 23 -preset medium \
  -c:a aac -pix_fmt yuv420p \
  "$OUTPUT"
```

---

## Extract Subclip and Resize Together

```bash
ffmpeg -n -i "$INPUT" \
  -ss "00:00:10" -t "00:00:05" \
  -vf "scale=1280:-2" \
  -c:v libx264 -crf 23 -preset medium -c:a aac \
  "$OUTPUT"
```

---

## Styled Burn-in Subtitles

```bash
ffmpeg -n -i "$INPUT" \
  -vf "subtitles=subs.srt:force_style='FontName=Poppins,FontSize=24,PrimaryColour=&HFFFFFF'" \
  -c:v libx264 -crf 23 -preset medium -c:a aac \
  "$OUTPUT"
```

Use `fontsdir=.` if custom fonts are in the current directory. ASS subtitles (`subs.ass`) support richer styling natively.

---

## Thumbnail / Single Frame

High-quality JPEG thumbnail:

```bash
ffmpeg -n -ss "00:00:07" -i "$INPUT" -frames:v 1 -q:v 2 thumbnail.jpg
```

PNG (lossless):

```bash
ffmpeg -n -ss "00:00:07" -i "$INPUT" -frames:v 1 thumbnail.png
```

---

## Storyboard / Contact Sheet

Sample one frame every 10 seconds, arrange in a 3x3 grid:

```bash
ffmpeg -n -i "$INPUT" \
  -vf "fps=1/10,scale=320:-1,tile=3x3" \
  -frames:v 1 \
  storyboard.jpg
```

Adjust `fps=1/N` for density (1/5 = every 5s, 1/30 = every 30s). Change `tile=CxR` for grid size.

---

## Slideshow From Images

```bash
ffmpeg -n -framerate 1/3 \
  -pattern_type glob -i "slides/*.jpg" \
  -c:v libx264 -crf 23 -pix_fmt yuv420p \
  -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" \
  slideshow.mp4
```

`-framerate 1/3` means each image is shown for 3 seconds. Input images should have the same dimensions. If they differ, use `scale` + `pad` to fit a fixed canvas (e.g. `scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:black`). The `scale` filter alone only ensures even dimensions, it does not normalize different sizes.

With audio track:

```bash
ffmpeg -n -framerate 1/3 \
  -pattern_type glob -i "slides/*.jpg" \
  -i background_music.mp3 \
  -c:v libx264 -crf 23 -pix_fmt yuv420p \
  -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" \
  -c:a aac -shortest \
  slideshow.mp4
```

---

## Social-Media Crop / Reformat

Vertical 9:16 (Reels/Shorts/TikTok) with center crop:

```bash
ffmpeg -n -i "$INPUT" \
  -vf "crop='if(gt(iw/ih,9/16),ih*9/16,iw)':'if(gt(iw/ih,9/16),ih,iw*16/9)',scale=1080:1920,setsar=1" \
  -c:v libx264 -crf 23 -preset medium -c:a aac -b:a 128k -pix_fmt yuv420p \
  "$OUTPUT"
```

Square 1:1 (Instagram feed):

```bash
ffmpeg -n -i "$INPUT" \
  -vf "crop='min(iw,ih)':'min(iw,ih)',scale=1080:1080,setsar=1" \
  -c:v libx264 -crf 23 -preset medium -c:a aac -b:a 128k -pix_fmt yuv420p \
  "$OUTPUT"
```

Letterbox/pillarbox (fit into canvas with padding) -- see "Fit Into a Canvas With Padding" above.
