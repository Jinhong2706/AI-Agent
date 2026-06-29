#!/usr/bin/env python3
"""
第2步：将演讲稿处理为结构化字幕数据。

功能说明：
1. 读取 Markdown 格式的演讲稿
2. 清洗特殊字符和格式标记
3. 按页拆分为带句子的片段
4. 输出用于 TTS 和字幕生成的 JSON 结构

使用方法：
    python step2_process_speech.py --input <演讲稿.md> --output <输出.json>

输出 JSON 格式：
{
    "slides": [
        {
            "slide_number": 1,
            "title": "幻灯片标题",
            "sentences": [
                "原始文本（用于字幕显示）",
                ...
            ],
            "tts_sentences": [
                "发音优化后的文本（用于TTS合成）",
                ...
            ],
            "full_text": "所有句子拼接。"
        },
        ...
    ]
}
"""

import argparse
import json
import os
import re
import sys


def read_speech_file(filepath: str) -> str:
    """Read the speech markdown file."""
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


def _load_pronunciation_map() -> list:
    """
    Load pronunciation mapping rules from config/pronunciation_map.json.
    Falls back to an empty list if the file is missing or malformed.
    """
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "config", "pronunciation_map.json"
    )
    if not os.path.isfile(config_path):
        print(f"[WARN] pronunciation_map.json not found: {config_path}")
        return []
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        rules = []
        for entry in data.get("rules", []):
            pat = entry.get("pattern", "")
            rep = entry.get("replacement", "")
            if pat:
                if "\\." in pat:
                    # Pattern contains literal dot (e.g., file extensions)
                    # Use \b at start, but not at end (dot breaks \b)
                    rules.append((rf'\b{pat}(?!\w)', rep))
                else:
                    # Wrap with word boundaries automatically
                    rules.append((rf'\b{pat}\b', rep))
        return rules
    except Exception as e:
        print(f"[WARN] Failed to load pronunciation_map.json: {e}")
        return []


# Module-level cache — loaded once per process
_PRONUNCIATION_MAP = None


def _normalize_paths(text: str) -> str:
    """
    Convert directory/file paths to TTS-friendly pronunciation.

    Rules:
    - ~/  prefix → "家目录下"
    - Leading dot in directory names (e.g. .codebuddy) → stripped
    - Path segments joined by spaces
    - Trailing / → append "目录"
    - File extensions (e.g. api.md) → "api点md"

    Examples:
    - ~/.codebuddy/skills/  → "家目录下 codebuddy skills 目录"
    - .codebuddy/skills/    → "codebuddy skills 目录"
    - references/api.md     → "references api点md"
    - ./config/             → "当前目录下 config 目录"
    """
    # Valid path characters (excluding /)
    _PATH_CHARS = set('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_.-')

    result = []
    i = 0
    n = len(text)

    while i < n:
        # Try to detect a path starting here
        # A path can start with ~/, ./, or a path-char followed eventually by /
        start = i
        prefix = ''

        # Check for ~/ or ./ prefix
        if i < n and text[i] == '~':
            if i + 1 < n and text[i + 1] == '/':
                prefix = '~/'
                i += 2
            else:
                result.append(text[i])
                i += 1
                continue
        elif i < n and text[i] == '.' and i + 1 < n and text[i + 1] == '/':
            # ./ prefix — but only if not preceded by a word char
            if start > 0 and text[start - 1].isalnum():
                result.append(text[i])
                i += 1
                continue
            prefix = './'
            i += 2

        # Now try to read path segments: name/name/name or name/name
        segments = []
        seg_start = i
        found_slash = False

        while i < n and (text[i] in _PATH_CHARS or text[i] == '/'):
            if text[i] == '/':
                seg = text[seg_start:i]
                if seg:
                    segments.append(seg)
                found_slash = True
                i += 1
                seg_start = i
                # Allow trailing slash (empty segment after last /)
            else:
                i += 1

        # Collect any remaining segment after last /
        trailing_seg = text[seg_start:i]
        is_dir = (not trailing_seg and found_slash)
        if trailing_seg:
            segments.append(trailing_seg)

        # Must have at least one / to be a path
        if not found_slash and not prefix:
            # Not a path, output original chars
            result.append(text[start:i] if i > start else text[start])
            if i == start:
                i += 1
            continue

        # If no segments found (e.g. just ~/ alone), skip
        if not segments and not prefix:
            result.append(text[start:i])
            continue

        # Verify it's not preceded by a word char (for non-prefix paths)
        if not prefix and start > 0 and (text[start - 1].isalnum() or text[start - 1] == '_'):
            result.append(text[start:i])
            continue

        # Build spoken form
        parts = []

        if prefix == '~/':
            parts.append('家目录下')
        elif prefix == './':
            parts.append('当前目录下')

        for idx, seg in enumerate(segments):
            clean_seg = seg.lstrip('.')
            if not clean_seg:
                continue
            # Handle file extension for the last segment (only if not a dir)
            if not is_dir and idx == len(segments) - 1 and '.' in clean_seg:
                name, ext = clean_seg.rsplit('.', 1)
                if name and ext and ext.isalnum():
                    parts.append(f'{name}点{ext}')
                    continue
            parts.append(clean_seg)

        if is_dir:
            # Check what follows to avoid duplicate "目录"
            following = text[i:i + 5].lstrip()
            if not following.startswith(('目录', '下')):
                parts.append('目录')

        if parts:
            result.append(' '.join(parts))
        else:
            result.append(text[start:i])

    return ''.join(result)


def normalize_pronunciation(text: str) -> str:
    """
    Replace technical terms that TTS engines tend to spell out
    letter-by-letter with phonetically-friendly alternatives.

    Processing order:
    1. Path normalization (directory/file paths → spoken form)
    2. Term replacement from config/pronunciation_map.json

    This runs AFTER markdown cleanup and BEFORE sentence splitting,
    so it only affects audio generation — the original manuscript
    is untouched.
    """
    global _PRONUNCIATION_MAP
    if _PRONUNCIATION_MAP is None:
        _PRONUNCIATION_MAP = _load_pronunciation_map()

    # Step 1: Normalize directory/file paths
    text = _normalize_paths(text)

    # Step 2: Apply term-level pronunciation rules
    for pattern, replacement in _PRONUNCIATION_MAP:
        text = re.sub(pattern, replacement, text,
                      flags=re.IGNORECASE)

    return text


def clean_text(text: str) -> str:
    """
    Clean special characters from speech text.
    - Remove markdown bold/italic markers
    - Remove blockquotes
    - Remove time annotations like (约 1 分钟)
    - Remove markdown links but keep text
    - Clean up excessive whitespace
    - Keep actual punctuation for natural speech
    """
    # Remove time/duration annotations like **（约 1 分钟）** or （约 30 秒）
    text = re.sub(r'[*]*（[^）]*(?:分钟|秒|min|sec)[^）]*）[*]*', '', text)

    # Remove meta info like *总时长：约 5 分钟*
    text = re.sub(r'[*]*总时长[：:].*$', '', text, flags=re.MULTILINE)

    # Remove markdown bold markers **text** -> text
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)

    # Remove markdown italic markers *text* -> text
    text = re.sub(r'\*([^*]+)\*', r'\1', text)

    # Remove markdown links [text](url) -> text
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)

    # Remove inline code backticks
    text = re.sub(r'`([^`]+)`', r'\1', text)

    # Remove blockquote markers
    text = re.sub(r'^>\s*', '', text, flags=re.MULTILINE)

    # Remove horizontal rules
    text = re.sub(r'^---+\s*$', '', text, flags=re.MULTILINE)

    # Remove heading markers but keep text
    text = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)

    # Clean up em-dashes and special dashes
    text = text.replace('——', '，')
    text = text.replace('—', '，')

    # Clean up multiple newlines to single space (speech is continuous)
    text = re.sub(r'\n+', ' ', text)
    text = re.sub(r'[ \t]+', ' ', text)

    return text.strip()


def _detect_english_segment(text: str, pos: int) -> bool:
    """
    Detect whether a comma at position `pos` is inside an English segment.

    Heuristic: look at the surrounding context (up to 30 chars before and after
    the comma). If the majority of alphabetic characters around it are ASCII
    letters, it's likely inside an English phrase/sentence and should NOT be
    used as a split point.
    """
    window = 30
    start = max(0, pos - window)
    end = min(len(text), pos + window + 1)
    context = text[start:end]

    ascii_alpha = sum(1 for c in context if c.isascii() and c.isalpha())
    cjk = sum(1 for c in context if '\u4e00' <= c <= '\u9fff')

    # If ASCII letters dominate (at least 3x more than CJK), treat as English
    return ascii_alpha > 0 and ascii_alpha >= cjk * 3


def split_into_sentences(text: str) -> list:
    """
    Split text into natural sentences for TTS.
    Split on Chinese/English sentence-ending punctuation.
    Avoid splitting at:
    - Decimal points (e.g., 1.5, 3.0, 0.02)
    - File extensions (e.g., activator.sh, CLAUDE.md, config.yaml)
    - Domain names / URLs (e.g., github.com)
    - Punctuation inside quotation marks (e.g., "引导够详细吗？")
    - English commas inside English segments (e.g., "Extract text, fill forms, merge docs")
    """
    # ── Step 0: Protect quoted content ──
    # Temporarily replace content inside quotation marks with placeholders
    # so that punctuation inside quotes is NOT treated as sentence boundaries.
    # Supports: "…" "…" \"…\"
    quoted_chunks = []

    def _protect_quote(m):
        idx = len(quoted_chunks)
        quoted_chunks.append(m.group(0))
        return f'\x00QUOTE{idx}\x00'

    # Match Chinese quotes "…", English smart quotes \u201c…\u201d, and escaped straight quotes \"…\"
    protected = re.sub(
        r'(?:'
        r'\u201c[^\u201d]*\u201d'    # Chinese "…"
        r'|'
        r'\u300c[^\u300d]*\u300d'    # Japanese-style 「…」
        r'|'
        r'"[^"]*"'                   # English curly "…"
        r'|'
        r'(?<=\\)"[^"]*(?:\\")'      # escaped \"…\"
        r'|'
        r'"[^"]*"'                   # plain straight "…"
        r')',
        _protect_quote,
        text,
    )

    # ── Step 1: Split on sentence-ending punctuation ──
    # For English period '.':
    #   - NOT preceded by a digit (avoid decimals like 1.5)
    #   - NOT followed by a digit (avoid decimals like .5)
    #   - NOT preceded by a word char AND followed by a word char (avoid file.ext, domain.com)
    sentences = re.split(
        r'(?<=[。！？；\!\?\;])\s*|(?<=\.)(?<!\d\.)(?!\d)(?<!\w\.)(?!\w)\s*',
        protected
    )

    # ── Step 2: Split long sentences on Chinese commas only ──
    # English commas inside English segments are preserved to keep English
    # phrases/sentences intact (e.g., "Extract text, fill forms, merge docs").
    result = []
    for sent in sentences:
        sent = sent.strip()
        if not sent:
            continue

        # If sentence is very long (>80 chars), try splitting on commas
        if len(sent) > 80:
            # Find all comma positions and decide which are valid split points
            # Only split on Chinese commas (，) or English commas (,) that are
            # NOT inside an English segment.
            split_positions = []
            for m in re.finditer(r'[，,]', sent):
                ch = m.group()
                pos = m.start()
                if ch == '，':
                    # Chinese comma: always a valid split point
                    split_positions.append(pos)
                else:
                    # English comma: only split if NOT in English context
                    if not _detect_english_segment(sent, pos):
                        split_positions.append(pos)

            if split_positions:
                # Build chunks by splitting at valid positions
                parts = []
                prev = 0
                for sp in split_positions:
                    # Include the comma in the preceding part
                    parts.append(sent[prev:sp + 1])
                    prev = sp + 1
                # Remaining tail
                if prev < len(sent):
                    parts.append(sent[prev:])

                current = ""
                for part in parts:
                    if len(current) + len(part) > 60 and current:
                        result.append(current.strip())
                        current = part
                    else:
                        current += part
                if current.strip():
                    result.append(current.strip())
            else:
                result.append(sent)
        else:
            result.append(sent)

    # ── Step 3: Restore quoted content ──
    restored = []
    for sent in result:
        for idx, chunk in enumerate(quoted_chunks):
            sent = sent.replace(f'\x00QUOTE{idx}\x00', chunk)
        restored.append(sent)
    result = restored

    # ── Step 4: Merge orphaned quote fragments ──
    # If a fragment starts with a closing quote or is just quote + punctuation
    # (e.g. '"；' or '" 匹配'), merge it back into the previous sentence.
    merged = []
    for sent in result:
        stripped = sent.strip()
        if not stripped or len(stripped) <= 1:
            continue
        # Detect orphaned fragment: starts with a quote mark and is very short,
        # or consists of only quote + punctuation
        is_orphan = False
        if merged:
            # Starts with closing quote char (straight ", curly ", \")
            if stripped[0] in '"\u201d\u300d':
                is_orphan = True
            # Or is just punctuation like "；" or "。"
            elif len(stripped) <= 3 and all(
                c in '"\u201c\u201d\u300c\u300d""\\"；;。.！!？? \t'
                for c in stripped
            ):
                is_orphan = True
        if is_orphan and merged:
            merged[-1] = merged[-1] + stripped
        else:
            merged.append(sent)

    # Filter out empty or whitespace-only entries
    merged = [s for s in merged if s.strip() and len(s.strip()) > 1]

    return merged


def parse_slides(content: str) -> list:
    """
    Parse the speech markdown into slide segments.
    Detects slide boundaries by ## headings with slide numbers.

    Each slide contains:
    - sentences: original text (used for subtitles)
    - tts_sentences: pronunciation-normalized text (used for TTS)
    """
    slides = []

    # Split by slide headings (## 第 X 页 or ## Slide X patterns)
    slide_pattern = r'##\s*第\s*(\d+)\s*页[·\s]*(.+?)$'
    parts = re.split(slide_pattern, content, flags=re.MULTILINE)

    if len(parts) < 4:
        # Try alternative pattern: just ## headings
        slide_pattern = r'##\s+(.+?)$'
        sections = re.split(slide_pattern, content, flags=re.MULTILINE)

        # Pair up: sections[0] is preamble, then alternating title/content
        slide_num = 0
        for i in range(1, len(sections), 2):
            slide_num += 1
            title = sections[i].strip()
            body = sections[i + 1] if i + 1 < len(sections) else ""
            cleaned = clean_text(body)
            sentences = split_into_sentences(cleaned)
            if sentences:
                # Generate TTS-friendly versions
                tts_sentences = [
                    normalize_pronunciation(s) for s in sentences
                ]
                slides.append({
                    "slide_number": slide_num,
                    "title": clean_text(title),
                    "sentences": sentences,
                    "tts_sentences": tts_sentences,
                    "full_text": " ".join(sentences)
                })
    else:
        # parts[0] is preamble, then groups of (slide_num, title, content)
        for i in range(1, len(parts), 3):
            slide_num = int(parts[i])
            title = parts[i + 1].strip() if i + 1 < len(parts) else ""
            body = parts[i + 2] if i + 2 < len(parts) else ""

            cleaned = clean_text(body)
            sentences = split_into_sentences(cleaned)

            if sentences:
                # Generate TTS-friendly versions
                tts_sentences = [
                    normalize_pronunciation(s) for s in sentences
                ]
                slides.append({
                    "slide_number": slide_num,
                    "title": clean_text(title),
                    "sentences": sentences,
                    "tts_sentences": tts_sentences,
                    "full_text": " ".join(sentences)
                })

    return slides


def main():
    parser = argparse.ArgumentParser(description="Process speech manuscript into structured data")
    parser.add_argument("--input", required=True, help="Path to speech markdown file")
    parser.add_argument("--output", required=True, help="Output JSON path")
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"[ERROR] Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    content = read_speech_file(args.input)
    slides = parse_slides(content)

    if not slides:
        print("[ERROR] No slides found in the speech file.", file=sys.stderr)
        sys.exit(1)

    output_data = {"slides": slides}

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    # Print summary
    total_sentences = sum(len(s["sentences"]) for s in slides)
    total_chars = sum(len(s["full_text"]) for s in slides)
    print(f"\n[Step 2 DONE] Speech processed successfully.")
    print(f"  Total slides: {len(slides)}")
    print(f"  Total sentences: {total_sentences}")
    print(f"  Total characters: {total_chars}")
    print(f"  Output: {args.output}")

    for slide in slides:
        print(f"\n  Slide {slide['slide_number']}: {slide['title']}")
        print(f"    Sentences: {len(slide['sentences'])}")
        print(f"    Characters: {len(slide['full_text'])}")

    return output_data


if __name__ == "__main__":
    main()
