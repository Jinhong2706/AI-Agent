# -*- coding: utf-8 -*-
"""
记忆管家 V3.0 - 摘要生成模块
来源: memory_manager.py (summary)
V3.0: 模块化重构
"""

import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path

from .config import (
    VERSION, _, SUMMARY_DIR,
    SUMMARY_MAX_CHARS, SUMMARY_MIN_CHARS, TOKEN_RATIO,
    SUMMARY_SCHEMA_VERSION,
    is_symlink, safe_file_read, get_file_info,
)


def extract_keywords(content, max_keywords=5):
    stopwords = {
        '的', '了', '是', '在', '和', '与', '或', '等', '于', '对',
        '这', '那', '有', '我', '你', '他', '她', '它', '们',
        '一个', '我们', '他们', '这个', '什么', '如何', '怎么',
        '可以', '需要', '如果', '因为', '所以', '但是', '而且',
        '或者', '以及', '对于', '关于', '通过', '使用', '进行',
        '实现', '完成', '开始', '结束', '之后', '之前', '时候',
        '情况', '问题', '方法', '内容', '文件', '功能', '支持',
    }

    try:
        import jieba
        words = list(jieba.cut(content.lower()))
        words = [w.strip() for w in words if len(w.strip()) > 1 and w.strip() not in stopwords]
    except (ImportError, Exception):
        words = re.findall(r'[\w]{2,}', content.lower())
        words = [w for w in words if w not in stopwords and len(w) > 1]

    counter = Counter(words)
    return [w for w, _ in counter.most_common(max_keywords)]


def smart_truncate(text, max_chars=SUMMARY_MAX_CHARS):
    if len(text) <= max_chars:
        return text

    sentence_ends = ['。', '！', '？', '.', '!', '?']
    search_start = int(max_chars * 0.7)
    search_text = text[search_start:max_chars]

    for end_char in sentence_ends:
        pos = search_text.rfind(end_char)
        if pos != -1:
            actual_pos = search_start + pos + len(end_char)
            return text[:actual_pos] + "..."

    last_newline = text.rfind('\n', search_start, max_chars)
    if last_newline > search_start:
        return text[:last_newline] + "\n..."

    last_space = text.rfind(' ', search_start, max_chars)
    if last_space > search_start:
        return text[:last_space] + "..."

    return text[:max_chars] + "..."


def generate_summary(content, max_chars=SUMMARY_MAX_CHARS):
    if len(content) <= SUMMARY_MIN_CHARS:
        return content[:max_chars] if len(content) > max_chars else content

    lines = content.split('\n')
    summary_parts = []

    headers = [l.strip() for l in lines if l.strip().startswith('#') and len(l) < 100]
    if headers:
        summary_parts.extend(headers[:3])

    bullets = [l.strip().lstrip('-*').strip() for l in lines
               if l.strip().startswith(('-', '*')) and len(l) > 5]
    if bullets:
        summary_parts.extend(bullets[:5])

    summary = '\n'.join(summary_parts)
    if len(summary) < 100 and lines:
        for l in lines:
            if l.strip() and not l.strip().startswith('#'):
                para = l.strip()
                if len(summary) < max_chars:
                    summary += '\n' + para

    if len(summary) > max_chars:
        summary = smart_truncate(summary, max_chars)

    return summary.strip()


def _iter_memory_files(memory_path):
    """公共迭代器：遍历记忆目录下的 .md 文件，跳过符号链接"""
    if not memory_path.exists():
        return
    for md_file in memory_path.glob("*.md"):
        if is_symlink(md_file):
            continue
        yield md_file


def summarize_memory(workspace_path, file_name=None, regenerate=False):
    base_path = Path(workspace_path).resolve()
    memory_path = base_path / ".workbuddy" / "memory"
    summary_path = base_path / ".workbuddy" / SUMMARY_DIR

    summary_path.mkdir(parents=True, exist_ok=True)

    result = {
        "version": VERSION,
        "timestamp": datetime.now().isoformat(),
        "summarized": [],
        "skipped": [],
        "errors": []
    }

    if not memory_path.exists():
        result["error"] = _("memory_dir_not_exist")
        return result

    def process_file(md_file):
        if is_symlink(md_file):
            return None

        summary_file = summary_path / f"{md_file.stem}.summary"

        if summary_file.exists() and not regenerate:
            try:
                with open(summary_file, 'r', encoding='utf-8') as f:
                    return json.loads(f.read())
            except (json.JSONDecodeError, OSError, IOError):
                pass

        content, status = safe_file_read(md_file)
        if content is None:
            return None

        summary = generate_summary(content)
        keywords = extract_keywords(content)

        mtime, size_kb = get_file_info(md_file)

        summary_data = {
            "schema_version": SUMMARY_SCHEMA_VERSION,
            "file": md_file.name,
            "summary": summary,
            "keywords": keywords,
            "size_kb": size_kb,
            "modified": mtime.strftime("%Y-%m-%d") if mtime else "unknown",
            "generated": datetime.now().isoformat(),
            "token_estimate": len(summary) // TOKEN_RATIO
        }

        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, ensure_ascii=False, indent=2)

        return summary_data

    if file_name:
        md_file = memory_path / file_name
        if not md_file.exists():
            result["error"] = f"文件不存在: {file_name}"
            return result
        data = process_file(md_file)
        if data:
            result["summarized"].append(data)
        else:
            result["errors"].append(f"处理失败: {file_name}")
    else:
        for md_file in _iter_memory_files(memory_path):
            data = process_file(md_file)
            if data:
                result["summarized"].append(data)
            else:
                result["skipped"].append(md_file.name)

    return result
