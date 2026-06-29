#!/usr/bin/env python3
"""Lightweight tests for idle-cut segment math."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from screen_idle_cutter import Span, kept_spans_from_removed, removable_spans_from_static  # noqa: E402


def assert_spans(actual: list[Span], expected: list[Span]) -> None:
    if actual != expected:
        raise AssertionError(f"Expected {expected}, got {actual}")


def test_short_static_span_is_not_cut() -> None:
    removed = removable_spans_from_static([Span(10, 20)], min_static_seconds=15, guard_seconds=5)
    assert_spans(removed, [])


def test_fifteen_second_static_span_cuts_middle_five_seconds() -> None:
    removed = removable_spans_from_static([Span(10, 25)], min_static_seconds=15, guard_seconds=5)
    assert_spans(removed, [Span(15, 20)])


def test_dynamic_spans_are_preserved_by_inverse_kept_spans() -> None:
    kept = kept_spans_from_removed([Span(15, 20)], duration=30)
    assert_spans(kept, [Span(0.0, 15), Span(20, 30)])


def test_adjacent_removed_intervals_do_not_overlap_kept_spans() -> None:
    removed = removable_spans_from_static(
        [Span(0, 20), Span(20, 40)],
        min_static_seconds=15,
        guard_seconds=5,
    )
    assert_spans(removed, [Span(5, 15), Span(25, 35)])
    kept = kept_spans_from_removed(removed, duration=40)
    assert_spans(kept, [Span(0.0, 5), Span(15, 25), Span(35, 40)])


def main() -> int:
    tests = [
        test_short_static_span_is_not_cut,
        test_fifteen_second_static_span_cuts_middle_five_seconds,
        test_dynamic_spans_are_preserved_by_inverse_kept_spans,
        test_adjacent_removed_intervals_do_not_overlap_kept_spans,
    ]
    for test in tests:
        test()
        print(f"[OK] {test.__name__}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
