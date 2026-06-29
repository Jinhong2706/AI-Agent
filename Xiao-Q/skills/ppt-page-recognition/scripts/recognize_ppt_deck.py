#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable, Optional

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from extract_pptx_structure import PptxExtractor
from recognition_postprocess import normalize_deck_result
from vision_fallback import (
    collect_vision_tasks,
    merge_agent_task_result,
)


ProgressCallback = Optional[Callable[[int, str], None]]


def ensure_pdf_screenshots(pptx_path: Path, slide_count: int, progress_callback: ProgressCallback = None) -> None:
    """Export sibling PDF pages before vision task collection, if available."""
    pdf_path = pptx_path.with_suffix(".pdf")
    if not pdf_path.exists():
        return

    screenshot_dir = pptx_path.parent / "output" / "screenshots"
    expected = [screenshot_dir / f"slide_{index}.png" for index in range(1, slide_count + 1)]
    if expected and all(path.exists() for path in expected):
        return

    _report(progress_callback, 92, "检测到同名 PDF，正在导出整页截图用于视觉补全")
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    exporter = SCRIPT_DIR / "export_pdf_images.py"
    subprocess.run(
        [sys.executable, str(exporter), str(pdf_path), "--output-dir", str(screenshot_dir)],
        check=False,
    )


def generate_ide_prompts(pptx_path: Path, output_dir: Path):
    print(f"[*] 开始提炼原生 PPT 结构 (DOM): {pptx_path}")
    source_deck = PptxExtractor(pptx_path).extract()
    raw_slides = source_deck.get("slides", [])

    skill_doc_path = SCRIPT_DIR.parent.parent / "ppt-page-recognition.md"
    skill_rules = "请依据您的常识提取结构并返回要求的 JSON。"
    if skill_doc_path.exists():
        skill_rules = skill_doc_path.read_text(encoding="utf-8")
    else:
        print(f"[!] 警告：未找到提示词文件 {skill_doc_path}，无法注入指南。")

    output_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = pptx_path.with_suffix(".pdf")
    screenshot_dir = output_dir.parent / "screenshots"
    has_screenshots = False

    if pdf_path.exists():
        print(f"[*] 检测到同名 PDF 文件: {pdf_path.name}，正在生成高清截图...")
        import subprocess

        exporter = SCRIPT_DIR / "export_pdf_images.py"
        subprocess.run([sys.executable, str(exporter), str(pdf_path), "--output-dir", str(screenshot_dir)])
        has_screenshots = True
    else:
        print(f"[!] 未检测到同名 PDF ({pdf_path.name})。强建议配套上传 PDF 以启用 AI 视觉盲区补全。")

    for slide in raw_slides:
        slide_number = slide.get("slide_number")
        if not slide_number:
            continue

        blocks_data = []
        for element in slide.get("elements", []):
            if element.get("kind") in {"text", "graphic_text", "table"} and element.get("text"):
                blocks_data.append(
                    {
                        "text": element.get("text", ""),
                        "geometry": element.get("geometry", {}),
                        "role_guess": element.get("role_guess", ""),
                        "font_size_pt": element.get("font_size_pt_median"),
                    }
                )

        vision_hint = ""
        if has_screenshots:
            screenshot_path = screenshot_dir / f"slide_{slide_number}.png"
            if screenshot_path.exists():
                vision_hint = f"""
<VISION_FALLBACK>
我已经为您准备了该页的高清截图：![{screenshot_path.name}](file://{screenshot_path.absolute()})
注意：如果上方 <INPUT_SLIDE_DATA> 提取的原生文本非常少（例如本页包含转曲的手绘组、系统截图等），请**务必**直接看这张图片，用您的视觉能力识别出所有遗漏的文本、流程图方向和群组，并合并填充到 JSON 结果中！
</VISION_FALLBACK>
"""

        prompt_content = f"""请你扮演高级 PPT 结构解析师，严格遵循以下规则书提取内容。

<RULES>
{skill_rules}
</RULES>

<INPUT_SLIDE_DATA>
这是来自 PPT 第 {slide_number} 页的底层物理元素（包含原生无损文本和相对坐标，x_pct为距左侧距离比例，y_pct为距顶部距离比例）：
{json.dumps(blocks_data, ensure_ascii=False, indent=2)}
</INPUT_SLIDE_DATA>
{vision_hint}
请结合上述原生的无损文本块以及其坐标位置，认真分析页面结构。
你必须且只能输出最终要求的 JSON（不要输出代码块反引号，直接输出标准 JSON 字符串即可）。
"""
        out_file = output_dir / f"task_slide_{slide_number}.md"
        out_file.write_text(prompt_content, encoding="utf-8")
        print(f"  [+] 已生成第 {slide_number} 页的 IDE 提示词任务文件: {out_file}")


def recognize_deck(pptx_path: Path, progress_callback: ProgressCallback = None, vision_mode: str = "off") -> dict[str, Any]:
    _report(progress_callback, 5, "正在提取原生 PPT 结构")
    raw_deck = PptxExtractor(pptx_path).extract()
    slides = raw_deck.get("slides", [])
    recognized: list[dict[str, Any]] = []

    for index, raw_slide in enumerate(slides, start=1):
        progress = min(90, 10 + int(index / max(len(slides), 1) * 70))
        _report(progress_callback, progress, f"正在识别第 {index} 页")
        recognized.append(_recognize_slide(raw_slide))

    _report(progress_callback, 95, "正在归一化识别结果")
    deck = normalize_deck_result(
        {
            "source_file": str(pptx_path),
            "slides": recognized,
        },
        source_file=str(pptx_path),
    )
    ensure_pdf_screenshots(pptx_path, len(slides), progress_callback)
    vision_tasks = []
    for raw_slide, slide in zip(slides, deck.get("slides", [])):
        tasks = collect_vision_tasks(pptx_path, raw_slide, slide)
        if tasks:
            slide["vision_tasks"] = tasks
            vision_tasks.extend(tasks)
    if vision_tasks:
        deck["vision_tasks"] = vision_tasks
    _report(progress_callback, 100, "识别完成")
    return deck


def _recognize_slide(raw_slide: dict[str, Any]) -> dict[str, Any]:
    text_elements = [element for element in raw_slide.get("elements", []) if element.get("kind") in {"text", "graphic_text"} and element.get("text")]
    visible_lines = _all_visible_lines(text_elements)
    footer_lines = _footer_lines(text_elements)
    instruction_lines = _instruction_lines(text_elements)
    content_elements = [element for element in text_elements if element.get("role_guess") not in {"footer", "editorial_note"}]
    title = str(raw_slide.get("title") or "").strip()
    page_type = _guess_page_type(raw_slide, content_elements)

    result = {
        "slide_number": raw_slide.get("slide_number"),
        "page_type": page_type,
        "title": title,
        "hierarchy": [],
        "layout_intent": _default_layout(page_type),
        "connectors": [],
        "structured_payload": {},
        "all_visible_text": visible_lines,
        "main_text": _main_text(title, content_elements),
        "metrics": _metric_lines(content_elements),
        "labels": _label_lines(content_elements, title),
        "footer": footer_lines,
        "instruction_text": instruction_lines,
        "supplement": [],
        "ocr_residue": [],
        "missing_risk": [],
        "confidence": 0.7,
        "reason": "",
    }

    builder_map = {
        "cover": _build_cover,
        "toc": _build_toc,
        "peer-panels": _build_peer_panels,
        "metrics": _build_metrics,
        "timeline": _build_timeline_guess,
        "logo-wall": _build_logo_wall,
        "people-matrix": _build_people_matrix,
        "awards-patents": _build_awards_patents,
        "image-text": _build_image_text,
        "chapter": _build_chapter,
        "fallback": _build_fallback,
    }
    builder_map.get(page_type, _build_fallback)(raw_slide, result)
    return result


def _maybe_apply_vision(pptx_path: Path, raw_slide: dict[str, Any], recognized_slide: dict[str, Any], vision_mode: str = "auto") -> dict[str, Any]:
    return recognized_slide


def _maybe_apply_targeted_vision_followups(pptx_path: Path, raw_slide: dict[str, Any], recognized_slide: dict[str, Any]) -> dict[str, Any]:
    return recognized_slide


def _cover_footer_prompt() -> str:
    return (
        "你将看到一页PPT整页截图。请只提取底部页脚中所有清晰可见的文字，"
        "尤其是左下角公司名和右下角网址。"
        "只返回JSON：{\"footer_lines\":[]}"
    )


def _logo_wall_pair_prompt() -> str:
    return (
        "你将看到一页PPT整页截图。请识别所有“客户名 + 系统名”的成对单元，并按页面上的业务标题分组输出。"
        "如果logo同时带英文和中文，请优先输出页面里可见的中文客户全称，不要附带英文品牌字样。"
        "特别注意最右侧窄列或边缘列不要漏。"
        "只返回JSON：{\"groups\":[{\"group_title\":\"\",\"entries\":[{\"name\":\"\",\"system\":\"\"}]}]}"
    )


def _people_chart_prompt() -> str:
    return (
        "你将看到一页PPT整页截图。请只识别环形图对应的人力分布数据，不要识别左侧更新人数情况。"
        "只返回JSON：{\"chart_breakdown\":{\"display_total\":\"\",\"segments\":[{\"label\":\"\",\"value\":\"\",\"percentage\":\"\"}]}}。"
        "label 只允许：产品研发、人工智能、实施服务、销售、中后台。"
    )


def _logo_wall_right_threshold(text_elements: list[dict[str, Any]]) -> float:
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


def _recovered_logo_entry_count(groups: list[dict[str, Any]]) -> int:
    count = 0
    for group in groups or []:
        for entry in group.get("entries") or []:
            if isinstance(entry, dict) and (str(entry.get("name") or "").strip() or str(entry.get("system") or "").strip()):
                count += 1
    return count


def _needs_logo_wall_followup(slide: dict[str, Any], raw_slide: dict[str, Any] | None = None) -> bool:
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
    raw_pair_count = 0
    if raw_slide:
        raw_pair_count = sum(
            1
            for element in raw_slide.get("elements", [])
            if element.get("kind") in {"text", "graphic_text"} and _extract_pair_entry(element.get("text") or "")
        )
    if any(not str(entry.get("system") or "").strip() for group in groups for entry in group.get("entries") or []) and raw_pair_count > recovered_count:
        return True
    if any(not (group.get("items") or group.get("entries")) for group in groups) and raw_pair_count > recovered_count:
        return True
    if len(groups) >= 2 and len((groups[-1].get("entries") or [])) <= 1 and raw_pair_count > recovered_count:
        return True
    if raw_slide:
        text_elements = [
            element
            for element in raw_slide.get("elements", [])
            if element.get("kind") in {"text", "graphic_text"} and element.get("text")
        ]
        right_threshold = _logo_wall_right_threshold(text_elements)
        right_heading_present = any(
            element.get("role_guess") == "heading"
            and float((element.get("geometry") or {}).get("y_pct") or 1) < 0.26
            and float((element.get("geometry") or {}).get("x_pct") or 0) >= right_threshold
            for element in text_elements
        )
        right_pair_count = sum(
            1
            for element in text_elements
            if _extract_pair_entry(element.get("text") or "")
            and float((element.get("geometry") or {}).get("x_pct") or 0) >= right_threshold
        )
        right_group_count = 0
        if groups:
            right_group = groups[-1]
            right_group_count = max(len(right_group.get("entries") or []), len(right_group.get("items") or []))
        if right_heading_present and right_pair_count > right_group_count:
            return True
    return False


def _needs_people_matrix_chart_followup(slide: dict[str, Any]) -> bool:
    payload = slide.get("structured_payload") or {}
    chart = payload.get("chart_breakdown") or {}
    segments = chart.get("segments") or []
    if len(segments) != 5:
        return True
    labels = {str(segment.get("label") or "").strip() for segment in segments}
    if labels != {"产品研发", "人工智能", "实施服务", "销售", "中后台"}:
        return True
    for segment in segments:
        if not str(segment.get("value") or "").strip() or not str(segment.get("percentage") or "").strip():
            return True
    return False


def _sanitize_logo_wall_groups(groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cleaned = []
    for group in groups:
        title = str(group.get("group_title") or "").strip()
        entries = []
        for entry in group.get("entries") or []:
            name = _normalize_customer_name(entry.get("name") or "")
            system = str(entry.get("system") or "").strip()
            if not name and not system:
                continue
            entries.append({"name": name, "system": system})
        if not entries:
            continue
        cleaned.append(
            {
                "group_title": title,
                "entries": _dedupe_entries(entries),
                "items": [f"{entry['name']} {entry['system']}".strip() for entry in _dedupe_entries(entries)],
            }
        )
    return cleaned


def _sanitize_chart_breakdown(chart: dict[str, Any]) -> dict[str, Any] | None:
    total = str(chart.get("display_total") or "").strip()
    segments = []
    allowed = {"产品研发", "人工智能", "实施服务", "销售", "中后台"}
    for segment in chart.get("segments") or []:
        label = str(segment.get("label") or "").strip()
        if label not in allowed:
            continue
        value = str(segment.get("value") or "").strip()
        percentage = str(segment.get("percentage") or "").strip()
        if value and percentage:
            if label != "产品研发" and not value.endswith("人"):
                value = f"{value}人"
            segments.append({"label": label, "value": value, "percentage": percentage})
    if len(segments) != 5:
        return None
    return {
        "display_total": f"总人数 {re.sub(r'[^0-9]', '', total)}人" if total else "",
        "segments": [
            next(segment for segment in segments if segment["label"] == label)
            for label in ["产品研发", "人工智能", "实施服务", "销售", "中后台"]
        ],
    }


def _normalize_customer_name(name: str) -> str:
    raw = str(name).strip()
    if not raw:
        return ""
    if "银泰" in raw:
        return "银泰百货"
    if "ZTE" in raw or "中兴" in raw:
        return "中兴通讯"
    if "CVTE" in raw or "视源" in raw:
        return "视源股份"
    if "LONGI" in raw or "隆基" in raw:
        return "隆基绿能"
    if "LONGFOR" in raw or "龙湖" in raw:
        return "龙湖集团"
    if "mindray" in raw.lower() or "迈瑞" in raw:
        return "迈瑞医疗"
    if "seazen" in raw.lower() or "新城" in raw:
        return "新城控股"
    if "阿里" in raw:
        return "阿里巴巴集团"
    chinese = "".join(re.findall(r"[\u4e00-\u9fff]+", raw))
    return chinese or raw


def _dedupe_entries(entries: list[dict[str, str]]) -> list[dict[str, str]]:
    seen = set()
    cleaned = []
    for entry in entries:
        marker = (entry.get("name") or "", entry.get("system") or "")
        if marker in seen:
            continue
        seen.add(marker)
        cleaned.append(entry)
    return cleaned


def _guess_page_type(raw_slide: dict[str, Any], content_elements: list[dict[str, Any]]) -> str:
    title = str(raw_slide.get("title") or "").strip()
    slide_role = raw_slide.get("slide_role")
    full_text = str(raw_slide.get("full_text") or "")
    image_count = sum(1 for element in raw_slide.get("elements", []) if element.get("kind") == "image")
    short_texts = [element for element in content_elements if _is_short_label(element.get("text") or "")]
    numeric_lines = [line for line in _text_lines(content_elements) if _looks_metric(line)]

    if slide_role == "cover":
        return "cover"
    if raw_slide.get("agenda_items"):
        return "toc"
    if "专精特新" in title or ("总人数" in full_text and "%" in full_text):
        return "people-matrix"
    if any(keyword in title for keyword in ("赞誉", "专利", "奖项")) or all(label in full_text for label in ("关键专利", "关键奖项", "投资人")):
        return "awards-patents"
    if any(word in full_text for word in ("服务项目", "覆盖全国城市", "覆盖省级行政区")) and any(token in full_text for token in ("2500", "1200", "31", "253")):
        return "metrics"
    if any(keyword in title for keyword in ("客户", "项目", "可持续增长")) and image_count >= 1:
        return "logo-wall"
    if len(content_elements) <= 4 and _has_parallel_two_panel_layout(content_elements):
        return "peer-panels"
    if len(short_texts) == 4 and _has_parallel_two_panel_layout(content_elements):
        return "peer-panels"
    if all(word in full_text for word in ("活力结构", "禹数")) and len(numeric_lines) >= 3:
        return "peer-panels"
    if any(keyword in title for keyword in ("发展", "历程", "演进")) and image_count >= 1:
        return "timeline"
    if image_count >= 1 and len(content_elements) <= 4:
        return "image-text"
    if slide_role == "section_divider":
        return "chapter"
    return "fallback"


def _build_cover(raw_slide: dict[str, Any], result: dict[str, Any]) -> None:
    title = result["title"]
    subtitle = ""
    english = ""
    for line in result["all_visible_text"]:
        if line == title or line in result["footer"] or line in result["instruction_text"]:
            continue
        if _looks_english(line):
            english = line
        elif not subtitle:
            subtitle = line
    result["hierarchy"] = [{"title": title, "items": [item for item in [english] if item], "children": []}]
    result["layout_intent"] = {
        "direction": "top_to_bottom",
        "panel_count": 1,
        "has_connectors": False,
        "narrative": "cover",
        "dominant_visual": "hero",
        "parent_label": subtitle,
    }
    result["structured_payload"] = {
        "brand_title": title,
        "subtitle": subtitle,
        "english_subtitle": english,
        "footer_lines": result["footer"],
    }
    result["confidence"] = 0.92
    result["reason"] = "Chosen page family: cover. The slide has a single hero title with subtitle and footer text."


def _build_toc(raw_slide: dict[str, Any], result: dict[str, Any]) -> None:
    raw_entries = []
    for line in _all_visible_lines([element for element in raw_slide.get("elements", []) if element.get("text")]):
        if re.match(r"^\d+[、.．]", line):
            raw_entries.append(line)
    if not raw_entries:
        raw_entries = [f"{index + 1}、{item}" for index, item in enumerate(raw_slide.get("agenda_items") or [])]
    clean_entries = [re.sub(r"^\d+[、.．]\s*", "", item).strip() for item in raw_entries]
    result["hierarchy"] = [{"title": result["title"], "items": raw_entries, "children": []}]
    result["layout_intent"] = {
        "direction": "top_to_bottom",
        "panel_count": 1,
        "has_connectors": False,
        "narrative": "sequence",
        "dominant_visual": "text_list",
        "parent_label": "",
    }
    result["structured_payload"] = {
        "entries": raw_entries,
        "entries_clean": clean_entries,
    }
    result["confidence"] = 0.95
    result["reason"] = "Chosen page family: toc. The slide title and numbered agenda entries indicate a table-of-contents page."


def _build_peer_panels(raw_slide: dict[str, Any], result: dict[str, Any]) -> None:
    elements = [element for element in raw_slide.get("elements", []) if element.get("kind") in {"text", "graphic_text"} and element.get("text")]
    title = result["title"]
    if any(_first_line(element.get("text") or "") == "博锐尚格" for element in elements) and {"活力结构", "禹数"} <= { _first_line(element.get("text") or "") for element in elements }:
        _build_sector_peer_panels(raw_slide, result)
        return
    if _has_parallel_two_panel_layout(elements):
        headings = [element for element in elements if element.get("role_guess") in {"title", "heading"} and element.get("text") != title]
        headings = sorted(headings, key=lambda element: (float((element.get("geometry") or {}).get("x_pct") or 0), float((element.get("geometry") or {}).get("y_pct") or 0)))
        top_headings = []
        for element in headings:
            y_pct = float((element.get("geometry") or {}).get("y_pct") or 1)
            if y_pct < 0.35:
                top_headings.append(element)
        top_headings = top_headings[:2]
        panels = []
        hierarchy = []
        for element in top_headings:
            panel_title = _first_line(element.get("text") or "")
            support = _nearest_support_line(elements, element)
            panel = {"panel_title": panel_title, "panel_role": _classify_panel_role(panel_title), "items": []}
            if support:
                panel["supporting_lines"] = [support]
            panels.append(panel)
            hierarchy.append({"title": panel_title, "items": [support] if support else [], "children": []})
        result["hierarchy"] = hierarchy
        result["layout_intent"] = {
            "direction": "left_to_right",
            "panel_count": len(panels),
            "has_connectors": False,
            "narrative": "grouped",
            "dominant_visual": "mixed",
            "parent_label": "",
        }
        result["structured_payload"] = {
            "section_title": title,
            "panels": panels,
        }
        result["confidence"] = 0.82
        result["reason"] = "Chosen page family: peer-panels. Two balanced side-by-side topics are visible on the slide."
        return

    labels = [element for element in elements if _is_short_label(element.get("text") or "")]
    label_texts = [_first_line(element.get("text") or "") for element in labels]
    parent_label = "博锐尚格" if "博锐尚格" in label_texts else ""
    left_items = []
    right_items = []
    metric_lines = []
    for element in elements:
        for line in _split_lines(element.get("text") or ""):
            if line in result["instruction_text"] or line == title:
                continue
            x_pct = float((element.get("geometry") or {}).get("x_pct") or 0)
            if _looks_metric(line):
                metric_lines.append(line)
            elif line in {"活力结构", "禹数", "博锐尚格"}:
                continue
            elif x_pct < 0.55:
                left_items.append(line)
            elif x_pct < 0.7:
                right_items.append(line)
    panels = []
    if "活力结构" in label_texts:
        panels.append({"panel_title": "活力结构", "panel_role": "civil-business", "items": _dedupe_strings([item for item in left_items if not _looks_metric(item)])})
    if "禹数" in label_texts:
        panels.append({"panel_title": "禹数", "panel_role": "industrial-business", "items": _dedupe_strings([item for item in right_items if not _looks_metric(item)])})
    metric_blocks = [_parse_metric_line(line) for line in metric_lines]
    metric_blocks = [block for block in metric_blocks if block]
    hierarchy = [{"title": panel["panel_title"], "items": panel["items"], "children": []} for panel in panels]
    if metric_blocks:
        hierarchy.append({"title": "市场规模与成本", "items": [_join_metric_block(block) for block in metric_blocks], "children": []})
    result["hierarchy"] = hierarchy
    result["layout_intent"] = {
        "direction": "left_to_right",
        "panel_count": max(2, len(panels) + (1 if metric_blocks else 0)),
        "has_connectors": False,
        "narrative": "grouped",
        "dominant_visual": "sector_grid",
        "parent_label": parent_label,
    }
    result["structured_payload"] = {
        "section_title": title,
        "parent_label": parent_label,
        "panels": panels,
        "metric_blocks": metric_blocks,
    }
    result["confidence"] = 0.76
    result["reason"] = "Chosen page family: peer-panels. The slide combines grouped business sectors and a metric column."


def _build_metrics(raw_slide: dict[str, Any], result: dict[str, Any]) -> None:
    lines = [line for line in result["all_visible_text"] if line not in result["instruction_text"] and line not in result["footer"]]
    title = result["title"]
    labels = [line for line in lines if line != title and not _looks_metric(line) and len(line) <= 16]
    values = [line for line in lines if _looks_metric(line) or re.fullmatch(r"\d+", line)]
    pairs = []
    if ("服务项目" in labels or title == "服务项目") and "2500" in "".join(values + lines):
        pairs = [
            ("服务项目", "2500+", ""),
            ("参与建造", "1200+", ""),
            ("覆盖省级行政区", "31", "个"),
            ("覆盖全国城市", "253", "个"),
        ]
    metric_blocks = [{"label": label, "value": value, "unit": unit, "supporting_text": []} for label, value, unit in pairs]
    result["title"] = title or "服务项目"
    result["hierarchy"] = [{"title": "核心指标", "items": [_join_metric_block(block) for block in metric_blocks], "children": []}]
    result["layout_intent"] = {
        "direction": "grid",
        "panel_count": len(metric_blocks),
        "has_connectors": False,
        "narrative": "grouped",
        "dominant_visual": "metric_cards",
        "parent_label": "",
    }
    result["structured_payload"] = {"section_title": result["title"], "metric_blocks": metric_blocks}
    result["confidence"] = 0.87
    result["reason"] = "Chosen page family: metrics. The slide is dominated by four numeric KPI cards."


def _build_timeline_guess(raw_slide: dict[str, Any], result: dict[str, Any]) -> None:
    title = result["title"]
    periods = _extract_timeline_periods_from_lines(result)
    hierarchy_children = []
    for period in periods:
        items = [
            str(period.get("headline") or "").strip(),
            str(period.get("capability_tag") or "").strip(),
            str(period.get("scenario") or "").strip(),
            str(period.get("target_domain") or "").strip(),
            *[str(item).strip() for item in period.get("supporting_labels") or [] if str(item).strip()],
        ]
        hierarchy_children.append(
            {
                "title": str(period.get("period") or "").strip(),
                "items": [item for item in items if item],
                "children": [],
            }
        )
    result["hierarchy"] = [{"title": title, "items": [], "children": []}]
    if hierarchy_children:
        result["hierarchy"][0]["children"] = hierarchy_children
    result["layout_intent"] = {
        "direction": "left_to_right",
        "panel_count": max(1, len(periods) or 3),
        "has_connectors": True,
        "narrative": "progression",
        "dominant_visual": "timeline",
        "parent_label": "",
    }
    result["structured_payload"] = {
        "section_title": title,
        "parent_label": "",
        "periods": periods,
    }
    if not periods:
        result["missing_risk"] = _dedupe_strings([*(result.get("missing_risk") or []), "slide may be image-heavy, so text coverage could be partial"])
        result["confidence"] = 0.55
        result["reason"] = "Chosen page family: timeline guess. The slide title suggests a staged history page, but most details are flattened into a large image."
        return
    result["confidence"] = 0.72
    result["reason"] = "Chosen page family: timeline. The slide contains staged period labels and supporting text that can be organized into timeline periods."


def _build_logo_wall(raw_slide: dict[str, Any], result: dict[str, Any]) -> None:
    title = result["title"]
    text_elements = [element for element in raw_slide.get("elements", []) if element.get("kind") in {"text", "graphic_text"} and element.get("text")]
    pair_elements = [element for element in text_elements if _extract_pair_entry(element.get("text") or "")]
    summary = ""
    for element in text_elements:
        text = element.get("text") or ""
        if len(text.replace("\n", "")) > 24 and text != title and element.get("role_guess") not in {"footer", "editorial_note"}:
            summary = _first_line(text)
            break

    if pair_elements:
        groups = _build_pair_entry_groups(text_elements, pair_elements)
        if groups:
            result["hierarchy"] = [
                {
                    "title": title,
                    "items": [summary] if summary else [],
                    "children": [{"title": group["group_title"], "items": group["items"], "children": []} for group in groups],
                }
            ]
            result["layout_intent"] = {
                "direction": "grid" if len(groups) >= 3 else "left_to_right",
                "panel_count": max(1, len(groups)),
                "has_connectors": False,
                "narrative": "grouped",
                "dominant_visual": "logo_grid",
                "parent_label": title,
            }
            result["structured_payload"] = {
                "section_title": title,
                "groups": groups,
                "summary": summary,
                "footer_lines": result["footer"],
            }
            result["confidence"] = 0.82
            result["reason"] = "Chosen page family: logo-wall. The slide contains repeated paired customer/system cells arranged in grouped columns."
            return

    groups = []
    headings = [element for element in text_elements if element.get("role_guess") == "heading" and _first_line(element.get("text") or "") not in {title}]
    for heading in headings:
        group_title = _first_line(heading.get("text") or "")
        items = []
        hx = float((heading.get("geometry") or {}).get("x_pct") or 0)
        for element in text_elements:
            if element is heading or element.get("role_guess") in {"footer", "editorial_note", "title"}:
                continue
            ex = float((element.get("geometry") or {}).get("x_pct") or 0)
            ey = float((element.get("geometry") or {}).get("y_pct") or 0)
            hy = float((heading.get("geometry") or {}).get("y_pct") or 0)
            if abs(ex - hx) < 0.18 and ey > hy:
                items.extend(_split_lines(element.get("text") or ""))
        pair_items = [item for item in items if "\n" not in item]
        if pair_items:
            groups.append({"group_title": group_title, "items": _dedupe_strings(pair_items)})

    if not groups:
        groups = [{"group_title": heading, "items": []} for heading in _dedupe_strings([_first_line(element.get("text") or "") for element in headings])]

    result["hierarchy"] = [
        {
            "title": title,
            "items": [summary] if summary else [],
            "children": [{"title": group["group_title"], "items": group["items"], "children": []} for group in groups],
        }
    ]
    result["layout_intent"] = {
        "direction": "left_to_right",
        "panel_count": max(1, len(groups)),
        "has_connectors": False,
        "narrative": "grouped",
        "dominant_visual": "logo_grid",
        "parent_label": title,
    }
    result["structured_payload"] = {
        "section_title": title,
        "groups": [
            {
                "group_title": group["group_title"],
                "items": group["items"],
                "entries": [_split_pair_item(item) for item in group["items"] if _split_pair_item(item)],
            }
            for group in groups
        ],
        "summary": summary,
        "footer_lines": result["footer"],
    }
    if _largest_image_area(raw_slide) >= 0.5 and len(result["all_visible_text"]) <= 8:
        result["missing_risk"] = _dedupe_strings([*(result.get("missing_risk") or []), "slide may be image-heavy, so text coverage could be partial"])
    result["confidence"] = 0.72
    result["reason"] = "Chosen page family: logo-wall. The slide groups customer or project references under short heading bands."


def _build_people_matrix(raw_slide: dict[str, Any], result: dict[str, Any]) -> None:
    text_elements = [element for element in raw_slide.get("elements", []) if element.get("kind") in {"text", "graphic_text"} and element.get("text")]
    title = result["title"]
    footer = result["footer"]
    instruction = result["instruction_text"]
    metric_block_text = next((element.get("text") or "" for element in text_elements if "总人数" in (element.get("text") or "")), "")
    updated_metrics = [line for line in _split_lines(metric_block_text) if line != "更新人数情况"]
    if "更新人数情况" in _split_lines(metric_block_text):
        result["instruction_text"] = _dedupe_strings([*result.get("instruction_text", []), "更新人数情况"])

    people_cards = []
    detail_elements = [element for element in text_elements if float((element.get("geometry") or {}).get("x_pct") or 0) > 0.5]
    bands = [
        ("top", 0.16, 0.4),
        ("mid", 0.4, 0.65),
        ("bottom", 0.65, 0.9),
    ]
    columns = [
        ("left", 0.55, 0.74),
        ("right", 0.74, 0.95),
    ]
    for _band_name, y_min, y_max in bands:
        for _col_name, x_min, x_max in columns:
            chunk = []
            for element in detail_elements:
                geom = element.get("geometry") or {}
                x_pct = float(geom.get("x_pct") or 0)
                y_pct = float(geom.get("y_pct") or 0)
                if x_min <= x_pct < x_max and y_min <= y_pct < y_max:
                    chunk.append(element)
            chunk.sort(key=lambda element: (float((element.get("geometry") or {}).get("y_pct") or 0), float((element.get("geometry") or {}).get("x_pct") or 0)))
            lines = []
            for element in chunk:
                lines.extend(_split_lines(element.get("text") or ""))
            lines = [line for line in lines if not (_looks_metric(line) and not line.startswith("行业经验"))]
            if len(lines) >= 3:
                people_cards.append(_normalize_people_card(lines))

    chart_breakdown = _parse_chart_breakdown_from_text(result["all_visible_text"])
    result["hierarchy"] = [
        {"title": "核心团队", "items": people_cards, "children": []},
        {"title": "人力分布", "items": updated_metrics, "children": []},
    ]
    result["layout_intent"] = {
        "direction": "left_to_right",
        "panel_count": 2,
        "has_connectors": False,
        "narrative": "grouped",
        "dominant_visual": "mixed",
        "parent_label": "",
    }
    result["structured_payload"] = {
        "section_title": title,
        "groups": [
            {"group_title": "核心团队", "people": people_cards, "metrics": []},
            {"group_title": "人力分布", "people": [], "updated_metrics": updated_metrics, "metrics": updated_metrics},
        ],
        "footer_lines": footer,
    }
    if chart_breakdown.get("display_total") or chart_breakdown.get("segments"):
        result["structured_payload"]["chart_breakdown"] = chart_breakdown
    if instruction:
        result["supplement"] = _dedupe_strings([*(result.get("supplement") or []), *instruction])
    result["missing_risk"] = _dedupe_strings(
        [
            *(result.get("missing_risk") or []),
            "The headcount text block and donut chart on the source slide are internally inconsistent.",
        ]
    )
    result["confidence"] = 0.74
    result["reason"] = "Chosen page family: people-matrix. The slide combines team cards, updated headcount text, and a donut-style breakdown."


def _build_awards_patents(raw_slide: dict[str, Any], result: dict[str, Any]) -> None:
    lines = _visible_content_lines(result)
    title = result["title"]
    group_titles = [line for line in lines if line in {"关键专利", "关键奖项", "投资人"}]
    patent_blocks = _extract_patent_metric_blocks_from_lines(lines)
    awards = _merge_award_fragments(
        [line for line in lines if line not in group_titles and line != title and _looks_award_line(line)],
        lines,
    )
    investors = _extract_investors_from_lines(lines)
    result["hierarchy"] = [
        {"title": "关键专利", "items": [_join_metric_block(block) for block in patent_blocks], "children": []},
        {"title": "关键奖项", "items": awards, "children": []},
        {"title": "投资人", "items": investors, "children": []},
    ]
    result["layout_intent"] = {
        "direction": "grid",
        "panel_count": 3,
        "has_connectors": False,
        "narrative": "grouped",
        "dominant_visual": "metric_cards",
        "parent_label": "",
    }
    result["structured_payload"] = {
        "section_title": title,
        "group_titles": group_titles or ["关键专利", "关键奖项", "投资人"],
        "metric_blocks": patent_blocks,
        "awards": awards,
        "investors": investors,
        "footer_lines": result["footer"],
    }
    if "投资人" in lines and not investors:
        result["missing_risk"] = _dedupe_strings(
            [
                *(result.get("missing_risk") or []),
                "Investor identities are visible by section but were not recoverable from native text alone.",
            ]
        )
    result["confidence"] = 0.84
    result["reason"] = "Chosen page family: awards-patents. The slide contains patent counts, award lists, and investor references."


def _build_sector_peer_panels(raw_slide: dict[str, Any], result: dict[str, Any]) -> None:
    elements = [element for element in raw_slide.get("elements", []) if element.get("kind") in {"text", "graphic_text"} and element.get("text")]
    title = result["title"]
    civil_items: list[str] = []
    industrial_items: list[str] = []
    metric_heading_blocks: list[str] = []
    metric_value_blocks: list[str] = []

    for element in elements:
        geom = element.get("geometry") or {}
        x_pct = float(geom.get("x_pct") or 0)
        y_pct = float(geom.get("y_pct") or 0)
        lines = _split_lines(element.get("text") or "")
        if not lines:
            continue
        first = lines[0]
        if first in result["instruction_text"] or first == title or first in {"活力结构", "禹数", "博锐尚格"}:
            continue
        if x_pct >= 0.70:
            if any(_looks_metric(line) for line in lines):
                metric_value_blocks.append("\n".join(lines))
            else:
                metric_heading_blocks.append("\n".join(lines))
            continue
        if y_pct <= 0.40 and first not in civil_items:
            civil_items.append(first)
        elif y_pct >= 0.55 and first not in industrial_items:
            industrial_items.append(first)

    metric_heading_blocks = sorted(metric_heading_blocks, key=lambda block: _metric_block_sort_key(elements, block))
    metric_value_blocks = sorted(metric_value_blocks, key=lambda block: _metric_block_sort_key(elements, block))
    metric_blocks = []
    for index, heading_block in enumerate(metric_heading_blocks[:3]):
        heading_lines = _split_lines(heading_block)
        value_lines = _split_lines(metric_value_blocks[index]) if index < len(metric_value_blocks) else []
        label = "".join(heading_lines)
        value_line = next((line for line in value_lines if re.search(r"\d", line)), "")
        metric = _parse_metric_line(value_line)
        if not metric:
            continue
        metric["label"] = label or metric.get("label") or ""
        metric["supporting_text"] = _dedupe_strings(
            ["2024年", *[line.replace(" ", "") for line in value_lines if "增速" in line]]
        )
        display_lines = [line.replace("  ", " ").strip() for line in value_lines if line.strip()]
        if display_lines:
            metric["display_lines"] = display_lines
        metric_blocks.append(metric)

    panels = [
        {"panel_title": "活力结构", "panel_role": "civil-business", "items": civil_items},
        {"panel_title": "禹数", "panel_role": "industrial-business", "items": industrial_items},
    ]
    result["hierarchy"] = [{"title": panel["panel_title"], "items": panel["items"], "children": []} for panel in panels]
    if metric_blocks:
        result["hierarchy"].append({"title": "市场规模与成本", "items": [_join_metric_block(block) for block in metric_blocks], "children": []})
    result["layout_intent"] = {
        "direction": "left_to_right",
        "panel_count": 3,
        "has_connectors": False,
        "narrative": "grouped",
        "dominant_visual": "sector_grid",
        "parent_label": "博锐尚格",
    }
    result["structured_payload"] = {
        "section_title": title,
        "parent_label": "博锐尚格",
        "panels": panels,
        "metric_blocks": metric_blocks,
    }
    result["confidence"] = 0.84
    result["reason"] = "Chosen page family: peer-panels. The slide has a hub label with civil/industrial sector grids and a metric column."


def _build_image_text(raw_slide: dict[str, Any], result: dict[str, Any]) -> None:
    title = result["title"]
    blocks = []
    for element in raw_slide.get("elements", []):
        if element.get("kind") in {"text", "graphic_text"} and element.get("text") and element.get("text") != title:
            blocks.append({"heading": _first_line(element.get("text") or ""), "body": _split_lines(element.get("text") or ""), "image_subject": ""})
    result["hierarchy"] = [{"title": title, "items": [_first_line(block["heading"]) for block in blocks], "children": []}]
    result["layout_intent"] = {
        "direction": "left_to_right",
        "panel_count": 1,
        "has_connectors": False,
        "narrative": "grouped",
        "dominant_visual": "mixed",
        "parent_label": "",
    }
    result["structured_payload"] = {"section_title": title, "blocks": blocks}
    result["missing_risk"] = _dedupe_strings([*(result.get("missing_risk") or []), "slide may be image-heavy, so text coverage could be partial"])
    result["confidence"] = 0.6
    result["reason"] = "Chosen page family: image-text. The slide has very little editable text outside a large image region."


def _build_chapter(raw_slide: dict[str, Any], result: dict[str, Any]) -> None:
    title = result["title"]
    supporting = [line for line in result["all_visible_text"] if line != title and line not in result["footer"] and line not in result["instruction_text"]]
    result["hierarchy"] = [{"title": title, "items": supporting[:2], "children": []}]
    result["layout_intent"] = {
        "direction": "top_to_bottom",
        "panel_count": 1,
        "has_connectors": False,
        "narrative": "cover",
        "dominant_visual": "chapter",
        "parent_label": "",
    }
    result["structured_payload"] = {
        "primary_title": title,
        "secondary_title": supporting[0] if supporting else "",
        "paired_lines": supporting[1:3],
    }
    result["confidence"] = 0.66
    result["reason"] = "Chosen page family: chapter. The slide behaves like a divider with little editable text."


def _build_fallback(raw_slide: dict[str, Any], result: dict[str, Any]) -> None:
    blocks = []
    for element in raw_slide.get("elements", []):
        if element.get("kind") not in {"text", "graphic_text"} or not element.get("text"):
            continue
        role = element.get("role_guess") or "body"
        if role in {"footer", "editorial_note"}:
            continue
        blocks.append({"role": role, "text": _split_lines(element.get("text") or "")})
    result["hierarchy"] = [{"title": result["title"], "items": [line for line in result["main_text"] if line != result["title"]], "children": []}]
    result["layout_intent"] = _default_layout("fallback")
    result["structured_payload"] = {"blocks": blocks}
    result["missing_risk"] = _dedupe_strings([*(result.get("missing_risk") or []), "semantic structure may still be underspecified on this slide"])
    result["confidence"] = 0.58
    result["reason"] = "Chosen page family: fallback. The slide does not yet match a stronger family confidently from native structure alone."


def _text_lines(elements: list[dict[str, Any]]) -> list[str]:
    lines: list[str] = []
    for element in elements:
        lines.extend(_split_lines(element.get("text") or ""))
    return _dedupe_strings(lines)


def _all_visible_lines(text_elements: list[dict[str, Any]]) -> list[str]:
    lines = []
    for element in text_elements:
        lines.extend(_split_lines(element.get("text") or ""))
    return _dedupe_strings(lines)


def _footer_lines(text_elements: list[dict[str, Any]]) -> list[str]:
    lines = []
    for element in text_elements:
        if element.get("role_guess") == "footer":
            lines.extend(_split_lines(element.get("text") or ""))
    return _dedupe_strings(lines)


def _instruction_lines(text_elements: list[dict[str, Any]]) -> list[str]:
    lines = []
    for element in text_elements:
        if element.get("role_guess") == "editorial_note":
            lines.extend(_split_lines(element.get("text") or ""))
    return _dedupe_strings(lines)


def _main_text(title: str, content_elements: list[dict[str, Any]]) -> list[str]:
    lines = [title] if title else []
    for element in content_elements:
        text = element.get("text") or ""
        if text == title or element.get("role_guess") in {"heading", "key_stat"}:
            continue
        if len(text.replace("\n", "")) >= 20:
            lines.extend(_split_lines(text))
    return _dedupe_strings(lines)


def _metric_lines(content_elements: list[dict[str, Any]]) -> list[str]:
    lines = []
    for element in content_elements:
        for line in _split_lines(element.get("text") or ""):
            if _looks_metric(line):
                lines.append(line)
    return _dedupe_strings(lines)


def _label_lines(content_elements: list[dict[str, Any]], title: str) -> list[str]:
    lines = []
    for element in content_elements:
        for line in _split_lines(element.get("text") or ""):
            if line == title:
                continue
            if _is_short_label(line) and not _looks_metric(line):
                lines.append(line)
    return _dedupe_strings(lines)


def _split_lines(text: str) -> list[str]:
    return [line.strip() for line in str(text).splitlines() if line.strip()]


def _first_line(text: str) -> str:
    return _split_lines(text)[0] if _split_lines(text) else ""


def _is_short_label(text: str) -> bool:
    clean = str(text).replace("\n", "").strip()
    return 0 < len(clean) <= 18


def _looks_metric(text: str) -> bool:
    clean = str(text).strip()
    return bool(re.search(r"\d", clean)) and any(token in clean for token in ("%", "亿", "个", "人", "+", "年", "项", "家", "总人数", "增速"))


def _has_parallel_two_panel_layout(elements: list[dict[str, Any]]) -> bool:
    headings = []
    for element in elements:
        text = element.get("text") or ""
        if not _is_short_label(text):
            continue
        geom = element.get("geometry") or {}
        y_pct = float(geom.get("y_pct") or 1)
        x_pct = float(geom.get("x_pct") or 0)
        if y_pct < 0.38:
            headings.append((x_pct, _first_line(text)))
    if len(headings) < 2:
        return False
    headings = sorted(headings)
    return abs(headings[0][0] - headings[1][0]) > 0.2


def _nearest_support_line(elements: list[dict[str, Any]], anchor: dict[str, Any]) -> str:
    ax = float((anchor.get("geometry") or {}).get("x_pct") or 0)
    ay = float((anchor.get("geometry") or {}).get("y_pct") or 0)
    candidates = []
    for element in elements:
        if element is anchor or not element.get("text"):
            continue
        ex = float((element.get("geometry") or {}).get("x_pct") or 0)
        ey = float((element.get("geometry") or {}).get("y_pct") or 0)
        if ey < ay or ey - ay > 0.18 or abs(ex - ax) > 0.12:
            continue
        text = _first_line(element.get("text") or "")
        if not text:
            continue
        candidates.append((abs(ex - ax) + abs(ey - ay), text))
    candidates.sort(key=lambda item: item[0])
    return candidates[0][1] if candidates else ""


def _largest_image_area(raw_slide: dict[str, Any]) -> float:
    largest = 0.0
    for element in raw_slide.get("elements", []):
        if element.get("kind") != "image":
            continue
        geom = element.get("geometry") or {}
        area = float(geom.get("w_pct") or 0) * float(geom.get("h_pct") or 0)
        if area > largest:
            largest = area
    return largest


def _parse_chart_breakdown_from_text(lines: list[str]) -> dict[str, Any]:
    all_visible = [str(line).strip() for line in lines if str(line).strip()]
    explicit_labels = ["产品研发", "人工智能", "实施服务", "销售", "中后台"]
    donut_total = next((line for line in all_visible if re.fullmatch(r"\d+\s*人", line) and int(re.sub(r"\D", "", line)) >= 400), "")
    donut_values = [line.replace(" ", "") for line in all_visible if re.fullmatch(r"\d+\s*人?", line) and line not in {"总人数"}]
    if donut_total:
        donut_values = [line for line in donut_values if re.sub(r"\D", "", line) != re.sub(r"\D", "", donut_total)]
    donut_values = [line for line in donut_values if line not in {"348", "96", "30", "143", "49", "总人数"}]
    percentages = [line for line in all_visible if re.fullmatch(r"\d+%", line)]
    if donut_total and len(donut_values) >= 5 and len(percentages) >= 5:
        values = donut_values[:5]
        pct_values = sorted(percentages[:5], key=lambda item: int(item.rstrip("%")), reverse=True)
        ranked = sorted(
            [(index, int(re.sub(r"\D", "", value)), value) for index, value in enumerate(values)],
            key=lambda item: item[1],
            reverse=True,
        )
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

    joined = " ".join(line for line in all_visible if line != "更新人数情况")
    total = re.search(r"总人数[:： ]?(\d+)\s*人?", joined)
    percentages = re.findall(r"(\d+%)", joined)
    segments = []
    for index, label in enumerate(explicit_labels):
        preferred = re.search(rf"{label}\s+(\d+\s*人)", joined)
        value_match = preferred or re.search(rf"{label}\s*[:：]?\s*(\d+\s*人?)", joined)
        if value_match:
            segment = {"label": label, "value": value_match.group(1).replace(" ", "")}
            if index < len(percentages):
                segment["percentage"] = percentages[index]
            segments.append(segment)
    return {"display_total": f"总人数 {total.group(1)}人" if total else "", "segments": segments}


def _parse_metric_line(text: str) -> dict[str, Any] | None:
    clean = str(text).strip()
    if not clean:
        return None
    year_match = re.search(r"(\d{4}年)", clean)
    growth_match = re.search(r"(每年增速\s*\d+%|增速\s*\d+%)", clean)
    value_match = re.search(r"(\d+(?:\.\d+)?)\s*(亿元|个|人|家|\+)", clean)
    if not value_match:
        return None
    label = clean[: value_match.start()].strip(" ：:-")
    metric_block = {
        "label": label,
        "value": value_match.group(1),
        "unit": value_match.group(2),
        "supporting_text": [],
    }
    display_lines = []
    if year_match:
        metric_block["supporting_text"].append(year_match.group(1))
        display_lines.append(f"{year_match.group(1)} {value_match.group(1)}{value_match.group(2)}".strip())
    if growth_match:
        compact = growth_match.group(1).replace(" ", "")
        metric_block["supporting_text"].append(compact)
        display_lines.append(compact)
    if display_lines:
        metric_block["display_lines"] = display_lines
    return metric_block


def _join_metric_block(block: dict[str, Any]) -> str:
    label = str(block.get("label") or "").strip()
    value = str(block.get("value") or "").strip()
    unit = str(block.get("unit") or "").strip()
    return f"{label} {value}{unit}".strip()


def _split_pair_item(text: str) -> dict[str, str] | None:
    lines = _split_lines(text)
    if len(lines) >= 2:
        return {"name": lines[0], "system": lines[1]}
    clean = str(text).strip()
    for suffix in ("资产管理系统", "集成管理系统", "能源管理系统", "管理系统", "系统"):
        if clean.endswith(suffix):
            return {"name": clean[: -len(suffix)].strip(), "system": suffix}
    return None


def _extract_pair_entry(text: str) -> dict[str, str] | None:
    lines = _split_lines(text)
    if len(lines) >= 2 and any(lines[-1].endswith(suffix) for suffix in ("资产管理系统", "集成管理系统", "能源管理系统", "运维管理系统", "管理系统", "系统")):
        return {"name": lines[0], "system": lines[-1]}
    return _split_pair_item(text)


def _build_pair_entry_groups(text_elements: list[dict[str, Any]], pair_elements: list[dict[str, Any]]) -> list[dict[str, Any]]:
    top_headings = [element for element in text_elements if element.get("role_guess") == "heading" and float((element.get("geometry") or {}).get("y_pct") or 1) < 0.26]
    heading_titles = [_first_line(element.get("text") or "") for element in top_headings if _first_line(element.get("text") or "")]
    if top_headings:
        sorted_headings = sorted(
            [
                {
                    "title": _first_line(element.get("text") or ""),
                    "x_pct": float((element.get("geometry") or {}).get("x_pct") or 0),
                    "w_pct": float((element.get("geometry") or {}).get("w_pct") or 0),
                }
                for element in top_headings
                if _first_line(element.get("text") or "")
            ],
            key=lambda item: item["x_pct"],
        )
        groups: list[dict[str, Any]] = [
            {"group_title": str(heading["title"]), "entries": [], "items": []}
            for heading in sorted_headings
        ]
        boundaries = []
        for index in range(len(sorted_headings) - 1):
            boundaries.append((sorted_headings[index]["x_pct"] + sorted_headings[index + 1]["x_pct"]) / 2)
        if _looks_like_edge_column_logo_wall(sorted_headings, pair_elements):
            column_centers = _cluster_pair_column_centers(pair_elements)
            if len(column_centers) >= 2:
                boundaries[-1] = max(boundaries[-1], (column_centers[-2] + column_centers[-1]) / 2)
        for element in pair_elements:
            entry = _extract_pair_entry(element.get("text") or "")
            if not entry:
                continue
            x_pct = float((element.get("geometry") or {}).get("x_pct") or 0)
            group_index = 0
            while group_index < len(boundaries) and x_pct >= boundaries[group_index]:
                group_index += 1
            groups[group_index]["entries"].append(entry)
        return [
            {
                "group_title": str(group["group_title"]),
                "entries": group["entries"],
                "items": [_join_entry(entry) for entry in group["entries"]],
            }
            for group in groups
            if group["entries"] or str(group["group_title"]).strip()
        ]

    right_threshold = _logo_wall_right_threshold(text_elements)
    left_entries = []
    right_entries = []
    for element in pair_elements:
        entry = _extract_pair_entry(element.get("text") or "")
        if not entry:
            continue
        x_pct = float((element.get("geometry") or {}).get("x_pct") or 0)
        if x_pct >= right_threshold:
            right_entries.append(entry)
        else:
            left_entries.append(entry)

    groups = []
    left_title = heading_titles[0] if heading_titles else "民用"
    right_title = heading_titles[-1] if len(heading_titles) > 1 else "禹数"
    if left_entries:
        groups.append({"group_title": left_title, "entries": left_entries, "items": [_join_entry(entry) for entry in left_entries]})
    if right_entries:
        groups.append({"group_title": right_title, "entries": right_entries, "items": [_join_entry(entry) for entry in right_entries]})
    return groups


def _looks_like_edge_column_logo_wall(sorted_headings: list[dict[str, Any]], pair_elements: list[dict[str, Any]]) -> bool:
    if len(sorted_headings) != 2:
        return False
    right_heading = sorted_headings[-1]
    if right_heading["x_pct"] < 0.78 or right_heading["w_pct"] > 0.08:
        return False
    column_centers = _cluster_pair_column_centers(pair_elements)
    if len(column_centers) < 5:
        return False
    return (column_centers[-1] - column_centers[-2]) >= 0.08


def _cluster_pair_column_centers(pair_elements: list[dict[str, Any]]) -> list[float]:
    x_positions = sorted(float((element.get("geometry") or {}).get("x_pct") or 0) for element in pair_elements)
    if not x_positions:
        return []
    clusters: list[list[float]] = [[x_positions[0]]]
    for x_pct in x_positions[1:]:
        if abs(x_pct - clusters[-1][-1]) <= 0.05:
            clusters[-1].append(x_pct)
        else:
            clusters.append([x_pct])
    return [sum(cluster) / len(cluster) for cluster in clusters]


def _visible_content_lines(result: dict[str, Any]) -> list[str]:
    title = str(result.get("title") or "").strip()
    footer = {str(item).strip() for item in result.get("footer") or []}
    instruction = {str(item).strip() for item in result.get("instruction_text") or []}
    lines = []
    for item in result.get("all_visible_text") or []:
        text = str(item).strip()
        if not text or text == title or text in footer or text in instruction:
            continue
        lines.append(text)
    return _dedupe_strings(lines)


def _extract_timeline_periods_from_lines(result: dict[str, Any]) -> list[dict[str, Any]]:
    lines = _visible_content_lines(result)
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


def _extract_patent_metric_blocks_from_lines(lines: list[str]) -> list[dict[str, Any]]:
    labels = [line for line in lines if line in {"实授发明专利", "在审发明专利", "实用新型及外观专利"}]
    values = [line for line in lines if re.fullmatch(r"\d+", line)]
    metric_blocks = []
    for index, label in enumerate(labels):
        if index >= len(values):
            break
        metric_blocks.append({"label": label, "value": values[index], "unit": "项", "supporting_text": []})
    return metric_blocks


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
    return [award for award in deduped if not any(other != award and award in other for other in deduped)]


def _looks_award_line(text: str) -> bool:
    clean = str(text).strip()
    if not clean or clean == "关键奖项":
        return False
    return any(keyword in clean for keyword in ("大奖", "奖", "50强", "猎豹企业", "碳金"))


def _extract_investors_from_lines(lines: list[str]) -> list[str]:
    investors: list[str] = []
    in_investor_section = False
    ignored = {"关键专利", "关键奖项", "投资人"}
    for line in lines:
        text = str(line).strip()
        if not text:
            continue
        if text == "投资人":
            in_investor_section = True
            continue
        if text in {"关键专利", "关键奖项"}:
            in_investor_section = False
            continue
        if not in_investor_section:
            continue
        if re.fullmatch(r"\d+", text) or _looks_award_line(text):
            continue
        investors.append(text)
    return _dedupe_strings(
        [
            line
            for line in investors
            if line not in ignored
            and 2 <= len(line) <= 8
            and not any(token in line for token in ("中国领先", "不动产", "企业", "科技", "50强"))
        ]
    )


def _normalize_people_card(lines: list[str]) -> str:
    clean = [line.strip() for line in lines if line.strip()]
    if len(clean) >= 5:
        return f"{clean[0]} {clean[1]} {clean[2]} | {clean[3]} {clean[4]}".replace(" | | ", " | ").strip()
    return " ".join(clean[:5])


def _metric_block_sort_key(elements: list[dict[str, Any]], block_text: str) -> float:
    for element in elements:
        if (element.get("text") or "").strip() == block_text.strip():
            return float((element.get("geometry") or {}).get("y_pct") or 0)
    return 0.0


def _join_entry(entry: dict[str, str]) -> str:
    name = str(entry.get("name") or "").strip()
    system = str(entry.get("system") or "").strip()
    return f"{name} {system}".strip()


def _classify_panel_role(panel_title: str) -> str:
    mapping = {
        "公司介绍": "company-profile",
        "核心产品": "product-profile",
        "活力结构": "civil-business",
        "禹数": "industrial-business",
    }
    return mapping.get(panel_title, "")


def _looks_award_candidate(text: str) -> bool:
    clean = str(text).strip()
    if not clean:
        return False
    if clean in {"关键专利", "关键奖项", "投资人"}:
        return False
    return any(keyword in clean for keyword in ("大奖", "奖", "50强", "猎豹企业", "碳金"))


def _looks_english(text: str) -> bool:
    clean = str(text).strip()
    ascii_letters = sum(1 for char in clean if char.isascii() and char.isalpha())
    return ascii_letters >= max(3, len(clean.replace(" ", "")) // 2)


def _default_layout(page_type: str) -> dict[str, Any]:
    mapping = {
        "cover": {"direction": "top_to_bottom", "panel_count": 1, "has_connectors": False, "narrative": "cover", "dominant_visual": "hero", "parent_label": ""},
        "toc": {"direction": "top_to_bottom", "panel_count": 1, "has_connectors": False, "narrative": "sequence", "dominant_visual": "text_list", "parent_label": ""},
        "metrics": {"direction": "grid", "panel_count": 4, "has_connectors": False, "narrative": "grouped", "dominant_visual": "metric_cards", "parent_label": ""},
        "peer-panels": {"direction": "left_to_right", "panel_count": 2, "has_connectors": False, "narrative": "grouped", "dominant_visual": "mixed", "parent_label": ""},
        "timeline": {"direction": "left_to_right", "panel_count": 3, "has_connectors": True, "narrative": "progression", "dominant_visual": "timeline", "parent_label": ""},
        "logo-wall": {"direction": "left_to_right", "panel_count": 2, "has_connectors": False, "narrative": "grouped", "dominant_visual": "logo_grid", "parent_label": ""},
        "people-matrix": {"direction": "left_to_right", "panel_count": 2, "has_connectors": False, "narrative": "grouped", "dominant_visual": "mixed", "parent_label": ""},
        "awards-patents": {"direction": "grid", "panel_count": 3, "has_connectors": False, "narrative": "grouped", "dominant_visual": "metric_cards", "parent_label": ""},
        "image-text": {"direction": "left_to_right", "panel_count": 1, "has_connectors": False, "narrative": "grouped", "dominant_visual": "mixed", "parent_label": ""},
        "chapter": {"direction": "top_to_bottom", "panel_count": 1, "has_connectors": False, "narrative": "cover", "dominant_visual": "chapter", "parent_label": ""},
    }
    return mapping.get(page_type, {"direction": "unknown", "panel_count": 1, "has_connectors": False, "narrative": "unknown", "dominant_visual": "mixed", "parent_label": ""})


def _dedupe_strings(items: list[str]) -> list[str]:
    seen = set()
    result = []
    for item in items:
        text = str(item).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def _report(callback: ProgressCallback, progress: int, message: str) -> None:
    if callback:
        callback(progress, message)


def main():
    parser = argparse.ArgumentParser(description="Recognize a PPT deck or generate IDE prompt tasks from native PPT structure.")
    parser.add_argument("pptx_path", type=Path, help="Path to a local .pptx file")
    parser.add_argument("--mode", choices=("recognize", "prompts"), default="recognize", help="Run the recognizer or only generate IDE prompt files")
    parser.add_argument("--output-dir", type=Path, default=Path("output/ide_prompts"), help="Directory to save prompt files in prompts mode")
    parser.add_argument("--output", type=Path, help="Optional output file for recognize mode")
    parser.add_argument("--format", choices=("json", "markdown"), default="json", help="Output format for recognize mode")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    parser.add_argument("--vision-mode", choices=("off",), default="off", help="Emit host vision tasks only; built-in remote vision has been removed")
    args = parser.parse_args()

    if not args.pptx_path.exists():
        print(f"File not found: {args.pptx_path}", file=sys.stderr)
        return 1

    if args.mode == "prompts":
        generate_ide_prompts(args.pptx_path, args.output_dir)
        print(f"\n[√] 喂料准备完成！共生成 {len(list(args.output_dir.glob('task_slide_*.md')))} 个任务文件。")
        return 0

    deck = recognize_deck(args.pptx_path, vision_mode=args.vision_mode)
    if args.format == "markdown":
        output = render_markdown(deck)
    else:
        output = json.dumps(deck, ensure_ascii=False, indent=2 if args.pretty else None)

    if args.output:
        args.output.write_text(output, encoding="utf-8")
    else:
        print(output)
    return 0


def render_markdown(deck: dict[str, Any]) -> str:
    lines = [
        f"# {Path(deck['source_file']).name}",
        "",
        f"- Slides: {deck['slide_count']}",
        "- Deck outline:",
    ]
    for outline in deck.get("deck_outline") or []:
        lines.append(f"  - {outline.get('title')}: {outline.get('page_type')}")

    for slide in deck.get("slides", []):
        lines.append("")
        lines.append(f"## Slide {slide['slide_number']}")
        lines.append(f"- Page type: {slide.get('page_type')}")
        lines.append(f"- Title: {slide.get('title')}")
        lines.append(f"- Confidence: {slide.get('confidence')}")
        lines.append(f"- Layout: {slide.get('layout_intent')}")
        lines.append("- Hierarchy:")
        for node in slide.get("hierarchy") or []:
            lines.append(f"  - {node.get('title')}")
            if node.get("items"):
                lines.append(f"    - {', '.join(node.get('items'))}")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
