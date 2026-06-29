#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from audit_recognition_output import build_audit_report  # noqa: E402
from recognition_postprocess import normalize_deck_result  # noqa: E402
from vision_fallback import merge_agent_task_result  # noqa: E402


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _ensure_task_payload(entry: dict[str, Any]) -> dict[str, Any]:
    payload = entry.get("task_payload")
    if isinstance(payload, dict):
        return payload
    payload = entry.get("payload")
    if isinstance(payload, dict):
        return payload
    payload = entry.get("result")
    if isinstance(payload, dict):
        return payload
    return {}


def normalize_task_results(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        raw_entries = payload
    elif isinstance(payload, dict):
        for key in ("vision_task_results", "task_results", "completed_tasks", "results"):
            if isinstance(payload.get(key), list):
                raw_entries = payload[key]
                break
        else:
            raw_entries = []
    else:
        raw_entries = []

    results: list[dict[str, Any]] = []
    for entry in raw_entries:
        if not isinstance(entry, dict):
            continue
        task_type = str(entry.get("task_type") or "").strip()
        if not task_type:
            continue
        try:
            slide_number = int(entry.get("slide_number") or 0)
        except (TypeError, ValueError):
            continue
        task_payload = _ensure_task_payload(entry)
        if not task_payload:
            continue
        results.append(
            {
                "slide_number": slide_number,
                "task_type": task_type,
                "task_payload": task_payload,
            }
        )
    return results


def _task_key(task: dict[str, Any]) -> tuple[int, str]:
    try:
        slide_number = int(task.get("slide_number") or 0)
    except (TypeError, ValueError):
        slide_number = 0
    return slide_number, str(task.get("task_type") or "").strip()


def apply_task_results(deck: dict[str, Any], task_results: list[dict[str, Any]]) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    merged = deepcopy(deck)
    slides = merged.get("slides") or []
    slides_by_number = {
        int(slide.get("slide_number") or 0): index
        for index, slide in enumerate(slides)
        if slide.get("slide_number") is not None
    }
    applied: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []

    for entry in task_results:
        slide_number = int(entry["slide_number"])
        task_type = str(entry["task_type"]).strip()
        payload = entry["task_payload"]
        slide_index = slides_by_number.get(slide_number)
        if slide_index is None:
            skipped.append(
                {
                    "slide_number": slide_number,
                    "task_type": task_type,
                    "reason": "slide_not_found",
                }
            )
            continue

        slides[slide_index] = merge_agent_task_result(slides[slide_index], task_type, payload)
        applied.append(
            {
                "slide_number": slide_number,
                "task_type": task_type,
            }
        )

    applied_keys = {(item["slide_number"], item["task_type"]) for item in applied}

    for slide in slides:
        pending = [
            task
            for task in (slide.get("vision_tasks") or [])
            if _task_key(task) not in applied_keys
        ]
        if pending:
            slide["vision_tasks"] = pending
        else:
            slide.pop("vision_tasks", None)

    pending_deck_tasks = [
        task
        for task in (merged.get("vision_tasks") or [])
        if _task_key(task) not in applied_keys
    ]
    if pending_deck_tasks:
        merged["vision_tasks"] = pending_deck_tasks
    else:
        merged.pop("vision_tasks", None)

    merged["slides"] = slides
    return merged, applied, skipped


def resolve_source_ppt(args: argparse.Namespace, deck: dict[str, Any]) -> Path | None:
    if args.source_ppt:
        return args.source_ppt.resolve()
    source_file = str(deck.get("source_file") or "").strip()
    if not source_file:
        return None
    candidate = Path(source_file)
    if candidate.exists():
        return candidate.resolve()
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply host IDE / agent vision task results back into a recognized PPT deck JSON.")
    parser.add_argument("deck_json", type=Path, help="Deck JSON that contains pending vision_tasks")
    parser.add_argument("task_results_json", type=Path, help="JSON file with completed task results")
    parser.add_argument("--output", type=Path, help="Optional output file for the merged deck JSON")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print output JSON")
    parser.add_argument("--source-ppt", type=Path, help="Optional source PPTX path for audit generation")
    parser.add_argument("--audit-output", type=Path, help="Optional JSON audit report output path")
    args = parser.parse_args()

    deck = load_json(args.deck_json)
    task_results = normalize_task_results(load_json(args.task_results_json))
    merged_deck, applied, skipped = apply_task_results(deck, task_results)

    source_ppt = resolve_source_ppt(args, deck)
    source_file = str(source_ppt) if source_ppt else str(deck.get("source_file") or "")
    normalized_deck = normalize_deck_result(merged_deck, source_file=source_file)
    if applied:
        normalized_deck["applied_vision_tasks"] = applied
    if skipped:
        normalized_deck["skipped_vision_task_results"] = skipped

    output = json.dumps(normalized_deck, ensure_ascii=False, indent=2 if args.pretty else None)
    if args.output:
        args.output.write_text(output, encoding="utf-8")
    else:
        print(output)

    if args.audit_output:
        if not source_ppt:
            raise SystemExit("--audit-output requires --source-ppt or a valid source_file in the deck JSON")
        report = build_audit_report(source_ppt, normalized_deck)
        report["master_json"] = str(args.output or args.deck_json)
        args.audit_output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
