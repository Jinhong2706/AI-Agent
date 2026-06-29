#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
extract_epub.py
从 EPUB 文件提取章节，返回 JSON 结构
用法: python extract_epub.py <epub_path> <output_json_path>
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import json
import os
import re

try:
    import ebooklib
    from ebooklib import epub
    from bs4 import BeautifulSoup
except ImportError:
    print("ERROR: 需要安装依赖: pip install ebooklib beautifulsoup4")
    sys.exit(1)


def extract_chapters(epub_path):
    """从 EPUB 提取章节列表"""
    book = epub.read_epub(epub_path)
    items = list(book.get_items_of_type(ebooklib.ITEM_DOCUMENT))

    chapters = []
    seen_titles = set()

    for item in items:
        name = item.get_name().lower()
        if 'cover' in name or 'toc' in name:
            continue

        soup = BeautifulSoup(item.content, 'html.parser')
        text = soup.get_text(separator='\n').strip()
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        real_lines = [l for l in lines if not re.match(r'^chapter\s+\d+\s*-\s*\d+\s*$', l, re.IGNORECASE)]

        if not real_lines:
            continue

        # 找章节标题
        title = None
        title_candidates = []
        for l in real_lines[:8]:
            if any(kw in l for kw in ['章', '序', '卷', '节', '篇', '集', '第']):
                # 清理标题：去掉前后空白和可能的标点
                t = l.strip().strip('，。、；：""''【】')
                if len(t) <= 30 and t not in seen_titles:
                    title_candidates.append(t)

        if title_candidates:
            title = title_candidates[0]
        else:
            title = real_lines[0][:30]

        seen_titles.add(title)
        chapters.append({
            'title': title,
            'content': real_lines
        })

    return chapters


def main():
    if len(sys.argv) < 3:
        print("用法: python extract_epub.py <epub_path> <output_json_path>")
        sys.exit(1)

    epub_path = sys.argv[1]
    output_path = sys.argv[2]

    if not os.path.exists(epub_path):
        print(f"错误: 文件不存在 {epub_path}")
        sys.exit(1)

    print(f"正在解析: {epub_path}")
    chapters = extract_chapters(epub_path)
    print(f"提取到 {len(chapters)} 章")

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(chapters, f, ensure_ascii=False, indent=2)

    print(f"已保存到: {output_path}")


if __name__ == '__main__':
    main()
