#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多格式导出脚本（v3.0）
支持导出为 Markdown、HTML、PDF 格式
支持完整知识结构导出
"""

import sys
import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path


def export_framework_to_markdown(book_data: Dict) -> str:
    """导出章节框架（v3.0）"""
    framework = book_data.get("chapter_framework", {})
    chapters = framework.get("chapters", [])
    
    md_lines = []
    md_lines.append("## 章节框架")
    md_lines.append("")
    
    for chapter in chapters:
        md_lines.append(f"### {chapter.get('chapter_name', '未知章节')}")
        md_lines.append("")
        
        summary = chapter.get("summary", "")
        if summary:
            md_lines.append(f"**摘要**: {summary}")
            md_lines.append("")
        
        key_points = chapter.get("key_points", [])
        if key_points:
            md_lines.append("**关键要点**:")
            for point in key_points:
                md_lines.append(f"- {point}")
            md_lines.append("")
        
        excerpt_count = chapter.get("excerpt_count", 0)
        md_lines.append(f"**摘录数量**: {excerpt_count}")
        md_lines.append("")
        md_lines.append("---")
        md_lines.append("")
    
    return '\n'.join(md_lines)


def export_five_dimension_card(excerpt: Dict) -> str:
    """导出五维摘录卡片（v3.0）"""
    md_lines = []
    
    # 原文
    md_lines.append("> " + excerpt.get("content", ""))
    md_lines.append("")
    
    # 标签
    tags = excerpt.get("tags", [])
    if tags:
        md_lines.append(f"**标签**: {', '.join(tags)}")
        md_lines.append("")
    
    # 深层含义
    deep_meaning = excerpt.get("deep_meaning", "")
    if deep_meaning:
        md_lines.append("**深层含义**:")
        md_lines.append("")
        md_lines.append(deep_meaning)
        md_lines.append("")
    
    # 应用
    application = excerpt.get("application", "")
    if application:
        md_lines.append("**应用**:")
        md_lines.append("")
        md_lines.append(application)
        md_lines.append("")
    
    # 提问
    question = excerpt.get("question", "")
    if question:
        md_lines.append("**提问**:")
        md_lines.append("")
        md_lines.append(question)
        md_lines.append("")
    
    return '\n'.join(md_lines)


def export_concept_index_to_markdown(book_data: Dict) -> str:
    """导出核心概念索引（v3.0）"""
    concept_index = book_data.get("knowledge_structure", {}).get("concept_index", {})
    concepts = concept_index.get("concepts", [])
    
    md_lines = []
    md_lines.append("## 核心概念索引")
    md_lines.append("")
    
    if not concepts:
        md_lines.append("*暂无概念索引*")
        md_lines.append("")
        return '\n'.join(md_lines)
    
    for i, concept in enumerate(concepts, 1):
        md_lines.append(f"### {i}. {concept.get('name', '未知概念')}")
        md_lines.append("")
        
        definition = concept.get("definition", "")
        if definition:
            md_lines.append(f"**定义**: {definition}")
            md_lines.append("")
        
        first_appearance = concept.get("first_appearance", "")
        if first_appearance:
            md_lines.append(f"**首次出现**: {first_appearance}")
            md_lines.append("")
        
        occurrences = concept.get("occurrences", [])
        if occurrences:
            md_lines.append(f"**出现位置**: {len(occurrences)}处")
            md_lines.append("")
        
        md_lines.append("---")
        md_lines.append("")
    
    return '\n'.join(md_lines)


def export_concept_connections_to_markdown(book_data: Dict) -> str:
    """导出概念联结图（v3.0）"""
    connections = book_data.get("knowledge_structure", {}).get("concept_connections", {}).get("connections", [])
    
    md_lines = []
    md_lines.append("## 概念联结图")
    md_lines.append("")
    
    if not connections:
        md_lines.append("*暂无概念联结*")
        md_lines.append("")
        return '\n'.join(md_lines)
    
    for conn in connections:
        from_concept = conn.get("from", "")
        to_concept = conn.get("to", "")
        relationship = conn.get("relationship", "")
        
        md_lines.append(f"- **{from_concept}** → **{to_concept}**")
        if relationship:
            md_lines.append(f"  - 关系: {relationship}")
        md_lines.append("")
    
    return '\n'.join(md_lines)


def export_questions_to_markdown(book_data: Dict) -> str:
    """导出待思考问题（v3.0）"""
    questions = book_data.get("knowledge_structure", {}).get("questions", {})
    pending = questions.get("pending", [])
    answered = questions.get("answered", [])
    
    md_lines = []
    md_lines.append("## 待思考问题")
    md_lines.append("")
    
    if pending:
        md_lines.append("### 待回答")
        md_lines.append("")
        for q in pending:
            md_lines.append(f"- {q.get('question', '')}")
        md_lines.append("")
    
    if answered:
        md_lines.append("### 已回答")
        md_lines.append("")
        for q in answered:
            md_lines.append(f"- **{q.get('question', '')}**")
            answer = q.get('answer', '')
            if answer:
                md_lines.append(f"  - 回答: {answer}")
        md_lines.append("")
    
    if not pending and not answered:
        md_lines.append("*暂无问题*")
        md_lines.append("")
    
    return '\n'.join(md_lines)


def export_experiments_to_markdown(book_data: Dict) -> str:
    """导出关键实验/研究（v3.0）"""
    experiments = book_data.get("knowledge_structure", {}).get("experiments", {}).get("items", [])
    
    md_lines = []
    md_lines.append("## 关键实验/研究")
    md_lines.append("")
    
    if not experiments:
        md_lines.append("*暂无实验/研究记录*")
        md_lines.append("")
        return '\n'.join(md_lines)
    
    for exp in experiments:
        md_lines.append(f"### {exp.get('name', '未知实验')}")
        md_lines.append("")
        
        description = exp.get("description", "")
        if description:
            md_lines.append(f"**描述**: {description}")
            md_lines.append("")
        
        researcher = exp.get("researcher", "")
        year = exp.get("year", "")
        if researcher or year:
            md_lines.append(f"**研究者**: {researcher} {year}".strip())
            md_lines.append("")
        
        md_lines.append("---")
        md_lines.append("")
    
    return '\n'.join(md_lines)


def export_cross_chapter_links_to_markdown(book_data: Dict) -> str:
    """导出跨章联结表（v3.0）"""
    cross_links = book_data.get("knowledge_structure", {}).get("cross_chapter_links", {}).get("links", [])
    
    md_lines = []
    md_lines.append("## 跨章联结")
    md_lines.append("")
    
    if not cross_links:
        md_lines.append("*暂无跨章联结*")
        md_lines.append("")
        return '\n'.join(md_lines)
    
    for link in cross_links:
        chapter_a = link.get("chapter_a", "")
        chapter_b = link.get("chapter_b", "")
        relationship = link.get("relationship", "")
        
        md_lines.append(f"- **{chapter_a}** ↔ **{chapter_b}**")
        if relationship:
            md_lines.append(f"  - 关系: {relationship}")
        md_lines.append("")
    
    return '\n'.join(md_lines)


def export_reading_output_to_markdown(book_data: Dict) -> str:
    """导出阅读输出（v3.0）"""
    reading_output = book_data.get("knowledge_structure", {}).get("reading_output")
    
    md_lines = []
    md_lines.append("## 阅读输出")
    md_lines.append("")
    
    if not reading_output:
        md_lines.append("*暂无阅读输出*")
        md_lines.append("")
        return '\n'.join(md_lines)
    
    summary = reading_output.get("summary", "")
    if summary:
        md_lines.append("### 核心观点总结")
        md_lines.append("")
        md_lines.append(summary)
        md_lines.append("")
    
    applications = reading_output.get("applications", [])
    if applications:
        md_lines.append("### 应用场景")
        md_lines.append("")
        for app in applications:
            md_lines.append(f"- {app}")
        md_lines.append("")
    
    knowledge_connections = reading_output.get("knowledge_connections", [])
    if knowledge_connections:
        md_lines.append("### 知识关联")
        md_lines.append("")
        for conn in knowledge_connections:
            md_lines.append(f"- {conn}")
        md_lines.append("")
    
    return '\n'.join(md_lines)


def export_to_markdown(
    book_data: Dict,
    include_framework: bool = True,
    include_analysis: bool = True,
    include_knowledge_structure: bool = True
) -> str:
    """
    导出为 Markdown 格式（v3.0 完整版）
    
    参数:
        book_data: 书籍数据
        include_framework: 是否包含章节框架
        include_analysis: 是否包含深层分析（五维卡片）
        include_knowledge_structure: 是否包含知识结构
    
    返回:
        Markdown 格式的文本
    """
    book_info = book_data.get("book_info", {})
    excerpts = book_data.get("excerpts", [])
    
    # 按章节组织
    chapters = {}
    for excerpt in excerpts:
        chapter_name = excerpt.get("chapter_name") or excerpt.get("chapter") or "未分类"
        if chapter_name not in chapters:
            chapters[chapter_name] = []
        chapters[chapter_name].append(excerpt)
    
    # 生成 Markdown
    md_lines = []
    
    # 标题
    md_lines.append(f"# {book_info.get('title', '未知书名')}")
    md_lines.append("")
    
    # 元信息
    if book_info.get("author"):
        md_lines.append(f"**作者**: {book_info['author']}")
    if book_info.get("tags"):
        md_lines.append(f"**标签**: {', '.join(book_info['tags'])}")
    md_lines.append(f"**创建时间**: {book_info.get('created_at', '未知')}")
    md_lines.append(f"**摘录数量**: {len(excerpts)}")
    md_lines.append(f"**数据版本**: {book_info.get('version', 'v1.0')}")
    md_lines.append("")
    md_lines.append("---")
    md_lines.append("")
    
    # 章节框架（v3.0 新增）
    if include_framework and book_data.get("chapter_framework"):
        md_lines.append(export_framework_to_markdown(book_data))
    
    # 知识结构模块（v3.0 新增）
    if include_knowledge_structure:
        md_lines.append(export_concept_index_to_markdown(book_data))
        md_lines.append(export_concept_connections_to_markdown(book_data))
        md_lines.append(export_questions_to_markdown(book_data))
        md_lines.append(export_experiments_to_markdown(book_data))
        md_lines.append(export_cross_chapter_links_to_markdown(book_data))
        md_lines.append(export_reading_output_to_markdown(book_data))
    
    # 五维摘录卡片（v3.0 完整版）
    if include_analysis:
        md_lines.append("## 五维摘录卡片")
        md_lines.append("")
        
        for chapter_name, chapter_excerpts in chapters.items():
            md_lines.append(f"### {chapter_name}")
            md_lines.append("")
            
            for i, excerpt in enumerate(chapter_excerpts, 1):
                md_lines.append(f"#### 摘录 {i}")
                md_lines.append("")
                md_lines.append(export_five_dimension_card(excerpt))
                md_lines.append("")
                md_lines.append("---")
                md_lines.append("")
    else:
        # 简化版：仅原文
        md_lines.append("## 摘录列表")
        md_lines.append("")
        
        for chapter_name, chapter_excerpts in chapters.items():
            md_lines.append(f"### {chapter_name}")
            md_lines.append("")
            
            for i, excerpt in enumerate(chapter_excerpts, 1):
                md_lines.append(f"**{i}.** {excerpt.get('content', '')}")
                md_lines.append("")
    
    return '\n'.join(md_lines)


def export_to_html(book_data: Dict, include_framework: bool = True,
                   include_analysis: bool = True, include_knowledge_structure: bool = True) -> str:
    """
    导出为 HTML 格式（v3.0 完整版）
    """
    book_info = book_data.get("book_info", {})
    excerpts = book_data.get("excerpts", [])
    version = book_info.get("version", "v1.0")
    
    html_lines = []
    
    # HTML 头部
    html_lines.append('<!DOCTYPE html>')
    html_lines.append('<html lang="zh-CN">')
    html_lines.append('<head>')
    html_lines.append('    <meta charset="UTF-8">')
    html_lines.append('    <meta name="viewport" content="width=device-width, initial-scale=1.0">')
    html_lines.append(f'    <title>{book_info.get("title", "读书笔记")} - v{version}</title>')
    html_lines.append('    <style>')
    html_lines.append('        :root { --primary: #3498db; --secondary: #2ecc71; --warning: #f39c12; --dark: #2c3e50; --light: #ecf0f1; }')
    html_lines.append('        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; line-height: 1.8; color: #333; background: #fafafa; }')
    html_lines.append('        h1 { color: var(--dark); border-bottom: 4px solid var(--primary); padding-bottom: 15px; margin-top: 40px; }')
    html_lines.append('        h2 { color: var(--dark); border-left: 5px solid var(--primary); padding-left: 15px; margin-top: 35px; }')
    html_lines.append('        h3 { color: #555; margin-top: 25px; }')
    html_lines.append('        h4 { color: #666; margin-top: 20px; }')
    html_lines.append('        blockquote { background: #fff; border-left: 5px solid var(--primary); padding: 15px 20px; margin: 15px 0; border-radius: 0 8px 8px 0; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }')
    html_lines.append('        .tag { display: inline-block; background: var(--primary); color: white; padding: 3px 12px; border-radius: 15px; font-size: 0.85em; margin-right: 5px; }')
    html_lines.append('        .meta { color: #888; font-size: 0.95em; margin-bottom: 30px; padding: 15px; background: white; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }')
    html_lines.append('        .card { background: white; padding: 25px; margin: 20px 0; border-radius: 10px; box-shadow: 0 3px 10px rgba(0,0,0,0.08); }')
    html_lines.append('        .concept { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; margin: 15px 0; }')
    html_lines.append('        .question { background: #fff3cd; padding: 15px; border-radius: 8px; margin: 10px 0; border-left: 4px solid var(--warning); }')
    html_lines.append('        .connection { background: #d4edda; padding: 15px; border-radius: 8px; margin: 10px 0; border-left: 4px solid var(--secondary); }')
    html_lines.append('        .label { font-weight: bold; color: var(--dark); margin-top: 15px; display: block; }')
    html_lines.append('        .divider { border: none; border-top: 2px dashed #ddd; margin: 30px 0; }')
    html_lines.append('        .chapter { background: var(--light); padding: 20px; border-radius: 10px; margin: 20px 0; }')
    html_lines.append('    </style>')
    html_lines.append('</head>')
    html_lines.append('<body>')
    
    # 标题
    html_lines.append(f'    <h1>{book_info.get("title", "未知书名")}</h1>')
    html_lines.append('    <div class="meta">')
    if book_info.get("author"):
        html_lines.append(f'        <strong>作者:</strong> {book_info["author"]} | ')
    if book_info.get("tags"):
        html_lines.append(f'        <strong>标签:</strong> {", ".join(book_info["tags"])} | ')
    html_lines.append(f'        <strong>摘录数量:</strong> {len(excerpts)} | ')
    html_lines.append(f'        <strong>版本:</strong> {version}')
    html_lines.append('    </div>')
    
    # 章节框架（v3.0）
    if include_framework and book_data.get("chapter_framework"):
        framework = book_data.get("chapter_framework", {})
        chapters_fw = framework.get("chapters", [])
        
        html_lines.append('    <div class="card">')
        html_lines.append('        <h2>章节框架</h2>')
        for chapter in chapters_fw:
            html_lines.append(f'        <div class="chapter">')
            html_lines.append(f'            <h3>{chapter.get("chapter_name", "未知章节")}</h3>')
            if chapter.get("summary"):
                html_lines.append(f'            <p><strong>摘要:</strong> {chapter["summary"]}</p>')
            if chapter.get("key_points"):
                html_lines.append(f'            <p><strong>关键要点:</strong></p>')
                html_lines.append(f'            <ul>')
                for point in chapter.get("key_points", []):
                    html_lines.append(f'                <li>{point}</li>')
                html_lines.append(f'            </ul>')
            html_lines.append(f'            <p><strong>摘录数量:</strong> {chapter.get("excerpt_count", 0)}</p>')
            html_lines.append(f'        </div>')
        html_lines.append('    </div>')
    
    # 知识结构（v3.0）
    if include_knowledge_structure:
        ks = book_data.get("knowledge_structure", {})
        
        # 概念索引
        concepts = ks.get("concept_index", {}).get("concepts", [])
        if concepts:
            html_lines.append('    <div class="card">')
            html_lines.append('        <h2>核心概念索引</h2>')
            for concept in concepts:
                html_lines.append(f'        <div class="concept">')
                html_lines.append(f'            <h3>{concept.get("name", "未知概念")}</h3>')
                if concept.get("definition"):
                    html_lines.append(f'            <p><strong>定义:</strong> {concept["definition"]}</p>')
                if concept.get("first_appearance"):
                    html_lines.append(f'            <p><strong>首次出现:</strong> {concept["first_appearance"]}</p>')
                if concept.get("occurrences"):
                    html_lines.append(f'            <p><strong>出现次数:</strong> {len(concept["occurrences"])}处</p>')
                html_lines.append(f'        </div>')
            html_lines.append('    </div>')
        
        # 概念联结
        connections = ks.get("concept_connections", {}).get("connections", [])
        if connections:
            html_lines.append('    <div class="card">')
            html_lines.append('        <h2>概念联结图</h2>')
            for conn in connections:
                html_lines.append(f'        <div class="connection">')
                html_lines.append(f'            <strong>{conn.get("from", "")}</strong> → <strong>{conn.get("to", "")}</strong>')
                if conn.get("relationship"):
                    html_lines.append(f'            <p>{conn["relationship"]}</p>')
                html_lines.append(f'        </div>')
            html_lines.append('    </div>')
        
        # 待思考问题
        questions = ks.get("questions", {})
        pending = questions.get("pending", [])
        answered = questions.get("answered", [])
        if pending or answered:
            html_lines.append('    <div class="card">')
            html_lines.append('        <h2>待思考问题</h2>')
            for q in pending:
                html_lines.append(f'        <div class="question">')
                html_lines.append(f'            <strong>❓ {q.get("question", "")}</strong>')
                html_lines.append(f'        </div>')
            for q in answered:
                html_lines.append(f'        <div>')
                html_lines.append(f'            <strong>✅ {q.get("question", "")}</strong>')
                html_lines.append(f'            <p><em>回答: {q.get("answer", "")}</em></p>')
                html_lines.append(f'        </div>')
            html_lines.append('    </div>')
    
    # 五维摘录卡片（v3.0）
    if include_analysis:
        chapters = {}
        for excerpt in excerpts:
            chapter_name = excerpt.get("chapter_name") or excerpt.get("chapter") or "未分类"
            if chapter_name not in chapters:
                chapters[chapter_name] = []
            chapters[chapter_name].append(excerpt)
        
        html_lines.append('    <div class="card">')
        html_lines.append('        <h2>五维摘录卡片</h2>')
        
        for chapter_name, chapter_excerpts in chapters.items():
            html_lines.append(f'        <div class="chapter">')
            html_lines.append(f'            <h3>{chapter_name}</h3>')
            
            for i, excerpt in enumerate(chapter_excerpts, 1):
                html_lines.append(f'            <div style="background: white; padding: 20px; margin: 15px 0; border-radius: 8px;">')
                html_lines.append(f'                <h4>摘录 {i}</h4>')
                html_lines.append(f'                <blockquote>{excerpt.get("content", "")}</blockquote>')
                
                tags = excerpt.get("tags", [])
                if tags:
                    html_lines.append(f'                <div>')
                    for tag in tags:
                        html_lines.append(f'                    <span class="tag">{tag}</span>')
                    html_lines.append(f'                </div>')
                
                if excerpt.get("deep_meaning"):
                    html_lines.append(f'                <span class="label">💡 深层含义:</span>')
                    html_lines.append(f'                <p>{excerpt["deep_meaning"]}</p>')
                
                if excerpt.get("application"):
                    html_lines.append(f'                <span class="label">🔧 应用:</span>')
                    html_lines.append(f'                <p>{excerpt["application"]}</p>')
                
                if excerpt.get("question"):
                    html_lines.append(f'                <span class="label">❓ 提问:</span>')
                    html_lines.append(f'                <p>{excerpt["question"]}</p>')
                
                html_lines.append(f'            </div>')
            
            html_lines.append(f'        </div>')
        html_lines.append('    </div>')
    
    html_lines.append('</body>')
    html_lines.append('</html>')
    
    return '\n'.join(html_lines)


def export_notes(
    book_name: str,
    format: str = "markdown",
    output_path: Optional[str] = None,
    include_framework: bool = True,
    include_analysis: bool = True,
    include_knowledge_structure: bool = True,
    base_path: str = "./reading-notes"
) -> Dict[str, any]:
    """
    导出笔记（v3.0）
    
    参数:
        book_name: 书籍名称
        format: 导出格式（markdown/html/pdf）
        output_path: 输出路径（可选）
        include_framework: 是否包含章节框架
        include_analysis: 是否包含五维卡片
        include_knowledge_structure: 是否包含知识结构
        base_path: 笔记存储路径
    
    返回:
        {
            "success": True/False,
            "output_path": "输出文件路径",
            "format": "格式",
            "excerpt_count": 摘录数量,
            "included": {
                "framework": True/False,
                "analysis": True/False,
                "knowledge_structure": True/False
            },
            "error": "错误信息（如果失败）"
        }
    """
    try:
        # 加载书籍档案
        book_file = os.path.join(base_path, "books", f"{book_name}.json")
        
        if not os.path.exists(book_file):
            return {
                "success": False,
                "error": f"书籍档案不存在: {book_name}"
            }
        
        with open(book_file, 'r', encoding='utf-8') as f:
            book_data = json.load(f)
        
        # 确定输出路径
        if not output_path:
            export_dir = os.path.join(base_path, "exports")
            if not os.path.exists(export_dir):
                os.makedirs(export_dir)
            
            ext = "md" if format == "markdown" else "html"
            suffix = ""
            if include_framework:
                suffix += "-框架"
            if include_knowledge_structure:
                suffix += "-知识"
            output_path = os.path.join(export_dir, f"{book_name}{suffix}.{ext}")
        
        # 导出
        if format == "markdown":
            content = export_to_markdown(book_data, include_framework, include_analysis, include_knowledge_structure)
        elif format == "html":
            content = export_to_html(book_data, include_framework, include_analysis, include_knowledge_structure)
        elif format == "pdf":
            # PDF 需要额外依赖，这里先生成 HTML
            content = export_to_html(book_data, include_framework, include_analysis, include_knowledge_structure)
            output_path = output_path.replace('.pdf', '.html')
        else:
            return {
                "success": False,
                "error": f"不支持的格式: {format}"
            }
        
        # 保存文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return {
            "success": True,
            "output_path": output_path,
            "format": format,
            "excerpt_count": len(book_data.get("excerpts", [])),
            "included": {
                "framework": include_framework,
                "analysis": include_analysis,
                "knowledge_structure": include_knowledge_structure
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"导出失败: {str(e)}"
        }


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='笔记导出工具（v3.0）')
    parser.add_argument('book_name', help='书籍名称')
    parser.add_argument('--format', '-f', choices=['markdown', 'html', 'pdf'],
                       default='markdown', help='导出格式')
    parser.add_argument('--output', '-o', help='输出路径')
    parser.add_argument('--no-framework', action='store_true', help='不包含章节框架')
    parser.add_argument('--no-analysis', action='store_true', help='不包含五维卡片')
    parser.add_argument('--no-knowledge', action='store_true', help='不包含知识结构')
    parser.add_argument('--base-path', default='./reading-notes', help='笔记存储路径')
    
    args = parser.parse_args()
    
    result = export_notes(
        book_name=args.book_name,
        format=args.format,
        output_path=args.output,
        include_framework=not args.no_framework,
        include_analysis=not args.no_analysis,
        include_knowledge_structure=not args.no_knowledge,
        base_path=args.base_path
    )
    
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
