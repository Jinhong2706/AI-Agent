---
name: screen-idle-video-cutter
description: Detect and remove long static idle sections from screen recordings with local ffmpeg frame sampling, conservative guard seconds, auditable reports, and low token usage.
version: 1.0.0
updated_at: 2026-05-22
---

# Screen Idle Video Cutter

## Purpose

Use this skill to cut long static sections from screen recordings without spending tokens on video inspection. Prefer the bundled local script over manually reading screenshots or sampling video frames into the conversation.

Default policy:

- detect static screen regions locally with `ffmpeg`, `Pillow`, and `numpy`
- treat `15` seconds of low visual change as idle
- keep `5` seconds before and after every removed static section
- preserve dynamic or uncertain footage
- produce both an auditable report and an edited video

## When To Use

Use this skill when the user wants to:

- remove long no-action pauses from a screen recording
- shrink tutorial, coding, meeting, or workflow videos
- create a cut list before final video editing
- avoid high-token visual review of long videos

Do not use it for cinematic footage, scene-change editing, highlight detection, audio-based silence removal, or content-aware storytelling cuts.

## Default Workflow

1. Confirm the input path and output path if they are not obvious.
2. For important source videos, run a dry run first:

```bash
python3 scripts/screen_idle_cutter.py input.mp4 --output output.mp4 --dry-run --report report.json --segments segments.txt
```

3. Review the report at a high level: detected static spans, removed spans, kept spans, and saved duration.
4. Render the edited video:

```bash
python3 scripts/screen_idle_cutter.py input.mp4 --output output.mp4 --report report.json --segments segments.txt
```

5. If the result is too aggressive, rerun with a larger `--min-static-seconds`, lower `--sample-fps`, or higher `--diff-threshold`. If it misses obvious pauses, lower `--diff-threshold` or `--min-static-seconds`.

## Core Command

```bash
python3 scripts/screen_idle_cutter.py input.mp4 --output output.mp4
```

Useful options:

```bash
--min-static-seconds 15
--guard-seconds 5
--sample-fps 1
--diff-threshold auto
--dry-run
--report report.json
--segments segments.txt
```

## Token-Saving Rules

- Do not load the full video into context.
- Do not extract representative screenshots unless diagnosing a failed detection.
- Prefer the JSON report and segment list as the review surface.
- Keep first replies short: state the detected plan, command, and expected artifacts.
- Ask for confirmation only when overwrite behavior, paths, or cut aggressiveness are unclear.

## Safety Rules

- Default to conservative cutting.
- Never remove a static span unless the removable interior remains positive after both guard windows are applied.
- Preserve all dynamic, uncertain, very short, or boundary-problem sections.
- Use `--dry-run` for irreplaceable videos before rendering.
- Do not delete or overwrite source videos.

## Output Contract

The script should create:

- edited video at `--output` unless `--dry-run` is set
- JSON report at `--report` when requested
- ffmpeg concat segment file at `--segments` when requested

The report includes parameters, source duration, detected static spans, removed spans, kept spans, and estimated saved duration.
