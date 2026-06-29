# Screen Idle Video Cutter

[中文](./README.md)

`screen-idle-video-cutter` is a low-token video editing Skill for screen recordings. It detects long static no-action sections locally, removes only the safe middle of those sections, and keeps 5 seconds before and after every removed span.

## Current Version

- Version: `1.0.0`
- Updated at: `2026-05-22`
- Skill file: [SKILL.md](./SKILL.md)
- Publish info: [PUBLISH_INFO.md](./PUBLISH_INFO.md)
- Changelog: [CHANGELOG.md](./CHANGELOG.md)

## What This Skill Solves

Screen recordings often contain long idle pauses: waiting for loading, thinking, copying material, or switching context. Finding these spans manually is slow, while asking a model to inspect video frames wastes tokens.

This Skill uses a local-first workflow:

- sample frames with `ffmpeg`
- compare adjacent frames with `Pillow` and `numpy`
- detect static spans locally
- remove only the interior of static spans
- preserve `5` seconds before and after each removed span by default

## Defaults

- Static threshold: `15` continuous seconds of low visual change
- Guard window: `5` seconds before and after every removed span
- Sampling rate: `1 fps`
- Outputs: edited video, JSON report, optional segment file
- Principle: cut conservatively; keep dynamic or uncertain footage

## Quick Start

```bash
cd skills/screen-idle-video-cutter
python3 scripts/screen_idle_cutter.py input.mp4 --output output.mp4 --report report.json --segments segments.txt
```

For important videos, preview first:

```bash
python3 scripts/screen_idle_cutter.py input.mp4 --output output.mp4 --dry-run --report report.json --segments segments.txt
```

## Common Options

- `--min-static-seconds 15`: minimum continuous idle duration before a span can be cut.
- `--guard-seconds 5`: seconds to preserve before and after each removed span.
- `--sample-fps 1`: frame sampling rate for detection.
- `--diff-threshold auto`: auto-estimate the static threshold, or pass a numeric value.
- `--dry-run`: generate report and segment list without rendering video.
- `--report report.json`: write an auditable JSON report.
- `--segments segments.txt`: write an ffmpeg concat segment file.

## Package Contents

```text
screen-idle-video-cutter/
├── SKILL.md
├── README.md
├── README.en.md
├── CHANGELOG.md
├── PUBLISH_INFO.md
├── .skillignore
├── scripts/
│   ├── screen_idle_cutter.py
│   ├── validate_skill.py
│   ├── package_skill.py
│   └── validate_release_package.py
└── tests/
    └── test_segment_math.py
```

## Current MVP Scope

This version intentionally does not include `references/`, `templates/`, or `examples/`.

Why:

- the core workflow is already captured by one runnable local-first script
- the MVP goal is a publishable minimum loop for low-token idle detection and cutting
- those directories can be added later when the Skill needs presets, richer examples, or advanced operating notes

## Validate And Package

```bash
python3 scripts/validate_skill.py
python3 tests/test_segment_math.py
python3 scripts/package_skill.py
python3 scripts/package_skillhub.py
python3 scripts/validate_release_package.py dist/screen-idle-video-cutter.skill
python3 scripts/validate_release_package.py dist/screen-idle-video-cutter.zip
```

## Publishing

Primary upload file:

```text
dist/publish/screen-idle-video-cutter-skillhub-v1.0.0.zip
```

Fallback upload file:

```text
dist/screen-idle-video-cutter.skill
```

Do not upload the repository root or a GitHub-generated source archive.
