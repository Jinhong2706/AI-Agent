#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量导入脚本（v3.0）
支持从微信读书、Kindle等平台导入笔记
支持 v1.0/v2.0/v3.0 数据结构
"""

import sys
import json
import os
import re
from datetime import datetime
from typing import Dict, List, Optional, Set
from pathlib import Path


def parse_wechat_export(file_path: str) -> Dict[str, any]:
    """
    解析微信读书导出文件
    
    支持格式：
    1. 纯文本格式（每条摘录以换行分隔）
    2. CSV格式
    
    返回:
        {
            "success": True/False,
            "excerpts": [摘录列表],
            "chapters": [章节列表],
            "count": 摘录数量,
            "error": "错误信息（如果失败）"
        }
    """
    try:
        excerpts = []
        chapters_found = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 微信读书导出格式：通常包含章节标题和划线内容
        # 格式示例：
        # 第一章 标题
        # 这是划线内容...
        # ◆ 这也是划线内容
        
        lines = content.split('\n')
        current_chapter = None
        current_content = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 检测章节标题
            chapter_match = re.match(r'^第[一二三四五六七八九十\d]+[章节回部篇]', line)
            if chapter_match:
                # 保存之前的摘录
                if current_content:
                    excerpts.append({
                        "content": '\n'.join(current_content),
                        "chapter": current_chapter,
                        "source": "wechat"
                    })
                    current_content = []
                
                current_chapter = line
                if line not in chapters_found:
                    chapters_found.append(line)
                continue
            
            # 检测划线内容（微信读书用◆标记）
            if line.startswith('◆'):
                if current_content:
                    excerpts.append({
                        "content": '\n'.join(current_content),
                        "chapter": current_chapter,
                        "source": "wechat"
                    })
                    current_content = []
                
                current_content.append(line[1:].strip())  # 去掉◆
            else:
                # 普通内容
                current_content.append(line)
        
        # 保存最后一条
        if current_content:
            excerpts.append({
                "content": '\n'.join(current_content),
                "chapter": current_chapter,
                "source": "wechat"
            })
        
        return {
            "success": True,
            "excerpts": excerpts,
            "chapters": chapters_found,
            "count": len(excerpts)
        }
        
    except Exception as e:
        return {
            "success": False,
            "excerpts": [],
            "chapters": [],
            "count": 0,
            "error": f"解析微信读书文件失败: {str(e)}"
        }


def parse_kindle_export(file_path: str) -> Dict[str, any]:
    """
    解析Kindle导出文件
    
    支持格式：
    1. My Clippings.txt（Kindle设备导出）
    2. CSV格式（Kindle App导出）
    
    返回:
        同 parse_wechat_export
    """
    try:
        excerpts = []
        chapters_found = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Kindle My Clippings.txt 格式
        # 每条笔记格式：
        # 书名 (作者)
        # - 您在位置 #123-125 的标注 | 添加于 2024年1月1日星期一
        # 
        # 摘录内容...
        # ==========
        
        if '==========' in content:
            # My Clippings.txt 格式
            notes = content.split('==========')
            
            for note in notes:
                if not note.strip():
                    continue
                
                lines = note.strip().split('\n')
                if len(lines) < 3:
                    continue
                
                # 提取位置信息
                location_match = re.search(r'位置 #(\d+)', lines[1]) if len(lines) > 1 else None
                location = location_match.group(1) if location_match else None
                
                # 提取内容（从第3行开始）
                content_lines = lines[2:]
                note_content = '\n'.join(content_lines).strip()
                
                if note_content:
                    chapters_found.append(f"位置 {location}" if location else "未分类")
                    excerpts.append({
                        "content": note_content,
                        "chapter": f"位置 {location}" if location else None,
                        "source": "kindle"
                    })
        else:
            # 尝试CSV格式
            import csv
            
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    content = row.get('Highlight', row.get('Text', ''))
                    chapter = row.get('Chapter', row.get('Location', ''))
                    
                    if content:
                        chapters_found.append(chapter if chapter else "未分类")
                        excerpts.append({
                            "content": content,
                            "chapter": chapter if chapter else None,
                            "source": "kindle"
                        })
        
        return {
            "success": True,
            "excerpts": excerpts,
            "chapters": chapters_found,
            "count": len(excerpts)
        }
        
    except Exception as e:
        return {
            "success": False,
            "excerpts": [],
            "chapters": [],
            "count": 0,
            "error": f"解析Kindle文件失败: {str(e)}"
        }


def generate_chapter_framework(excerpts: List[Dict]) -> Dict:
    """
    从摘录自动生成章节框架（v3.0）
    
    参数:
        excerpts: 摘录列表
    
    返回:
        章节框架对象
    """
    chapters = []
    chapter_map = {}
    
    for excerpt in excerpts:
        chapter_name = excerpt.get("chapter") or "未分类"
        
        if chapter_name not in chapter_map:
            chapter_id = f"ch_{len(chapters) + 1:03d}"
            chapter_map[chapter_name] = {
                "chapter_id": chapter_id,
                "chapter_name": chapter_name,
                "summary": f"本章节包含摘录内容",
                "key_points": [],
                "excerpt_count": 0
            }
            chapters.append(chapter_map[chapter_name])
        
        chapter_map[chapter_name]["excerpt_count"] += 1
    
    return {
        "chapters": chapters,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }


def extract_concepts(excerpts: List[Dict]) -> List[Dict]:
    """
    从摘录中提取核心概念（v3.0）
    
    注意：此函数只做初步提取，智能分析由 Agent 完成
    
    参数:
        excerpts: 摘录列表
    
    返回:
        概念列表（待智能体完善定义）
    """
    # 初步提取：使用正则匹配常见关键词模式
    concept_patterns = [
        r'[\u4e00-\u9fa5]{2,4}(?:思想|理论|原则|方法|定律|效应)',
        r'[\u4e00-\u9fa5]{2,4}(?:之|的)(?:定义|概念|含义|本质|核心)',
        r'(?:所谓的)([\u4e00-\u9fa5]{2,4})',
    ]
    
    concepts_found = set()
    
    for excerpt in excerpts:
        content = excerpt.get("content", "")
        for pattern in concept_patterns:
            matches = re.findall(pattern, content)
            concepts_found.update(matches)
    
    # 转换为概念对象
    concepts = []
    for i, name in enumerate(list(concepts_found)[:20]):  # 限制最多20个
        concepts.append({
            "name": name,
            "definition": None,  # 待智能体填充
            "first_appearance": excerpt.get("chapter"),
            "occurrences": []
        })
    
    return concepts


def migrate_to_v3(book_data: Dict) -> Dict:
    """
    将旧版本数据迁移到 v3.0
    
    参数:
        book_data: 原始数据（v1.0 或 v2.0）
    
    返回:
        v3.0 格式数据
    """
    # 检查版本
    version = book_data.get("book_info", {}).get("version", "v1.0")
    
    # 创建 v3.0 基础结构
    v3_data = {
        "book_info": {
            "title": book_data.get("book_info", {}).get("title", "未知书名"),
            "author": book_data.get("book_info", {}).get("author"),
            "status": book_data.get("book_info", {}).get("status", "reading"),
            "reading_stage": book_data.get("book_info", {}).get("reading_stage", "interpretation"),
            "created_at": book_data.get("book_info", {}).get("created_at", datetime.now().strftime("%Y-%m-%d")),
            "completed_at": book_data.get("book_info", {}).get("completed_at"),
            "tags": book_data.get("book_info", {}).get("tags", []),
            "cover": book_data.get("book_info", {}).get("cover"),
            "total_chapters": 0,
            "total_excerpts": len(book_data.get("excerpts", [])),
            "version": "v3.0"
        },
        "chapter_framework": generate_chapter_framework(book_data.get("excerpts", [])),
        "excerpts": [],
        "knowledge_structure": {
            "concept_index": {
                "concepts": [],
                "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            },
            "concept_connections": {
                "connections": [],
                "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            },
            "questions": {
                "pending": [],
                "answered": [],
                "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            },
            "experiments": {
                "items": [],
                "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            },
            "cross_chapter_links": {
                "links": [],
                "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            },
            "reading_output": None
        }
    }
    
    # 更新章节数
    v3_data["book_info"]["total_chapters"] = len(v3_data["chapter_framework"]["chapters"])
    
    # 迁移摘录（转换为五维卡片格式）
    existing_excerpts = book_data.get("excerpts", [])
    concept_map = {}  # 用于去重
    
    for i, excerpt in enumerate(existing_excerpts):
        v3_excerpt = {
            "id": excerpt.get("id", f"exc_{datetime.now().strftime('%Y%m%d%H%M%S')}_{i}"),
            "content": excerpt.get("content", excerpt.get("原文", "")),
            "tags": excerpt.get("tags", excerpt.get("标签", [])),
            "deep_meaning": excerpt.get("deep_meaning", excerpt.get("深层含义", excerpt.get("deep_analysis", ""))),
            "application": excerpt.get("application", excerpt.get("应用", excerpt.get("应用建议", ""))),
            "question": excerpt.get("question", excerpt.get("提问", "")),  # v3.0 新增
            "chapter_id": excerpt.get("chapter_id"),
            "chapter_name": excerpt.get("chapter_name", excerpt.get("chapter", excerpt.get("章节", ""))),
            "created_at": excerpt.get("created_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            "source": excerpt.get("source", excerpt.get("来源", "import"))
        }
        
        # 如果摘录有关联的提问，迁移到 questions
        if v3_excerpt["question"]:
            v3_data["knowledge_structure"]["questions"]["pending"].append({
                "id": f"q_{datetime.now().strftime('%Y%m%d%H%M%S')}_{i}",
                "question": v3_excerpt["question"],
                "source_excerpt": v3_excerpt["id"],
                "created_at": v3_excerpt["created_at"]
            })
        
        v3_data["excerpts"].append(v3_excerpt)
    
    # 从摘录中提取概念
    extracted_concepts = extract_concepts(existing_excerpts)
    v3_data["knowledge_structure"]["concept_index"]["concepts"] = extracted_concepts
    
    return v3_data


def import_notes(
    file_path: str,
    source_type: str = "wechat",
    book_name: Optional[str] = None,
    preview_only: bool = True,
    force_migrate: bool = False
) -> Dict[str, any]:
    """
    批量导入笔记（v3.0）
    
    参数:
        file_path: 导入文件路径
        source_type: 来源类型（wechat/kindle）
        book_name: 书籍名称（可选，从文件中提取）
        preview_only: 是否仅预览（不保存）
        force_migrate: 是否强制迁移旧版本数据
    
    返回:
        {
            "success": True/False,
            "preview": {
                "total_count": 总数,
                "chapters": {"章节名": 数量},
                "framework": 章节框架预览,
                "sample": [示例摘录]
            },
            "imported_count": 导入数量（如果已保存）,
            "migrated": 是否发生了版本迁移,
            "error": "错误信息（如果失败）"
        }
    """
    try:
        # 解析文件
        if source_type == "wechat":
            parse_result = parse_wechat_export(file_path)
        elif source_type == "kindle":
            parse_result = parse_kindle_export(file_path)
        else:
            return {
                "success": False,
                "error": f"不支持的来源类型: {source_type}"
            }
        
        if not parse_result["success"]:
            return parse_result
        
        excerpts = parse_result["excerpts"]
        chapters_found = parse_result["chapters"]
        
        # 生成预览
        chapters_count = {}
        for excerpt in excerpts:
            chapter = excerpt.get("chapter") or "未分类"
            chapters_count[chapter] = chapters_count.get(chapter, 0) + 1
        
        # 生成章节框架预览
        framework_preview = generate_chapter_framework(excerpts)
        
        preview = {
            "total_count": len(excerpts),
            "chapters": chapters_count,
            "framework": framework_preview,
            "sample": excerpts[:3]
        }
        
        if preview_only:
            return {
                "success": True,
                "preview": preview,
                "imported_count": 0,
                "migrated": False
            }
        
        # 保存到书籍档案
        base_path = "./reading-notes"
        books_dir = os.path.join(base_path, "books")
        
        if not os.path.exists(books_dir):
            os.makedirs(books_dir)
        
        # 如果没有指定书名，从文件名提取
        if not book_name:
            book_name = Path(file_path).stem
        
        book_path = os.path.join(books_dir, f"{book_name}.json")
        
        # 检查是否需要迁移
        migrated = False
        if os.path.exists(book_path):
            with open(book_path, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
            
            existing_version = existing_data.get("book_info", {}).get("version", "v1.0")
            
            if existing_version != "v3.0" or force_migrate:
                # 迁移到 v3.0
                book_data = migrate_to_v3(existing_data)
                migrated = True
            else:
                book_data = existing_data
        else:
            # 创建新的 v3.0 档案
            book_data = {
                "book_info": {
                    "title": book_name,
                    "author": None,
                    "status": "reading",
                    "reading_stage": "interpretation",
                    "created_at": datetime.now().strftime("%Y-%m-%d"),
                    "tags": [],
                    "total_chapters": 0,
                    "total_excerpts": 0,
                    "version": "v3.0"
                },
                "chapter_framework": framework_preview,
                "excerpts": [],
                "knowledge_structure": {
                    "concept_index": {
                        "concepts": [],
                        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    },
                    "concept_connections": {
                        "connections": [],
                        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    },
                    "questions": {
                        "pending": [],
                        "answered": [],
                        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    },
                    "experiments": {
                        "items": [],
                        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    },
                    "cross_chapter_links": {
                        "links": [],
                        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    },
                    "reading_output": None
                }
            }
        
        # 添加摘录（带时间戳和ID）
        start_idx = len(book_data["excerpts"])
        for i, excerpt in enumerate(excerpts):
            new_excerpt = {
                "id": f"exc_{datetime.now().strftime('%Y%m%d%H%M%S')}_{start_idx + i}",
                "content": excerpt.get("content"),
                "tags": excerpt.get("tags", []),
                "deep_meaning": excerpt.get("deep_meaning", ""),
                "application": excerpt.get("application", ""),
                "question": excerpt.get("question", ""),
                "chapter_name": excerpt.get("chapter"),
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "source": excerpt.get("source", source_type)
            }
            
            # 更新章节ID
            chapter_name = excerpt.get("chapter") or "未分类"
            for chapter in book_data["chapter_framework"]["chapters"]:
                if chapter["chapter_name"] == chapter_name:
                    new_excerpt["chapter_id"] = chapter["chapter_id"]
                    chapter["excerpt_count"] = chapter.get("excerpt_count", 0) + 1
                    break
            
            book_data["excerpts"].append(new_excerpt)
        
        # 更新统计
        book_data["book_info"]["total_excerpts"] = len(book_data["excerpts"])
        book_data["book_info"]["total_chapters"] = len(book_data["chapter_framework"]["chapters"])
        book_data["chapter_framework"]["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 保存
        with open(book_path, 'w', encoding='utf-8') as f:
            json.dump(book_data, f, ensure_ascii=False, indent=2)
        
        return {
            "success": True,
            "preview": preview,
            "imported_count": len(excerpts),
            "migrated": migrated
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"导入失败: {str(e)}"
        }


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='笔记批量导入工具（v3.0）')
    parser.add_argument('file_path', help='导入文件路径')
    parser.add_argument('--source', '-s', choices=['wechat', 'kindle'], 
                       default='wechat', help='来源类型')
    parser.add_argument('--book', '-b', help='书籍名称')
    parser.add_argument('--save', action='store_true', help='保存到档案（默认仅预览）')
    parser.add_argument('--migrate', '-m', action='store_true', help='强制迁移旧版本数据')
    
    args = parser.parse_args()
    
    result = import_notes(
        file_path=args.file_path,
        source_type=args.source,
        book_name=args.book,
        preview_only=not args.save,
        force_migrate=args.migrate
    )
    
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
