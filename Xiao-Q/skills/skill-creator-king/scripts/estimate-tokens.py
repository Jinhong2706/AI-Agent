#!/usr/bin/env python3
"""
estimate-tokens.py — 字符计数法 Token 估算器
不依赖 tiktoken，基于字符类型加权估算，适用于任何 LLM 的粗略预算。

用法：python3 scripts/estimate-tokens.py <文件或目录> [--detail]
输出：L0 / L1 / L2 / 总计 四级分布
"""

import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR.parent))
from scripts.yaml_utils import extract_frontmatter


def count_chars(text: str) -> dict:
    """统计文本中各类字符的数量"""
    chinese = len(re.findall(r'[\u4e00-\u9fff\u3400-\u4dbf]', text))
    english = len(re.findall(r'[a-zA-Z]', text))
    other = len(text) - chinese - english
    return {"chinese": chinese, "english": english, "other": other}


def estimate_tokens(text: str, chinese_ratio=0.67, english_ratio=0.25) -> int:
    """字符计数法估算 Token 数

    中文约 0.67 tokens/字（1.5 汉字 ≈ 1 token），英文约 0.25 tokens/字符。
    注意：这是粗略估算，实际 token 数因 tokenizer 而异。
    """
    counts = count_chars(text)
    tokens = int(counts["chinese"] * chinese_ratio + counts["english"] * english_ratio + counts["other"] * 0.1)
    return max(tokens, 0)


def estimate_file(filepath: Path, chinese_ratio=0.67, english_ratio=0.25) -> int:
    """估算单个文件的 Token 数"""
    try:
        content = filepath.read_text(encoding='utf-8', errors='replace')
    except (OSError, UnicodeDecodeError):
        return 0
    return estimate_tokens(content, chinese_ratio, english_ratio)


# extract_frontmatter 已迁移至 yaml_utils.extract_frontmatter


def estimate_skill(skill_dir: Path, detail=False) -> dict:
    """估算 skill 的四级 Token 分布"""
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return {"error": "SKILL.md 不存在"}

    content = skill_md.read_text(encoding='utf-8', errors='replace')
    fm_end = content.find('---', 3)
    fm_text = content[3:fm_end] if fm_end > 0 else ""
    body_text = content[fm_end + 4:] if fm_end > 0 else content

    fm_tokens = estimate_tokens(fm_text)
    body_tokens = estimate_tokens(body_text)

    # L2: references/ + data/ + rules/ 目录
    l2_tokens = 0
    l2_files = []
    for subdir in ['references', 'data', 'rules']:
        d = skill_dir / subdir
        if d.exists():
            for f in sorted(d.rglob('*')):
                if f.is_file() and 'cache' not in f.parts and f.name != '.DS_Store' and f.suffix != '.jsonl':
                    t = estimate_file(f)
                    l2_tokens += t
                    l2_files.append({"path": str(f.relative_to(skill_dir)), "tokens": t})

    total = fm_tokens + body_tokens + l2_tokens

    fm = extract_frontmatter(skill_md)[1]  # (raw_str, parsed_dict)
    budget = {
        "L0_trigger": fm.get("L0_trigger", "未定义"),
        "L1_core": fm.get("L1_core", "未定义"),
        "L2_deep": fm.get("L2_deep", "未定义"),
        "hard_cap": fm.get("hard_cap", "未定义"),
    }

    result = {
        "skill": skill_dir.name,
        "token_budget": budget,
        "L0_trigger": fm_tokens,
        "L1_core": body_tokens,
        "L2_deep": l2_tokens,
        "总计": total,
    }
    if detail:
        result["L2_files"] = l2_files

    return result


def main():
    if len(sys.argv) < 2:
        print("用法: python3 scripts/estimate-tokens.py <文件或目录> [--detail]")
        sys.exit(1)

    target = Path(sys.argv[1]).expanduser().resolve()
    detail = '--detail' in sys.argv

    if not target.exists():
        print(f"错误: 路径不存在: {target}")
        sys.exit(1)

    if target.is_file():
        tokens = estimate_file(target)
        print(f"{target.name}: {tokens} tokens")
    else:
        result = estimate_skill(target, detail=detail)
        if "error" in result:
            print(f"错误: {result['error']}")
            sys.exit(1)

        print(f"Skill: {result['skill']}")
        print(f"Token 预算声明: L0_trigger={result['token_budget']['L0_trigger']}, "
              f"L1_core={result['token_budget']['L1_core']}, "
              f"L2_deep={result['token_budget']['L2_deep']}, "
              f"hard_cap={result['token_budget']['hard_cap']}")
        print(f"L0 (frontmatter): {result['L0_trigger']}")
        print(f"L1 (body):        {result['L1_core']}")
        print(f"L2 (references):  {result['L2_deep']}")
        print(f"总计:              {result['总计']}")

        if detail:
            print("\nL2 文件明细:")
            for f in result.get("L2_files", []):
                print(f"  {f['path']}: {f['tokens']}")


if __name__ == '__main__':
    main()
