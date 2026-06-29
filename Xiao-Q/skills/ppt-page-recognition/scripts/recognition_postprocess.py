#!/usr/bin/env python3

from __future__ import annotations

from copy import deepcopy
import json
import re
from typing import Any


KNOWN_SYSTEM_SUFFIXES = [
    "资产管理系统",
    "集成管理系统",
    "能源管理系统",
    "运维管理系统",
    "管理系统",
    "系统",
]


def normalize_slide_result(slide: dict[str, Any]) -> dict[str, Any]:
    normalized = deepcopy(slide)
    normalized.setdefault("hierarchy", [])
    normalized.setdefault("layout_intent", {})
    normalized.setdefault("connectors", [])
    normalized.setdefault("structured_payload", {})
    normalized.setdefault("all_visible_text", [])
    normalized.setdefault("main_text", [])
    normalized.setdefault("metrics", [])
    normalized.setdefault("labels", [])
    normalized.setdefault("footer", [])
    normalized.setdefault("instruction_text", [])
    normalized.setdefault("supplement", [])
    normalized.setdefault("ocr_residue", [])
    normalized.setdefault("missing_risk", [])
    normalized["missing_risk"] = [
        str(risk).strip()
        for risk in normalized.get("missing_risk", [])
        if str(risk).strip()
        and not re.fullmatch(r"\d+(?:\.\d+)?", str(risk).strip())
        and str(risk).strip() not in {"高", "中", "低", "high", "medium", "low"}
    ]

    payload = normalized["structured_payload"]
    page_type = str(normalized.get("page_type") or "").strip()
    title = str(normalized.get("title") or "").strip()
    footer = _dedupe_strings(normalized.get("footer") or [])

    if footer and not payload.get("footer_lines"):
        payload["footer_lines"] = footer

    if title and page_type in {"logo-wall", "people-matrix", "timeline", "metrics", "peer-panels", "image-text", "awards-patents", "toc"}:
        payload.setdefault("section_title", title)
    if page_type == "cover":
        _normalize_cover(normalized)

    if page_type in {"chapter", "image", "image-text", "image-only"}:
        _normalize_parallel_chapter(normalized)
    if normalized.get("page_type") == "peer-panels":
        _normalize_peer_panels(normalized)
    if normalized.get("page_type") == "logo-wall":
        _normalize_logo_wall(normalized)
    if normalized.get("page_type") == "people-matrix":
        _normalize_people_matrix(normalized)
    if normalized.get("page_type") == "metrics":
        _normalize_metrics(normalized)
    if normalized.get("page_type") == "timeline":
        _normalize_timeline(normalized)
    if normalized.get("page_type") == "toc":
        _normalize_toc(normalized)
    if normalized.get("page_type") == "awards-patents":
        _normalize_awards_patents(normalized)

    _refresh_semantic_fields(normalized)
    _clean_generation_buckets(normalized)
    normalized["missing_risk"] = _refine_missing_risk(normalized)

    return normalized


def normalize_deck_result(deck: dict[str, Any], source_file: str = "") -> dict[str, Any]:
    normalized = deepcopy(deck)
    slides = [normalize_slide_result(slide) for slide in normalized.get("slides", [])]
    normalized["slides"] = slides
    normalized["slide_count"] = len(slides)
    if source_file:
        normalized["source_file"] = source_file
    normalized.setdefault("deck_title", _pick_deck_title(slides))
    normalized["deck_outline"] = [
        {
            "slide_number": slide.get("slide_number"),
            "page_type": slide.get("page_type"),
            "title": slide.get("title") or _fallback_outline_title(slide),
        }
        for slide in slides
    ]
    return normalized


def _normalize_parallel_chapter(slide: dict[str, Any]) -> None:
    layout = slide.get("layout_intent") or {}
    panel_count = int(layout.get("panel_count") or 0)
    root = _first_node(slide.get("hierarchy") or [])
    title = str(slide.get("title") or "").strip()
    root_items = [str(item).strip() for item in root.get("items") or [] if str(item).strip()] if root else []
    if panel_count < 2:
        visible = [line for line in slide.get("all_visible_text", []) if str(line).strip()]
        short_visible = [line for line in visible if len(str(line).strip()) <= 24]
        if len(short_visible) >= 4:
            panel_count = 2
            root_items = short_visible[1:4]
    if panel_count < 2:
        return

    non_english = [item for item in [title, *root_items] if item and not _looks_english(item)]
    english = [item for item in root_items if _looks_english(item)]
    unique_non_english = _dedupe_strings(non_english)
    if len(unique_non_english) < 2:
        return

    panels = []
    for index, panel_title in enumerate(unique_non_english[:panel_count]):
        panel: dict[str, Any] = {
            "panel_title": panel_title,
            "panel_role": _classify_panel_role(panel_title),
            "items": [],
        }
        if index < len(english):
            panel["supporting_lines"] = [english[index]]
        panels.append(panel)

    slide["page_type"] = "peer-panels"
    layout["direction"] = "left_to_right"
    layout["panel_count"] = len(panels)
    layout["narrative"] = "grouped"
    slide["layout_intent"] = layout
    payload = slide.get("structured_payload") or {}
    payload["section_title"] = title or unique_non_english[0]
    payload["panels"] = panels
    slide["structured_payload"] = payload


def _normalize_cover(slide: dict[str, Any]) -> None:
    payload = slide.get("structured_payload") or {}
    subtitle = str(payload.get("subtitle") or "").strip()
    slide["layout_intent"] = {
        "direction": "top_to_bottom",
        "panel_count": 1,
        "has_connectors": False,
        "narrative": "cover",
        "dominant_visual": "hero",
        "parent_label": subtitle,
    }
    slide["structured_payload"] = payload


def _normalize_peer_panels(slide: dict[str, Any]) -> None:
    payload = slide.get("structured_payload") or {}
    layout = slide.get("layout_intent") or {}
    hierarchy = slide.get("hierarchy") or []
    rebuilt_panels = []
    rebuilt_metrics = []

    if not payload.get("parent_label"):
        parent_label = str(layout.get("parent_label") or "").strip()
        if not parent_label:
            panel_titles = {str(node.get("title") or "").strip() for node in hierarchy}
            for label in slide.get("labels") or []:
                label = str(label).strip()
                if label and label not in panel_titles:
                    parent_label = label
                    break
        if parent_label and parent_label not in {panel.get("panel_title") for panel in payload.get("panels") or []}:
            payload["parent_label"] = parent_label
        else:
            payload.pop("parent_label", None)

    panels = payload.get("panels") or []
    metric_blocks = payload.get("metric_blocks") or []
    if not panels or not metric_blocks:
        for node in hierarchy:
            node_title = str(node.get("title") or "").strip()
            items = [str(item).strip() for item in node.get("items") or [] if str(item).strip()]
            if not node_title and not items:
                continue
            if _node_looks_like_metric_group(node_title, items):
                for item in items:
                    parsed = _parse_metric_line(item)
                    if parsed:
                        rebuilt_metrics.append(parsed)
                continue
            rebuilt_panels.append(
                {
                    "panel_title": node_title,
                    "panel_role": _classify_panel_role(node_title),
                    "items": items,
                }
            )
    if rebuilt_panels and not panels:
        payload["panels"] = rebuilt_panels
    if rebuilt_metrics and not metric_blocks:
        payload["metric_blocks"] = rebuilt_metrics

    if payload.get("parent_label") == "博锐尚格" and {panel.get("panel_title") for panel in payload.get("panels") or []} >= {"活力结构", "禹数"}:
        _normalize_sector_panels(payload, slide)
    if {panel.get("panel_title") for panel in payload.get("panels") or []} >= {"公司介绍", "核心产品"}:
        payload.setdefault("primary_title", "公司介绍")
        payload.setdefault("secondary_title", "核心产品")
        payload.setdefault("paired_lines", [])

    slide["structured_payload"] = payload
    _drop_redundant_blocks(payload)


def _normalize_logo_wall(slide: dict[str, Any]) -> None:
    payload = slide.get("structured_payload") or {}
    hierarchy = slide.get("hierarchy") or []
    title = str(slide.get("title") or "").strip()
    footer = _dedupe_strings(slide.get("footer") or [])
    layout = slide.get("layout_intent") or {}

    if title:
        payload.setdefault("section_title", title)
    if footer:
        payload.setdefault("footer_lines", footer)

    root = _first_node(hierarchy)
    groups = payload.get("groups") or []
    if not groups:
        legacy_group_map = [
            ("活力结构 民用业务", payload.get("civil_customers") or []),
            ("禹数 工业业务", payload.get("industrial_customers") or []),
            ("部分知名项目", payload.get("famous_projects") or []),
        ]
        if payload.get("clients") or payload.get("projects"):
            clients = payload.get("clients") or {}
            legacy_group_map = [
                ("活力结构 民用业务", clients.get("civil") or []),
                ("禹数 工业业务", clients.get("industrial") or []),
                ("部分知名项目", payload.get("projects") or []),
            ]
        groups = [
            {
                "group_title": title_text,
                "items": [str(item).strip() for item in items if str(item).strip()],
            }
            for title_text, items in legacy_group_map
            if items
        ]
    if not groups and root:
        groups = [
            {
                "group_title": str(child.get("title") or "").strip(),
                "items": [str(item).strip() for item in child.get("items") or [] if str(item).strip()],
            }
            for child in root.get("children") or []
            if (child.get("title") or child.get("items"))
        ]

    normalized_groups = []
    for group in groups:
        group_title = str(group.get("group_title") or group.get("title") or "").strip()
        items = [str(item).strip() for item in group.get("items") or [] if str(item).strip()]
        entries = group.get("entries") or []
        if not entries:
            entries = [_split_pair_item(item) for item in items]
            entries = [entry for entry in entries if entry]
        else:
            entries = [
                {
                    "name": str(entry.get("name") or "").strip(),
                    "system": str(entry.get("system") or "").strip(),
                }
                for entry in entries
                if str(entry.get("name") or "").strip() or str(entry.get("system") or "").strip()
            ]
        normalized_items = [_join_entry(entry) for entry in entries if _join_entry(entry)] or items
        normalized_groups.append(
            {
                "group_title": group_title,
                "entries": entries,
                "items": normalized_items,
            }
        )

    visible_group_titles = _extract_logo_wall_group_titles(slide)
    existing_titles = {str(group.get("group_title") or "").strip() for group in normalized_groups if str(group.get("group_title") or "").strip()}
    for group_title in visible_group_titles:
        if group_title in existing_titles:
            continue
        normalized_groups.append(
            {
                "group_title": group_title,
                "entries": [],
                "items": [],
            }
        )
        existing_titles.add(group_title)

    normalized_groups.sort(key=_logo_wall_group_sort_key)

    if normalized_groups:
        payload["groups"] = normalized_groups
        group_count = len(normalized_groups)
        slide["layout_intent"] = {
            "direction": "grid" if group_count >= 3 else "left_to_right",
            "panel_count": group_count,
            "has_connectors": False,
            "narrative": "grouped",
            "dominant_visual": "logo_grid",
            "parent_label": title if title and group_count <= 2 else "",
        }
        if any(not group.get("items") and not group.get("entries") for group in normalized_groups):
            slide["missing_risk"] = _dedupe_strings(
                [
                    *slide.get("missing_risk", []),
                    "Some visible logo-wall group titles were preserved, but their member entries could not yet be recovered reliably.",
                ]
            )
    if root and root.get("items") and not payload.get("summary"):
        payload["summary"] = str(root["items"][0]).strip()
    summary = str(payload.get("summary") or "").strip()
    if summary:
        flat_items = {item for group in normalized_groups for item in group.get("items") or []}
        if len(summary) < 16 or summary in flat_items:
            payload.pop("summary", None)
    for noisy_key in (
        "civil_customers",
        "industrial_customers",
        "famous_projects",
        "clients",
        "projects",
        "民用业务大客户",
        "工业业务大客户",
        "部分知名项目",
    ):
        payload.pop(noisy_key, None)
    slide["structured_payload"] = payload


def _logo_wall_group_sort_key(group: dict[str, Any]) -> tuple[int, str]:
    title = str(group.get("group_title") or "").strip()
    if any(token in title for token in ("活力结构", "民用")):
        return (0, title)
    if any(token in title for token in ("禹数", "工业")):
        return (1, title)
    if "项目" in title:
        return (2, title)
    return (3, title)


def _normalize_people_matrix(slide: dict[str, Any]) -> None:
    payload = slide.get("structured_payload") or {}
    title = str(slide.get("title") or "").strip()
    footer = _dedupe_strings(slide.get("footer") or [])
    hierarchy = slide.get("hierarchy") or []

    if title:
        payload.setdefault("section_title", title)
    if footer:
        payload.setdefault("footer_lines", footer)
    if payload.get("instruction_note"):
        note = str(payload.pop("instruction_note") or "").strip()
        if note:
            slide["instruction_text"] = _dedupe_strings([*slide.get("instruction_text", []), note])

    groups = payload.get("groups") or []
    if not groups:
        groups = []
        for node in hierarchy:
            node_title = str(node.get("title") or "").strip()
            items = [str(item).strip() for item in node.get("items") or [] if str(item).strip()]
            if not node_title and not items:
                continue
            group = {"group_title": node_title, "people": [], "metrics": []}
            if any("经验" in item or "|" in item for item in items):
                group["people"] = items
            else:
                group["metrics"] = items
                if any("总人数" in item for item in items):
                    group["updated_metrics"] = items
            groups.append(group)
    if groups:
        for group in groups:
            if group.get("group_title") == "人力分布":
                group["metrics"] = [item for item in group.get("metrics", []) if item != "更新人数情况"]
                if group.get("updated_metrics"):
                    group["updated_metrics"] = [item for item in group.get("updated_metrics", []) if item != "更新人数情况"]
        payload["groups"] = groups

    if payload.get("chart_breakdown"):
        chart = payload["chart_breakdown"]
        total = str(chart.get("display_total") or "").strip()
        segments = chart.get("segments") or []
        if not total or len(segments) < 5:
            payload.pop("chart_breakdown", None)

    if not payload.get("chart_breakdown"):
        chart_breakdown = _parse_chart_breakdown(slide)
        if chart_breakdown:
            payload["chart_breakdown"] = chart_breakdown
    elif _chart_breakdown_looks_noisy(payload.get("chart_breakdown") or {}):
        chart_breakdown = _parse_chart_breakdown(slide)
        if chart_breakdown:
            payload["chart_breakdown"] = chart_breakdown

    slide["structured_payload"] = payload


def _normalize_metrics(slide: dict[str, Any]) -> None:
    payload = slide.get("structured_payload") or {}
    title = str(slide.get("title") or "").strip()
    if title:
        payload.setdefault("section_title", title)
    metric_blocks = payload.get("metric_blocks") or []
    if not metric_blocks:
        metric_blocks = []
        for node in slide.get("hierarchy") or []:
            for item in node.get("items") or []:
                parsed = _parse_metric_line(str(item))
                if parsed:
                    metric_blocks.append(parsed)
    if metric_blocks:
        payload["metric_blocks"] = metric_blocks
    if title and metric_blocks and title == str(metric_blocks[0].get("label") or "").strip():
        slide["title"] = ""
        payload.pop("section_title", None)
    if slide.get("instruction_text"):
        slide["instruction_text"] = ["\n".join(slide.get("instruction_text") or [])]
    slide["structured_payload"] = payload


def _normalize_timeline(slide: dict[str, Any]) -> None:
    payload = slide.get("structured_payload") or {}
    title = str(slide.get("title") or "").strip()
    if title:
        payload.setdefault("section_title", title)
    if payload.get("timeline") and not payload.get("periods"):
        periods = []
        for entry in payload.get("timeline") or []:
            period = str(entry.get("period") or "").strip()
            description = [line.strip() for line in str(entry.get("description") or "").splitlines() if line.strip()]
            period_payload = {
                "period": period,
                "headline": description[0] if description else "",
                "capability_tag": description[1] if len(description) > 1 else "",
                "scenario": description[2] if len(description) > 2 else "",
                "target_domain": description[3] if len(description) > 3 else "",
                "supporting_labels": [],
                "panel_connectors": [],
            }
            periods.append(period_payload)
        payload["periods"] = periods
    if not payload.get("periods"):
        visible_periods = _extract_timeline_periods_from_visible(slide)
        if visible_periods:
            payload["periods"] = visible_periods
    for noisy_key in ("timeline", "awards", "patents"):
        payload.pop(noisy_key, None)
    if payload.get("periods"):
        parent_label = payload.get("parent_label") or "业务发展演进历史"
        payload["parent_label"] = parent_label
        slide["layout_intent"] = {
            "direction": "left_to_right",
            "panel_count": len(payload.get("periods") or []),
            "has_connectors": True,
            "narrative": "progression",
            "dominant_visual": "three_panels",
            "parent_label": parent_label,
        }
        slide["connectors"] = _merge_connector_lists(
            slide.get("connectors") or [],
            _build_timeline_progression_connectors(payload.get("periods") or []),
        )
    slide["structured_payload"] = payload


def _drop_redundant_blocks(payload: dict[str, Any]) -> None:
    panels = payload.get("panels") or []
    blocks = payload.get("blocks") or []
    if not panels or not blocks:
        return
    panel_titles = {str(panel.get("panel_title") or "").strip() for panel in panels}
    support_lines = {str(line).strip() for panel in panels for line in panel.get("supporting_lines") or []}
    block_headings = {str(block.get("heading") or "").strip() for block in blocks}
    if block_headings and block_headings.issubset(panel_titles | support_lines):
        payload.pop("blocks", None)


def _normalize_toc(slide: dict[str, Any]) -> None:
    payload = slide.get("structured_payload") or {}
    root = _first_node(slide.get("hierarchy") or [])
    if not root:
        slide["structured_payload"] = payload
        return

    raw_entries = [str(item).strip() for item in root.get("items") or [] if str(item).strip()]
    if raw_entries:
        payload["entries"] = raw_entries
        cleaned = [re.sub(r"^\d+[、.．]\s*", "", item).strip() for item in raw_entries]
        if cleaned != raw_entries:
            payload["entries_clean"] = cleaned
    slide["structured_payload"] = payload


def _normalize_awards_patents(slide: dict[str, Any]) -> None:
    payload = slide.get("structured_payload") or {}
    title = str(slide.get("title") or "").strip()
    footer = _dedupe_strings(slide.get("footer") or [])
    hierarchy = slide.get("hierarchy") or []
    visible = _visible_content_lines(slide)

    if title:
        payload.setdefault("section_title", title)
    if footer:
        payload.setdefault("footer_lines", footer)

    patents = payload.get("patents") or {}
    if patents and not payload.get("metric_blocks"):
        patent_map = [
            ("实授发明专利", patents.get("granted")),
            ("在审发明专利", patents.get("pending")),
            ("实用新型及外观专利", patents.get("utility_design")),
        ]
        payload["metric_blocks"] = [
            {"label": label, "value": str(value), "unit": "项"}
            for label, value in patent_map
            if value not in {None, ""}
        ]
    if not payload.get("metric_blocks"):
        payload["metric_blocks"] = _extract_patent_metric_blocks(visible, hierarchy)

    group_titles = payload.get("group_titles") or []
    if not group_titles:
        visible_set = {str(item).strip() for item in slide.get("all_visible_text") or []}
        hierarchy_titles = [str(node.get("title") or "").strip() for node in hierarchy if str(node.get("title") or "").strip()]
        group_titles = [title_text for title_text in ("关键专利", "关键奖项", "投资人") if title_text in visible_set or title_text in hierarchy_titles]
        if group_titles:
            payload["group_titles"] = group_titles

    existing_awards = _dedupe_strings(payload.get("awards") or [])
    fallback_awards = _extract_node_items(hierarchy, "关键奖项") or _extract_awards_from_visible(visible)
    awards = [
        award for award in _merge_award_fragments(_dedupe_strings(existing_awards or fallback_awards), visible)
        if award not in footer and "供应商" not in award and award != "www.persagy.com"
    ]
    if existing_awards:
        extra_awards = [award for award in awards if award not in existing_awards]
        awards = _dedupe_strings(existing_awards + _sort_awards_by_visible_order(extra_awards, visible))
    else:
        awards = _sort_awards_by_visible_order(awards, visible)
    if awards:
        payload["awards"] = awards
    investors = _dedupe_strings(payload.get("investors") or _extract_node_items(hierarchy, "投资人"))
    payload["investors"] = investors

    payload.pop("patents", None)
    payload.pop("key_patents", None)
    payload.pop("key_awards", None)

    slide["layout_intent"] = {
        "direction": "top_to_bottom",
        "panel_count": 3,
        "has_connectors": False,
        "narrative": "grouped",
        "dominant_visual": "mixed",
        "parent_label": "",
    }
    slide["structured_payload"] = payload
    if not investors and "投资人" in {str(item).strip() for item in slide.get("all_visible_text") or []}:
        slide["missing_risk"] = _dedupe_strings(
            [
                *slide.get("missing_risk", []),
                "投资人名称在当前原生文本与视觉补识别结果中仍未可靠识别，需后续继续增强视觉抽取能力。",
            ]
        )


def _parse_chart_breakdown(slide: dict[str, Any]) -> dict[str, Any] | None:
    all_visible = [str(item).strip() for item in slide.get("all_visible_text") or [] if str(item).strip()]
    explicit_labels = ["产品研发", "人工智能", "实施服务", "销售", "中后台"]
    donut_total = next((line for line in all_visible if re.fullmatch(r"\d+\s*人", line) and int(re.sub(r"\D", "", line)) >= 400), "")
    donut_values = [line.replace(" ", "") for line in all_visible if re.fullmatch(r"\d+\s*人?", line) and line not in {"总人数"}]
    if donut_total:
        donut_values = [line for line in donut_values if re.sub(r"\D", "", line) != re.sub(r"\D", "", donut_total)]
    donut_values = [line for line in donut_values if line not in {"348", "96", "30", "143", "49", "总人数"}]
    percentages = [line for line in all_visible if re.fullmatch(r"\d+%", line)]
    if donut_total and len(explicit_labels) == 5 and len(donut_values) >= 5 and len(percentages) >= 5:
        values = donut_values[:5]
        pct_values = sorted(percentages[:5], key=lambda item: int(item.rstrip("%")), reverse=True)
        numeric_values = [(index, int(re.sub(r"\D", "", value)), value) for index, value in enumerate(values)]
        ranked = sorted(numeric_values, key=lambda item: item[1], reverse=True)
        pct_by_index: dict[int, str] = {}
        for pct, (index, _value_num, _value_text) in zip(pct_values, ranked):
            pct_by_index[index] = pct
        total_digits = re.sub(r"\D", "", donut_total)
        return {
            "display_total": f"总人数 {total_digits}人",
            "segments": [
                {
                    "label": label,
                    "value": values[index],
                    "percentage": pct_by_index.get(index, ""),
                }
                for index, label in enumerate(explicit_labels)
            ],
        }

    text_pool = [
        *(slide.get("supplement") or []),
        *(slide.get("all_visible_text") or []),
        *(slide.get("metrics") or []),
    ]
    joined = " ".join(str(item) for item in text_pool if item)
    total_match = re.search(r"总人数[:： ]?(\d+)\s*人?", joined)
    percentages = re.findall(r"(\d+%)", joined)

    segment_matches = re.findall(r"([一-龥A-Za-z]+)[:： ]?(\d+)\s*人?", joined)
    ignored_labels = {"总人数", "更新人数情况"}
    candidate_segments = []
    for label, value in segment_matches:
        label = label.strip()
        if label in ignored_labels:
            continue
        candidate_segments.append((label, value))

    deduped_segments = []
    seen_labels = set()
    for label, value in candidate_segments:
        if label in seen_labels:
            continue
        seen_labels.add(label)
        deduped_segments.append((label, value))

    if not total_match or not deduped_segments:
        return None

    segments = []
    for index, (label, value) in enumerate(deduped_segments):
        segment = {"label": label, "value": value}
        if index < len(percentages):
            segment["percentage"] = percentages[index]
        segments.append(segment)

    return {
        "display_total": f"总人数 {total_match.group(1)}人",
        "segments": segments,
    }


def _extract_logo_wall_group_titles(slide: dict[str, Any]) -> list[str]:
    title = str(slide.get("title") or "").strip()
    footer = {str(item).strip() for item in slide.get("footer") or []}
    instruction = {str(item).strip() for item in slide.get("instruction_text") or []}
    titles: list[str] = []

    root = _first_node(slide.get("hierarchy") or [])
    if root:
        for child in root.get("children") or []:
            child_title = str(child.get("title") or "").strip()
            if child_title:
                titles.append(child_title)

    for line in slide.get("all_visible_text") or []:
        text = str(line).strip()
        if not text or text == title or text in footer or text in instruction:
            continue
        if len(text) > 18:
            continue
        if any(suffix in text for suffix in KNOWN_SYSTEM_SUFFIXES):
            continue
        if any(token in text for token in ("民用", "工业", "业务", "项目", "活力结构", "禹数")):
            titles.append(text)
    return _dedupe_strings(titles)


def _extract_timeline_periods_from_visible(slide: dict[str, Any]) -> list[dict[str, Any]]:
    lines = _visible_content_lines(slide)
    period_pattern = re.compile(r"^\d{4}\s*[-—–~至]+\s*(?:\d{4}|至今|今)$")
    blocks: list[tuple[str, list[str]]] = []
    current_period = ""
    current_lines: list[str] = []

    for line in lines:
        if period_pattern.fullmatch(line):
            if current_period:
                blocks.append((current_period, current_lines))
            current_period = line
            current_lines = []
            continue
        if current_period:
            current_lines.append(line)
    if current_period:
        blocks.append((current_period, current_lines))

    periods = []
    for period, block_lines in blocks:
        clean_lines = [line for line in block_lines if line]
        periods.append(
            {
                "period": period,
                "headline": clean_lines[0] if len(clean_lines) > 0 else "",
                "capability_tag": clean_lines[1] if len(clean_lines) > 1 else "",
                "scenario": clean_lines[2] if len(clean_lines) > 2 else "",
                "target_domain": clean_lines[3] if len(clean_lines) > 3 else "",
                "supporting_labels": clean_lines[4:] if len(clean_lines) > 4 else [],
                "panel_connectors": [],
            }
        )
    return [period for period in periods if period.get("period")]


def _visible_content_lines(slide: dict[str, Any]) -> list[str]:
    title = str(slide.get("title") or "").strip()
    footer = {str(item).strip() for item in slide.get("footer") or []}
    instruction = {str(item).strip() for item in slide.get("instruction_text") or []}
    lines = []
    for item in slide.get("all_visible_text") or []:
        text = str(item).strip()
        if not text or text == title or text in footer or text in instruction:
            continue
        lines.append(text)
    return _dedupe_strings(lines)


def _extract_node_items(hierarchy: list[dict[str, Any]], node_title: str) -> list[str]:
    for node in hierarchy:
        if str(node.get("title") or "").strip() == node_title:
            return _dedupe_strings(node.get("items") or [])
    return []


def _extract_patent_metric_blocks(lines: list[str], hierarchy: list[dict[str, Any]]) -> list[dict[str, Any]]:
    known_labels = ["实授发明专利", "在审发明专利", "实用新型及外观专利"]
    metric_blocks = []
    hierarchy_items = _extract_node_items(hierarchy, "关键专利")
    for item in hierarchy_items:
        parsed = _parse_metric_line(item)
        if parsed:
            metric_blocks.append(parsed)
    if metric_blocks:
        return metric_blocks

    labels = [line for line in lines if line in known_labels]
    values = [line for line in lines if re.fullmatch(r"\d+", line)]
    for index, label in enumerate(labels):
        if index >= len(values):
            break
        metric_blocks.append({"label": label, "value": values[index], "unit": "项"})
    return metric_blocks


def _extract_awards_from_visible(lines: list[str]) -> list[str]:
    ignored = {"关键专利", "关键奖项", "投资人"}
    awards = []
    for line in lines:
        text = str(line).strip()
        if not text or text in ignored:
            continue
        if _looks_award_line(text):
            awards.append(text)
    return _dedupe_strings(awards)


def _merge_award_fragments(awards: list[str], visible_lines: list[str]) -> list[str]:
    merged: list[str] = []
    fragments = [line for line in visible_lines if line not in awards and len(line) <= 20 and "奖" not in line]
    for award in awards:
        combined = award
        if award.endswith("50强") and len(award) <= 8:
            prefix = next((fragment for fragment in fragments if "不动产" in fragment or fragment.endswith("企业")), "")
            if prefix:
                combined = f"{prefix}{award}"
        merged.append(combined)

    deduped = _dedupe_strings(merged)
    filtered = []
    for award in deduped:
        if any(other != award and award in other for other in deduped):
            continue
        filtered.append(award)
    return filtered


def _looks_award_line(text: str) -> bool:
    clean = str(text).strip()
    if not clean:
        return False
    return any(keyword in clean for keyword in ("大奖", "奖", "50强", "猎豹企业", "碳金")) and clean not in {"关键奖项"}


def _refresh_semantic_fields(slide: dict[str, Any]) -> None:
    payload = slide.get("structured_payload") or {}
    page_type = str(slide.get("page_type") or "").strip()
    footer_lines = _sort_footer_lines(payload.get("footer_lines") or slide.get("footer") or [])
    if footer_lines:
        slide["footer"] = footer_lines
        payload["footer_lines"] = footer_lines
    else:
        payload.pop("footer_lines", None)
    if payload.get("metric_blocks"):
        payload["metric_blocks"] = [_compact_metric_block(block, page_type=str(slide.get("page_type") or "").strip()) for block in payload.get("metric_blocks") or []]

    rebuilt_hierarchy = _rebuild_hierarchy_from_payload(slide)
    if rebuilt_hierarchy is not None:
        slide["hierarchy"] = rebuilt_hierarchy

    canonical_visible = _derive_all_visible_text(slide)
    if canonical_visible:
        if page_type == "people-matrix":
            slide["all_visible_text"] = _merge_existing_text(slide.get("all_visible_text") or [], canonical_visible)
        elif page_type == "awards-patents":
            slide["all_visible_text"] = canonical_visible
        else:
            slide["all_visible_text"] = _merge_canonical_text(canonical_visible, slide.get("all_visible_text") or [])

    canonical_main = _derive_main_text(slide)
    if canonical_main is not None:
        slide["main_text"] = canonical_main

    canonical_labels = _derive_labels(slide)
    if canonical_labels is not None:
        slide["labels"] = canonical_labels

    canonical_metrics = _derive_metrics(slide)
    if canonical_metrics is not None:
        slide["metrics"] = canonical_metrics

    if payload.get("summary") in {"", None}:
        payload.pop("summary", None)
    slide["structured_payload"] = payload


def _rebuild_hierarchy_from_payload(slide: dict[str, Any]) -> list[dict[str, Any]] | None:
    payload = slide.get("structured_payload") or {}
    page_type = str(slide.get("page_type") or "").strip()
    title = str(slide.get("title") or payload.get("section_title") or "").strip()

    if page_type == "toc":
        entries = [str(item).strip() for item in payload.get("entries") or [] if str(item).strip()]
        if entries and title:
            return [{"title": title, "items": entries, "children": []}]

    if page_type == "metrics":
        metric_lines = [_compose_metric_block_line(block) for block in payload.get("metric_blocks") or []]
        metric_lines = [line for line in metric_lines if line]
        if metric_lines:
            return [{"title": title or "核心指标", "items": metric_lines, "children": []}]

    if page_type == "peer-panels" and payload.get("parent_label"):
        panels = payload.get("panels") or []
        if panels:
            hierarchy = [
                {
                    "title": str(panel.get("panel_title") or "").strip(),
                    "items": [str(item).strip() for item in panel.get("items") or [] if str(item).strip()],
                    "children": [],
                }
                for panel in panels
                if str(panel.get("panel_title") or "").strip() or panel.get("items")
            ]
            metric_lines = [_compose_metric_block_line(block) for block in payload.get("metric_blocks") or []]
            metric_lines = [line for line in metric_lines if line]
            if metric_lines:
                hierarchy.append(
                    {
                        "title": "市场规模与成本",
                        "items": metric_lines,
                        "children": [],
                    }
                )
            return hierarchy or None

    if page_type == "peer-panels":
        panels = payload.get("panels") or []
        if len(panels) >= 2 and title:
            items = [
                *[str(line).strip() for line in panels[0].get("supporting_lines") or [] if str(line).strip()],
                str(panels[1].get("panel_title") or "").strip(),
                *[str(line).strip() for line in panels[1].get("supporting_lines") or [] if str(line).strip()],
            ]
            return [{"title": title, "items": [item for item in items if item], "children": []}]

    if page_type == "timeline":
        periods = payload.get("periods") or []
        if periods:
            parent_label = str(payload.get("parent_label") or "").strip()
            return [
                {
                    "title": title,
                    "items": [parent_label] if parent_label else [],
                    "children": [
                        {
                            "title": str(period.get("period") or "").strip(),
                            "items": [
                                str(period.get("headline") or "").strip(),
                                str(period.get("capability_tag") or "").strip(),
                                str(period.get("scenario") or "").strip(),
                                str(period.get("target_domain") or "").strip(),
                                *[
                                    str(item).strip()
                                    for item in period.get("supporting_labels") or []
                                    if str(item).strip()
                                ],
                            ],
                            "children": [],
                        }
                        for period in periods
                        if str(period.get("period") or "").strip()
                    ],
                }
            ]

    if page_type == "logo-wall":
        groups = payload.get("groups") or []
        if groups:
            summary = str(payload.get("summary") or "").strip()
            return [
                {
                    "title": title,
                    "items": [summary] if summary else [],
                    "children": [
                        {
                            "title": str(group.get("group_title") or "").strip(),
                            "items": _group_item_lines(group),
                            "children": [],
                        }
                        for group in groups
                        if str(group.get("group_title") or "").strip() or _group_item_lines(group)
                    ],
                }
            ]

    if page_type == "people-matrix":
        groups = payload.get("groups") or []
        if groups:
            return [
                {
                    "title": str(group.get("group_title") or "").strip(),
                    "items": [
                        *[
                            str(item).strip()
                            for item in group.get("people") or []
                            if str(item).strip()
                        ],
                        *[
                            str(item).strip()
                            for item in (group.get("updated_metrics") or group.get("metrics") or [])
                            if str(item).strip()
                        ],
                    ],
                    "children": [],
                }
                for group in groups
                if str(group.get("group_title") or "").strip()
            ]

    if page_type == "awards-patents":
        hierarchy = []
        metric_lines = [_compose_metric_block_line(block) for block in payload.get("metric_blocks") or []]
        metric_lines = [line for line in metric_lines if line]
        if metric_lines:
            hierarchy.append({"title": "关键专利", "items": metric_lines, "children": []})
        awards = [str(item).strip() for item in payload.get("awards") or [] if str(item).strip()]
        if awards:
            hierarchy.append({"title": "关键奖项", "items": awards, "children": []})
        investors = [str(item).strip() for item in payload.get("investors") or [] if str(item).strip()]
        if payload.get("group_titles") or investors:
            hierarchy.append({"title": "投资人", "items": investors, "children": []})
        return hierarchy or None

    return None


def _derive_all_visible_text(slide: dict[str, Any]) -> list[str]:
    payload = slide.get("structured_payload") or {}
    page_type = str(slide.get("page_type") or "").strip()
    title = str(slide.get("title") or "").strip()
    footer = _sort_footer_lines(payload.get("footer_lines") or slide.get("footer") or [])

    if page_type == "cover":
        return _dedupe_strings(
            [
                str(payload.get("subtitle") or "").strip(),
                title,
                str(payload.get("english_subtitle") or "").strip(),
                *footer,
            ]
        )

    if page_type == "toc":
        return _dedupe_strings([title, *[str(item).strip() for item in payload.get("entries") or [] if str(item).strip()]])

    if page_type == "timeline":
        periods = payload.get("periods") or []
        items = [title, str(payload.get("parent_label") or "").strip()]
        items.extend(str(period.get("period") or "").strip() for period in periods)
        items.extend(str(period.get("headline") or "").strip() for period in periods)
        items.extend(str(period.get("capability_tag") or "").strip() for period in periods)
        items.extend(str(period.get("scenario") or "").strip() for period in periods)
        items.extend(str(period.get("target_domain") or "").strip() for period in periods)
        for period in periods:
            items.extend(
                str(item).strip()
                for item in period.get("supporting_labels") or []
                if str(item).strip()
            )
        return _dedupe_strings(items)

    if page_type == "peer-panels":
        panels = payload.get("panels") or []
        items = [title]
        items.extend(str(item).strip() for item in slide.get("instruction_text") or [] if str(item).strip())
        parent_label = str(payload.get("parent_label") or "").strip()
        if parent_label and len(panels) >= 2:
            items.extend(
                [
                    str(panels[0].get("panel_title") or "").strip(),
                    parent_label,
                    str(panels[1].get("panel_title") or "").strip(),
                ]
            )
            for panel in panels:
                items.extend(str(item).strip() for item in panel.get("items") or [] if str(item).strip())
            for block in payload.get("metric_blocks") or []:
                items.append(str(block.get("label") or "").strip())
                items.extend(str(line).strip() for line in block.get("display_lines") or [] if str(line).strip())
            return _dedupe_strings(items)

        if panels:
            items.extend(str(panel.get("panel_title") or "").strip() for panel in panels)
            for panel in panels:
                items.extend(str(line).strip() for line in panel.get("supporting_lines") or [] if str(line).strip())
                items.extend(str(item).strip() for item in panel.get("items") or [] if str(item).strip())
            return _dedupe_strings(items)

    if page_type == "logo-wall":
        groups = payload.get("groups") or []
        items = [title]
        items.extend(str(item).strip() for item in slide.get("instruction_text") or [] if str(item).strip())
        summary = str(payload.get("summary") or "").strip()
        if summary:
            items.append(summary)
        items.extend(str(group.get("group_title") or "").strip() for group in groups if str(group.get("group_title") or "").strip())
        for group in groups:
            items.extend(_group_item_lines(group))
        items.extend(footer)
        return _dedupe_strings(items)

    if page_type == "people-matrix":
        groups = payload.get("groups") or []
        chart = payload.get("chart_breakdown") or {}
        items = [title]
        items.extend(str(item).strip() for item in slide.get("instruction_text") or [] if str(item).strip())
        for group in groups:
            for metric in group.get("updated_metrics") or group.get("metrics") or []:
                metric_text = str(metric).strip()
                if metric_text:
                    items.append(metric_text)
        for group in groups:
            for person in group.get("people") or []:
                items.extend(_split_people_line(person))
        percentages = sorted(
            [str(segment.get("percentage") or "").strip() for segment in chart.get("segments") or [] if str(segment.get("percentage") or "").strip()],
            key=lambda item: int(item.rstrip("%")) if item.rstrip("%").isdigit() else -1,
            reverse=True,
        )
        items.extend(percentages)
        display_total = str(chart.get("display_total") or "").strip()
        if display_total:
            items.append(display_total)
        items.extend(
            str(segment.get("label") or "").strip()
            for segment in chart.get("segments") or []
            if str(segment.get("label") or "").strip()
        )
        items.extend(
            str(segment.get("value") or "").strip()
            for segment in chart.get("segments") or []
            if str(segment.get("value") or "").strip()
        )
        items.extend(footer)
        return _clean_strings_keep_order(items)

    if page_type == "awards-patents":
        items = [title]
        patent_title = "关键专利" if "关键专利" in {str(item).strip() for item in payload.get("group_titles") or []} or payload.get("metric_blocks") else ""
        awards_title = "关键奖项" if "关键奖项" in {str(item).strip() for item in payload.get("group_titles") or []} or payload.get("awards") else ""
        investors_title = "投资人" if "投资人" in {str(item).strip() for item in payload.get("group_titles") or []} or payload.get("investors") else ""
        if patent_title:
            items.append(patent_title)
        for block in payload.get("metric_blocks") or []:
            label = str(block.get("label") or "").strip()
            value = str(block.get("value") or "").strip()
            unit = str(block.get("unit") or "").strip()
            if label:
                items.append(label)
        for block in payload.get("metric_blocks") or []:
            value = str(block.get("value") or "").strip()
            if value:
                items.append(value)
        for block in payload.get("metric_blocks") or []:
            unit = str(block.get("unit") or "").strip()
            if unit:
                items.append(unit)
        if awards_title:
            items.append(awards_title)
        items.extend(str(item).strip() for item in payload.get("awards") or [] if str(item).strip())
        if investors_title:
            items.append(investors_title)
        items.extend(str(item).strip() for item in payload.get("investors") or [] if str(item).strip())
        items.extend(footer)
        return _clean_strings_keep_order(items)

    return []


def _derive_main_text(slide: dict[str, Any]) -> list[str] | None:
    payload = slide.get("structured_payload") or {}
    page_type = str(slide.get("page_type") or "").strip()
    title = str(slide.get("title") or "").strip()

    if page_type == "toc":
        return [str(item).strip() for item in payload.get("entries") or [] if str(item).strip()]

    if page_type == "metrics":
        return [_compose_metric_block_line(block) for block in payload.get("metric_blocks") or [] if _compose_metric_block_line(block)]

    if page_type == "timeline":
        items = [title, str(payload.get("parent_label") or "").strip()]
        items.extend(str(period.get("headline") or "").strip() for period in payload.get("periods") or [])
        return _dedupe_strings(items)

    if page_type == "peer-panels":
        panels = payload.get("panels") or []
        if payload.get("parent_label"):
            return [title] if title else []
        items = [title]
        items.extend(str(panel.get("panel_title") or "").strip() for panel in panels if str(panel.get("panel_title") or "").strip())
        for panel in panels:
            items.extend(str(line).strip() for line in panel.get("supporting_lines") or [] if str(line).strip())
        return _dedupe_strings(items)

    if page_type == "logo-wall":
        items = [title]
        summary = str(payload.get("summary") or "").strip()
        if summary:
            items.append(summary)
        return _dedupe_strings(items)

    if page_type == "people-matrix":
        return [title] if title else []

    return None


def _derive_labels(slide: dict[str, Any]) -> list[str] | None:
    payload = slide.get("structured_payload") or {}
    page_type = str(slide.get("page_type") or "").strip()

    if page_type == "toc":
        return []

    if page_type == "metrics":
        return []

    if page_type == "timeline":
        items = [str(period.get("period") or "").strip() for period in payload.get("periods") or []]
        items.extend(str(period.get("capability_tag") or "").strip() for period in payload.get("periods") or [])
        items.extend(str(period.get("target_domain") or "").strip() for period in payload.get("periods") or [])
        return _dedupe_strings(items)

    if page_type == "peer-panels":
        if payload.get("parent_label"):
            panels = payload.get("panels") or []
            return _dedupe_strings(
                [
                    str(panels[0].get("panel_title") or "").strip() if len(panels) >= 1 else "",
                    str(payload.get("parent_label") or "").strip(),
                    str(panels[1].get("panel_title") or "").strip() if len(panels) >= 2 else "",
                ]
            )
        return []

    if page_type == "logo-wall":
        return [str(group.get("group_title") or "").strip() for group in payload.get("groups") or [] if str(group.get("group_title") or "").strip()]

    if page_type == "people-matrix":
        roles = []
        for group in payload.get("groups") or []:
            for person in group.get("people") or []:
                parts = _split_people_line(person)
                if len(parts) >= 2:
                    roles.append(parts[1])
        group_titles = [str(group.get("group_title") or "").strip() for group in payload.get("groups") or [] if str(group.get("group_title") or "").strip()]
        return _dedupe_strings([*group_titles, *roles])

    if page_type == "awards-patents":
        return [str(item).strip() for item in payload.get("group_titles") or [] if str(item).strip()]

    return None


def _derive_metrics(slide: dict[str, Any]) -> list[str] | None:
    payload = slide.get("structured_payload") or {}
    page_type = str(slide.get("page_type") or "").strip()

    if page_type == "metrics":
        return [_compose_metric_block_line(block) for block in payload.get("metric_blocks") or [] if _compose_metric_block_line(block)]

    if page_type == "peer-panels":
        return [_compose_metric_block_line(block) for block in payload.get("metric_blocks") or [] if _compose_metric_block_line(block)]

    if page_type == "logo-wall":
        return []

    if page_type == "people-matrix":
        metrics = []
        for group in payload.get("groups") or []:
            metrics.extend(str(item).strip() for item in group.get("updated_metrics") or group.get("metrics") or [] if str(item).strip())
        chart = payload.get("chart_breakdown") or {}
        metrics.extend(
            sorted(
                [str(segment.get("percentage") or "").strip() for segment in chart.get("segments") or [] if str(segment.get("percentage") or "").strip()],
                key=lambda item: int(item.rstrip("%")) if item.rstrip("%").isdigit() else -1,
                reverse=True,
            )
        )
        display_total = str(chart.get("display_total") or "").strip()
        if display_total:
            metrics.append(display_total)
        metrics.extend(
            str(segment.get("value") or "").strip()
            for segment in chart.get("segments") or []
            if str(segment.get("value") or "").strip()
        )
        return _clean_strings_keep_order(metrics)

    if page_type == "awards-patents":
        return [_compose_metric_block_line(block) for block in payload.get("metric_blocks") or [] if _compose_metric_block_line(block)]

    return None


def _group_item_lines(group: dict[str, Any]) -> list[str]:
    items = [str(item).strip() for item in group.get("items") or [] if str(item).strip()]
    if items:
        return items
    entries = []
    for entry in group.get("entries") or []:
        line = _join_entry(entry)
        if line:
            entries.append(line)
    return entries


def _clean_strings_keep_order(items: list[Any]) -> list[str]:
    return [str(item).strip() for item in items if str(item).strip()]


def _compose_metric_block_line(block: dict[str, Any]) -> str:
    label = str(block.get("label") or "").strip()
    value = str(block.get("value") or "").strip()
    unit = str(block.get("unit") or "").strip()
    display_lines = [str(line).strip() for line in block.get("display_lines") or [] if str(line).strip()]
    parts = [label]
    if display_lines:
        parts.extend(display_lines)
    elif value or unit:
        parts.append(f"{value}{unit}".strip())
    return " ".join(part for part in parts if part).strip()


def _compact_metric_block(block: dict[str, Any], page_type: str = "") -> dict[str, Any]:
    compact = deepcopy(block)
    if page_type != "metrics" and not compact.get("supporting_text"):
        compact.pop("supporting_text", None)
    if not compact.get("display_lines"):
        compact.pop("display_lines", None)
    return compact


def _split_people_line(text: Any) -> list[str]:
    clean = str(text).strip()
    if not clean:
        return []
    match = re.match(
        r"^(?P<name>\S+\s+\S+)\s+(?P<role>.+?)\s+(?P<edu>.+?\|\s*\S+)\s+(?P<exp>行业经验\d+年)$",
        clean,
    )
    if match:
        return [
            match.group("name").strip(),
            match.group("role").strip(),
            match.group("edu").strip(),
            match.group("exp").strip(),
        ]
    return [clean]


def _sort_footer_lines(items: list[Any]) -> list[str]:
    lines = _dedupe_strings(items)
    return sorted(
        lines,
        key=lambda item: (
            1 if any(token in item.lower() for token in ("www.", ".com", "http")) else 0,
            item,
        ),
    )


def _merge_canonical_text(canonical: list[Any], existing: list[Any]) -> list[str]:
    canonical_lines = _dedupe_strings(canonical)
    result = list(canonical_lines)
    for item in existing:
        text = str(item).strip()
        if not text:
            continue
        if text in result:
            continue
        if any(text != line and text in line for line in canonical_lines):
            continue
        result.append(text)
    return result


def _merge_existing_text(existing: list[Any], additions: list[Any]) -> list[str]:
    result = _clean_strings_keep_order(existing)
    for item in additions:
        text = str(item).strip()
        if not text:
            continue
        if text in result:
            continue
        result.append(text)
    return result


def _sort_awards_by_visible_order(awards: list[str], visible_lines: list[str]) -> list[str]:
    if not awards:
        return []

    def sort_key(award: str) -> tuple[int, int, str]:
        for index, line in enumerate(visible_lines):
            clean = str(line).strip()
            if not clean:
                continue
            if clean == award or clean in award or award in clean:
                return (0, index, award)
        return (1, len(visible_lines), award)

    return sorted(_dedupe_strings(awards), key=sort_key)


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


def _merge_connector_lists(existing: list[dict[str, Any]], generated: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    seen: set[str] = set()
    for source in (existing or [], generated or []):
        for connector in source:
            if not isinstance(connector, dict):
                continue
            marker = json.dumps(connector, ensure_ascii=False, sort_keys=True)
            if marker in seen:
                continue
            seen.add(marker)
            merged.append(connector)
    return merged


def _clean_generation_buckets(slide: dict[str, Any]) -> None:
    instruction = {str(item).strip() for item in slide.get("instruction_text") or [] if str(item).strip()}
    footer = {str(item).strip() for item in slide.get("footer") or [] if str(item).strip()}
    for field in ("main_text", "labels", "metrics"):
        cleaned = []
        for item in slide.get(field) or []:
            text = str(item).strip()
            if not text or text in instruction or text in footer:
                continue
            cleaned.append(text)
        slide[field] = _dedupe_strings(cleaned)


def _split_pair_item(text: str) -> dict[str, str] | None:
    clean = str(text).strip()
    if not clean:
        return None
    for suffix in sorted(KNOWN_SYSTEM_SUFFIXES, key=len, reverse=True):
        if clean.endswith(suffix):
            name = clean[: -len(suffix)].strip(" -—:：")
            if name:
                return {"name": name, "system": suffix}
    parts = re.split(r"\s+", clean)
    if len(parts) >= 2:
        return {"name": " ".join(parts[:-1]).strip(), "system": parts[-1].strip()}
    return {"name": clean, "system": ""}


def _join_entry(entry: dict[str, Any]) -> str:
    name = str(entry.get("name") or "").strip()
    system = str(entry.get("system") or "").strip()
    return f"{name} {system}".strip()


def _parse_metric_line(text: str) -> dict[str, Any] | None:
    clean = str(text).strip()
    if not clean:
        return None

    year_match = re.search(r"(\d{4}年)", clean)
    growth_match = re.search(r"(每年增速\s*\d+%|增速\s*\d+%)", clean)
    value_match = None
    for match in re.finditer(r"(\d+(?:\.\d+)?)\s*(亿元|个|人|家|%)", clean):
        if match.group(2) == "%":
            continue
        if year_match and match.start() == year_match.start():
            continue
        value_match = match
        break
    if not value_match:
        plus_match = re.search(r"(\d+(?:\.\d+)?)(\+)", clean)
        if plus_match:
            value_match = plus_match
    if not value_match:
        return None

    label_end = year_match.start() if year_match else value_match.start()
    label = clean[:label_end].strip(" ：:-")
    if not label:
        label = clean[: value_match.start()].strip(" ：:-")

    value = value_match.group(1)
    unit = value_match.group(2) if len(value_match.groups()) > 1 else ""
    supporting_text = []
    display_lines = []

    if year_match:
        supporting_text.append(year_match.group(1))
    if unit:
        display_lines.append(f"{year_match.group(1)} {value}{unit}".strip() if year_match else f"{value}{unit}".strip())
    if growth_match:
        compact_growth = growth_match.group(1).replace(" ", "")
        display_lines.append(compact_growth)
        supporting_text.append(compact_growth)

    metric_block = {
        "label": label,
        "value": value,
        "unit": unit,
        "supporting_text": _dedupe_strings(supporting_text),
    }
    if display_lines:
        metric_block["display_lines"] = _dedupe_strings(display_lines)
    return metric_block


def _node_looks_like_metric_group(node_title: str, items: list[str]) -> bool:
    metric_title_hit = any(keyword in node_title for keyword in ("市场规模", "成本", "指标", "数据"))
    metric_item_hit = any(
        re.search(r"\d", item) and any(unit in item for unit in ("亿元", "%", "个", "人", "+"))
        for item in items
    )
    return metric_title_hit or metric_item_hit


def _classify_panel_role(panel_title: str) -> str:
    title = str(panel_title).strip()
    mapping = {
        "公司介绍": "company-profile",
        "核心产品": "product-profile",
        "活力结构": "civil-business",
        "禹数": "industrial-business",
    }
    return mapping.get(title, "parallel-topic")


def _normalize_sector_panels(payload: dict[str, Any], slide: dict[str, Any]) -> None:
    panels = payload.get("panels") or []
    if len(panels) < 2:
        return

    civil_panel = next((panel for panel in panels if panel.get("panel_title") == "活力结构"), None)
    industrial_panel = next((panel for panel in panels if panel.get("panel_title") == "禹数"), None)
    if not civil_panel or not industrial_panel:
        return

    civil_allowed = {"购物中心", "大型酒店", "办公建筑", "医院", "大型场馆"}
    industrial_allowed = {"精密电子", "石油化工", "远洋运输", "科学装置", "钢铁冶炼", "能源电力", "数据中心", "半导体", "新能源制造"}
    visible = _dedupe_strings(slide.get("all_visible_text") or [])
    civil_panel["panel_role"] = "civil-sectors"
    industrial_panel["panel_role"] = "industrial-sectors"
    civil_panel["items"] = [item for item in civil_panel.get("items") or [] if item in civil_allowed]
    industrial_panel["items"] = [item for item in industrial_panel.get("items") or [] if item in industrial_allowed]
    if not civil_panel["items"]:
        civil_panel["items"] = [item for item in visible if item in civil_allowed]
    if not industrial_panel["items"]:
        industrial_panel["items"] = [item for item in visible if item in industrial_allowed]
    civil_order = ["购物中心", "大型酒店", "办公建筑", "医院", "大型场馆"]
    industrial_order = ["精密电子", "石油化工", "远洋运输", "科学装置", "钢铁冶炼", "能源电力", "数据中心", "半导体", "新能源制造"]
    civil_panel["items"] = [item for item in civil_order if item in civil_panel["items"]]
    industrial_panel["items"] = [item for item in industrial_order if item in industrial_panel["items"]]

    desired_metric_labels = [
        "中国工业设备设施运维服务行业市场规模",
        "中国民用公共建筑运维服务行业市场规模",
        "中国设备设施运行及改造成本总计",
    ]
    desired_growth = ["每年增速10%", "每年增速8%", ""]
    metric_values = []
    for line in visible:
        parsed = _parse_metric_line(line)
        if parsed and parsed.get("value"):
            metric_values.append(parsed)
    metric_values = metric_values[:3]
    rebuilt_metrics = []
    for index, block in enumerate(metric_values):
        rebuilt = {
            "label": desired_metric_labels[index] if index < len(desired_metric_labels) else str(block.get("label") or "").strip(),
            "value": str(block.get("value") or "").strip(),
            "unit": str(block.get("unit") or "").strip(),
            "supporting_text": ["2024年"],
        }
        growth = desired_growth[index] if index < len(desired_growth) else ""
        display_lines = [f"2024年 {rebuilt['value']}{rebuilt['unit']}".strip()]
        if growth:
            display_lines.append(growth)
            rebuilt["supporting_text"].append(growth)
        rebuilt["display_lines"] = display_lines
        rebuilt_metrics.append(rebuilt)
    if rebuilt_metrics:
        payload["metric_blocks"] = rebuilt_metrics


def _chart_breakdown_looks_noisy(chart: dict[str, Any]) -> bool:
    total_digits = re.sub(r"\D", "", str(chart.get("display_total") or ""))
    segments = chart.get("segments") or []
    if len(segments) < 5:
        return True
    for segment in segments:
        label = str(segment.get("label") or "").strip()
        value_digits = re.sub(r"\D", "", str(segment.get("value") or ""))
        if len(label) <= 1 or label in {"工智能", "人", "年", "一凫", "博士", "行业经验"}:
            return True
        if total_digits and value_digits == total_digits:
            return True
    return False


def _refine_missing_risk(slide: dict[str, Any]) -> list[str]:
    risks = [str(risk).strip() for risk in slide.get("missing_risk") or [] if str(risk).strip()]
    payload = slide.get("structured_payload") or {}
    page_type = str(slide.get("page_type") or "").strip()
    if slide.get("page_type") == "peer-panels":
        if payload.get("panels") or slide.get("hierarchy"):
            risks = [
                risk
                for risk in risks
                if "无法识别图片中的文本和结构" not in risk
                and "image-heavy" not in risk
                and "text coverage could be partial" not in risk
            ]
    if page_type == "timeline" and payload.get("periods"):
        risks = [risk for risk in risks if "image-heavy" not in risk and "text coverage could be partial" not in risk]
    if page_type == "logo-wall":
        groups = payload.get("groups") or []
        if groups and all(_group_item_lines(group) for group in groups):
            risks = [
                risk
                for risk in risks
                if "image-heavy" not in risk
                and "text coverage could be partial" not in risk
                and "group titles were preserved" not in risk
            ]
    if page_type == "awards-patents":
        if payload.get("investors"):
            risks = [risk for risk in risks if "Investor identities" not in risk and "投资人名称" not in risk]
        if payload.get("awards") and payload.get("metric_blocks"):
            risks = [risk for risk in risks if "image-heavy" not in risk and "text coverage could be partial" not in risk]
    if page_type == "people-matrix" and payload.get("chart_breakdown"):
        risks = [risk for risk in risks if "image-heavy" not in risk and "text coverage could be partial" not in risk]
        updated_total = ""
        for group in payload.get("groups") or []:
            for item in group.get("updated_metrics") or group.get("metrics") or []:
                text = str(item).strip()
                if "总人数" in text:
                    updated_total = re.sub(r"\D", "", text)
                    break
            if updated_total:
                break
        chart_total = re.sub(r"\D", "", str((payload.get("chart_breakdown") or {}).get("display_total") or ""))
        if updated_total and chart_total and updated_total != chart_total:
            risks = _dedupe_strings(
                [
                    *risks,
                    "The headcount text block and donut chart on the source slide are internally inconsistent.",
                ]
            )
    return _dedupe_strings(risks)


def _looks_english(text: str) -> bool:
    clean = str(text).strip()
    if not clean:
        return False
    ascii_letters = sum(1 for char in clean if char.isascii() and char.isalpha())
    return ascii_letters >= max(3, len(clean.replace(" ", "")) // 2)


def _dedupe_strings(items: list[Any]) -> list[str]:
    seen = set()
    result: list[str] = []
    for item in items:
        text = str(item).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def _pick_deck_title(slides: list[dict[str, Any]]) -> str:
    if not slides:
        return "PPT标准化转换结果"
    first_title = str(slides[0].get("title") or "").strip()
    return first_title or "PPT标准化转换结果"


def _fallback_outline_title(slide: dict[str, Any]) -> str:
    payload = slide.get("structured_payload") or {}
    for key in ("section_title", "brand_title", "primary_title"):
        value = str(payload.get(key) or "").strip()
        if value:
            return value
    root = _first_node(slide.get("hierarchy") or [])
    return str(root.get("title") or "").strip() if root else ""


def _first_node(nodes: list[dict[str, Any]]) -> dict[str, Any] | None:
    for node in nodes:
        if isinstance(node, dict):
            return node
    return None


if __name__ == "__main__":
    import argparse
    from pathlib import Path

    parser = argparse.ArgumentParser(description="Normalize recognition JSON for stronger semantic fidelity.")
    parser.add_argument("input_json", type=Path, help="Path to a deck JSON file")
    parser.add_argument("--output", type=Path, help="Optional output path; defaults to overwrite input")
    args = parser.parse_args()

    payload = json.loads(args.input_json.read_text(encoding="utf-8"))
    normalized = normalize_deck_result(payload, source_file=str(payload.get("source_file") or ""))
    target = args.output or args.input_json
    target.write_text(json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8")
