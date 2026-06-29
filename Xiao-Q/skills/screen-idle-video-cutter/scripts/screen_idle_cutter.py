#!/usr/bin/env python3
"""Cut long static idle sections from screen recordings.

The script keeps video analysis local and low-token: ffmpeg samples frames,
Pillow/numpy compare frame differences, then ffmpeg renders the kept ranges.
"""

from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
from PIL import Image


DEFAULT_MIN_STATIC_SECONDS = 15.0
DEFAULT_GUARD_SECONDS = 5.0
DEFAULT_SAMPLE_FPS = 1.0
DEFAULT_AUTO_THRESHOLD_FLOOR = 0.08
DEFAULT_AUTO_THRESHOLD_CEILING = 0.75


@dataclass(frozen=True)
class Span:
    start: float
    end: float

    @property
    def duration(self) -> float:
        return max(0.0, self.end - self.start)


def run_command(command: list[str]) -> None:
    completed = subprocess.run(command, text=True, capture_output=True)
    if completed.returncode != 0:
        stderr = completed.stderr.strip()
        stdout = completed.stdout.strip()
        detail = stderr or stdout or "unknown error"
        raise RuntimeError(f"Command failed: {' '.join(command)}\n{detail}")


def probe_duration(input_path: Path) -> float:
    command = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(input_path),
    ]
    completed = subprocess.run(command, text=True, capture_output=True)
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "ffprobe failed")
    try:
        return float(completed.stdout.strip())
    except ValueError as exc:
        raise RuntimeError(f"Could not parse video duration: {completed.stdout!r}") from exc


def extract_sample_frames(input_path: Path, frames_dir: Path, sample_fps: float) -> list[Path]:
    frames_dir.mkdir(parents=True, exist_ok=True)
    output_pattern = frames_dir / "frame_%06d.jpg"
    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(input_path),
        "-vf",
        f"fps={sample_fps},scale=320:-1:flags=fast_bilinear",
        "-q:v",
        "4",
        str(output_pattern),
    ]
    run_command(command)
    frames = sorted(frames_dir.glob("frame_*.jpg"))
    if len(frames) < 2:
        raise RuntimeError("Not enough sampled frames to detect static spans.")
    return frames


def frame_difference_percent(left: Path, right: Path) -> float:
    with Image.open(left) as left_image, Image.open(right) as right_image:
        left_array = np.asarray(left_image.convert("RGB"), dtype=np.int16)
        right_array = np.asarray(right_image.convert("RGB"), dtype=np.int16)
    if left_array.shape != right_array.shape:
        raise RuntimeError(f"Frame dimensions differ: {left} vs {right}")
    return float(np.mean(np.abs(left_array - right_array)) / 255.0 * 100.0)


def compute_frame_differences(frames: list[Path]) -> list[float]:
    return [frame_difference_percent(frames[index - 1], frames[index]) for index in range(1, len(frames))]


def auto_diff_threshold(differences: list[float]) -> float:
    if not differences:
        return DEFAULT_AUTO_THRESHOLD_FLOOR
    percentile_20 = float(np.percentile(np.asarray(differences, dtype=float), 20))
    threshold = percentile_20 * 1.25
    return min(max(threshold, DEFAULT_AUTO_THRESHOLD_FLOOR), DEFAULT_AUTO_THRESHOLD_CEILING)


def detect_static_spans(
    differences: list[float],
    sample_fps: float,
    diff_threshold: float,
    duration: float,
) -> list[Span]:
    spans: list[Span] = []
    run_start: int | None = None

    for index, diff in enumerate(differences):
        if diff <= diff_threshold:
            if run_start is None:
                run_start = index
            continue
        if run_start is not None:
            spans.append(diff_run_to_span(run_start, index - 1, sample_fps, duration))
            run_start = None

    if run_start is not None:
        spans.append(diff_run_to_span(run_start, len(differences) - 1, sample_fps, duration))

    return [span for span in spans if span.duration > 0]


def diff_run_to_span(run_start: int, run_end: int, sample_fps: float, duration: float) -> Span:
    start = run_start / sample_fps
    end = min(duration, (run_end + 1) / sample_fps)
    return Span(round(start, 3), round(end, 3))


def merge_spans(spans: Iterable[Span]) -> list[Span]:
    sorted_spans = sorted((span for span in spans if span.duration > 0), key=lambda item: item.start)
    if not sorted_spans:
        return []

    merged = [sorted_spans[0]]
    for span in sorted_spans[1:]:
        previous = merged[-1]
        if span.start <= previous.end:
            merged[-1] = Span(previous.start, max(previous.end, span.end))
        else:
            merged.append(span)
    return merged


def removable_spans_from_static(
    static_spans: Iterable[Span],
    min_static_seconds: float,
    guard_seconds: float,
) -> list[Span]:
    removable: list[Span] = []
    for span in static_spans:
        if span.duration < min_static_seconds:
            continue
        cut_start = span.start + guard_seconds
        cut_end = span.end - guard_seconds
        if cut_end > cut_start:
            removable.append(Span(round(cut_start, 3), round(cut_end, 3)))
    return merge_spans(removable)


def kept_spans_from_removed(removed_spans: Iterable[Span], duration: float) -> list[Span]:
    kept: list[Span] = []
    cursor = 0.0
    for span in merge_spans(removed_spans):
        start = max(0.0, min(duration, span.start))
        end = max(0.0, min(duration, span.end))
        if start > cursor:
            kept.append(Span(round(cursor, 3), round(start, 3)))
        cursor = max(cursor, end)
    if cursor < duration:
        kept.append(Span(round(cursor, 3), round(duration, 3)))
    return [span for span in kept if span.duration > 0]


def quote_concat_path(path: Path) -> str:
    return "'" + str(path.resolve()).replace("'", "'\\''") + "'"


def write_segments_file(input_path: Path, kept_spans: list[Span], segments_path: Path) -> None:
    lines: list[str] = []
    for span in kept_spans:
        lines.append(f"file {quote_concat_path(input_path)}")
        lines.append(f"inpoint {span.start:.3f}")
        lines.append(f"outpoint {span.end:.3f}")
    segments_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def render_video(segments_path: Path, output_path: Path, overwrite: bool) -> None:
    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
    ]
    if overwrite:
        command.append("-y")
    else:
        command.append("-n")
    command.extend(
        [
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(segments_path),
            "-map",
            "0",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "18",
            "-c:a",
            "aac",
            "-movflags",
            "+faststart",
            str(output_path),
        ]
    )
    run_command(command)


def span_dicts(spans: Iterable[Span]) -> list[dict[str, float]]:
    return [asdict(span) | {"duration": round(span.duration, 3)} for span in spans]


def build_report(
    input_path: Path,
    output_path: Path,
    duration: float,
    sample_fps: float,
    threshold_mode: str,
    threshold_value: float,
    min_static_seconds: float,
    guard_seconds: float,
    static_spans: list[Span],
    removed_spans: list[Span],
    kept_spans: list[Span],
    dry_run: bool,
) -> dict[str, object]:
    removed_duration = sum(span.duration for span in removed_spans)
    kept_duration = sum(span.duration for span in kept_spans)
    return {
        "input": str(input_path),
        "output": str(output_path),
        "dry_run": dry_run,
        "parameters": {
            "sample_fps": sample_fps,
            "diff_threshold": threshold_value,
            "diff_threshold_mode": threshold_mode,
            "min_static_seconds": min_static_seconds,
            "guard_seconds": guard_seconds,
        },
        "source_duration": round(duration, 3),
        "estimated_output_duration": round(kept_duration, 3),
        "estimated_saved_duration": round(removed_duration, 3),
        "detected_static_spans": span_dicts(static_spans),
        "removed_spans": span_dicts(removed_spans),
        "kept_spans": span_dicts(kept_spans),
    }


def parse_threshold(value: str, differences: list[float]) -> tuple[str, float]:
    if value == "auto":
        return "auto", auto_diff_threshold(differences)
    try:
        threshold = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("--diff-threshold must be `auto` or a number") from exc
    if threshold < 0:
        raise argparse.ArgumentTypeError("--diff-threshold must be non-negative")
    return "manual", threshold


def positive_float(value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed) or parsed <= 0:
        raise argparse.ArgumentTypeError("value must be a positive number")
    return parsed


def non_negative_float(value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed) or parsed < 0:
        raise argparse.ArgumentTypeError("value must be a non-negative number")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Cut long static idle sections from screen recordings.")
    parser.add_argument("input", type=Path, help="Input video file.")
    parser.add_argument("--output", type=Path, required=True, help="Output video file.")
    parser.add_argument("--min-static-seconds", type=positive_float, default=DEFAULT_MIN_STATIC_SECONDS)
    parser.add_argument("--guard-seconds", type=non_negative_float, default=DEFAULT_GUARD_SECONDS)
    parser.add_argument("--sample-fps", type=positive_float, default=DEFAULT_SAMPLE_FPS)
    parser.add_argument("--diff-threshold", default="auto", help="Use `auto` or a numeric difference percent.")
    parser.add_argument("--dry-run", action="store_true", help="Generate report/segments without rendering.")
    parser.add_argument("--report", type=Path, help="Write a JSON report.")
    parser.add_argument("--segments", type=Path, help="Write an ffmpeg concat segment file.")
    parser.add_argument("--overwrite", action="store_true", help="Allow overwriting the output file.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    input_path = args.input.resolve()
    output_path = args.output.resolve()

    if not input_path.is_file():
        print(f"[FAIL] Input video does not exist: {input_path}", file=sys.stderr)
        return 1
    if input_path == output_path:
        print("[FAIL] Refusing to overwrite the source video.", file=sys.stderr)
        return 1
    if output_path.exists() and not args.overwrite and not args.dry_run:
        print(f"[FAIL] Output exists. Use --overwrite to replace it: {output_path}", file=sys.stderr)
        return 1
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        print("[FAIL] ffmpeg and ffprobe must be available on PATH.", file=sys.stderr)
        return 1

    try:
        duration = probe_duration(input_path)
        with tempfile.TemporaryDirectory(prefix="screen-idle-cutter-") as temp_name:
            frames_dir = Path(temp_name) / "frames"
            frames = extract_sample_frames(input_path, frames_dir, args.sample_fps)
            differences = compute_frame_differences(frames)
            threshold_mode, threshold_value = parse_threshold(args.diff_threshold, differences)
            static_spans = detect_static_spans(differences, args.sample_fps, threshold_value, duration)
            removed_spans = removable_spans_from_static(
                static_spans,
                args.min_static_seconds,
                args.guard_seconds,
            )
            kept_spans = kept_spans_from_removed(removed_spans, duration)

            if args.segments:
                args.segments.parent.mkdir(parents=True, exist_ok=True)
                write_segments_file(input_path, kept_spans, args.segments)

            report = build_report(
                input_path=input_path,
                output_path=output_path,
                duration=duration,
                sample_fps=args.sample_fps,
                threshold_mode=threshold_mode,
                threshold_value=threshold_value,
                min_static_seconds=args.min_static_seconds,
                guard_seconds=args.guard_seconds,
                static_spans=static_spans,
                removed_spans=removed_spans,
                kept_spans=kept_spans,
                dry_run=args.dry_run,
            )

            if args.report:
                args.report.parent.mkdir(parents=True, exist_ok=True)
                args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

            if not args.dry_run:
                segment_path = args.segments
                if segment_path is None:
                    segment_path = Path(temp_name) / "segments.txt"
                    write_segments_file(input_path, kept_spans, segment_path)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                render_video(segment_path, output_path, args.overwrite)

            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 0
    except Exception as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
