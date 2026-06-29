# -*- coding: utf-8 -*-
"""
记忆管家 V3.0 - 核心记忆分析、加载、分级、搜索模块
来源: memory_manager.py (analyze/load/rank/search)
V3.0: 模块化重构
"""

import heapq
import json
import re
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from .config import (
    VERSION, _, SUMMARY_DIR, SUMMARY_INDEX_FILE,
    MAX_OUTPUT_CHARS, MAX_REPORT_ITEMS, MAX_TOTAL_READ,
    TOKEN_RATIO, SUMMARY_MIN_CHARS,
    RANK_CORE_THRESHOLD, RANK_NORMAL_THRESHOLD,
    LOAD_BRIEF, LOAD_NORMAL, LOAD_FULL,
    MEMORY_LARGE_SIZE_KB, MEMORY_MANY_FILES,
    is_symlink, safe_resolve, safe_file_read, get_file_info,
    iter_memory_files, parse_front_matter,
)
from .summarize import generate_summary, extract_keywords, smart_truncate
from .token import record_token_usage


# 跨引用模式：[[YYYY-MM-DD]] 和 [[MEMORY]]
_CROSS_REF_PATTERN = re.compile(r'\[\[([^\]]+)\]\]')


def _detect_cross_references(content):
    """检测记忆文件中的跨引用 [[YYYY-MM-DD]] / [[MEMORY]]。

    Returns:
        list[str]: 被引用的目标标识列表（已去重）
    """
    if not content:
        return []
    refs = []
    for m in _CROSS_REF_PATTERN.finditer(content):
        target = m.group(1).strip()
        # 匹配日期格式 YYYY-MM-DD 或特殊名称 MEMORY
        if re.match(r'^\d{4}-\d{2}-\d{2}$', target) or target.upper() == 'MEMORY':
            if target not in refs:
                refs.append(target)
    return refs


def analyze_memory(workspace_path, age_days=None, exclude_patterns=None):
    base_path = Path(workspace_path).resolve()
    memory_path = base_path / ".workbuddy" / "memory"
    result = {
        "version": VERSION,
        "workspace": workspace_path,
        "timestamp": datetime.now().isoformat(),
        "files": [],
        "cross_references": {},
        "stats": {
            "total_files": 0,
            "total_size_kb": 0,
            "cleanable_files": 0,
            "cleanable_size_kb": 0,
            "by_folder": {}
        },
        "recommendations": [],
        "warnings": []
    }

    if not memory_path.exists():
        result["error"] = _("memory_dir_not_exist")
        return result

    if exclude_patterns is None:
        exclude_patterns = []

    total_read = 0

    try:
        for md_file, mtime, size_kb, rel_path in iter_memory_files(
                memory_path, skip_memory_md=False, include_dirs=True):
            if total_read + int(size_kb * 1024) > MAX_TOTAL_READ:
                result["warnings"].append(_("scan_warning_limit").format(limit=MAX_TOTAL_READ // 1024))
                break

            age = (datetime.now() - mtime).days
            if age_days is not None and age > age_days:
                continue

            is_cleanable = (
                md_file.name != "MEMORY.md" and
                age > 30
            )

            # 计算所属文件夹（子目录分组）
            parts = Path(rel_path).parts
            folder = parts[0] if len(parts) > 1 else "/"

            file_info = {
                "name": md_file.name,
                "path": rel_path,
                "folder": folder,
                "size_kb": round(size_kb, 2),
                "modified": mtime.strftime("%Y-%m-%d"),
                "age_days": age,
                "cleanable": is_cleanable
            }

            result["files"].append(file_info)
            result["stats"]["total_files"] += 1
            result["stats"]["total_size_kb"] += size_kb
            if is_cleanable:
                result["stats"]["cleanable_files"] += 1
                result["stats"]["cleanable_size_kb"] += size_kb

            # P2-5: 跨引用检测 — 仅读取前 4KB 即可捕获 front-matter 和头部引用
            try:
                with open(md_file, 'r', encoding='utf-8', errors='ignore') as _f:
                    head = _f.read(4096)
                refs = _detect_cross_references(head)
                if refs:
                    result["cross_references"][md_file.name] = refs
            except Exception:
                pass

            # 按文件夹累计
            if folder not in result["stats"]["by_folder"]:
                result["stats"]["by_folder"][folder] = {"files": 0, "size_kb": 0}
            result["stats"]["by_folder"][folder]["files"] += 1
            result["stats"]["by_folder"][folder]["size_kb"] += size_kb

            if len(result["files"]) >= MAX_REPORT_ITEMS:
                result["warnings"].append(_("files_over_limit").format(limit=MAX_REPORT_ITEMS))
                break

        result["recommendations"] = _generate_recommendations(result["files"], result["stats"])

    except Exception as e:
        result["error"] = _("analyze_failed").format(error=f"{type(e).__name__}: {str(e)}")

    return result


def _generate_recommendations(files, stats):
    recs = []

    if stats["total_size_kb"] > MEMORY_LARGE_SIZE_KB:
        recs.append(_("rec_large_memory").format(size=f"{stats['total_size_kb']:.1f}"))

    if stats["total_files"] > MEMORY_MANY_FILES:
        recs.append(_("rec_many_files").format(count=stats['total_files']))

    cleanable_count = stats.get("cleanable_files", 0)
    if cleanable_count > 0:
        recs.append(_("rec_cleanable_count").format(count=cleanable_count))

    if not recs:
        recs.append(_("rec_good_state"))

    return recs


def _read_summary_file(summary_path, stem):
    summary_file = summary_path / f"{stem}.summary"
    if not summary_file.exists():
        return None
    try:
        with open(summary_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None


def _load_memory_file(md_file, load_mode, summary_path):
    if is_symlink(md_file):
        return None

    mtime, size_kb = get_file_info(md_file)
    if mtime is None:
        return None

    content, status = safe_file_read(md_file)
    if content is None:
        return None

    def _truncate(text, max_chars=MAX_OUTPUT_CHARS):
        return text if len(text) <= max_chars else text[:max_chars] + "..."

    if load_mode == LOAD_BRIEF:
        summary_data = _read_summary_file(summary_path, md_file.stem)
        if summary_data:
            body = _truncate(summary_data.get("summary", ""))
            if len(body) >= len(content):
                body = smart_truncate(content, SUMMARY_MIN_CHARS)
                return {
                    "file": md_file.name, "type": "truncated",
                    "content": body, "keywords": [],
                    "modified": mtime.strftime("%Y-%m-%d"),
                    "token_estimate": len(body) // TOKEN_RATIO
                }
            return {
                "file": md_file.name, "type": "summary",
                "content": body, "keywords": summary_data.get("keywords", []),
                "modified": mtime.strftime("%Y-%m-%d"),
                "token_estimate": summary_data.get("token_estimate", 0)
            }
        else:
            summary = generate_summary(content, SUMMARY_MIN_CHARS)
            return {
                "file": md_file.name, "type": "summary",
                "content": _truncate(summary), "keywords": extract_keywords(content),
                "modified": mtime.strftime("%Y-%m-%d"),
                "token_estimate": len(summary) // TOKEN_RATIO
            }

    elif load_mode == LOAD_NORMAL:
        summary_data = _read_summary_file(summary_path, md_file.stem)
        if summary_data:
            summary = summary_data.get("summary", "")
            key_lines = [l for l in content.split('\n') if l.strip().startswith(('-', '*'))][:5]
            extra = '\n'.join(key_lines)
            body = summary[:200] + ("\n\n关键要点:\n" + extra[:100] if extra else "")
        else:
            body = generate_summary(content, 500)
            summary_data = {}
        return {
            "file": md_file.name, "type": "summary+keys",
            "content": _truncate(body, MAX_OUTPUT_CHARS),
            "keywords": summary_data.get("keywords", extract_keywords(content)),
            "modified": mtime.strftime("%Y-%m-%d"),
            "token_estimate": len(body) // TOKEN_RATIO
        }

    else:  # full
        return {
            "file": md_file.name, "type": "full",
            "content": content[:5000] if len(content) > 5000 else content,
            "modified": mtime.strftime("%Y-%m-%d"),
            "token_estimate": len(content) // TOKEN_RATIO
        }


def load_memory(workspace_path, mode=LOAD_NORMAL, keyword=None, limit=10, days=None, folder=None):
    base_path = Path(workspace_path).resolve()
    memory_path = base_path / ".workbuddy" / "memory"
    summary_path = base_path / ".workbuddy" / SUMMARY_DIR

    result = {
        "version": VERSION,
        "timestamp": datetime.now().isoformat(),
        "mode": mode,
        "days_filter": days,
        "folder_filter": folder,
        "loaded": [],
        "total_tokens_estimate": 0
    }

    rank_result = rank_memory_top(workspace_path, top_k=limit, days=days, folder=folder)

    files_to_load = []
    for item in rank_result.get("core", [])[:limit]:
        files_to_load.append((memory_path / item["file"], LOAD_FULL))

    normal_limit = limit - len(files_to_load)
    for item in rank_result.get("normal", [])[:max(0, normal_limit)]:
        files_to_load.append((memory_path / item["file"], mode))

    cold_limit = limit - len(files_to_load)
    for item in rank_result.get("cold", [])[:max(0, cold_limit)]:
        files_to_load.append((memory_path / item["file"], LOAD_BRIEF))

    if keyword:
        keyword = keyword.lower()
        files_to_load = [
            (f, m) for f, m in files_to_load
            if keyword in f.name.lower() or (summary_path / f"{f.stem}.summary").exists()
        ]

    for md_file, load_mode in files_to_load:
        data = _load_memory_file(md_file, load_mode, summary_path)
        if data:
            result["loaded"].append(data)
            result["total_tokens_estimate"] += data.get("token_estimate", 0)

    if result["total_tokens_estimate"] > 0:
        try:
            record_token_usage(workspace_path, result["total_tokens_estimate"], operation="load")
        except Exception:
            pass

    return result


def search_memory(workspace_path, keyword, mode="brief", folder=None, tag=None, use_tfidf=False):
    base_path = Path(workspace_path).resolve()
    memory_path = base_path / ".workbuddy" / "memory"
    summary_path = base_path / ".workbuddy" / SUMMARY_DIR

    result = {
        "version": VERSION,
        "timestamp": datetime.now().isoformat(),
        "keyword": keyword,
        "folder": folder,
        "tag": tag,
        "tfidf_enabled": use_tfidf,
        "matches": [],
        "total": 0
    }

    if not memory_path.exists():
        result["error"] = _("memory_dir_not_exist")
        return result

    keyword_lower = keyword.lower()
    matches = []
    need_tag = bool(tag)              # 预计算
    need_full_read = (mode == LOAD_FULL)  # 预计算，仅 full 时才读正文

    for md_file, mtime, size_kb, rel_path in iter_memory_files(
            memory_path, skip_memory_md=False):
        # 1) 文件夹过滤（O(1)）
        if folder:
            parts = Path(rel_path).parts
            file_folder = parts[0] if len(parts) > 1 else "/"
            if file_folder != folder:
                continue

        # 2) 摘要优先：先看 summary 是否命中
        summary_data = _read_summary_file(summary_path, md_file.stem)
        score = 0
        file_tags = []

        if summary_data:
            if keyword_lower in (summary_data.get("summary", "") or "").lower():
                score += 10
            if keyword_lower in " ".join(summary_data.get("keywords", [])).lower():
                score += 20
            # 摘要命中时，tags 字段直接复用，避免再读 front-matter
            file_tags = summary_data.get("tags", []) or []
        else:
            # 无摘要：无关键词也允许纯标签搜索匹配
            score = 1 if not keyword_lower else 0

        # 3) tag 过滤：仅在确实需要时解析 front-matter（最多读 1 次）
        if need_tag:
            if not file_tags:
                content_raw, _ = safe_file_read(md_file)
                if content_raw:
                    fm = parse_front_matter(content_raw)
                    file_tags = fm.get("tags", [])
            if not any(t.lower() == tag.lower() for t in file_tags):
                continue
            score += 30  # tag 命中加分

        if score <= 0:
            continue

        # 4) 预览：full 模式才读正文；brief/normal 直接用 summary
        if mode == LOAD_BRIEF:
            content_preview = (summary_data or {}).get("summary", "")[:200]
        elif mode == LOAD_NORMAL:
            content_preview = (summary_data or {}).get("summary", "")
        else:  # full
            content_full, _ = safe_file_read(md_file)
            content_preview = content_full[:500] if content_full else ""

        matches.append({
            "file": md_file.name,
            "path": rel_path,
            "folder": Path(rel_path).parts[0] if len(Path(rel_path).parts) > 1 else "/",
            "tags": file_tags,
            "score": score,
            "modified": mtime.strftime("%Y-%m-%d") if mtime else "unknown",
            "preview": content_preview,
            "size_kb": round(size_kb, 2) if size_kb else 0
        })

    matches.sort(key=lambda x: x["score"], reverse=True)

    # P2-3: TF-IDF 语义搜索 — 作为额外评分层
    if use_tfidf and matches:
        try:
            from .tfidf import build_tfidf_index, search_tfidf

            # 收集所有摘要文本构建索引
            docs = []
            doc_names = []
            for m in matches:
                summary_data = _read_summary_file(summary_path, Path(m["file"]).stem)
                doc_text = (summary_data or {}).get("summary", m.get("preview", ""))
                docs.append(doc_text)
                doc_names.append(m["file"])

            if docs:
                index = build_tfidf_index(docs, doc_names)
                tfidf_results = search_tfidf(index, keyword, top_k=len(matches), min_score=0.01)

                # 将 TF-IDF 分数合并到原有评分
                tfidf_scores = {r["doc_id"]: r["score"] for r in tfidf_results}
                max_tfidf = max(tfidf_scores.values()) if tfidf_scores else 1.0

                for m in matches:
                    tfidf = tfidf_scores.get(m["file"], 0)
                    # 归一化 TF-IDF 分数 (0-30)，与 keyword/keyword score 同量级
                    normalized = int(tfidf / max_tfidf * 30) if max_tfidf > 0 else 0
                    m["tfidf_score"] = round(tfidf, 4)
                    m["score"] += normalized

                # 按合并分数重新排序
                matches.sort(key=lambda x: x["score"], reverse=True)
        except ImportError:
            pass  # tfidf 模块导入失败，静默回退

    result["matches"] = matches
    result["total"] = len(matches)

    return result


def rank_memory(workspace_path, weights=None, days=None, folder=None):
    base_path = Path(workspace_path).resolve()
    memory_path = base_path / ".workbuddy" / "memory"

    if weights is None:
        weights = {"access": 0.4, "recency": 0.3, "length": 0.15, "keywords": 0.15}

    result = {
        "version": VERSION,
        "timestamp": datetime.now().isoformat(),
        "days_filter": days,
        "folder_filter": folder,
        "core": [],
        "normal": [],
        "cold": [],
        "stats": {
            "total": 0,
            "core_count": 0,
            "normal_count": 0,
            "cold_count": 0
        }
    }

    if not memory_path.exists():
        result["error"] = _("memory_dir_not_exist")
        return result

    cutoff_date = None
    if days is not None:
        cutoff_date = datetime.now() - timedelta(days=days)

    summary_path = base_path / ".workbuddy" / SUMMARY_DIR
    index_file = summary_path / SUMMARY_INDEX_FILE
    access_counts = {}

    if index_file.exists():
        try:
            with open(index_file, 'r', encoding='utf-8') as f:
                index_data = json.load(f)
                access_counts = index_data.get("access_counts", {})
        except (json.JSONDecodeError, OSError, IOError):
            access_counts = {}

    memory_scores = []

    for md_file, mtime, size_kb, rel_path in iter_memory_files(memory_path):
        if cutoff_date and mtime < cutoff_date:
            continue

        # 文件夹过滤
        if folder:
            parts = Path(rel_path).parts
            file_folder = parts[0] if len(parts) > 1 else "/"
            if file_folder != folder:
                continue

        age_days = (datetime.now() - mtime).days
        size_kb = size_kb or 0

        access_count = access_counts.get(md_file.name, 0)
        access_score = min(100, access_count * 20)

        recency_score = max(0, 100 - age_days * 2)

        if size_kb < 0.5:
            length_score = size_kb * 100
        elif size_kb > 10:
            length_score = max(0, 100 - (size_kb - 10) * 5)
        else:
            length_score = 100

        keyword_score = 50
        summary_file = summary_path / f"{md_file.stem}.summary"
        if summary_file.exists():
            try:
                with open(summary_file, 'r', encoding='utf-8') as f:
                    summary_data = json.load(f)
            except (json.JSONDecodeError, OSError, IOError):
                summary_data = {}
            # 注意：keywords 提取必须在 try/except 之外，否则仅在异常时执行
            keywords = summary_data.get("keywords", [])
            if keywords:
                keyword_score = 70

        total_score = (
            access_score * weights["access"] +
            recency_score * weights["recency"] +
            length_score * weights["length"] +
            keyword_score * weights["keywords"]
        ) / 100

        memory_info = {
            "file": md_file.name,
            "path": rel_path,
            "folder": Path(rel_path).parts[0] if len(Path(rel_path).parts) > 1 else "/",
            "score": round(total_score, 2),
            "size_kb": round(size_kb, 2),
            "age_days": age_days,
            "modified": mtime.strftime("%Y-%m-%d"),
            "details": {
                "access_score": round(access_score, 1),
                "recency_score": round(recency_score, 1),
                "length_score": round(length_score, 1),
                "keyword_score": round(keyword_score, 1)
            }
        }

        if total_score >= RANK_CORE_THRESHOLD * 100:
            result["core"].append(memory_info)
        elif total_score >= RANK_NORMAL_THRESHOLD * 100:
            result["normal"].append(memory_info)
        else:
            result["cold"].append(memory_info)

        memory_scores.append(total_score)

    result["stats"]["total"] = len(memory_scores)
    result["stats"]["core_count"] = len(result["core"])
    result["stats"]["normal_count"] = len(result["normal"])
    result["stats"]["cold_count"] = len(result["cold"])

    result["core"].sort(key=lambda x: x["score"], reverse=True)
    result["normal"].sort(key=lambda x: x["score"], reverse=True)
    result["cold"].sort(key=lambda x: x["score"], reverse=True)

    return result


def rank_memory_top(workspace_path, top_k=10, weights=None, days=None, folder=None):
    """P1-2 优化：只取 top-K，跳过 O(n log n) 完整排序 → O(n log K)。

    适用场景：load_memory 实际只需要 core/normal/cold 各 top_k 个。
    """
    full = rank_memory(workspace_path, weights=weights, days=days, folder=folder)
    for bucket in ("core", "normal", "cold"):
        full[bucket] = heapq.nlargest(top_k, full[bucket], key=lambda x: x["score"])
    return full
