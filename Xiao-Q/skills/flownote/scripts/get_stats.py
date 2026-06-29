#!/usr/bin/env python3
"""
FlowNote - 获取统计信息

功能：统计笔记库的基本信息
"""

import argparse
import json
from collections import Counter
from datetime import datetime
from pathlib import Path


def get_stats(notes_root: str) -> dict:
    """
    获取笔记库统计信息
    
    Args:
        notes_root: 笔记库根路径
        
    Returns:
        统计信息
    """
    root_path = Path(notes_root)
    
    if not root_path.exists():
        return {
            "success": False,
            "error": f"笔记库不存在: {notes_root}"
        }
    
    # 加载索引
    index_path = root_path / "index.json"
    if not index_path.exists():
        return {
            "success": False,
            "error": "索引文件不存在，请先初始化笔记库"
        }
    
    with open(index_path, "r", encoding="utf-8") as f:
        index = json.load(f)
    
    notes = index.get("notes", [])
    topics = index.get("topics", [])
    
    # 统计各类型笔记数量
    type_counter = Counter(note.get("type", "unknown") for note in notes)
    
    # 统计标签分布
    all_tags = []
    for note in notes:
        all_tags.extend(note.get("tags", []))
    tag_counter = Counter(all_tags)
    
    # 统计最近活动
    recent_notes = []
    if notes:
        sorted_notes = sorted(
            notes,
            key=lambda x: x.get("created_at", ""),
            reverse=True
        )
        recent_notes = sorted_notes[:5]
    
    # 计算文件数量
    ideas_files = list((root_path / "ideas").glob("*.md")) if (root_path / "ideas").exists() else []
    topics_files = list((root_path / "topics").glob("*.md")) if (root_path / "topics").exists() else []
    drafts_files = list((root_path / "drafts").glob("*.md")) if (root_path / "drafts").exists() else []
    
    return {
        "success": True,
        "notes_root": str(root_path.absolute()),
        "stats": {
            "total_notes": len(notes),
            "total_topics": len(topics),
            "by_type": {
                "idea": type_counter.get("idea", 0),
                "topic": type_counter.get("topic", 0),
                "draft": type_counter.get("draft", 0)
            },
            "by_file": {
                "ideas_files": len(ideas_files),
                "topics_files": len(topics_files),
                "drafts_files": len(drafts_files)
            },
            "top_tags": [
                {"tag": tag, "count": count}
                for tag, count in tag_counter.most_common(10)
            ],
            "last_updated": index.get("stats", {}).get("last_updated")
        },
        "recent_notes": [
            {
                "id": note.get("id"),
                "title": note.get("title"),
                "type": note.get("type"),
                "created_at": note.get("created_at")
            }
            for note in recent_notes
        ]
    }


def main():
    parser = argparse.ArgumentParser(description="获取 FlowNote 统计信息")
    parser.add_argument(
        "--notes-root",
        type=str,
        default="./notes",
        help="笔记库根路径，默认为 ./notes"
    )
    
    args = parser.parse_args()
    
    result = get_stats(args.notes_root)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
