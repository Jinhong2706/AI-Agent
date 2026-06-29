#!/usr/bin/env python3

from __future__ import annotations

import json
import mimetypes
import re
import zipfile
from pathlib import Path
from typing import Any


def _image_area(element: dict[str, Any]) -> float:
    geometry = element.get("geometry") or {}
    width = float(geometry.get("w_pct") or 0.0)
    height = float(geometry.get("h_pct") or 0.0)
    return width * height


def _image_text_candidate(element: dict[str, Any]) -> bool:
    area = _image_area(element)
    return area >= 0.008


def should_enhance_slide(raw_slide: dict[str, Any], recognized_slide: dict[str, Any]) -> bool:
    if not raw_slide.get("elements"):
        return False
    images = [element for element in raw_slide["elements"] if element.get("kind") == "image" and element.get("media_target")]
    if not images:
        return False
    largest_image = max(images, key=_image_area)
    largest_area = _image_area(largest_image)
    text_count = len(recognized_slide.get("all_visible_text") or [])
    page_type = recognized_slide.get("page_type")
    return (
        largest_area >= 0.12
        and text_count <= 3
        and page_type in {"chapter", "image-text", "fallback"}
    )


def should_recover_full_slide(raw_slide: dict[str, Any], recognized_slide: dict[str, Any]) -> bool:
    """Return True when native extraction is mostly just a title over an image slide."""
    elements = raw_slide.get("elements") or []
    images = [element for element in elements if element.get("kind") == "image" and element.get("media_target")]
    if not images:
        return False

    largest_area = max((_image_area(image) for image in images), default=0.0)
    visible_lines = [str(item).strip() for item in recognized_slide.get("all_visible_text") or [] if str(item).strip()]
    title = str(recognized_slide.get("title") or "").strip()
    non_title_lines = [line for line in visible_lines if line and line != title]
    payload = recognized_slide.get("structured_payload") or {}
    page_type = str(recognized_slide.get("page_type") or "").strip()
    risks = " ".join(str(item) for item in recognized_slide.get("missing_risk") or [])

    low_native_coverage = len(visible_lines) <= 3 or not non_title_lines
    weak_structured_payload = not payload or all(value in (None, "", [], {}) for value in payload.values())
    image_heavy_risk = "image-heavy" in risks or "图片" in risks
    recoverable_type = page_type in {
        "image-text",
        "fallback",
        "chapter",
        "logo-wall",
        "metrics",
        "peer-panels",
        "people-matrix",
        "awards-patents",
        "timeline",
    }
    return (
        recoverable_type
        and largest_area >= 0.12
        and (low_native_coverage or weak_structured_payload or image_heavy_risk)
    )


def should_ocr_small_images(raw_slide: dict[str, Any], recognized_slide: dict[str, Any]) -> bool:
    images = [element for element in raw_slide.get("elements", []) if element.get("kind") == "image" and element.get("media_target")]
    if len(images) < 1:
        return False
    page_type = recognized_slide.get("page_type")
    return page_type in {"people-matrix", "awards-patents", "logo-wall", "metrics", "peer-panels", "image-text", "fallback", "timeline"}


def extract_primary_image(pptx_path: Path, raw_slide: dict[str, Any]) -> tuple[bytes, str, str] | None:
    images = [element for element in raw_slide.get("elements", []) if element.get("kind") == "image" and element.get("media_target")]
    if not images:
        return None
    largest = max(images, key=_image_area)
    target = largest.get("media_target")
    if not target:
        return None
    with zipfile.ZipFile(pptx_path) as archive:
        data = archive.read(target)
    mime = mimetypes.guess_type(target)[0] or "image/png"
    return data, mime, target


def extract_slide_screenshot(slide_number: int, search_root: Path | None = None) -> tuple[bytes, str, str] | None:
    roots = []
    if search_root:
        roots.append(search_root)
    roots.extend([Path.cwd(), Path(__file__).resolve().parents[2]])
    checked = set()
    for root in roots:
        root = root.resolve()
        if root in checked:
            continue
        checked.add(root)
        for candidate in (
            root / "output" / "screenshots" / f"slide_{slide_number}.png",
            root / "screenshots" / f"slide_{slide_number}.png",
        ):
            if candidate.exists():
                return candidate.read_bytes(), "image/png", str(candidate)
    return None


def extract_candidate_images(pptx_path: Path, raw_slide: dict[str, Any], limit: int = 4) -> list[tuple[bytes, str, str]]:
    images = [
        element
        for element in raw_slide.get("elements", [])
        if element.get("kind") == "image" and element.get("media_target") and _image_text_candidate(element)
    ]
    images = sorted(images, key=_image_area, reverse=True)[:limit]
    outputs: list[tuple[bytes, str, str]] = []
    with zipfile.ZipFile(pptx_path) as archive:
        for image in images:
            target = image.get("media_target")
            if not target:
                continue
            data = archive.read(target)
            mime = mimetypes.guess_type(target)[0] or "image/png"
            outputs.append((data, mime, target))
    return outputs


def _extract_json(text: str) -> dict[str, Any]:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


def call_siliconflow_vision(image_bytes: bytes, mime: str, prompt_text: str, retries: int = 2) -> dict[str, Any]:
    raise RuntimeError(
        "Built-in remote vision has been removed. "
        "Use host vision tasks in the IDE and merge the returned payloads with apply_vision_tasks.py."
    )


def build_timeline_task_prompt(recognized_slide: dict[str, Any]) -> str:
    return (
        "你将看到一页PPT整页截图。请补全这页时间线的结构语义，"
        "识别顶部父标题、每个时期、每个时期的主能力标签、场景和目标领域。"
        "只返回 JSON："
        "{\"parent_label\":\"\",\"periods\":[{\"period\":\"\",\"headline\":\"\",\"capability_tag\":\"\",\"scenario\":\"\",\"target_domain\":\"\",\"supporting_labels\":[],\"panel_connectors\":[]}]}。"
    )


def build_cover_footer_task_prompt() -> str:
    return (
        "你将看到一页PPT整页截图。请只提取底部页脚中所有清晰可见的文字，"
        "尤其是左下角公司名和右下角网址。"
        "只返回JSON：{\"footer_lines\":[]}"
    )


def build_logo_wall_task_prompt() -> str:
    return (
        "你将看到一页PPT整页截图。请识别所有“客户名 + 系统名”的成对单元，并按页面上的业务标题分组输出。"
        "如果logo同时带英文和中文，请优先输出页面里可见的中文客户全称，不要附带英文品牌字样。"
        "特别注意最右侧窄列或边缘列不要漏。"
        "只返回JSON：{\"groups\":[{\"group_title\":\"\",\"entries\":[{\"name\":\"\",\"system\":\"\"}]}]}"
    )


def build_people_chart_task_prompt() -> str:
    return (
        "你将看到一页PPT整页截图。请只识别环形图对应的人力分布数据，不要识别左侧更新人数情况。"
        "只返回JSON：{\"chart_breakdown\":{\"display_total\":\"\",\"segments\":[{\"label\":\"\",\"value\":\"\",\"percentage\":\"\"}]}}。"
        "label 只允许：产品研发、人工智能、实施服务、销售、中后台。"
    )


def build_awards_investors_task_prompt(recognized_slide: dict[str, Any]) -> str:
    return (
        "你将看到一页PPT整页截图。请只补全关键奖项和投资人区域，"
        "尤其注意被拆开的奖项名和右侧投资人 logo 对应名称。"
        "只返回 JSON："
        "{\"awards\":[],\"investors\":[]}"
    )


def build_full_slide_recovery_prompt(raw_slide: dict[str, Any], recognized_slide: dict[str, Any]) -> str:
    return build_prompt(raw_slide, recognized_slide)


def full_slide_recovery_schema() -> dict[str, Any]:
    return {
        "page_type": "",
        "title": "",
        "hierarchy": [{"title": "", "items": [], "children": []}],
        "layout_intent": {
            "direction": "",
            "panel_count": 0,
            "has_connectors": False,
            "narrative": "",
            "dominant_visual": "",
            "parent_label": "",
        },
        "connectors": [{"scope": "", "type": "", "from": "", "to": "", "meaning": ""}],
        "structured_payload": {},
        "all_visible_text": [],
        "main_text": [],
        "metrics": [{"label": "", "value": "", "unit": "", "supporting_text": []}],
        "labels": [],
        "supplement": [],
        "missing_risk": [],
        "confidence": 0.0,
        "reason": "",
    }


def build_agent_vision_task(raw_slide: dict[str, Any], recognized_slide: dict[str, Any], image_path: str, task_type: str, prompt: str, expected_schema: dict[str, Any], goal: str) -> dict[str, Any]:
    return {
        "slide_number": int(raw_slide.get("slide_number") or recognized_slide.get("slide_number") or 0),
        "page_type": str(recognized_slide.get("page_type") or "").strip(),
        "task_type": task_type,
        "goal": goal,
        "image_path": image_path,
        "host_capability": "vision",
        "prompt": prompt,
        "expected_schema": expected_schema,
        "merge_strategy": "deep-merge-structured-payload-and-refresh-audit-buckets",
    }


def _looks_pair_text(text: str) -> bool:
    lines = [line.strip() for line in str(text).splitlines() if line.strip()]
    suffixes = ("资产管理系统", "集成管理系统", "能源管理系统", "运维管理系统", "管理系统", "系统")
    if len(lines) >= 2 and any(lines[-1].endswith(suffix) for suffix in suffixes):
        return True
    clean = str(text).strip()
    return any(clean.endswith(suffix) for suffix in suffixes)


def _logo_wall_right_threshold(raw_slide: dict[str, Any]) -> float:
    text_elements = [
        element
        for element in raw_slide.get("elements", [])
        if element.get("kind") in {"text", "graphic_text"} and element.get("text")
    ]
    top_headings = [
        element
        for element in text_elements
        if element.get("role_guess") == "heading" and float((element.get("geometry") or {}).get("y_pct") or 1) < 0.26
    ]
    right_heading = next((element for element in top_headings if float((element.get("geometry") or {}).get("x_pct") or 0) > 0.75), None)
    if not right_heading:
        return 0.78
    right_x = float(((right_heading or {}).get("geometry") or {}).get("x_pct") or 0)
    return max(0.72, right_x - 0.1)


def collect_vision_tasks(pptx_path: Path, raw_slide: dict[str, Any], recognized_slide: dict[str, Any]) -> list[dict[str, Any]]:
    screenshot = extract_slide_screenshot(int(raw_slide.get("slide_number") or 0), search_root=pptx_path.parent)
    if not screenshot:
        return []

    _image_bytes, _mime, image_path = screenshot
    page_type = str(recognized_slide.get("page_type") or "").strip()
    tasks: list[dict[str, Any]] = []
    payload = recognized_slide.get("structured_payload") or {}
    visible = {str(item).strip() for item in recognized_slide.get("all_visible_text") or [] if str(item).strip()}

    if page_type == "timeline" and not (payload.get("periods") or []):
        tasks.append(
            build_agent_vision_task(
                raw_slide,
                recognized_slide,
                image_path,
                "timeline_recovery",
                build_timeline_task_prompt(recognized_slide),
                {
                    "parent_label": "",
                    "periods": [
                        {
                            "period": "",
                            "headline": "",
                            "capability_tag": "",
                            "scenario": "",
                            "target_domain": "",
                            "supporting_labels": [],
                            "panel_connectors": [],
                        }
                    ],
                },
                "Recover the full timeline semantics from the slide image.",
            )
        )

    if page_type == "logo-wall" and needs_logo_wall_followup(raw_slide, recognized_slide):
        tasks.append(
            build_agent_vision_task(
                raw_slide,
                recognized_slide,
                image_path,
                "logo_wall_group_recovery",
                build_logo_wall_task_prompt(),
                {"groups": [{"group_title": "", "entries": [{"name": "", "system": ""}]}]},
                "Recover grouped customer/project entries from the slide image.",
            )
        )

    if page_type == "people-matrix" and needs_people_matrix_chart_followup(recognized_slide):
        tasks.append(
            build_agent_vision_task(
                raw_slide,
                recognized_slide,
                image_path,
                "people_chart_recovery",
                build_people_chart_task_prompt(),
                {
                    "chart_breakdown": {
                        "display_total": "",
                        "segments": [{"label": "", "value": "", "percentage": ""}],
                    }
                },
                "Recover the donut-chart headcount breakdown while keeping updated text metrics separate.",
            )
        )

    if page_type == "awards-patents" and ("投资人" in visible and not (payload.get("investors") or [])):
        tasks.append(
            build_agent_vision_task(
                raw_slide,
                recognized_slide,
                image_path,
                "awards_and_investors_recovery",
                build_awards_investors_task_prompt(recognized_slide),
                {"awards": [], "investors": []},
                "Recover split award names and investor identities from the slide image.",
            )
        )

    if page_type == "cover" and len(recognized_slide.get("footer") or []) <= 1:
        tasks.append(
            build_agent_vision_task(
                raw_slide,
                recognized_slide,
                image_path,
                "cover_footer_recovery",
                build_cover_footer_task_prompt(),
                {"footer_lines": []},
                "Recover missing footer text from the cover slide image.",
            )
        )

    has_full_slide_recovery = any(task.get("task_type") == "slide_visual_recovery" for task in tasks)
    if should_recover_full_slide(raw_slide, recognized_slide) and not has_full_slide_recovery:
        tasks.append(
            build_agent_vision_task(
                raw_slide,
                recognized_slide,
                image_path,
                "slide_visual_recovery",
                build_full_slide_recovery_prompt(raw_slide, recognized_slide),
                full_slide_recovery_schema(),
                "Recover the full page text, hierarchy, metrics, connectors, and structured payload from the slide image.",
            )
        )

    return tasks


def _nonempty_text(value: Any) -> str:
    return str(value or "").strip()


def _dedupe_strings(items: list[Any]) -> list[str]:
    return [str(item).strip() for item in _dedupe([str(item).strip() for item in items if str(item).strip()])]


def _entry_identity(entry: dict[str, Any]) -> str:
    name = _nonempty_text(entry.get("name"))
    system = _nonempty_text(entry.get("system"))
    if name:
        return f"name:{name.lower()}"
    if system:
        return f"system:{system.lower()}"
    return json.dumps(entry, ensure_ascii=False, sort_keys=True)


def _merge_entry(existing: dict[str, Any], new: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": _nonempty_text(new.get("name")) or _nonempty_text(existing.get("name")),
        "system": _nonempty_text(new.get("system")) or _nonempty_text(existing.get("system")),
    }


def _entry_score(entry: dict[str, Any]) -> int:
    return int(bool(_nonempty_text(entry.get("name")))) + int(bool(_nonempty_text(entry.get("system"))))


def _merge_entries(existing_entries: list[dict[str, Any]], new_entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    seen: dict[str, int] = {}
    for source in [existing_entries or [], new_entries or []]:
        for raw_entry in source:
            if not isinstance(raw_entry, dict):
                continue
            entry = {
                "name": _nonempty_text(raw_entry.get("name")),
                "system": _nonempty_text(raw_entry.get("system")),
            }
            if not entry["name"] and not entry["system"]:
                continue
            key = _entry_identity(entry)
            if key in seen:
                merged[seen[key]] = _merge_entry(merged[seen[key]], entry)
            else:
                seen[key] = len(merged)
                merged.append(entry)
    return merged


def _group_identity(group: dict[str, Any]) -> str:
    title = _nonempty_text(group.get("group_title"))
    if title:
        return title.lower()
    entries = group.get("entries") or []
    items = group.get("items") or []
    marker = entries or items
    return json.dumps(marker, ensure_ascii=False, sort_keys=True)


def _group_score(group: dict[str, Any]) -> int:
    entries = [entry for entry in group.get("entries") or [] if isinstance(entry, dict)]
    items = [item for item in group.get("items") or [] if _nonempty_text(item)]
    return (
        len(entries) * 3
        + sum(_entry_score(entry) for entry in entries)
        + len(items)
        + int(bool(_nonempty_text(group.get("group_title"))))
    )


def _merge_group(existing: dict[str, Any], new: dict[str, Any]) -> dict[str, Any]:
    prefer_new = _should_prefer_new_group(existing, new)
    merged_entries = _merge_entries(
        (new.get("entries") or []) if prefer_new else (existing.get("entries") or []),
        (existing.get("entries") or []) if prefer_new else (new.get("entries") or []),
    )
    preferred_entry_items = [f"{entry.get('name', '')} {entry.get('system', '')}".strip() for entry in merged_entries]
    base_items = (
        (new.get("items") or preferred_entry_items)
        if prefer_new
        else (existing.get("items") or preferred_entry_items)
    )
    extra_items = (existing.get("items") or []) if prefer_new else (new.get("items") or [])
    merged_items = preferred_entry_items or _merge_ordered_strings(base_items, extra_items)
    merged_group = {
        "group_title": _nonempty_text(new.get("group_title")) or _nonempty_text(existing.get("group_title")),
        "entries": merged_entries,
        "items": merged_items,
    }
    return merged_group


def _should_prefer_new_group(existing: dict[str, Any], new: dict[str, Any]) -> bool:
    existing_entries = [entry for entry in existing.get("entries") or [] if isinstance(entry, dict)]
    new_entries = [entry for entry in new.get("entries") or [] if isinstance(entry, dict)]
    if not new_entries:
        return False
    if not existing_entries:
        return True
    existing_identities = {_entry_identity(entry) for entry in existing_entries}
    new_identities = {_entry_identity(entry) for entry in new_entries}
    if existing_identities == new_identities and len(new_entries) == len(existing_entries):
        return True
    if existing_identities and existing_identities.issubset(new_identities) and _group_score(new) >= _group_score(existing):
        return True
    if len(new_entries) >= len(existing_entries) + 2 and _group_score(new) >= _group_score(existing):
        return True
    return False


def _merge_logo_wall_groups(existing_groups: list[dict[str, Any]], new_groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ordered: list[dict[str, Any]] = []
    seen: dict[str, int] = {}
    for source in [existing_groups or [], new_groups or []]:
        for raw_group in source:
            if not isinstance(raw_group, dict):
                continue
            group = {
                "group_title": _nonempty_text(raw_group.get("group_title") or raw_group.get("title")),
                "entries": [entry for entry in raw_group.get("entries") or [] if isinstance(entry, dict)],
                "items": _dedupe_strings(raw_group.get("items") or []),
            }
            key = _group_identity(group)
            if key in seen:
                ordered[seen[key]] = _merge_group(ordered[seen[key]], group)
            else:
                seen[key] = len(ordered)
                ordered.append(group)
    return ordered


def _merge_logo_wall_groups_with_host_order(existing_groups: list[dict[str, Any]], new_groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
    existing_by_key: dict[str, dict[str, Any]] = {}
    ordered_existing_keys: list[str] = []
    for raw_group in existing_groups or []:
        if not isinstance(raw_group, dict):
            continue
        group = {
            "group_title": _nonempty_text(raw_group.get("group_title") or raw_group.get("title")),
            "entries": [entry for entry in raw_group.get("entries") or [] if isinstance(entry, dict)],
            "items": _dedupe_strings(raw_group.get("items") or []),
        }
        key = _group_identity(group)
        if key not in existing_by_key:
            ordered_existing_keys.append(key)
        existing_by_key[key] = group

    merged_groups: list[dict[str, Any]] = []
    consumed: set[str] = set()

    for raw_group in new_groups or []:
        if not isinstance(raw_group, dict):
            continue
        new_group = {
            "group_title": _nonempty_text(raw_group.get("group_title") or raw_group.get("title")),
            "entries": [entry for entry in raw_group.get("entries") or [] if isinstance(entry, dict)],
            "items": _dedupe_strings(raw_group.get("items") or []),
        }
        key = _group_identity(new_group)
        consumed.add(key)
        existing_group = existing_by_key.get(key, {})
        merged_entries = _merge_entries(new_group.get("entries") or [], existing_group.get("entries") or [])
        merged_items = [f"{entry.get('name', '')} {entry.get('system', '')}".strip() for entry in merged_entries]
        if not merged_items:
            merged_items = _merge_ordered_strings(new_group.get("items") or [], existing_group.get("items") or [])
        merged_groups.append(
            {
                "group_title": _nonempty_text(new_group.get("group_title")) or _nonempty_text(existing_group.get("group_title")),
                "entries": merged_entries,
                "items": merged_items,
            }
        )

    for key in ordered_existing_keys:
        if key in consumed:
            continue
        merged_groups.append(existing_by_key[key])

    return merged_groups


def _period_identity(period: dict[str, Any]) -> str:
    for key in ("period", "headline", "capability_tag"):
        value = _nonempty_text(period.get(key))
        if value:
            return f"{key}:{value.lower()}"
    return json.dumps(period, ensure_ascii=False, sort_keys=True)


def _merge_period(existing: dict[str, Any], new: dict[str, Any]) -> dict[str, Any]:
    merged = dict(existing)
    for key in ("period", "headline", "capability_tag", "scenario", "target_domain"):
        merged[key] = _nonempty_text(new.get(key)) or _nonempty_text(existing.get(key))
    merged["supporting_labels"] = _dedupe_strings([*(existing.get("supporting_labels") or []), *(new.get("supporting_labels") or [])])
    merged["panel_connectors"] = _dedupe([*(existing.get("panel_connectors") or []), *(new.get("panel_connectors") or [])])
    return merged


def _merge_timeline_periods(existing_periods: list[dict[str, Any]], new_periods: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ordered: list[dict[str, Any]] = []
    seen: dict[str, int] = {}
    for source in [existing_periods or [], new_periods or []]:
        for raw_period in source:
            if not isinstance(raw_period, dict):
                continue
            key = _period_identity(raw_period)
            if key in seen:
                ordered[seen[key]] = _merge_period(ordered[seen[key]], raw_period)
            else:
                seen[key] = len(ordered)
                ordered.append(dict(raw_period))
    return ordered


def _segment_score(segment: dict[str, Any]) -> int:
    return sum(int(bool(_nonempty_text(segment.get(key)))) for key in ("label", "value", "percentage"))


def _merge_chart_breakdown(existing: dict[str, Any], new: dict[str, Any]) -> dict[str, Any]:
    merged = dict(existing or {})
    new_total = _nonempty_text(new.get("display_total"))
    if new_total:
        merged["display_total"] = new_total
    existing_segments = { _nonempty_text(seg.get("label")).lower(): dict(seg) for seg in existing.get("segments") or [] if isinstance(seg, dict) and _nonempty_text(seg.get("label")) }
    for raw_segment in new.get("segments") or []:
        if not isinstance(raw_segment, dict):
            continue
        label = _nonempty_text(raw_segment.get("label")).lower()
        if not label:
            continue
        current = existing_segments.get(label, {})
        merged_segment = {
            "label": _nonempty_text(raw_segment.get("label")) or _nonempty_text(current.get("label")),
            "value": _nonempty_text(raw_segment.get("value")) or _nonempty_text(current.get("value")),
            "percentage": _nonempty_text(raw_segment.get("percentage")) or _nonempty_text(current.get("percentage")),
        }
        if _segment_score(merged_segment) >= _segment_score(current):
            existing_segments[label] = merged_segment
    if existing_segments:
        merged["segments"] = list(existing_segments.values())
    return merged


def _merge_metric_blocks(existing_blocks: list[dict[str, Any]], new_blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    seen: dict[str, int] = {}
    for source in [existing_blocks or [], new_blocks or []]:
        for raw_block in source:
            if not isinstance(raw_block, dict):
                continue
            label = _nonempty_text(raw_block.get("label"))
            value = _nonempty_text(raw_block.get("value"))
            unit = _nonempty_text(raw_block.get("unit"))
            key = label.lower() if label else json.dumps(raw_block, ensure_ascii=False, sort_keys=True)
            block = {
                **raw_block,
                "label": label,
                "value": value,
                "unit": unit,
            }
            if key in seen:
                current = dict(merged[seen[key]])
                current["label"] = block["label"] or _nonempty_text(current.get("label"))
                current["value"] = block["value"] or _nonempty_text(current.get("value"))
                current["unit"] = block["unit"] or _nonempty_text(current.get("unit"))
                current["supporting_text"] = _dedupe_strings([*(current.get("supporting_text") or []), *(block.get("supporting_text") or [])])
                merged[seen[key]] = current
            else:
                seen[key] = len(merged)
                merged.append(block)
    return merged


def _merge_structured_payload(existing: dict[str, Any], new: dict[str, Any], page_type: str = "") -> dict[str, Any]:
    merged = dict(existing or {})
    page_type = _nonempty_text(page_type)
    for key, value in (new or {}).items():
        if value in (None, "", [], {}):
            continue
        if key == "groups":
            merged[key] = _merge_logo_wall_groups(merged.get(key) or [], value if isinstance(value, list) else [])
        elif key == "periods":
            merged[key] = _merge_timeline_periods(merged.get(key) or [], value if isinstance(value, list) else [])
        elif key in {"awards", "investors", "footer_lines"}:
            merged[key] = _dedupe_strings([*(merged.get(key) or []), *(value if isinstance(value, list) else [value])])
        elif key == "metric_blocks":
            merged[key] = _merge_metric_blocks(merged.get(key) or [], value if isinstance(value, list) else [])
        elif key == "chart_breakdown" and isinstance(value, dict):
            merged[key] = _merge_chart_breakdown(merged.get(key) or {}, value)
        elif isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _merge_structured_payload(merged.get(key) or {}, value, page_type=page_type)
        elif isinstance(value, list) and isinstance(merged.get(key), list):
            merged[key] = _dedupe([*(merged.get(key) or []), *value])
        else:
            if key not in merged or merged.get(key) in (None, "", [], {}):
                merged[key] = value
            elif page_type == "timeline" and key == "parent_label" and _nonempty_text(value):
                merged[key] = value
    return merged


def _merge_ordered_strings(preferred: list[Any], additional: list[Any]) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()
    for source in (preferred or [], additional or []):
        for item in source:
            text = str(item).strip()
            if not text or text in seen:
                continue
            seen.add(text)
            ordered.append(text)
    return ordered


def _build_timeline_progression_connectors(periods: list[dict[str, Any]]) -> list[dict[str, str]]:
    cleaned_periods = [str(period.get("period") or "").strip() for period in periods if str(period.get("period") or "").strip()]
    connectors: list[dict[str, str]] = []
    for left, right in zip(cleaned_periods, cleaned_periods[1:]):
        connectors.append(
            {
                "scope": "global",
                "type": "arrow",
                "from": left,
                "to": right,
                "panel": "",
                "meaning": "progression",
            }
        )
    return connectors


def _hierarchy_score(nodes: Any) -> int:
    if not isinstance(nodes, list):
        return 0
    score = 0
    for node in nodes:
        if not isinstance(node, dict):
            continue
        score += int(bool(_nonempty_text(node.get("title"))))
        score += len(node.get("items") or [])
        score += len(node.get("children") or []) * 2
    return score


def _connector_score(connectors: Any) -> int:
    if not isinstance(connectors, list):
        return 0
    return len([item for item in connectors if isinstance(item, dict) and any(_nonempty_text(item.get(key)) for key in ("from", "to", "meaning", "type"))])


def _recovered_logo_entry_count(groups: list[dict[str, Any]]) -> int:
    count = 0
    for group in groups or []:
        for entry in group.get("entries") or []:
            if isinstance(entry, dict) and (_nonempty_text(entry.get("name")) or _nonempty_text(entry.get("system"))):
                count += 1
    return count


def merge_agent_task_result(native_slide: dict[str, Any], task_type: str, task_payload: dict[str, Any]) -> dict[str, Any]:
    if task_type == "slide_visual_recovery":
        return merge_slide_result(native_slide, task_payload)

    merged = dict(native_slide)
    structured = dict(merged.get("structured_payload") or {})
    missing_risk = [str(item).strip() for item in merged.get("missing_risk") or [] if str(item).strip()]

    if task_type == "timeline_recovery":
        parent_label = str(task_payload.get("parent_label") or "").strip()
        periods = task_payload.get("periods") or []
        if parent_label:
            structured["parent_label"] = parent_label
        if periods:
            structured["periods"] = _merge_timeline_periods(structured.get("periods") or [], periods)
            merged["layout_intent"] = {
                "direction": "left_to_right",
                "panel_count": len(structured.get("periods") or []),
                "has_connectors": True,
                "narrative": "progression",
                "dominant_visual": "three_panels",
                "parent_label": structured.get("parent_label", ""),
            }
            merged["connectors"] = _build_timeline_progression_connectors(structured.get("periods") or [])
        if periods:
            missing_risk = [risk for risk in missing_risk if "时间线" not in risk.lower()]

    elif task_type == "logo_wall_group_recovery":
        groups = task_payload.get("groups") or []
        if groups:
            structured["groups"] = _merge_logo_wall_groups_with_host_order(structured.get("groups") or [], groups)
        if groups and all(group.get("entries") for group in structured.get("groups") or []):
            missing_risk = [
                risk
                for risk in missing_risk
                if "logo-wall group titles were preserved" not in risk
            ]

    elif task_type == "people_chart_recovery":
        chart = task_payload.get("chart_breakdown") or {}
        if chart:
            structured["chart_breakdown"] = _merge_chart_breakdown(structured.get("chart_breakdown") or {}, chart)
        segments = (structured.get("chart_breakdown") or {}).get("segments") or []
        if len(segments) == 5 and all(str(segment.get("value") or "").strip() and str(segment.get("percentage") or "").strip() for segment in segments):
            missing_risk = [risk for risk in missing_risk if "人数" not in risk and "chart" not in risk.lower()]

    elif task_type == "awards_and_investors_recovery":
        awards = task_payload.get("awards") or []
        investors = task_payload.get("investors") or []
        if awards:
            existing_awards = [str(item).strip() for item in structured.get("awards") or [] if str(item).strip()]
            new_awards = [str(item).strip() for item in awards if str(item).strip()]
            if existing_awards and set(existing_awards).issubset(set(new_awards)) and len(new_awards) >= len(existing_awards):
                structured["awards"] = _dedupe(list(new_awards) + [item for item in existing_awards if item not in new_awards])
            else:
                structured["awards"] = _dedupe(existing_awards + new_awards)
        if investors:
            structured["investors"] = _dedupe(list(structured.get("investors") or []) + list(investors))
            missing_risk = [risk for risk in missing_risk if "投资人" not in risk]

    elif task_type == "cover_footer_recovery":
        footer_lines = task_payload.get("footer_lines") or []
        if footer_lines:
            merged["footer"] = _dedupe(list(merged.get("footer") or []) + list(footer_lines))
            merged["all_visible_text"] = _dedupe(list(merged.get("all_visible_text") or []) + list(footer_lines))
            structured["footer_lines"] = merged["footer"]
            missing_risk = [risk for risk in missing_risk if "footer" not in risk.lower() and "页脚" not in risk]

    merged["structured_payload"] = structured
    merged["missing_risk"] = missing_risk
    merged["supplement"] = _dedupe(list(merged.get("supplement") or []) + [f"merged agent vision task: {task_type}"])
    return merged


def needs_logo_wall_followup(raw_slide: dict[str, Any], slide: dict[str, Any]) -> bool:
    payload = slide.get("structured_payload") or {}
    groups = payload.get("groups") or []
    visible = " ".join(str(item) for item in slide.get("all_visible_text") or [])
    has_system_markers = any(token in visible for token in ("能源管理系统", "集成管理系统", "资产管理系统"))
    recovered_count = _recovered_logo_entry_count(groups)
    if not has_system_markers:
        if any(not (group.get("items") or group.get("entries")) for group in groups):
            return True
        return False
    if not groups:
        return True
    raw_pair_count = sum(
        1
        for element in raw_slide.get("elements", [])
        if element.get("kind") in {"text", "graphic_text"} and _looks_pair_text(element.get("text") or "")
    )
    if any(not str(entry.get("system") or "").strip() for group in groups for entry in group.get("entries") or []) and raw_pair_count > recovered_count:
        return True
    if len(groups) >= 2 and len((groups[-1].get("entries") or [])) <= 1 and raw_pair_count > recovered_count:
        return True
    if any(not (group.get("items") or group.get("entries")) for group in groups) and raw_pair_count > recovered_count:
        return True
    if _looks_like_edge_column_logo_wall_followup(raw_slide):
        return True
    text_elements = [
        element
        for element in raw_slide.get("elements", [])
        if element.get("kind") in {"text", "graphic_text"} and element.get("text")
    ]
    right_threshold = _logo_wall_right_threshold(raw_slide)
    right_heading_present = any(
        element.get("role_guess") == "heading"
        and float((element.get("geometry") or {}).get("y_pct") or 1) < 0.26
        and float((element.get("geometry") or {}).get("x_pct") or 0) >= right_threshold
        for element in text_elements
    )
    right_pair_count = sum(
        1
        for element in text_elements
        if _looks_pair_text(element.get("text") or "")
        and float((element.get("geometry") or {}).get("x_pct") or 0) >= right_threshold
    )
    right_group_count = 0
    if groups:
        right_group = groups[-1]
        right_group_count = max(len(right_group.get("entries") or []), len(right_group.get("items") or []))
    if right_heading_present and right_pair_count > right_group_count:
        return True
    return False


def needs_people_matrix_chart_followup(slide: dict[str, Any]) -> bool:
    payload = slide.get("structured_payload") or {}
    chart = payload.get("chart_breakdown") or {}
    segments = chart.get("segments") or []
    if chart:
        return True
    if len(segments) != 5:
        return True
    labels = {str(segment.get("label") or "").strip() for segment in segments}
    if labels != {"产品研发", "人工智能", "实施服务", "销售", "中后台"}:
        return True
    for segment in segments:
        if not str(segment.get("value") or "").strip() or not str(segment.get("percentage") or "").strip():
            return True
    return False


def _looks_like_edge_column_logo_wall_followup(raw_slide: dict[str, Any]) -> bool:
    text_elements = [
        element
        for element in raw_slide.get("elements", [])
        if element.get("kind") in {"text", "graphic_text"} and element.get("text")
    ]
    headings = sorted(
        [
            {
                "x_pct": float((element.get("geometry") or {}).get("x_pct") or 0),
                "w_pct": float((element.get("geometry") or {}).get("w_pct") or 0),
            }
            for element in text_elements
            if element.get("role_guess") == "heading" and float((element.get("geometry") or {}).get("y_pct") or 1) < 0.26
        ],
        key=lambda item: item["x_pct"],
    )
    if len(headings) != 2:
        return False
    right_heading = headings[-1]
    if right_heading["x_pct"] < 0.78 or right_heading["w_pct"] > 0.08:
        return False
    pair_xs = sorted(
        float((element.get("geometry") or {}).get("x_pct") or 0)
        for element in text_elements
        if _looks_pair_text(element.get("text") or "")
    )
    if len(pair_xs) < 6:
        return False
    clusters: list[list[float]] = [[pair_xs[0]]]
    for x_pct in pair_xs[1:]:
        if abs(x_pct - clusters[-1][-1]) <= 0.05:
            clusters[-1].append(x_pct)
        else:
            clusters.append([x_pct])
    centers = [sum(cluster) / len(cluster) for cluster in clusters]
    return len(centers) >= 5 and (centers[-1] - centers[-2]) >= 0.08


def build_prompt(raw_slide: dict[str, Any], recognized_slide: dict[str, Any]) -> str:
    native_title = recognized_slide.get("title") or ""
    native_lines = recognized_slide.get("all_visible_text") or []
    page_type = recognized_slide.get("page_type")
    page_hints = []
    if page_type == "cover":
        page_hints.append("如果封面底部还有公司名、品牌名或网址，请补进 footer_lines / all_visible_text，不要遗漏小页脚。")
    if page_type == "awards-patents":
        page_hints.append("如果页面下方还有投资人 logo 或名称，请把投资人名称识别成 investors 数组，不要只识别到标题。")
    if page_type == "logo-wall":
        page_hints.append("如果页面里是客户名 + 系统名的二元单元，请在 structured_payload.groups[].entries 中输出 name/system 对，不要只给扁平字符串。")
    if page_type == "people-matrix":
        page_hints.append("如果页面同时存在更新后人数表和环形图旧数据，请双轨保留；不要让更新表覆盖环形图分布。")
    if page_type == "peer-panels":
        page_hints.append("如果页面是左右并列或中心枢纽 + 两侧分组，请保留这种并列层级，不要压平成普通正文块。")
    return f"""
你将看到一页PPT的整页图片。这一页在原始PPT里主要内容是图片，因此需要你补识别图片中的文本和结构。

已知原生信息：
- slide_number: {recognized_slide.get('slide_number')}
- native_title: {native_title}
- native_visible_text: {json.dumps(native_lines, ensure_ascii=False)}
- current_page_type_guess: {page_type}

请根据图片内容识别并输出一个 JSON 对象，只包含这些字段：
- page_type
- title
- hierarchy
- layout_intent
- connectors
- structured_payload
- all_visible_text
- main_text
- metrics
- labels
- supplement
- missing_risk
- confidence
- reason

要求：
1. 只返回 JSON。
2. 如果图片里是时间线、分栏、箭头关系，要把这些关系放进 hierarchy / layout_intent / connectors / structured_payload。
3. all_visible_text 尽量覆盖图片中的主要可见文本，但不要编造看不清的小字。
4. 如果能看出是 timeline、people-matrix、logo-wall、awards-patents 等页面类型，请明确输出。
5. confidence 用 0 到 1 的小数。
6. {(" ".join(page_hints) if page_hints else "请特别关注小页脚、成组标签和图片内文字，避免只识别大标题。")}
""".strip()


def build_ocr_prompt(target: str) -> str:
    return f"""
你将看到一张从PPT中抽出的图片片段，来源文件是 {target}。

请执行轻量 OCR 补漏，并只返回 JSON：
{{
  "visible_lines": [],
  "short_labels": [],
  "confidence": 0.0,
  "reason": ""
}}

要求：
1. 只提取图片里清晰可见的文字，不要猜测看不清的小字。
2. 如果图片主要是头像、插画、纯 logo 或没有可读文字，visible_lines 返回空数组。
3. short_labels 只保留适合作为标签的短文本。
4. 只返回 JSON。
""".strip()


def merge_slide_result(native: dict[str, Any], vision: dict[str, Any]) -> dict[str, Any]:
    merged = dict(native)

    def merge_list(key: str) -> None:
        native_list = _ensure_list(native.get(key))
        vision_list = _ensure_list(vision.get(key))
        merged[key] = _dedupe(native_list + vision_list)

    for key in ["all_visible_text", "main_text", "metrics", "labels", "supplement", "missing_risk"]:
        merge_list(key)

    native_page_type = str(native.get("page_type") or "").strip()
    vision_page_type = str(vision.get("page_type") or "").strip()
    if (
        vision_page_type
        and vision_page_type not in {"fallback"}
        and (
            native_page_type in {"fallback", "", "image-text", "chapter"}
            or vision_page_type == native_page_type
        )
    ):
        merged["page_type"] = vision_page_type
    if vision.get("title") and (not str(native.get("title") or "").strip() or len(str(vision.get("title") or "").strip()) > len(str(native.get("title") or "").strip())):
        merged["title"] = vision["title"]
    if vision.get("hierarchy") and _hierarchy_score(vision.get("hierarchy")) >= _hierarchy_score(native.get("hierarchy")):
        merged["hierarchy"] = vision["hierarchy"]
    if vision.get("layout_intent"):
        merged["layout_intent"] = {**(native.get("layout_intent") or {}), **vision["layout_intent"]}
    if vision.get("connectors") and _connector_score(vision.get("connectors")) >= _connector_score(native.get("connectors")):
        merged["connectors"] = vision["connectors"]
    if vision.get("structured_payload"):
        merged["structured_payload"] = _merge_structured_payload(
            native.get("structured_payload") or {},
            vision["structured_payload"],
            page_type=str(merged.get("page_type") or native.get("page_type") or ""),
        )

    vision_conf = vision.get("confidence")
    try:
        vision_conf = float(vision_conf)
    except Exception:  # noqa: BLE001
        vision_conf = None
    native_conf = float(native.get("confidence") or 0.0)
    merged["confidence"] = round(max(native_conf, vision_conf or 0.0), 3)
    vision_reason = str(vision.get("reason") or "").strip()
    base_reason = str(native.get("reason") or "").strip()
    merged["reason"] = f"{base_reason} Vision enhancement: {vision_reason}".strip()
    merged["supplement"] = _dedupe(_ensure_list(merged.get("supplement")) + ["enhanced with host vision on the primary slide image"])
    merged["missing_risk"] = [
        str(risk).strip()
        for risk in _ensure_list(merged.get("missing_risk"))
        if str(risk).strip() and "image-heavy" not in str(risk)
    ]
    return merged


def merge_small_image_ocr(native: dict[str, Any], ocr_payloads: list[dict[str, Any]]) -> dict[str, Any]:
    merged = dict(native)
    ocr_lines: list[str] = []
    ocr_labels: list[str] = []
    for payload in ocr_payloads:
        ocr_lines.extend(payload.get("visible_lines") or [])
        ocr_labels.extend(payload.get("short_labels") or [])
    merged["all_visible_text"] = _dedupe((merged.get("all_visible_text") or []) + ocr_lines)
    merged["labels"] = _dedupe((merged.get("labels") or []) + ocr_labels)
    if ocr_lines:
        merged["supplement"] = _dedupe((merged.get("supplement") or []) + ["supplemented visible text from embedded images"])
    return merged


def _dedupe(items: list[Any]) -> list[Any]:
    seen = set()
    result = []
    for item in items:
        marker = json.dumps(item, ensure_ascii=False, sort_keys=True) if isinstance(item, (dict, list)) else str(item)
        if not marker or marker in seen:
            continue
        seen.add(marker)
        result.append(item)
    return result


def _ensure_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]
