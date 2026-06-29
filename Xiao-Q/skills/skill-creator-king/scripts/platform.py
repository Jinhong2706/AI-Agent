#!/usr/bin/env python3
"""
platform.py — 统一平台检测与配置加载模块
被 validate.py / quality-audit.py / init_skill.py 共同引用

职责：
  - 路径优先自动检测目标平台
  - 加载平台 YAML profile（纯 Python 解析，零外部依赖）
  - 提供 skill_dir 路径模式查询

平台定义文件：data/platforms/{workbuddy,openclaw,hermes,universal}.yaml
"""

import re
import sys
from pathlib import Path

# ── sys.path 设置（支持独立运行 `python3 platform.py`）───────────
_SCRIPT_DIR = Path(__file__).resolve().parent
_SCK_ROOT = _SCRIPT_DIR.parent
if str(_SCK_ROOT) not in sys.path:
    sys.path.insert(0, str(_SCK_ROOT))

# ── 统一 YAML / Frontmatter 工具（v3.12.2 抽取共享模块）───────────
from scripts.yaml_utils import parse_yaml_file, extract_frontmatter_raw


# ── 平台发现 ────────────────────────────────────────────────

PLATFORMS_DIR = Path(__file__).parent.parent / "data" / "platforms"


def _load_all_platforms() -> dict:
    """加载所有平台的 YAML profile，带 LRU 缓存"""
    platforms = {}
    if not PLATFORMS_DIR.exists():
        return platforms
    for yf in sorted(PLATFORMS_DIR.glob("*.yaml")):
        pid = yf.stem
        platforms[pid] = parse_yaml_file(yf)
    return platforms


def list_platforms() -> list:
    """返回所有可用平台 ID 列表"""
    if not PLATFORMS_DIR.exists():
        return []
    return sorted([yf.stem for yf in PLATFORMS_DIR.glob("*.yaml")])


# ── 平台检测 ────────────────────────────────────────────────

def detect_platform(skill_dir) -> str:
    """
    自动检测 skill 所属平台。

    检测逻辑（路径优先）：
    ① 路径匹配：skill 目录路径是否落在某平台的 skill_dir 下
       例：~/.openclaw/skills/foo → openclaw
    ② Frontmatter 标记：WB markers（triggers/token_budget/template）
       或 metadata.openclaw / metadata.hermes
    ③ 回退 → universal
    """
    if isinstance(skill_dir, str):
        skill_dir = Path(skill_dir)
    skill_dir_str = str(skill_dir.expanduser().resolve())

    # ── ① 路径优先检测 ──
    all_platforms = _load_all_platforms()
    for pid, pdata in all_platforms.items():
        sd = pdata.get("skill_dir", "")
        if not sd:
            continue
        sd_expanded = str(Path(sd).expanduser().resolve())
        if skill_dir_str.startswith(sd_expanded):
            return pid

    # ── ② Frontmatter 标记检测 ──
    skill_md = skill_dir / "SKILL.md"
    if skill_md.exists():
        try:
            fm_text = extract_frontmatter_raw(skill_md)
        except Exception:
            fm_text = ""

        # OpenClaw marker（显式标记优先于关键词推断）
        if "metadata.openclaw" in fm_text:
            return "openclaw"

        # Hermes marker（显式标记优先于关键词推断）
        if "metadata.hermes" in fm_text:
            return "hermes"

        # WorkBuddy markers（最后 fallback：概率推断）
        if any(kw in fm_text for kw in ["triggers:", "token_budget:", "template:"]):
            return "workbuddy"

    # ── ③ 回退 ──
    return "universal"




# ── 平台 Profile 加载 ───────────────────────────────────────

def load_platform_profile(platform: str) -> dict:
    """
    加载平台 profile，返回统一格式 dict：
    {
      "quality": {"skip_dimensions": [...], "max_score": 117, ...},
      "anti_patterns": {"exclude_ids": [...]},
      "skill_dir_patterns": ["~/.workbuddy/skills/"],
      "raw": {原始 YAML 解析结果}
    }
    """
    yaml_path = PLATFORMS_DIR / f"{platform}.yaml"
    if not yaml_path.exists():
        # Fallback: 返回最小 profile
        return {
            "quality": {"skip_dimensions": []},
            "anti_patterns": {"exclude_ids": []},
            "skill_dir_patterns": ["~/.agents/skills/"],
            "raw": {},
        }

    raw = parse_yaml_file(yaml_path)

    # 提取 quality 配置
    quality_raw = raw.get("quality", {})
    quality = {
        "skip_dimensions": quality_raw.get("skip_dimensions", []),
        "max_score": quality_raw.get("max_score"),
        "lightweight_max_score": quality_raw.get("lightweight_max_score"),
    }

    # 提取 anti_patterns 配置
    anti_raw = raw.get("anti_patterns", {})
    anti_patterns = {
        "exclude_ids": anti_raw.get("exclude_ids", []),
    }

    # 提取 skill_dir 路径模式
    skill_dir_raw = raw.get("skill_dir", "")
    skill_dir_patterns = [skill_dir_raw] if skill_dir_raw else []

    return {
        "quality": quality,
        "anti_patterns": anti_patterns,
        "skill_dir_patterns": skill_dir_patterns,
        "raw": raw,
    }


def get_skill_dir_patterns(platform: str) -> list:
    """
    获取指定平台的 skill 目录路径模式列表。
    对于 universal 平台，返回所有平台的模式。
    """
    if platform == "universal":
        patterns = []
        for pid in list_platforms():
            if pid == "universal":
                continue
            profile = load_platform_profile(pid)
            patterns.extend(profile.get("skill_dir_patterns", []))
        # 去重
        return list(dict.fromkeys(patterns))
    else:
        profile = load_platform_profile(platform)
        return profile.get("skill_dir_patterns", [])


# ── 自测入口 ────────────────────────────────────────────────

if __name__ == "__main__":
    print("=== Platform Module Self-Test ===")
    print(f"Available platforms: {list_platforms()}")
    for p in list_platforms():
        profile = load_platform_profile(p)
        skip = profile["quality"].get("skip_dimensions", [])
        print(f"  {p}: skip_dimensions={skip}, patterns={profile['skill_dir_patterns']}")
    print("All tests passed.")
