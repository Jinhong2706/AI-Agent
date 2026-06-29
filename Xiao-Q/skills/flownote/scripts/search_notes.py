#!/usr/bin/env python3
"""
FlowNote - 检索笔记

功能：支持关键词、标签、时间三种检索模式
"""

import argparse
import json
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional


def load_index(notes_root: Path) -> dict:
    """
    加载索引文件
    
    Args:
        notes_root: 笔记库根路径
        
    Returns:
        索引数据
    """
    index_path = notes_root / "index.json"
    
    if not index_path.exists():
        return {
            "notes": [],
            "topics": [],
            "stats": {
                "total_notes": 0,
                "total_topics": 0,
                "last_updated": None
            }
        }
    
    with open(index_path, "r", encoding="utf-8") as f:
        return json.load(f)


def search_by_keyword(notes_root: Path, query: str, limit: int) -> list:
    """
    关键词检索：搜索标题和内容
    
    Args:
        notes_root: 笔记库根路径
        query: 检索词
        limit: 返回数量限制
        
    Returns:
        匹配的笔记列表
    """
    results = []
    index = load_index(notes_root)
    
    # 在索引中搜索
    query_lower = query.lower()
    for note in index["notes"]:
        title_match = query_lower in note.get("title", "").lower()
        content_match = query_lower in note.get("content", "").lower()
        
        if title_match or content_match:
            results.append({
                "id": note["id"],
                "type": note["type"],
                "title": note["title"],
                "content": note["content"],
                "tags": note.get("tags", []),
                "source": note.get("source"),
                "created_at": note.get("created_at"),
                "file_path": note.get("file_path"),
                "relevance": "high" if title_match else "medium"
            })
    
    # 在文件中搜索（补充未索引的内容）
    for md_file in notes_root.rglob("*.md"):
        if md_file.name == "index.json":
            continue
            
        with open(md_file, "r", encoding="utf-8") as f:
            content = f.read()
            
        if query_lower in content.lower():
            # 检查是否已在结果中
            relative_path = str(md_file.relative_to(notes_root))
            if not any(r.get("file_path") == relative_path for r in results):
                # 提取标题
                title = md_file.stem
                first_line = content.split("\n")[0]
                if first_line.startswith("# "):
                    title = first_line[2:].strip()
                
                results.append({
                    "id": md_file.stem,
                    "type": "file",
                    "title": title,
                    "content": content[:300] + "...",
                    "file_path": relative_path,
                    "relevance": "low"
                })
    
    # 按相关性排序
    results.sort(key=lambda x: 0 if x["relevance"] == "high" else (1 if x["relevance"] == "medium" else 2))
    
    return results[:limit]


def search_by_tag(notes_root: Path, query: str, limit: int) -> list:
    """
    标签检索：搜索包含指定标签的笔记
    
    Args:
        notes_root: 笔记库根路径
        query: 标签名称
        limit: 返回数量限制
        
    Returns:
        匹配的笔记列表
    """
    results = []
    index = load_index(notes_root)
    
    query_lower = query.lower().lstrip("#")
    
    for note in index["notes"]:
        tags = [t.lower().lstrip("#") for t in note.get("tags", [])]
        if query_lower in tags:
            results.append({
                "id": note["id"],
                "type": note["type"],
                "title": note["title"],
                "content": note["content"],
                "tags": note.get("tags", []),
                "source": note.get("source"),
                "created_at": note.get("created_at"),
                "file_path": note.get("file_path")
            })
    
    return results[:limit]


def search_by_time(notes_root: Path, query: str, limit: int) -> list:
    """
    时间检索：搜索指定时间范围内的笔记
    
    Args:
        notes_root: 笔记库根路径
        query: 时间范围（支持：today/yesterday/this-week/last-week/YYYY-MM-DD）
        limit: 返回数量限制
        
    Returns:
        匹配的笔记列表
    """
    results = []
    index = load_index(notes_root)
    
    # 解析时间范围
    now = datetime.now()
    
    if query.lower() == "today":
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=1)
    elif query.lower() == "yesterday":
        start_date = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=1)
    elif query.lower() == "this-week":
        start_date = now - timedelta(days=now.weekday())
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=7)
    elif query.lower() == "last-week":
        start_date = now - timedelta(days=now.weekday() + 7)
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=7)
    else:
        # 尝试解析为具体日期
        try:
            start_date = datetime.strptime(query, "%Y-%m-%d")
            end_date = start_date + timedelta(days=1)
        except ValueError:
            return []
    
    for note in index["notes"]:
        try:
            created_at = datetime.fromisoformat(note.get("created_at", ""))
            if start_date <= created_at < end_date:
                results.append({
                    "id": note["id"],
                    "type": note["type"],
                    "title": note["title"],
                    "content": note["content"],
                    "tags": note.get("tags", []),
                    "source": note.get("source"),
                    "created_at": note.get("created_at"),
                    "file_path": note.get("file_path")
                })
        except (ValueError, TypeError):
            continue
    
    return results[:limit]


def search_notes(notes_root: str, query: str, mode: str, limit: int) -> dict:
    """
    检索笔记
    
    Args:
        notes_root: 笔记库根路径
        query: 检索词
        mode: 检索模式 (keyword/tag/time)
        limit: 返回数量限制
        
    Returns:
        检索结果
    """
    root_path = Path(notes_root)
    
    if not root_path.exists():
        return {
            "success": False,
            "error": f"笔记库不存在: {notes_root}",
            "results": []
        }
    
    if mode == "keyword":
        results = search_by_keyword(root_path, query, limit)
    elif mode == "tag":
        results = search_by_tag(root_path, query, limit)
    elif mode == "time":
        results = search_by_time(root_path, query, limit)
    else:
        return {
            "success": False,
            "error": f"不支持的检索模式: {mode}",
            "results": []
        }
    
    return {
        "success": True,
        "query": query,
        "mode": mode,
        "count": len(results),
        "results": results
    }


def main():
    parser = argparse.ArgumentParser(description="检索 FlowNote 笔记")
    parser.add_argument(
        "--notes-root",
        type=str,
        default="./notes",
        help="笔记库根路径，默认为 ./notes"
    )
    parser.add_argument(
        "--query",
        type=str,
        required=True,
        help="检索词"
    )
    parser.add_argument(
        "--mode",
        type=str,
        default="keyword",
        choices=["keyword", "tag", "time"],
        help="检索模式"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="返回数量限制"
    )
    
    args = parser.parse_args()
    
    result = search_notes(
        notes_root=args.notes_root,
        query=args.query,
        mode=args.mode,
        limit=args.limit
    )
    
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
