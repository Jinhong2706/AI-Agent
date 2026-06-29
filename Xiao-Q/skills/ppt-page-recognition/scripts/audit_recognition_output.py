#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from extract_pptx_structure import PptxExtractor  # noqa: E402


GENERATION_FIELDS = ("title", "main_text", "labels", "metrics", "footer")
AUDIT_ONLY_FIELDS = ("all_visible_text", "instruction_text", "supplement", "missing_risk")


def sanitize_text(text: Any) -> str:
    if text is None:
        return ""
    return str(text).replace("\x0b", "\n").replace("\r", "\n").strip()


def normalize(text: Any) -> str:
    return "".join(sanitize_text(text).split()).lower()


def split_lines(text: Any) -> list[str]:
    return [line for line in sanitize_text(text).split("\n") if line.strip()]


def flatten_strings(value: Any) -> list[str]:
    items: list[str] = []
    if isinstance(value, dict):
        for child in value.values():
            items.extend(flatten_strings(child))
    elif isinstance(value, list):
        for child in value:
            items.extend(flatten_strings(child))
    elif isinstance(value, str):
        items.extend(split_lines(value))
    return items


def collect_source_lines(raw_slide: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    for element in raw_slide.get("elements", []):
        if element.get("kind") not in {"text", "graphic_text"}:
            continue
        text = element.get("text")
        if not sanitize_text(text):
            continue
        lines.extend(split_lines(text))
    deduped: list[str] = []
    for line in lines:
        if line not in deduped:
            deduped.append(line)
    return deduped


def collect_bucket_lines(slide: dict[str, Any], fields: tuple[str, ...]) -> list[str]:
    lines: list[str] = []
    for field in fields:
        lines.extend(flatten_strings(slide.get(field)))
    deduped: list[str] = []
    for line in lines:
        if line not in deduped:
            deduped.append(line)
    return deduped


def collect_structured_lines(slide: dict[str, Any]) -> list[str]:
    lines = flatten_strings(slide.get("structured_payload", {}))
    deduped: list[str] = []
    for line in lines:
        if line not in deduped:
            deduped.append(line)
    return deduped


def exclude_instruction_lines(source_lines: list[str], instruction_lines: list[str]) -> list[str]:
    filtered: list[str] = []
    for line in source_lines:
        if is_covered(line, instruction_lines):
            continue
        filtered.append(line)
    return filtered


def is_covered(source_line: str, target_lines: list[str]) -> bool:
    source_norm = normalize(source_line)
    if not source_norm:
        return True
    for target in target_lines:
        target_norm = normalize(target)
        if not target_norm:
            continue
        if source_norm == target_norm or source_norm in target_norm:
            return True
    return False


def detect_flattened_pairs(source_lines: list[str], structured_lines: list[str]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for left, right in zip(source_lines, source_lines[1:]):
        if len(left) > 24 or len(right) > 24:
            continue
        if any(ch in left for ch in "：:") and any(ch in right for ch in "：:"):
            continue
        combined = normalize(f"{left} {right}")
        if not combined:
            continue
        left_covered = is_covered(left, structured_lines)
        right_covered = is_covered(right, structured_lines)
        if left_covered and right_covered:
            continue
        for target in structured_lines:
            target_norm = normalize(target)
            if combined == target_norm:
                findings.append({"left": left, "right": right, "flattened_as": target})
                break
    deduped: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    for item in findings:
        key = (item["left"], item["right"], item["flattened_as"])
        if key not in seen:
            seen.add(key)
            deduped.append(item)
    return deduped


def build_audit_report(pptx_path: Path, master: dict[str, Any]) -> dict[str, Any]:
    raw = PptxExtractor(pptx_path).extract()
    report: dict[str, Any] = {
        "source_file": str(pptx_path),
        "slide_count": len(master.get("slides", [])),
        "slides": [],
    }

    for raw_slide, slide in zip(raw.get("slides", []), master.get("slides", [])):
        source_lines = collect_source_lines(raw_slide)
        generation_lines = collect_bucket_lines(slide, GENERATION_FIELDS)
        structured_lines = collect_structured_lines(slide)
        audit_lines = collect_bucket_lines(slide, AUDIT_ONLY_FIELDS)
        instruction_lines = collect_bucket_lines(slide, ("instruction_text",))
        semantic_source_lines = exclude_instruction_lines(source_lines, instruction_lines)
        json_lines = generation_lines + structured_lines + audit_lines

        missing_from_json = [line for line in semantic_source_lines if not is_covered(line, json_lines)]
        missing_from_generation = [line for line in semantic_source_lines if not is_covered(line, generation_lines + structured_lines)]
        missing_from_structured = [line for line in semantic_source_lines if not is_covered(line, structured_lines)]
        instruction_leaks = [line for line in instruction_lines if is_covered(line, generation_lines + structured_lines)]
        flattened_pairs = detect_flattened_pairs(semantic_source_lines, structured_lines)

        report["slides"].append(
            {
                "slide_number": raw_slide.get("slide_number"),
                "title": slide.get("title") or raw_slide.get("title"),
                "page_type": slide.get("page_type"),
                "source_visible_line_count": len(source_lines),
                "missing_from_json": missing_from_json,
                "missing_from_generation": missing_from_generation,
                "missing_from_structured_payload": missing_from_structured,
                "instruction_leaks": instruction_leaks,
                "flattened_pair_candidates": flattened_pairs,
                "existing_missing_risk": slide.get("missing_risk", []),
                "source_lines": source_lines,
                "generation_lines": generation_lines,
                "structured_lines": structured_lines,
                "audit_lines": audit_lines,
            }
        )

    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit recognition fidelity against a source PPTX and aggregated JSON.")
    parser.add_argument("pptx", type=Path, help="Source PPTX path")
    parser.add_argument("master_json", type=Path, help="Aggregated deck JSON path")
    parser.add_argument("--output", type=Path, help="Optional JSON report output path")
    args = parser.parse_args()

    master = json.loads(args.master_json.read_text(encoding="utf-8"))
    report = build_audit_report(args.pptx, master)
    report["master_json"] = str(args.master_json)

    if args.output:
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
