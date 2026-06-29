#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
阅读统计脚本（v3.0）
生成阅读统计报告
支持 v1.0/v2.0/v3.0 数据结构
"""

import sys
import json
import os
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from typing import Dict, List, Optional
from pathlib import Path


def get_book_stats(book_data: Dict) -> Dict:
    """
    获取单本书的统计数据（v3.0 增强版）
    
    参数:
        book_data: 书籍数据
    
    返回:
        统计数据字典
    """
    book_info = book_data.get("book_info", {})
    excerpts = book_data.get("excerpts", [])
    
    # v3.0 知识结构
    ks = book_data.get("knowledge_structure", {})
    
    stats = {
        "title": book_info.get("title", "未知书名"),
        "author": book_info.get("author"),
        "status": book_info.get("status", "reading"),
        "reading_stage": book_info.get("reading_stage", "interpretation"),
        "created_at": book_info.get("created_at"),
        "completed_at": book_info.get("completed_at"),
        "version": book_info.get("version", "v1.0"),
        "excerpt_count": len(excerpts),
        "chapters": set(),
        "tags": Counter(),
        "daily_counts": defaultdict(int),
        "sources": Counter(),
        # v3.0 新增统计
        "five_dimension_stats": {
            "with_deep_meaning": 0,
            "with_application": 0,
            "with_question": 0,
            "with_tags": 0,
            "complete_cards": 0  # 五维全齐
        },
        "framework_stats": {
            "chapter_count": 0,
            "total_key_points": 0,
            "chapters_with_excerpts": 0
        },
        "knowledge_structure_stats": {
            "concept_count": 0,
            "connection_count": 0,
            "pending_questions": 0,
            "answered_questions": 0,
            "experiments_count": 0,
            "cross_chapter_links": 0
        }
    }
    
    for excerpt in excerpts:
        # 章节统计（兼容 v1.0/v2.0/v3.0）
        chapter = excerpt.get("chapter_name") or excerpt.get("chapter", "")
        if chapter:
            stats["chapters"].add(chapter)
        
        # 标签统计
        tags = excerpt.get("tags", [])
        stats["tags"].update(tags)
        
        # v3.0 五维卡片统计
        if excerpt.get("tags"):
            stats["five_dimension_stats"]["with_tags"] += 1
        if excerpt.get("deep_meaning"):
            stats["five_dimension_stats"]["with_deep_meaning"] += 1
        if excerpt.get("application"):
            stats["five_dimension_stats"]["with_application"] += 1
        if excerpt.get("question"):
            stats["five_dimension_stats"]["with_question"] += 1
        
        # 五维全齐统计
        if all([excerpt.get("tags"), excerpt.get("deep_meaning"), 
                 excerpt.get("application"), excerpt.get("question")]):
            stats["five_dimension_stats"]["complete_cards"] += 1
        
        # 日期统计
        created_at = excerpt.get("created_at")
        if created_at:
            date_str = created_at.split(" ")[0] if " " in created_at else created_at
            stats["daily_counts"][date_str] += 1
        
        # 来源统计
        source = excerpt.get("source", "manual")
        stats["sources"][source] += 1
    
    # v3.0 章节框架统计
    framework = book_data.get("chapter_framework", {})
    chapters_fw = framework.get("chapters", [])
    stats["framework_stats"]["chapter_count"] = len(chapters_fw)
    
    for chapter in chapters_fw:
        key_points = chapter.get("key_points", [])
        stats["framework_stats"]["total_key_points"] += len(key_points)
        if chapter.get("excerpt_count", 0) > 0:
            stats["framework_stats"]["chapters_with_excerpts"] += 1
    
    # v3.0 知识结构统计
    concept_index = ks.get("concept_index", {})
    connections = ks.get("concept_connections", {}).get("connections", [])
    questions = ks.get("questions", {})
    experiments = ks.get("experiments", {}).get("items", [])
    cross_links = ks.get("cross_chapter_links", {}).get("links", [])
    
    stats["knowledge_structure_stats"]["concept_count"] = len(concept_index.get("concepts", []))
    stats["knowledge_structure_stats"]["connection_count"] = len(connections)
    stats["knowledge_structure_stats"]["pending_questions"] = len(questions.get("pending", []))
    stats["knowledge_structure_stats"]["answered_questions"] = len(questions.get("answered", []))
    stats["knowledge_structure_stats"]["experiments_count"] = len(experiments)
    stats["knowledge_structure_stats"]["cross_chapter_links"] = len(cross_links)
    
    # 转换 set 为 list 以便 JSON 序列化
    stats["chapters"] = list(stats["chapters"])
    stats["chapter_count"] = len(stats["chapters"])
    stats["tags"] = dict(stats["tags"].most_common(10))
    stats["daily_counts"] = dict(sorted(stats["daily_counts"].items()))
    stats["sources"] = dict(stats["sources"])
    
    return stats


def get_overall_stats(base_path: str = "./reading-notes") -> Dict[str, any]:
    """
    获取所有书籍的统计数据（v3.0 增强版）
    
    参数:
        base_path: 笔记存储根目录
    
    返回:
        {
            "success": True/False,
            "stats": {
                "total_books": 书籍总数,
                "books_by_status": {"reading": X, "completed": Y, "archived": Z},
                "books_by_stage": {"inspection": X, "interpretation": Y, ...},
                "books_by_version": {"v3.0": X, "v2.0": Y, ...},
                "total_excerpts": 总摘录数,
                "complete_five_dimension_cards": 五维全齐的摘录数,
                "total_concepts": 概念总数,
                "total_connections": 联结总数,
                "total_questions": 问题总数,
                "books": [每本书的统计],
                "all_tags": Counter,
                "reading_days": 阅读天数
            },
            "error": "错误信息（如果失败）"
        }
    """
    try:
        books_dir = os.path.join(base_path, "books")
        
        if not os.path.exists(books_dir):
            return {
                "success": False,
                "error": f"笔记目录不存在: {books_dir}"
            }
        
        book_files = [f for f in os.listdir(books_dir) if f.endswith('.json')]
        
        all_stats = []
        books_by_status = defaultdict(int)
        books_by_stage = defaultdict(int)
        books_by_version = defaultdict(int)
        total_excerpts = 0
        all_tags = Counter()
        all_dates = set()
        
        # v3.0 汇总统计
        complete_five_dimension_cards = 0
        total_concepts = 0
        total_connections = 0
        total_questions = 0
        
        for book_file in book_files:
            book_path = os.path.join(books_dir, book_file)
            
            with open(book_path, 'r', encoding='utf-8') as f:
                book_data = json.load(f)
            
            stats = get_book_stats(book_data)
            all_stats.append(stats)
            
            books_by_status[stats["status"]] += 1
            books_by_stage[stats["reading_stage"]] += 1
            books_by_version[stats["version"]] += 1
            total_excerpts += stats["excerpt_count"]
            all_tags.update(stats["tags"])
            all_dates.update(stats["daily_counts"].keys())
            
            # v3.0 统计
            complete_five_dimension_cards += stats["five_dimension_stats"]["complete_cards"]
            total_concepts += stats["knowledge_structure_stats"]["concept_count"]
            total_connections += stats["knowledge_structure_stats"]["connection_count"]
            total_questions += (stats["knowledge_structure_stats"]["pending_questions"] + 
                               stats["knowledge_structure_stats"]["answered_questions"])
        
        # 生成报告
        report = {
            "total_books": len(book_files),
            "books_by_status": dict(books_by_status),
            "books_by_stage": dict(books_by_stage),
            "books_by_version": dict(books_by_version),
            "total_excerpts": total_excerpts,
            "complete_five_dimension_cards": complete_five_dimension_cards,
            "total_concepts": total_concepts,
            "total_connections": total_connections,
            "total_questions": total_questions,
            "books": all_stats,
            "all_tags": dict(all_tags.most_common(20)),
            "reading_days": len(all_dates),
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        return {
            "success": True,
            "stats": report
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"统计失败: {str(e)}"
        }


def generate_reading_report(book_name: str, base_path: str = "./reading-notes") -> Dict[str, any]:
    """
    生成单本书的阅读报告（v3.0 增强版）
    
    参数:
        book_name: 书籍名称
        base_path: 笔记存储路径
    
    返回:
        {
            "success": True/False,
            "report": {
                "book_info": 书籍信息,
                "statistics": 统计数据,
                "timeline": 时间线,
                "tag_cloud": 标签云,
                "chapters": 章节分布,
                "five_dimension_analysis": 五维卡片分析（v3.0）,
                "knowledge_structure_summary": 知识结构概览（v3.0）,
                "reading_progress": 阅读进度（v3.0）
            },
            "error": "错误信息（如果失败）"
        }
    """
    try:
        book_file = os.path.join(base_path, "books", f"{book_name}.json")
        
        if not os.path.exists(book_file):
            return {
                "success": False,
                "error": f"书籍档案不存在: {book_name}"
            }
        
        with open(book_file, 'r', encoding='utf-8') as f:
            book_data = json.load(f)
        
        stats = get_book_stats(book_data)
        version = book_data.get("book_info", {}).get("version", "v1.0")
        
        # 生成章节分布
        excerpts = book_data.get("excerpts", [])
        chapter_dist = Counter()
        for excerpt in excerpts:
            chapter = excerpt.get("chapter_name") or excerpt.get("chapter", "未分类")
            chapter_dist[chapter] += 1
        
        # 生成时间线（最近7天）
        timeline = []
        today = datetime.now()
        for i in range(7):
            date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
            count = stats["daily_counts"].get(date, 0)
            timeline.append({
                "date": date,
                "count": count
            })
        timeline.reverse()
        
        # v3.0 五维卡片分析
        fd_stats = stats["five_dimension_stats"]
        excerpt_count = stats["excerpt_count"]
        five_dimension_analysis = {
            "completion_rate": round(fd_stats["complete_cards"] / excerpt_count * 100, 1) if excerpt_count > 0 else 0,
            "deep_meaning_rate": round(fd_stats["with_deep_meaning"] / excerpt_count * 100, 1) if excerpt_count > 0 else 0,
            "application_rate": round(fd_stats["with_application"] / excerpt_count * 100, 1) if excerpt_count > 0 else 0,
            "question_rate": round(fd_stats["with_question"] / excerpt_count * 100, 1) if excerpt_count > 0 else 0,
            "tags_rate": round(fd_stats["with_tags"] / excerpt_count * 100, 1) if excerpt_count > 0 else 0
        }
        
        # v3.0 知识结构概览
        ks_stats = stats["knowledge_structure_stats"]
        concept_index = book_data.get("knowledge_structure", {}).get("concept_index", {})
        concepts = concept_index.get("concepts", [])[:5]  # Top 5 概念
        
        knowledge_structure_summary = {
            "concept_count": ks_stats["concept_count"],
            "top_concepts": [{"name": c.get("name"), "occurrences": len(c.get("occurrences", []))} for c in concepts],
            "connection_count": ks_stats["connection_count"],
            "pending_questions": ks_stats["pending_questions"],
            "answered_questions": ks_stats["answered_questions"],
            "experiments_count": ks_stats["experiments_count"],
            "cross_chapter_links": ks_stats["cross_chapter_links"]
        }
        
        # v3.0 阅读进度
        framework = book_data.get("chapter_framework", {})
        framework_chapters = len(framework.get("chapters", []))
        fw_stats = stats["framework_stats"]
        
        reading_progress = {
            "framework_chapters": framework_chapters,
            "chapters_with_excerpts": fw_stats["chapters_with_excerpts"],
            "framework_completion_rate": round(fw_stats["chapters_with_excerpts"] / framework_chapters * 100, 1) if framework_chapters > 0 else 0,
            "total_key_points": fw_stats["total_key_points"],
            "reading_stage": stats["reading_stage"]
        }
        
        report = {
            "book_info": book_data.get("book_info", {}),
            "version": version,
            "statistics": {
                "excerpt_count": stats["excerpt_count"],
                "chapter_count": stats["chapter_count"],
                "tag_count": len(stats["tags"]),
                "reading_days": len(stats["daily_counts"])
            },
            "timeline": timeline,
            "tag_cloud": stats["tags"],
            "chapter_distribution": dict(chapter_dist.most_common(10)),
            "sources": stats["sources"],
            # v3.0 新增
            "five_dimension_analysis": five_dimension_analysis,
            "knowledge_structure_summary": knowledge_structure_summary,
            "reading_progress": reading_progress,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        return {
            "success": True,
            "report": report
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"生成报告失败: {str(e)}"
        }


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='阅读统计工具（v3.0）')
    parser.add_argument('--book', '-b', help='指定书籍名称（不指定则统计所有书籍）')
    parser.add_argument('--base-path', default='./reading-notes', help='笔记存储路径')
    
    args = parser.parse_args()
    
    if args.book:
        result = generate_reading_report(args.book, args.base_path)
    else:
        result = get_overall_stats(args.base_path)
    
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
