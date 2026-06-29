#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
笔记搜索脚本（v3.0）
支持关键词搜索、标签筛选、章节筛选、概念搜索
支持 v1.0/v2.0/v3.0 数据结构
"""

import sys
import json
import os
import re
from typing import Dict, List, Optional
from pathlib import Path


def load_book_data(book_path: str) -> Dict:
    """加载书籍档案"""
    try:
        with open(book_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        return {"error": str(e)}


def search_in_excerpt(excerpt: Dict, keyword: str, case_sensitive: bool = False) -> Dict:
    """
    在单条摘录中搜索关键词（v3.0 支持五维字段）
    
    返回:
        {
            "matched": True/False,
            "content_highlight": "高亮后的内容",
            "match_fields": ["匹配的字段列表"]
        }
    """
    if not keyword:
        return {
            "matched": True,
            "content_highlight": excerpt.get("content", ""),
            "match_fields": []
        }
    
    flags = 0 if case_sensitive else re.IGNORECASE
    keyword_pattern = re.compile(re.escape(keyword), flags)
    
    matched = False
    match_fields = []
    content_highlight = excerpt.get("content", "")
    
    # 在内容中搜索
    if keyword_pattern.search(content_highlight):
        matched = True
        match_fields.append("content")
        # 高亮关键词
        content_highlight = keyword_pattern.sub(
            f'**{keyword}**',
            content_highlight
        )
    
    # 在深层含义中搜索（v3.0 五维之一）
    if excerpt.get("deep_meaning") and keyword_pattern.search(excerpt["deep_meaning"]):
        matched = True
        match_fields.append("deep_meaning")
    
    # 在应用建议中搜索（v3.0 五维之一）
    if excerpt.get("application") and keyword_pattern.search(excerpt["application"]):
        matched = True
        match_fields.append("application")
    
    # 在提问中搜索（v3.0 五维之一）
    if excerpt.get("question") and keyword_pattern.search(excerpt["question"]):
        matched = True
        match_fields.append("question")
    
    # 在标签中搜索（v3.0 五维之一）
    tags = excerpt.get("tags", [])
    if any(keyword.lower() in tag.lower() for tag in tags):
        matched = True
        match_fields.append("tags")
    
    return {
        "matched": matched,
        "content_highlight": content_highlight,
        "match_fields": match_fields
    }


def search_concepts(book_data: Dict, concept_keyword: str, case_sensitive: bool = False) -> Dict:
    """
    搜索概念索引（v3.0 新增）
    
    返回:
        {
            "matched": True/False,
            "concepts": [匹配的概念列表],
            "connections": [关联的概念联结]
        }
    """
    concept_index = book_data.get("knowledge_structure", {}).get("concept_index", {})
    connections = book_data.get("knowledge_structure", {}).get("concept_connections", {}).get("connections", [])
    
    matched_concepts = []
    matched_connections = []
    
    flags = 0 if case_sensitive else re.IGNORECASE
    keyword_pattern = re.compile(re.escape(concept_keyword), flags)
    
    # 搜索概念
    for concept in concept_index.get("concepts", []):
        name = concept.get("name", "")
        definition = concept.get("definition", "")
        
        if keyword_pattern.search(name) or keyword_pattern.search(definition):
            matched_concepts.append(concept)
    
    # 搜索概念联结
    for conn in connections:
        from_concept = conn.get("from", "")
        to_concept = conn.get("to", "")
        relationship = conn.get("relationship", "")
        
        if (keyword_pattern.search(from_concept) or 
            keyword_pattern.search(to_concept) or 
            keyword_pattern.search(relationship)):
            matched_connections.append(conn)
    
    return {
        "matched": len(matched_concepts) > 0 or len(matched_connections) > 0,
        "concepts": matched_concepts,
        "connections": matched_connections
    }


def search_questions(book_data: Dict, question_keyword: str, case_sensitive: bool = False) -> Dict:
    """
    搜索待思考问题（v3.0 新增）
    
    返回:
        {
            "matched": True/False,
            "pending": [待回答问题],
            "answered": [已回答问题]
        }
    """
    questions = book_data.get("knowledge_structure", {}).get("questions", {})
    pending = questions.get("pending", [])
    answered = questions.get("answered", [])
    
    matched_pending = []
    matched_answered = []
    
    flags = 0 if case_sensitive else re.IGNORECASE
    keyword_pattern = re.compile(re.escape(question_keyword), flags)
    
    # 搜索待回答问题
    for q in pending:
        question_text = q.get("question", "")
        if keyword_pattern.search(question_text):
            matched_pending.append(q)
    
    # 搜索已回答问题
    for q in answered:
        question_text = q.get("question", "")
        answer_text = q.get("answer", "")
        
        if keyword_pattern.search(question_text) or keyword_pattern.search(answer_text):
            matched_answered.append(q)
    
    return {
        "matched": len(matched_pending) > 0 or len(matched_answered) > 0,
        "pending": matched_pending,
        "answered": matched_answered
    }


def search_notes(
    base_path: str = "./reading-notes",
    keyword: Optional[str] = None,
    book_name: Optional[str] = None,
    tag: Optional[str] = None,
    chapter: Optional[str] = None,
    concept: Optional[str] = None,
    question: Optional[str] = None,
    case_sensitive: bool = False
) -> Dict[str, any]:
    """
    搜索笔记（v3.0）
    
    参数:
        base_path: 笔记存储根目录
        keyword: 搜索关键词（搜索摘录）
        book_name: 指定书籍名称
        tag: 按标签筛选
        chapter: 按章节筛选
        concept: 按概念搜索（v3.0 新增）
        question: 按问题搜索（v3.0 新增）
        case_sensitive: 是否区分大小写
    
    返回:
        {
            "success": True/False,
            "total_count": 总匹配数,
            "excerpts": [摘录结果],
            "concepts": [概念结果，v3.0],
            "questions": [问题结果，v3.0],
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
        
        excerpt_results = []
        concept_results = []
        question_results = []
        
        # 确定要搜索的书籍
        if book_name:
            # 搜索指定书籍
            book_files = [f"{book_name}.json"]
        else:
            # 搜索所有书籍
            book_files = [f for f in os.listdir(books_dir) if f.endswith('.json')]
        
        for book_file in book_files:
            book_path = os.path.join(books_dir, book_file)
            book_data = load_book_data(book_path)
            
            if "error" in book_data:
                continue
            
            book_title = book_data.get("book_info", {}).get("title", book_file.replace('.json', ''))
            excerpts = book_data.get("excerpts", [])
            
            # 搜索概念（v3.0）
            if concept:
                concept_result = search_concepts(book_data, concept, case_sensitive)
                if concept_result["matched"]:
                    concept_results.append({
                        "book_name": book_title,
                        "concepts": concept_result["concepts"],
                        "connections": concept_result["connections"]
                    })
            
            # 搜索问题（v3.0）
            if question:
                question_result = search_questions(book_data, question, case_sensitive)
                if question_result["matched"]:
                    question_results.append({
                        "book_name": book_title,
                        "pending": question_result["pending"],
                        "answered": question_result["answered"]
                    })
            
            # 搜索摘录
            for excerpt in excerpts:
                # 章节筛选
                if chapter:
                    excerpt_chapter = excerpt.get("chapter_name") or excerpt.get("chapter", "")
                    if chapter.lower() not in excerpt_chapter.lower():
                        continue
                
                # 标签筛选
                if tag:
                    excerpt_tags = excerpt.get("tags", [])
                    if not any(tag.lower() in t.lower() for t in excerpt_tags):
                        continue
                
                # 关键词搜索（如果指定了关键词）
                if keyword:
                    search_result = search_in_excerpt(excerpt, keyword, case_sensitive)
                    
                    if search_result["matched"]:
                        excerpt_results.append({
                            "book_name": book_title,
                            "excerpt": excerpt,
                            "content_highlight": search_result["content_highlight"],
                            "match_fields": search_result["match_fields"]
                        })
                else:
                    # 如果没有关键词，返回所有符合条件的摘录
                    excerpt_results.append({
                        "book_name": book_title,
                        "excerpt": excerpt,
                        "content_highlight": excerpt.get("content", ""),
                        "match_fields": []
                    })
        
        return {
            "success": True,
            "total_count": len(excerpt_results) + len(concept_results) + len(question_results),
            "excerpts": excerpt_results,
            "concepts": concept_results,
            "questions": question_results
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"搜索失败: {str(e)}"
        }


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='笔记搜索工具（v3.0）')
    parser.add_argument('--keyword', '-k', help='搜索关键词')
    parser.add_argument('--book', '-b', help='指定书籍名称')
    parser.add_argument('--tag', '-t', help='按标签筛选')
    parser.add_argument('--chapter', '-c', help='按章节筛选')
    parser.add_argument('--concept', '-n', help='按概念搜索（v3.0）')
    parser.add_argument('--question', '-q', help='按问题搜索（v3.0）')
    parser.add_argument('--case-sensitive', action='store_true', help='区分大小写')
    parser.add_argument('--base-path', default='./reading-notes', help='笔记存储路径')
    
    args = parser.parse_args()
    
    result = search_notes(
        base_path=args.base_path,
        keyword=args.keyword,
        book_name=args.book,
        tag=args.tag,
        chapter=args.chapter,
        concept=args.concept,
        question=args.question,
        case_sensitive=args.case_sensitive
    )
    
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
