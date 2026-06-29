# Changelog

## 1.0.0 - 2026-05-22

- Added release-ready MVP Skill for static idle cutting in screen recordings.
- Added local `ffmpeg` + `Pillow` + `numpy` detection workflow.
- Added default 15-second static detection and 5-second guard windows.
- Added JSON reporting, optional ffmpeg segment output, and dry-run mode.
- Added source validation, release packaging, package validation, and segment math tests.
- Hardened release packaging to exclude local run artifacts from publish bundles.
- Added a dedicated SkillHub bundle script that strips `.skillignore`, `PUBLISH_INFO.md`, and other repo-only release helpers.
