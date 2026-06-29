#!/usr/bin/env python3
"""
yaml_utils.py — Unified YAML & Frontmatter utilities for SCK
共享模块，消除 validate.py / quality-audit.py / platform.py / estimate-tokens.py
中重复的 YAML 解析器和 frontmatter 提取代码。

v1.1.0 — 新增内联数组解析（triggers: [xxx, yyy]） + _coerce_value 列表透传 + falsy 空列表修复
"""

import re
from pathlib import Path


# ═══════════════════════════════════════════════════════════
# YAML 子集解析器（零外部依赖，支持 3 层嵌套 + 数字类型转换）
# ═══════════════════════════════════════════════════════════

def _coerce_value(val):
    """将字符串值转换为 int/float 或保持字符串。列表直接透传（由 _convert_numbers_recursive 递归处理元素）。"""
    if isinstance(val, list):
        return val
    if not isinstance(val, str):
        return val
    try:
        return int(val)
    except (ValueError, TypeError):
        try:
            return float(val)
        except (ValueError, TypeError):
            return val


def parse_yaml_text(text: str) -> dict:
    """解析 YAML 文本字符串。
    
    支持：
    - 顶层 key: value（缩进 0）
    - 二层 section key（缩进 2）
    - 三层 section key（缩进 4，如 quality.xxx）
    - 同级列表项（缩进 2 的 - item）
    - 内联数组：key: [val1, val2, ...]（含空数组 []）
    - 数字值自动转换为 int/float
    - 注释行（# 开头）自动跳过
    - YAML 块标量：>（折叠）和 |（保留换行）
    
    合并自 platform.py _parse_platform_yaml 和 quality-audit.py _parse_simple_yaml。
    """
    result = {}
    current_section = None
    current_list = None
    # Block scalar state machine
    in_block_scalar = False
    block_scalar_key = None
    block_scalar_mode = None      # '>' or '|'
    block_scalar_indent = None    # base indent level of the block
    block_scalar_lines = []

    # ── Detect indent step from first indented non-comment line ──
    indent_step = 2
    for _line in text.split('\n'):
        _stripped = _line.strip()
        if _stripped and not _stripped.startswith('#'):
            _ind = len(_line) - len(_line.lstrip(' '))
            if _ind > 0:
                indent_step = _ind
                break

    for line in text.split('\n'):
        stripped = line.strip()

        # ── Block scalar: collecting indented lines ──
        if in_block_scalar:
            current_indent = len(line) - len(line.lstrip(' '))
            # Empty line or line at/above block indent → end of block
            if not stripped or current_indent < block_scalar_indent:
                content = ' '.join(block_scalar_lines) if block_scalar_mode == '>' else '\n'.join(block_scalar_lines)
                _store_block_scalar(result, block_scalar_key, current_section, current_list, content)
                in_block_scalar = False
                block_scalar_key = None
                block_scalar_mode = None
                block_scalar_lines = []
                # Fall through to process this line as normal
                if not stripped:
                    continue
            else:
                # Still collecting block scalar content
                if stripped:
                    block_scalar_lines.append(stripped)
                continue
        
        # ── Normal parsing ──
        if not stripped or stripped.startswith('#'):
            continue

        indent = len(line) - len(line.lstrip(' '))

        if stripped.endswith(':') and not stripped.startswith('-'):
            # Section key
            key = stripped.rstrip(':')
            if indent == 0:
                result[key] = {}
                current_section = key
                current_list = None
            elif indent == indent_step and current_section:
                result[current_section][key] = {}
                current_list = key
            elif indent == 2 * indent_step and current_section:
                result[current_section][key] = {}
                current_list = key
        elif stripped.startswith('- '):
            value = stripped[2:].strip().strip('"').strip("'")
            if current_list and current_section:
                section = result[current_section]
                if isinstance(section, dict):
                    if current_list not in section:
                        section[current_list] = []
                    elif not isinstance(section[current_list], list):
                        section[current_list] = []
                    section[current_list].append(value)
            elif current_section:
                # 顶层列表项
                section = result[current_section]
                if isinstance(section, dict):
                    if not isinstance(section.get('_items'), list):
                        section['_items'] = []
                    section['_items'].append(value)
        elif ':' in stripped and not stripped.startswith('-'):
            key, _, val = stripped.partition(':')
            key = key.strip()
            val_raw = val.strip()
            
            # Detect YAML block scalar indicators (> or |)
            if val_raw in ('>', '|'):
                in_block_scalar = True
                block_scalar_key = key
                block_scalar_mode = val_raw
                block_scalar_indent = indent + indent_step  # next indented block
                block_scalar_lines = []
                continue
            
            val = val_raw.strip('"').strip("'")

            # Inline array: triggers: [对抗性严谨, 构造反例]
            if isinstance(val, str) and val.startswith('[') and val.endswith(']'):
                inner = val[1:-1].strip()
                if inner:
                    val = [v.strip().strip('"').strip("'") for v in inner.split(',') if v.strip()]
                else:
                    val = []

            # indent 0 key with value → reset section state, store at top level
            if indent == 0:
                current_section = None
                current_list = None
                result[key] = _coerce_value(val) if (val or isinstance(val, list)) else {}
            elif current_list and current_section:
                section = result[current_section]
                if isinstance(section, dict):
                    if current_list in section and isinstance(section[current_list], dict):
                        section[current_list][key] = _coerce_value(val)
                    else:
                        section[key] = _coerce_value(val)
            elif current_section and isinstance(result.get(current_section), dict):
                result[current_section][key] = _coerce_value(val)
            elif indent == 0:
                result[key] = _coerce_value(val) if (val or isinstance(val, list)) else {}

    # End-of-file: flush any open block scalar
    if in_block_scalar:
        content = ' '.join(block_scalar_lines) if block_scalar_mode == '>' else '\n'.join(block_scalar_lines)
        _store_block_scalar(result, block_scalar_key, current_section, current_list, content)

    # 递归转换所有剩余字符串值为数字
    return _convert_numbers_recursive(result)


def _store_block_scalar(result, key, current_section, current_list, content):
    """Store a block scalar value into the result dict at the correct nesting level."""
    if current_list and current_section:
        section = result[current_section]
        if isinstance(section, dict):
            if current_list in section and isinstance(section[current_list], dict):
                section[current_list][key] = content
            else:
                section[key] = content
    elif current_section and isinstance(result.get(current_section), dict):
        result[current_section][key] = content
    else:
        result[key] = content


def _convert_numbers_recursive(d):
    """递归转换字符串值为 int/float"""
    if isinstance(d, dict):
        return {k: _convert_numbers_recursive(v) for k, v in d.items()}
    if isinstance(d, list):
        return [_convert_numbers_recursive(v) for v in d]
    if isinstance(d, str):
        return _coerce_value(d)
    return d


def parse_yaml_file(filepath: Path) -> dict:
    """解析 YAML 文件"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return parse_yaml_text(f.read())


# ═══════════════════════════════════════════════════════════
# Frontmatter 提取（SKILL.md 的 YAML 头部）
# ═══════════════════════════════════════════════════════════

_FM_RE = re.compile(r'^---\s*\r?\n(.*?)\r?\n---', re.DOTALL)


def extract_frontmatter_raw(filepath: Path) -> str:
    """提取 SKILL.md 的 YAML frontmatter 原始字符串。
    
    不存在或格式不匹配时返回空字符串。
    合并自 quality-audit.py 和 platform.py 的 _extract_frontmatter。
    """
    if not filepath.exists():
        return ""
    content = filepath.read_text(encoding='utf-8')
    m = _FM_RE.match(content)
    return m.group(1) if m else ""


def extract_frontmatter(filepath: Path) -> tuple:
    """提取并解析 SKILL.md 的 YAML frontmatter。
    
    Returns:
        (raw_str, parsed_dict) — raw 是原始 YAML 字符串，parsed 是解析后的 dict。
        不存在时返回 ("", {})。
        
    合并自 validate.py _extract_frontmatter_blocks 和 estimate-tokens.py extract_frontmatter。
    v1.1.0: 使用 parse_yaml_text 统一解析，支持嵌套结构和块标量。
    """
    raw = extract_frontmatter_raw(filepath)
    if not raw:
        return ("", {})

    # 使用统一的 parse_yaml_text 解析器（支持嵌套 YAML、块标量 >/|）
    parsed = parse_yaml_text(raw)
    
    # 处理 triggers: 如果被解析为 {_items: [...]}，提取为 list
    if isinstance(parsed.get('triggers'), dict) and '_items' in parsed['triggers']:
        parsed['triggers'] = parsed['triggers']['_items']
    
    return (raw, parsed)
