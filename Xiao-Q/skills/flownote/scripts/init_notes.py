#!/usr/bin/env python3
"""
FlowNote - 初始化笔记库

功能：创建笔记库目录结构和初始索引文件
"""

import argparse
import json
import os
from pathlib import Path


def init_notes(notes_root: str) -> dict:
    """
    初始化笔记库目录结构
    
    Args:
        notes_root: 笔记库根路径
        
    Returns:
        初始化结果信息
    """
    root_path = Path(notes_root)
    
    # 创建目录结构
    directories = [
        "ideas",
        "topics",
        "drafts"
    ]
    
    created_dirs = []
    for dir_name in directories:
        dir_path = root_path / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
        created_dirs.append(str(dir_path))
    
    # 创建初始索引文件
    index_path = root_path / "index.json"
    initial_index = {
        "notes": [],
        "topics": [],
        "stats": {
            "total_notes": 0,
            "total_topics": 0,
            "last_updated": None
        }
    }
    
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(initial_index, f, ensure_ascii=False, indent=2)
    
    return {
        "success": True,
        "notes_root": str(root_path.absolute()),
        "created_directories": created_dirs,
        "index_file": str(index_path.absolute())
    }


def main():
    parser = argparse.ArgumentParser(description="初始化 FlowNote 笔记库")
    parser.add_argument(
        "--notes-root",
        type=str,
        default="./notes",
        help="笔记库根路径，默认为 ./notes"
    )
    
    args = parser.parse_args()
    
    result = init_notes(args.notes_root)
    
    if result["success"]:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(json.dumps({"success": False, "error": "初始化失败"}, ensure_ascii=False))
        exit(1)


if __name__ == "__main__":
    main()
