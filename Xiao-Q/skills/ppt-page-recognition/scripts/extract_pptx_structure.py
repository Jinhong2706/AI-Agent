#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import posixpath
import re
import statistics
import sys
import zipfile
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET


NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "c": "http://schemas.openxmlformats.org/drawingml/2006/chart",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}

REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
ODREL_NS = NS["r"]

AGENDA_TITLE_RE = re.compile(r"(agenda|contents|table of contents|目录)", re.IGNORECASE)
AGENDA_ITEM_RE = re.compile(
    r"^\s*(?:\d+[.)、．]|\(?[一二三四五六七八九十]+\)?[、.．]|[IVX]+\.)\s*(.+)$",
    re.IGNORECASE,
)
EDITORIAL_RE = re.compile(
    r"(仅用于|logo参考|放至|放到|请替换|请更新|待补|示意|画一张|可以通过|已更新|for reference|placeholder)",
    re.IGNORECASE,
)
URL_RE = re.compile(r"(https?://|www\.)", re.IGNORECASE)
NUMBERISH_RE = re.compile(r"^[\d\s+%.,，/:-]+(?:[A-Za-z\u4e00-\u9fff]+)?$")
REPEATED_LABEL_RE = re.compile(r"^[A-Za-z0-9\u4e00-\u9fff _|/.-]{2,32}$")


def local_name(tag: str) -> str:
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def qn(prefix: str, name: str) -> str:
    return f"{{{NS[prefix]}}}{name}"


def text_content(node: ET.Element | None, path: str) -> str:
    if node is None:
        return ""
    value = node.attrib.get(path, "")
    return value.strip()


def clean_text(value: str) -> str:
    value = value.replace("\xa0", " ").replace("\u200b", "")
    value = value.replace("\r", "\n")
    value = re.sub(r"[ \t]+", " ", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    return value.strip()


def to_number(value: str | None) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except ValueError:
        return None


def safe_float(value: float | None) -> float | None:
    if value is None:
        return None
    return round(float(value), 4)


def median_or_none(values: list[float]) -> float | None:
    if not values:
        return None
    return float(statistics.median(values))


def normalize_label(text: str) -> str:
    lowered = re.sub(r"\s+", "", text.strip().lower())
    return re.sub(r"[^0-9a-z\u4e00-\u9fff]+", "", lowered)


def is_probable_footer(text: str) -> bool:
    compact = normalize_label(text)
    return bool(URL_RE.search(text)) or compact in {
        "wwwpersagycom",
        "persagy",
    }


def is_editorial_text(text: str) -> bool:
    return bool(EDITORIAL_RE.search(text))


@dataclass
class Transform:
    base_x: float = 0.0
    base_y: float = 0.0
    scale_x: float = 1.0
    scale_y: float = 1.0

    def apply_box(self, x: int, y: int, cx: int, cy: int) -> tuple[float, float, float, float]:
        return (
            self.base_x + self.scale_x * x,
            self.base_y + self.scale_y * y,
            self.scale_x * cx,
            self.scale_y * cy,
        )


class PptxExtractor:
    def __init__(self, pptx_path: Path, include_notes: bool = False) -> None:
        self.pptx_path = pptx_path
        self.include_notes = include_notes
        self.zf = zipfile.ZipFile(pptx_path)
        self.presentation = self._read_xml("ppt/presentation.xml")
        self.presentation_rels = self._load_relationships("ppt/presentation.xml")
        self.slide_size = self._extract_slide_size()

    def _read_xml(self, archive_path: str) -> ET.Element:
        return ET.fromstring(self.zf.read(archive_path))

    def _load_relationships(self, source_path: str) -> dict[str, dict[str, str]]:
        rel_path = posixpath.join(
            posixpath.dirname(source_path),
            "_rels",
            posixpath.basename(source_path) + ".rels",
        )
        if rel_path not in self.zf.namelist():
            return {}
        root = self._read_xml(rel_path)
        relationships: dict[str, dict[str, str]] = {}
        for rel in root:
            if local_name(rel.tag) != "Relationship":
                continue
            rel_id = rel.attrib.get("Id")
            target = rel.attrib.get("Target", "")
            if not rel_id or not target:
                continue
            if rel.attrib.get("TargetMode") == "External":
                resolved = target
            else:
                resolved = posixpath.normpath(posixpath.join(posixpath.dirname(source_path), target))
            relationships[rel_id] = {
                "type": rel.attrib.get("Type", ""),
                "target": resolved,
            }
        return relationships

    def _extract_slide_size(self) -> dict[str, int]:
        slide_size = self.presentation.find("p:sldSz", NS)
        if slide_size is None:
            return {"cx": 0, "cy": 0}
        return {
            "cx": int(slide_size.attrib.get("cx", "0")),
            "cy": int(slide_size.attrib.get("cy", "0")),
        }

    def _slide_paths_in_order(self) -> list[str]:
        slide_list = self.presentation.find("p:sldIdLst", NS)
        if slide_list is None:
            return []
        ordered: list[str] = []
        for slide_id in slide_list:
            rid = slide_id.attrib.get(f"{{{ODREL_NS}}}id")
            if not rid:
                continue
            rel = self.presentation_rels.get(rid)
            if not rel:
                continue
            ordered.append(rel["target"])
        return ordered

    def _extract_geometry_dict(
        self,
        node: ET.Element,
        transform: Transform,
        xfrm_path: str,
    ) -> dict[str, float | None]:
        xfrm = node.find(xfrm_path, NS)
        if xfrm is None:
            return {
                "x": None,
                "y": None,
                "cx": None,
                "cy": None,
                "x_pct": None,
                "y_pct": None,
                "w_pct": None,
                "h_pct": None,
            }
        off = xfrm.find("a:off", NS)
        ext = xfrm.find("a:ext", NS)
        if off is None or ext is None:
            return {
                "x": None,
                "y": None,
                "cx": None,
                "cy": None,
                "x_pct": None,
                "y_pct": None,
                "w_pct": None,
                "h_pct": None,
            }
        x = int(off.attrib.get("x", "0"))
        y = int(off.attrib.get("y", "0"))
        cx = int(ext.attrib.get("cx", "0"))
        cy = int(ext.attrib.get("cy", "0"))
        abs_x, abs_y, abs_cx, abs_cy = transform.apply_box(x, y, cx, cy)
        slide_cx = self.slide_size["cx"] or 1
        slide_cy = self.slide_size["cy"] or 1
        return {
            "x": safe_float(abs_x),
            "y": safe_float(abs_y),
            "cx": safe_float(abs_cx),
            "cy": safe_float(abs_cy),
            "x_pct": safe_float(abs_x / slide_cx),
            "y_pct": safe_float(abs_y / slide_cy),
            "w_pct": safe_float(abs_cx / slide_cx),
            "h_pct": safe_float(abs_cy / slide_cy),
        }

    def _next_transform(self, group_node: ET.Element, transform: Transform) -> Transform:
        xfrm = group_node.find("./p:grpSpPr/a:xfrm", NS)
        if xfrm is None:
            return transform
        off = xfrm.find("a:off", NS)
        ext = xfrm.find("a:ext", NS)
        child_off = xfrm.find("a:chOff", NS)
        child_ext = xfrm.find("a:chExt", NS)
        if off is None or ext is None or child_off is None or child_ext is None:
            return transform

        off_x = int(off.attrib.get("x", "0"))
        off_y = int(off.attrib.get("y", "0"))
        ext_x = int(ext.attrib.get("cx", "0"))
        ext_y = int(ext.attrib.get("cy", "0"))
        ch_off_x = int(child_off.attrib.get("x", "0"))
        ch_off_y = int(child_off.attrib.get("y", "0"))
        ch_ext_x = int(child_ext.attrib.get("cx", "0")) or 1
        ch_ext_y = int(child_ext.attrib.get("cy", "0")) or 1

        return Transform(
            base_x=transform.base_x + transform.scale_x * (off_x - ch_off_x),
            base_y=transform.base_y + transform.scale_y * (off_y - ch_off_y),
            scale_x=transform.scale_x * (ext_x / ch_ext_x),
            scale_y=transform.scale_y * (ext_y / ch_ext_y),
        )

    def _extract_non_visual(self, node: ET.Element) -> dict[str, Any]:
        paths = {
            "sp": "./p:nvSpPr/p:cNvPr",
            "pic": "./p:nvPicPr/p:cNvPr",
            "graphicFrame": "./p:nvGraphicFramePr/p:cNvPr",
            "grpSp": "./p:nvGrpSpPr/p:cNvPr",
            "cxnSp": "./p:nvCxnSpPr/p:cNvPr",
        }
        entry = node.find(paths.get(local_name(node.tag), ""), NS)
        if entry is None:
            return {"shape_id": None, "name": None, "alt_text": None}
        return {
            "shape_id": to_number(entry.attrib.get("id")),
            "name": entry.attrib.get("name"),
            "alt_text": entry.attrib.get("descr") or entry.attrib.get("title"),
        }

    def _extract_placeholder(self, node: ET.Element) -> dict[str, Any] | None:
        placeholder = node.find("./p:nvSpPr/p:nvPr/p:ph", NS)
        if placeholder is None:
            return None
        return {
            "type": placeholder.attrib.get("type"),
            "idx": to_number(placeholder.attrib.get("idx")),
            "size": placeholder.attrib.get("sz"),
        }

    def _extract_paragraph(self, para: ET.Element) -> dict[str, Any] | None:
        text_parts: list[str] = []
        font_sizes: list[float] = []
        is_bold = False
        is_italic = False
        for child in para:
            child_name = local_name(child.tag)
            if child_name == "r":
                text_node = child.find("a:t", NS)
                if text_node is not None and text_node.text:
                    text_parts.append(text_node.text)
                rpr = child.find("a:rPr", NS)
                if rpr is not None:
                    size = to_number(rpr.attrib.get("sz"))
                    if size is not None:
                        font_sizes.append(size / 100.0)
                    if rpr.attrib.get("b") == "1":
                        is_bold = True
                    if rpr.attrib.get("i") == "1":
                        is_italic = True
            elif child_name == "fld":
                text_node = child.find("a:t", NS)
                if text_node is not None and text_node.text:
                    text_parts.append(text_node.text)
            elif child_name == "br":
                text_parts.append("\n")

        paragraph_text = clean_text("".join(text_parts))
        if not paragraph_text:
            return None

        ppr = para.find("a:pPr", NS)
        bullet_kind = None
        level = 0
        alignment = None
        if ppr is not None:
            level = int(ppr.attrib.get("lvl", "0"))
            alignment = ppr.attrib.get("algn")
            for child in ppr:
                marker = local_name(child.tag)
                if marker == "buChar":
                    bullet_kind = "char"
                elif marker == "buAutoNum":
                    bullet_kind = "auto"
                elif marker == "buNone":
                    bullet_kind = "none"

        end_rpr = para.find("a:endParaRPr", NS)
        if end_rpr is not None:
            size = to_number(end_rpr.attrib.get("sz"))
            if size is not None:
                font_sizes.append(size / 100.0)

        return {
            "text": paragraph_text,
            "level": level,
            "alignment": alignment,
            "bullet_kind": bullet_kind,
            "font_size_pt": safe_float(median_or_none(font_sizes)),
            "bold": is_bold,
            "italic": is_italic,
        }

    def _extract_text_shape(
        self,
        node: ET.Element,
        transform: Transform,
    ) -> dict[str, Any] | None:
        tx_body = node.find("./p:txBody", NS)
        if tx_body is None:
            return None
        paragraphs: list[dict[str, Any]] = []
        for para in tx_body.findall("a:p", NS):
            extracted = self._extract_paragraph(para)
            if extracted is not None:
                paragraphs.append(extracted)
        if not paragraphs:
            return None

        fonts = [p["font_size_pt"] for p in paragraphs if p["font_size_pt"] is not None]
        text_lines = [p["text"] for p in paragraphs]
        text = "\n".join(text_lines)
        shape = {
            "kind": "text",
            **self._extract_non_visual(node),
            "placeholder": self._extract_placeholder(node),
            "geometry": self._extract_geometry_dict(node, transform, "./p:spPr/a:xfrm"),
            "text": text,
            "text_lines": text_lines,
            "paragraphs": paragraphs,
            "line_count": len(text_lines),
            "font_size_pt_median": safe_float(median_or_none(fonts)),
            "font_size_pt_max": safe_float(max(fonts)) if fonts else None,
        }
        return shape

    def _extract_generic_shape(
        self,
        node: ET.Element,
        transform: Transform,
    ) -> dict[str, Any]:
        prst = node.find("./p:spPr/a:prstGeom", NS)
        return {
            "kind": "auto_shape",
            **self._extract_non_visual(node),
            "geometry": self._extract_geometry_dict(node, transform, "./p:spPr/a:xfrm"),
            "preset": prst.attrib.get("prst") if prst is not None else None,
        }

    def _extract_picture(
        self,
        node: ET.Element,
        slide_rels: dict[str, dict[str, str]],
        transform: Transform,
    ) -> dict[str, Any]:
        rel_id = node.find("./p:blipFill/a:blip", NS)
        target = None
        if rel_id is not None:
            embed = rel_id.attrib.get(f"{{{ODREL_NS}}}embed")
            if embed and embed in slide_rels:
                target = slide_rels[embed]["target"]
        return {
            "kind": "image",
            **self._extract_non_visual(node),
            "geometry": self._extract_geometry_dict(node, transform, "./p:spPr/a:xfrm"),
            "media_target": target,
        }

    def _extract_table(
        self,
        node: ET.Element,
        transform: Transform,
    ) -> dict[str, Any] | None:
        graphic_data = node.find("./a:graphic/a:graphicData", NS)
        if graphic_data is None:
            return None
        if not graphic_data.attrib.get("uri", "").endswith("/table"):
            return None

        table = graphic_data.find("a:tbl", NS)
        if table is None:
            return None

        rows: list[list[str]] = []
        for row in table.findall("a:tr", NS):
            cells: list[str] = []
            for cell in row.findall("a:tc", NS):
                cell_lines: list[str] = []
                for para in cell.findall("./a:txBody/a:p", NS):
                    paragraph = self._extract_paragraph(para)
                    if paragraph is not None:
                        cell_lines.append(paragraph["text"])
                cells.append("\n".join(cell_lines).strip())
            rows.append(cells)

        return {
            "kind": "table",
            **self._extract_non_visual(node),
            "geometry": self._extract_geometry_dict(node, transform, "./p:xfrm"),
            "rows": rows,
            "row_count": len(rows),
            "column_count": max((len(row) for row in rows), default=0),
            "headers": rows[0] if rows else [],
        }

    def _extract_chart(
        self,
        node: ET.Element,
        slide_rels: dict[str, dict[str, str]],
        transform: Transform,
    ) -> dict[str, Any] | None:
        graphic_data = node.find("./a:graphic/a:graphicData", NS)
        if graphic_data is None:
            return None
        if not graphic_data.attrib.get("uri", "").endswith("/chart"):
            return None

        chart_ref = graphic_data.find("c:chart", NS)
        chart_target = None
        if chart_ref is not None:
            rel_id = chart_ref.attrib.get(f"{{{ODREL_NS}}}id")
            if rel_id and rel_id in slide_rels:
                chart_target = slide_rels[rel_id]["target"]

        chart_title = None
        chart_type = None
        series: list[dict[str, Any]] = []
        if chart_target and chart_target in self.zf.namelist():
            chart_root = self._read_xml(chart_target)
            plot_area = chart_root.find(".//c:plotArea", NS)
            if plot_area is not None:
                for child in plot_area:
                    child_name = local_name(child.tag)
                    if child_name.endswith("Chart"):
                        chart_type = child_name
                        break

            title_texts = [node.text for node in chart_root.findall(".//c:title//a:t", NS) if node.text]
            if title_texts:
                chart_title = clean_text(" ".join(title_texts))

            for ser in chart_root.findall(".//c:ser", NS):
                series_name = []
                for candidate in ser.findall("./c:tx//a:t", NS) + ser.findall("./c:tx//c:v", NS):
                    if candidate.text:
                        series_name.append(candidate.text)
                categories = [clean_text(node.text or "") for node in ser.findall(".//c:cat//c:v", NS) if node.text]
                values = [clean_text(node.text or "") for node in ser.findall(".//c:val//c:v", NS) if node.text]
                series.append(
                    {
                        "name": clean_text(" ".join(series_name)) or None,
                        "categories": categories,
                        "values": values,
                    }
                )

        return {
            "kind": "chart",
            **self._extract_non_visual(node),
            "geometry": self._extract_geometry_dict(node, transform, "./p:xfrm"),
            "chart_path": chart_target,
            "chart_type": chart_type,
            "chart_title": chart_title,
            "series": series,
        }

    def _extract_connector_shape(
        self,
        node: ET.Element,
        transform: Transform,
    ) -> dict[str, Any]:
        prst = node.find("./p:spPr/a:prstGeom", NS)
        return {
            "kind": "connector_shape",
            **self._extract_non_visual(node),
            "geometry": self._extract_geometry_dict(node, transform, "./p:spPr/a:xfrm"),
            "preset": prst.attrib.get("prst") if prst is not None else None,
        }

    def _extract_graphic_frame(
        self,
        node: ET.Element,
        slide_rels: dict[str, dict[str, str]],
        transform: Transform,
    ) -> dict[str, Any] | None:
        table = self._extract_table(node, transform)
        if table is not None:
            return table

        chart = self._extract_chart(node, slide_rels, transform)
        if chart is not None:
            return chart

        texts = [clean_text(t.text or "") for t in node.findall(".//a:t", NS) if clean_text(t.text or "")]
        if not texts:
            return None
        return {
            "kind": "graphic_text",
            **self._extract_non_visual(node),
            "geometry": self._extract_geometry_dict(node, transform, "./p:xfrm"),
            "text": "\n".join(texts),
            "text_lines": texts,
        }

    def _extract_notes(self, slide_path: str, slide_rels: dict[str, dict[str, str]]) -> list[str]:
        if not self.include_notes:
            return []
        note_target = None
        for rel in slide_rels.values():
            if rel["type"].endswith("/notesSlide"):
                note_target = rel["target"]
                break
        if not note_target or note_target not in self.zf.namelist():
            return []
        note_root = self._read_xml(note_target)
        notes: list[str] = []
        for para in note_root.findall(".//a:p", NS):
            paragraph = self._extract_paragraph(para)
            if paragraph is not None:
                notes.append(paragraph["text"])
        return notes

    def _extract_layout_hint(self, slide_rels: dict[str, dict[str, str]]) -> dict[str, Any] | None:
        target = None
        for rel in slide_rels.values():
            if rel["type"].endswith("/slideLayout"):
                target = rel["target"]
                break
        if not target or target not in self.zf.namelist():
            return None
        root = self._read_xml(target)
        return {
            "path": target,
            "type": root.attrib.get("type"),
            "matching_name": root.attrib.get("matchingName"),
            "preserve": root.attrib.get("preserve"),
        }

    def _iter_slide_elements(
        self,
        container: ET.Element,
        slide_rels: dict[str, dict[str, str]],
        transform: Transform,
    ) -> list[dict[str, Any]]:
        elements: list[dict[str, Any]] = []
        for child in container:
            child_name = local_name(child.tag)
            if child_name in {"nvGrpSpPr", "grpSpPr", "extLst"}:
                continue
            if child_name == "sp":
                shape = self._extract_text_shape(child, transform)
                elements.append(shape if shape is not None else self._extract_generic_shape(child, transform))
            elif child_name == "pic":
                elements.append(self._extract_picture(child, slide_rels, transform))
            elif child_name == "graphicFrame":
                graphic = self._extract_graphic_frame(child, slide_rels, transform)
                if graphic is not None:
                    elements.append(graphic)
            elif child_name == "cxnSp":
                elements.append(self._extract_connector_shape(child, transform))
            elif child_name == "grpSp":
                nested_transform = self._next_transform(child, transform)
                elements.extend(self._iter_slide_elements(child, slide_rels, nested_transform))
        return elements

    def _sort_key(self, element: dict[str, Any]) -> tuple[float, float, float]:
        geometry = element.get("geometry", {})
        y = geometry.get("y_pct")
        x = geometry.get("x_pct")
        h = geometry.get("h_pct")
        return (
            float(y) if y is not None else 1.0,
            float(x) if x is not None else 1.0,
            float(h) if h is not None else 1.0,
        )

    def _is_visible_on_slide(self, element: dict[str, Any]) -> bool:
        geometry = element.get("geometry") or {}
        x = geometry.get("x_pct")
        y = geometry.get("y_pct")
        w = geometry.get("w_pct")
        h = geometry.get("h_pct")
        if x is None or y is None:
            return True
        width = float(w) if w is not None else 0.0
        height = float(h) if h is not None else 0.0
        left = float(x)
        top = float(y)
        right = left + width
        bottom = top + height
        return right > 0.0 and bottom > 0.0 and left < 1.0 and top < 1.0

    def _agenda_items(self, slide: dict[str, Any]) -> list[str]:
        agenda_items: list[str] = []
        title = slide.get("title") or ""
        slide_text = slide.get("full_text") or ""
        if not (AGENDA_TITLE_RE.search(title) or AGENDA_TITLE_RE.search(slide_text)):
            return agenda_items
        for line in slide_text.splitlines():
            match = AGENDA_ITEM_RE.match(line)
            if match:
                agenda_items.append(clean_text(match.group(1)))
        return agenda_items

    def _title_score(self, element: dict[str, Any]) -> float:
        if element["kind"] not in {"text", "graphic_text"}:
            return -1e9
        text = clean_text(element.get("text") or "")
        if not text:
            return -1e9
        geometry = element.get("geometry") or {}
        y_pct = geometry.get("y_pct") if geometry else None
        x_pct = geometry.get("x_pct") if geometry else None
        placeholder = element.get("placeholder") or {}
        max_font = element.get("font_size_pt_max")
        score = 0.0
        if placeholder.get("type") in {"title", "ctrTitle"}:
            score += 100.0
        if placeholder.get("type") == "subTitle":
            score += 40.0
        if y_pct is not None:
            score += max(0.0, 25.0 - 40.0 * float(y_pct))
        if max_font is not None:
            score += min(float(max_font) * 1.5, 70.0)
        length = len(text.replace("\n", ""))
        if length <= 80:
            score += 10.0
        if length > 160:
            score -= 25.0
        if NUMBERISH_RE.match(text):
            score -= 80.0 if length <= 16 else 40.0
        if is_probable_footer(text):
            score -= 50.0
        if is_editorial_text(text):
            score -= 60.0
        if "丨" in text and length <= 40:
            score -= 12.0
        return score

    def _classify_text_role(
        self,
        element: dict[str, Any],
        slide_title_id: int | None,
    ) -> str:
        if element.get("shape_id") == slide_title_id:
            return "title"
        if element["kind"] == "image":
            return "image"
        if element["kind"] == "table":
            return "table"
        if element["kind"] == "chart":
            return "chart"
        if element["kind"] == "graphic_text":
            return "body"

        text = clean_text(element.get("text") or "")
        geometry = element.get("geometry") or {}
        y_pct = geometry.get("y_pct")
        placeholder = element.get("placeholder") or {}
        paragraphs = element.get("paragraphs") or []

        if placeholder.get("type") == "subTitle":
            return "subtitle"
        if is_editorial_text(text):
            return "editorial_note"
        if is_probable_footer(text) or (y_pct is not None and float(y_pct) > 0.88):
            return "footer"
        if any((para.get("level") or 0) > 0 for para in paragraphs):
            return "bullet_list"
        if len(paragraphs) >= 3 and len(text) <= 200:
            return "bullet_list"
        if NUMBERISH_RE.match(text) and len(text) <= 24:
            return "key_stat"
        if len(paragraphs) <= 2 and len(text) <= 48 and (y_pct is not None and float(y_pct) < 0.35):
            return "heading"
        return "body"

    def _slide_role(self, slide: dict[str, Any]) -> str:
        title = clean_text(slide.get("title") or "")
        agenda_items = slide.get("agenda_items") or []
        text_elements = [element for element in slide["elements"] if element["kind"] in {"text", "graphic_text"}]
        structural_count = len(
            [
                element
                for element in text_elements
                if element.get("role_guess") not in {"footer", "editorial_note"}
            ]
        )
        text_length = len(slide.get("full_text") or "")
        if slide["slide_number"] == 1 and structural_count <= 4:
            return "cover"
        if agenda_items:
            return "agenda"
        if title and structural_count <= 3 and text_length <= 180:
            return "section_divider"
        if re.search(r"(thanks|thank you|q&a|结束|谢谢)", title, re.IGNORECASE):
            return "closing"
        return "content"

    def _post_process_slide(self, slide: dict[str, Any]) -> dict[str, Any]:
        slide["elements"] = [element for element in slide["elements"] if self._is_visible_on_slide(element)]
        slide["elements"] = sorted(slide["elements"], key=self._sort_key)
        for index, element in enumerate(slide["elements"], start=1):
            element["reading_order_index"] = index

        title_candidate = None
        best_score = -1e18
        for element in slide["elements"]:
            score = self._title_score(element)
            if score > best_score:
                best_score = score
                title_candidate = element

        slide_title = clean_text(title_candidate.get("text") or "") if title_candidate else None
        slide["title"] = slide_title
        slide["title_shape_id"] = title_candidate.get("shape_id") if title_candidate else None
        slide["title_source"] = (
            f"{(title_candidate.get('placeholder') or {}).get('type') or title_candidate['kind']}"
            if title_candidate
            else None
        )

        full_text_parts: list[str] = []
        for element in slide["elements"]:
            role = self._classify_text_role(element, slide["title_shape_id"])
            element["role_guess"] = role
            if (
                element["kind"] in {"text", "graphic_text"}
                and element.get("text")
                and role != "editorial_note"
            ):
                full_text_parts.append(clean_text(element["text"]))
            elif element["kind"] == "table":
                for row in element.get("rows", []):
                    full_text_parts.append(" | ".join(cell for cell in row if cell))

        slide["full_text"] = "\n".join(part for part in full_text_parts if part)
        slide["agenda_items"] = self._agenda_items(slide)
        if slide["agenda_items"] and title_candidate and title_candidate.get("text_lines"):
            slide["title"] = title_candidate["text_lines"][0]
        slide["slide_role"] = self._slide_role(slide)
        return slide

    def extract(self) -> dict[str, Any]:
        slides: list[dict[str, Any]] = []
        for slide_number, slide_path in enumerate(self._slide_paths_in_order(), start=1):
            slide_rels = self._load_relationships(slide_path)
            slide_root = self._read_xml(slide_path)
            sp_tree = slide_root.find("./p:cSld/p:spTree", NS)
            if sp_tree is None:
                continue

            slide = {
                "slide_number": slide_number,
                "path": slide_path,
                "layout_hint": self._extract_layout_hint(slide_rels),
                "elements": self._iter_slide_elements(sp_tree, slide_rels, Transform()),
                "notes": self._extract_notes(slide_path, slide_rels),
            }
            slides.append(self._post_process_slide(slide))

        repeated_labels = self._repeated_labels(slides)
        agenda_slides = [
            {
                "slide_number": slide["slide_number"],
                "title": slide.get("title"),
                "items": slide.get("agenda_items"),
            }
            for slide in slides
            if slide.get("agenda_items")
        ]
        outline_candidates = [
            {
                "slide_number": slide["slide_number"],
                "title": slide.get("title"),
                "slide_role": slide.get("slide_role"),
            }
            for slide in slides
            if slide.get("slide_role") in {"cover", "agenda", "section_divider", "closing"}
        ]

        return {
            "source_file": str(self.pptx_path),
            "slide_count": len(slides),
            "slide_size": self.slide_size,
            "include_notes": self.include_notes,
            "deck_signals": {
                "agenda_slides": agenda_slides,
                "repeated_labels": repeated_labels,
                "outline_candidates": outline_candidates,
            },
            "slides": slides,
        }

    def _repeated_labels(self, slides: list[dict[str, Any]]) -> list[dict[str, Any]]:
        occurrences: Counter[str] = Counter()
        labels: dict[str, str] = {}
        for slide in slides:
            seen_on_slide: set[str] = set()
            for element in slide["elements"]:
                if element["kind"] != "text":
                    continue
                if element.get("role_guess") in {"footer", "editorial_note"}:
                    continue
                text = clean_text(element.get("text") or "")
                if not text or "\n" in text or len(text) > 32:
                    continue
                if not REPEATED_LABEL_RE.match(text):
                    continue
                normalized = normalize_label(text)
                if not normalized or normalized in seen_on_slide:
                    continue
                seen_on_slide.add(normalized)
                labels.setdefault(normalized, text)
                occurrences[normalized] += 1

        repeated = []
        for normalized, count in occurrences.most_common():
            if count < 2:
                continue
            repeated.append({"label": labels[normalized], "slide_count": count})
        return repeated


def render_markdown(deck: dict[str, Any]) -> str:
    lines = [
        f"# {Path(deck['source_file']).name}",
        "",
        f"- Slides: {deck['slide_count']}",
        f"- Notes included: {'yes' if deck['include_notes'] else 'no'}",
    ]

    agenda_slides = deck["deck_signals"].get("agenda_slides") or []
    if agenda_slides:
        lines.append("- Agenda candidates:")
        for agenda in agenda_slides:
            items = "; ".join(agenda.get("items") or [])
            lines.append(f"  - Slide {agenda['slide_number']}: {items}")

    repeated_labels = deck["deck_signals"].get("repeated_labels") or []
    if repeated_labels:
        labels = ", ".join(f"{entry['label']} x{entry['slide_count']}" for entry in repeated_labels[:10])
        lines.append(f"- Repeated labels: {labels}")

    for slide in deck["slides"]:
        lines.append("")
        lines.append(f"## Slide {slide['slide_number']}")
        lines.append(f"- Role: {slide.get('slide_role')}")
        lines.append(f"- Title: {slide.get('title') or '(none)'}")
        for element in slide["elements"]:
            role = element.get("role_guess")
            if element["kind"] in {"text", "graphic_text"}:
                preview = (element.get("text") or "").replace("\n", " / ")
                lines.append(f"- [{role}] {preview}")
            elif element["kind"] == "table":
                headers = " | ".join(element.get("headers") or [])
                lines.append(f"- [table] {headers or '(no header text)'}")
            elif element["kind"] == "chart":
                title = element.get("chart_title") or element.get("name") or "(untitled chart)"
                lines.append(f"- [chart] {title}")
            elif element["kind"] == "image":
                title = element.get("name") or element.get("alt_text") or "(image)"
                lines.append(f"- [image] {title}")
            elif element["kind"] in {"auto_shape", "connector_shape"}:
                preset = element.get("preset") or "(shape)"
                lines.append(f"- [{element['kind']}] {preset}")
        if deck["include_notes"] and slide.get("notes"):
            lines.append("- Notes:")
            for note in slide["notes"]:
                lines.append(f"  - {note}")

    return "\n".join(lines)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract structured content and hierarchy signals from a PowerPoint .pptx file."
    )
    parser.add_argument("pptx_path", type=Path, help="Path to the .pptx file")
    parser.add_argument(
        "--format",
        choices=("json", "markdown"),
        default="json",
        help="Output format",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional output file path",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output",
    )
    parser.add_argument(
        "--include-notes",
        action="store_true",
        help="Include speaker notes in the output",
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    if args.pptx_path.suffix.lower() != ".pptx":
        print("Only .pptx files are supported.", file=sys.stderr)
        return 1
    if not args.pptx_path.exists():
        print(f"File not found: {args.pptx_path}", file=sys.stderr)
        return 1

    deck = PptxExtractor(args.pptx_path, include_notes=args.include_notes).extract()

    if args.format == "markdown":
        output = render_markdown(deck)
    else:
        output = json.dumps(deck, ensure_ascii=False, indent=2 if args.pretty else None)

    if args.output:
        args.output.write_text(output, encoding="utf-8")
    else:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
