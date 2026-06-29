#!/usr/bin/env python3
"""
FlowNote - 保存笔记

功能：将笔记保存到指定位置，支持 ideas/topics/drafts 三种类型
"""

import argparse
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional


def get_week_number(dt: datetime) -> str:
    """
    获取日期对应的周年份和周数
    
    Args:
        dt: 日期时间对象
        
    Returns:
        格式为 YYYY-WXX 的字符串
    """
    iso_calendar = dt.isocalendar()
    return f"{iso_calendar[0]}-W{iso_calendar[1]:02d}"


def generate_note_id(dt: datetime) -> str:
    """
    生成笔记唯一 ID
    
    Args:
        dt: 日期时间对象
        
    Returns:
        格式为 YYYY-MM-DD-HHMM 的 ID
    """
    return dt.strftime("%Y-%m-%d-%H%M")


def save_idea(notes_root: Path, note_id: str, title: str, content: str, 
              tags: list, source: Optional[str], relations: list, dt: datetime) -> dict:
    """
    保存灵感笔记到周文件
    
    Args:
        notes_root: 笔记库根路径
        note_id: 笔记 ID
        title: 标题
        content: 内容
        tags: 标签列表
        source: 来源
        relations: 关联笔记 ID 列表
        dt: 创建时间
        
    Returns:
        保存结果信息
    """
    week_str = get_week_number(dt)
    ideas_dir = notes_root / "ideas"
    ideas_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = ideas_dir / f"{week_str}.md"
    timestamp = dt.strftime("%Y-%m-%d %H:%M")
    
    # 构建笔记内容
    note_content = f"\n## {timestamp} {title}\n"
    note_content += f"- {content}\n"
    if source:
        note_content += f"- 来源：{source}\n"
    if tags:
        tags_str = " ".join([f"#{tag}" for tag in tags])
        note_content += f"- 标签：{tags_str}\n"
    if relations:
        relations_str = " ".join([f"[[{r}]]" for r in relations])
        note_content += f"- 关联：{relations_str}\n"
    
    # 追加到文件
    file_exists = file_path.exists()
    
    if not file_exists:
        # 创建新文件，添加标题
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"# {week_str} 灵感\n")
    
    with open(file_path, "a", encoding="utf-8") as f:
        f.write(note_content)
    
    return {
        "file_path": str(file_path.relative_to(notes_root)),
        "note_id": note_id,
        "week": week_str
    }


def save_topic(notes_root: Path, note_id: str, title: str, content: str,
               tags: list, source: Optional[str], relations: list, dt: datetime) -> dict:
    """
    保存或更新主题卡片
    
    Args:
        notes_root: 笔记库根路径
        note_id: 笔记 ID
        title: 标题（主题名）
        content: 内容
        tags: 标签列表
        source: 来源
        relations: 关联笔记 ID 列表
        dt: 创建时间
        
    Returns:
        保存结果信息
    """
    topics_dir = notes_root / "topics"
    topics_dir.mkdir(parents=True, exist_ok=True)
    
    # 使用标题作为文件名（转换为小写和连字符）
    topic_name = title.lower().replace(" ", "-").replace("_", "-")
    file_path = topics_dir / f"{topic_name}.md"
    
    timestamp = dt.strftime("%Y-%m-%d %H:%M")
    
    if not file_path.exists():
        # 创建新的主题文件
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"# {title}\n\n")
            f.write("## 核心观点\n\n")
            f.write(f"### {title}\n")
            f.write(f"- {content}\n")
            if source:
                f.write(f"- 来源：{source}\n")
            f.write("\n## 相关主题\n\n")
            if relations:
                for r in relations:
                    f.write(f"- [[{r}]]\n")
            f.write("\n## 待探索\n\n")
    else:
        # 追加到现有主题文件
        with open(file_path, "r", encoding="utf-8") as f:
            existing_content = f.read()
        
        # 在核心观点章节后追加
        new_point = f"\n### 观点（{timestamp}）\n"
        new_point += f"- {content}\n"
        if source:
            new_point += f"- 来源：{source}\n"
        
        # 找到核心观点章节的位置
        if "## 核心观点" in existing_content:
            # 在下一个 ## 之前插入
            lines = existing_content.split("\n")
            insert_index = -1
            for i, line in enumerate(lines):
                if line.startswith("## ") and i > 0 and "核心观点" not in line:
                    insert_index = i
                    break
            
            if insert_index > 0:
                lines.insert(insert_index, new_point)
                updated_content = "\n".join(lines)
            else:
                updated_content = existing_content + new_point
        else:
            updated_content = existing_content + "\n## 核心观点\n" + new_point
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(updated_content)
    
    return {
        "file_path": str(file_path.relative_to(notes_root)),
        "note_id": note_id,
        "topic_name": topic_name
    }


def save_draft(notes_root: Path, note_id: str, title: str, content: str,
               tags: list, source: Optional[str], relations: list, dt: datetime) -> dict:
    """
    保存草稿
    
    Args:
        notes_root: 笔记库根路径
        note_id: 笔记 ID
        title: 标题
        content: 内容
        tags: 标签列表
        source: 来源
        relations: 关联笔记 ID 列表
        dt: 创建时间
        
    Returns:
        保存结果信息
    """
    drafts_dir = notes_root / "drafts"
    drafts_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = dt.strftime("%Y-%m-%d")
    draft_name = f"{timestamp}-{title.lower().replace(' ', '-').replace('_', '-')}"
    file_path = drafts_dir / f"{draft_name}.md"
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(f"# {title}\n\n")
        f.write(f"*创建于 {dt.strftime('%Y-%m-%d %H:%M')}*\n\n")
        f.write(f"{content}\n\n")
        if tags:
            tags_str = " ".join([f"#{tag}" for tag in tags])
            f.write(f"标签：{tags_str}\n\n")
        if relations:
            f.write("## 相关笔记\n\n")
            for r in relations:
                f.write(f"- [[{r}]]\n")
    
    return {
        "file_path": str(file_path.relative_to(notes_root)),
        "note_id": note_id,
        "draft_name": draft_name
    }


def update_index(notes_root: Path, note_id: str, note_type: str, title: str,
                 content: str, file_path: str, tags: list, source: Optional[str],
                 relations: list, dt: datetime) -> None:
    """
    更新索引文件
    
    Args:
        notes_root: 笔记库根路径
        note_id: 笔记 ID
        note_type: 笔记类型
        title: 标题
        content: 内容
        file_path: 文件相对路径
        tags: 标签列表
        source: 来源
        relations: 关联笔记 ID 列表
        dt: 创建时间
    """
    index_path = notes_root / "index.json"
    
    if index_path.exists():
        with open(index_path, "r", encoding="utf-8") as f:
            index = json.load(f)
    else:
        index = {
            "notes": [],
            "topics": [],
            "stats": {
                "total_notes": 0,
                "total_topics": 0,
                "last_updated": None
            }
        }
    
    # 添加笔记条目
    note_entry = {
        "id": note_id,
        "type": note_type,
        "title": title,
        "content": content[:200] + "..." if len(content) > 200 else content,
        "file_path": file_path,
        "tags": tags,
        "source": source,
        "created_at": dt.isoformat(),
        "relations": relations
    }
    
    index["notes"].append(note_entry)
    
    # 更新主题列表
    if note_type == "topic" and title not in index["topics"]:
        index["topics"].append(title)
    
    # 更新统计信息
    index["stats"]["total_notes"] = len(index["notes"])
    index["stats"]["total_topics"] = len(index["topics"])
    index["stats"]["last_updated"] = dt.isoformat()
    
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)


def save_note(notes_root: str, note_type: str, title: str, content: str,
              tags: list, source: Optional[str], relations: list) -> dict:
    """
    保存笔记
    
    Args:
        notes_root: 笔记库根路径
        note_type: 笔记类型 (idea/topic/draft)
        title: 标题
        content: 内容
        tags: 标签列表
        source: 来源
        relations: 关联笔记 ID 列表
        
    Returns:
        保存结果信息
    """
    root_path = Path(notes_root)
    dt = datetime.now()
    note_id = generate_note_id(dt)
    
    if note_type == "idea":
        result = save_idea(root_path, note_id, title, content, tags, source, relations, dt)
    elif note_type == "topic":
        result = save_topic(root_path, note_id, title, content, tags, source, relations, dt)
    elif note_type == "draft":
        result = save_draft(root_path, note_id, title, content, tags, source, relations, dt)
    else:
        return {
            "success": False,
            "error": f"不支持的笔记类型: {note_type}"
        }
    
    # 更新索引
    update_index(root_path, note_id, note_type, title, content, 
                 result["file_path"], tags, source, relations, dt)
    
    result["success"] = True
    result["note_id"] = note_id
    result["created_at"] = dt.isoformat()
    
    return result


def main():
    parser = argparse.ArgumentParser(description="保存 FlowNote 笔记")
    parser.add_argument(
        "--notes-root",
        type=str,
        default="./notes",
        help="笔记库根路径，默认为 ./notes"
    )
    parser.add_argument(
        "--type",
        type=str,
        required=True,
        choices=["idea", "topic", "draft"],
        help="笔记类型"
    )
    parser.add_argument(
        "--title",
        type=str,
        required=True,
        help="笔记标题"
    )
    parser.add_argument(
        "--content",
        type=str,
        required=True,
        help="笔记内容"
    )
    parser.add_argument(
        "--tags",
        type=str,
        default="",
        help="标签列表，逗号分隔"
    )
    parser.add_argument(
        "--source",
        type=str,
        default=None,
        help="信息来源"
    )
    parser.add_argument(
        "--relations",
        type=str,
        default="",
        help="关联笔记 ID 列表，逗号分隔"
    )
    
    args = parser.parse_args()
    
    # 解析标签和关联
    tags = [t.strip() for t in args.tags.split(",") if t.strip()]
    relations = [r.strip() for r in args.relations.split(",") if r.strip()]
    
    result = save_note(
        notes_root=args.notes_root,
        note_type=args.type,
        title=args.title,
        content=args.content,
        tags=tags,
        source=args.source,
        relations=relations
    )
    
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
