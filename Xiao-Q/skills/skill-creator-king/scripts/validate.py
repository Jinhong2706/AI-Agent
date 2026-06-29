#!/usr/bin/env python3
"""
validate.py — Skill Creator King 验证器（版本见 SKILL.md frontmatter）
对目标 skill 执行结构、元数据、反模式、版本、跨文件一致性检查。

用法：python3 scripts/validate.py <skill目录路径> [--json] [--platform workbuddy|openclaw|hermes|universal] [--channel lightweight|full]
示例：
      python3 scripts/validate.py ~/.workbuddy/skills/my-skill/
      python3 scripts/validate.py ~/.openclaw/skills/my-skill/ --platform openclaw
      python3 scripts/validate.py ~/.workbuddy/skills/my-skill/ --channel lightweight
输出：默认终端彩色报告；--json 输出 JSON
"""

import json
import datetime
import os
import re
import sys
from pathlib import Path

# 将 SCK 根目录加入 Python path，支持 `from scripts.platform import ...`
SCRIPT_DIR = Path(__file__).resolve().parent
_SCK_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(_SCK_ROOT))

from scripts.platform import (detect_platform, load_platform_profile,
                               get_skill_dir_patterns, list_platforms as _list_platforms)
from scripts.yaml_utils import extract_frontmatter

# ── 常量 ──────────────────────────────────────────────────
DATA_DIR = _SCK_ROOT / "data"
ANTI_PATTERNS_FILE = DATA_DIR / "anti-patterns.yaml"

# _parse_yaml_simple / _extract_frontmatter_blocks 已迁移至 yaml_utils


# ── 文件表提取 ────────────────────────────────────────────
def _extract_file_table(content: str) -> list:
    """从 SKILL.md body 中提取文件结构表的文件路径列表"""
    files = []
    in_table = False
    for line in content.split('\n'):
        line = line.strip()
        # 非表行（空白行、标题、段落）→ 结束当前表解析
        if not line.startswith('|'):
            in_table = False
            continue
        if line.startswith('|') and line.endswith('|') and not line.startswith('|---'):
            if '文件' in line:
                in_table = True
                continue
            if in_table:
                parts = [p.strip() for p in line.split('|') if p.strip()]
                for p in parts:
                    p = p.strip('`').strip()
                    if not p or p.startswith('http'):
                        continue
                    # 接受含 / 的路径，或含文件扩展名的根级文件
                    is_file = '/' in p or any(p.endswith(ext) for ext in
                        ('.md', '.yaml', '.yml', '.py', '.json', '.txt', '.toml', '.cfg'))
                    if is_file:
                        files.append(p)
    return files


def _list_actual_files(skill_dir: Path) -> list:
    """列出 skill 目录下所有实际文件（相对路径），排除目录和缓存"""
    actual = []
    skill_dir = Path(skill_dir).expanduser().resolve()
    for root, dirs, filenames in os.walk(str(skill_dir)):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ('__pycache__', '_cache', 'node_modules')]
        for fn in filenames:
            if fn.startswith('.') and fn not in ('.consistency.yml',):
                continue
            full = Path(root) / fn
            rel = str(full.relative_to(skill_dir))
            actual.append(rel)
    return sorted(actual)


# ── 版本检查 ─────────────────────────────────────────────
def _check_version_consistency(fm: dict, skill_dir: Path) -> list:
    """遍历 skill 目录下所有 .md 文件，检测硬编码版本号是否与 SKILL.md 一致。

    遍历法替代格式匹配：不绑定特定格式（表格/blockquote/明文），
    直接扫描所有文件中的 vX.Y.Z，豁免 CHANGELOG.md（天然含历史版本）。
    """
    issues = []
    fm_version = str(fm.get('version', '')).strip()
    if not fm_version:
        return issues

    # CHANGELOG 专门处理：只检查最新条目版本
    changelog = skill_dir / "CHANGELOG.md"
    if changelog.exists():
        with open(changelog, 'r', encoding='utf-8') as f:
            cl_content = f.read()
        cl_match = re.search(r'## \[([\d.]+)\]|## ([^\n]*\d+\.\d+)', cl_content)
        cl_version = (cl_match.group(1) or cl_match.group(2)).strip() if cl_match else None
        if cl_version and cl_version != fm_version:
            issues.append({
                "id": "cross_changelog_version_mismatch",
                "severity": "HIGH",
                "check": f"CHANGELOG.md 最新条目版本为 {cl_version}，SKILL.md frontmatter 为 {fm_version}",
                "fix": f"在 CHANGELOG.md 顶部添加 ## [{fm_version}] - {datetime.date.today()} 条目",
                "reason": "CHANGELOG 最新条目版本应始终与 SKILL.md 一致，否则变更日志断裂",
            })

    # 跨文件 vX.Y.Z 版本一致性检查已迁移至 quality-audit 的 version_consistency 维度。
    # 注释性引用（"v3.12.0 新增"）和发行历史中的旧版本号无法用正则可靠区分，
    # 改由 LLM 在审计阶段逐文件读取上下文后裁断。
    
    # 文件树新鲜度：DESIGN.md 和 README.md 的结构化区域中是否列出了 references/ 下的实际文件
    # 策略：提取代码块 + Markdown 列表行 → 逐文件名搜索。不假设树形字符、缩进或排列顺序
    ref_dir = skill_dir / "references"
    if ref_dir.exists():
        actual_refs = set(f.name for f in ref_dir.iterdir() if f.suffix == '.md')

        def _check_tree_stale(doc_path, doc_id, doc_label):
            if not doc_path.exists():
                return
            with open(doc_path, 'r', encoding='utf-8') as f:
                content = f.read()
            # 结构化区域：代码块（树形图）或 Markdown 列表项（`- file.md — desc`）
            blocks = re.findall(r'```[\s\S]*?```', content)
            list_items = [l for l in content.split('\n') if re.match(r'^\s*[-*]\s', l)]
            haystack = '\n'.join(blocks + list_items)
            listed = {f for f in actual_refs if f in haystack}
            missing = actual_refs - listed
            if missing:
                issues.append({
                    "id": doc_id,
                    "severity": "LOW",
                    "check": f"{doc_label} 文件树中 references/ 段与实际文件不一致",
                    "fix": f"更新 {doc_label} 文件结构段中的 references/ 文件列表",
                    "reason": f"未列出: {sorted(missing)}",
                })

        _check_tree_stale(skill_dir / "DESIGN.md", "cross_design_tree_stale", "DESIGN.md")
        _check_tree_stale(skill_dir / "README.md", "cross_readme_tree_stale", "README.md")
    
    # 版本遗漏检测：源码比 CHANGELOG 新 → 可能忘了 bump
    # 容差窗口：同一编辑会话内文件依次写入，mtime 可能差几十秒——不报
    changelog_md = skill_dir / "CHANGELOG.md"
    if changelog_md.exists():
        changelog_mtime = changelog_md.stat().st_mtime
        max_src_mtime = 0
        for f in skill_dir.rglob('*'):
            if f.is_file() and f.suffix in ('.md', '.yaml', '.yml', '.py') and '__pycache__' not in str(f) and '_cache' not in str(f):
                mtime = f.stat().st_mtime
                if mtime > max_src_mtime:
                    max_src_mtime = mtime
        TOLERANCE = 300  # 5 分钟容差——同一编辑会话内文件依次写入的正常时间差
        if max_src_mtime > changelog_mtime + TOLERANCE:
            # 找到最新的源文件
            issues.append({
                "id": "cross_version_stale",
                "severity": "HIGH",
                "check": "有源码文件修改时间晚于 CHANGELOG.md，版本号可能未同步 bump",
                "fix": "确认是否需要 bump 版本号并在 CHANGELOG.md 添加对应条目",
                "reason": f"源码有变更（mtime={max_src_mtime:.0f}）但 CHANGELOG 未更新（mtime={changelog_mtime:.0f}），会丢失变更轨迹",
            })
    return issues


# ── 文件表检查 ────────────────────────────────────────────
def _check_file_table(skill_dir: Path, content: str) -> list:
    """检查 SKILL.md 文件结构表是否与实际文件一致"""
    issues = []
    table_files = _extract_file_table(content)
    
    # 委托模式：无文件表但声明了由 README 承载文件结构
    if not table_files and re.search(r'文件结构.*(?:详见|见|参考).*README\.md', content, re.DOTALL):
        readme = skill_dir / 'README.md'
        if readme.exists():
            with open(readme, 'r', encoding='utf-8') as f:
                r_content = f.read()
            has_tree = bool(re.search(r'(?:│\s*)?[├└]──', r_content))
            if not has_tree:
                issues.append({
                    "id": "file_table_delegation_no_tree",
                    "severity": "MEDIUM",
                    "check": "SKILL.md 委托 README.md 承载文件结构，但 README.md 中未找到树形描述",
                    "fix": "在 README.md 中添加文件树（``` 代码块 + ├── └── 结构）",
                    "reason": "委托目标中缺少可识别的文件树",
                })
            # 信任委托，不逐文件对比
            return issues
        else:
            issues.append({
                "id": "file_table_delegation_no_readme",
                "severity": "HIGH",
                "check": "SKILL.md 委托 README.md 承载文件结构，但 README.md 不存在",
                "fix": "创建 README.md 并添加文件树",
                "reason": "委托目标文件不存在",
            })
            return issues
    
    actual_files = _list_actual_files(skill_dir)
    table_set = set(table_files)
    actual_set = set(actual_files)

    # 排除不应出现在文件表中的文件
    excluded_patterns = ['__pycache__', '.pyc', '.DS_Store']
    actual_filtered = {f for f in actual_set if not any(ep in f for ep in excluded_patterns)}

    for f in sorted(actual_filtered - table_set):
        loc = "references/ " if f.startswith("references/") else "根目录 "
        issues.append({
            "id": "file_table_missing",
            "severity": "HIGH",
            "check": f"文件存在但 SKILL.md 文件结构表中遗漏: {f}",
            "fix": f"在 SKILL.md 的文件结构表中添加 `{f}` 对应的行",
            "reason": f"{loc}文件 {f} 未在文件结构表中列出，请同步更新",
        })
    for f in sorted(table_set - actual_filtered):
        issues.append({
            "id": "file_table_stale",
            "severity": "MEDIUM",
            "check": f"文件结构表中有但实际不存在的文件: {f}",
            "fix": f"从 SKILL.md 的文件结构表中移除 `{f}` 行，或恢复该文件",
            "reason": "已删除的文件残留引用会误导使用者",
        })
    return issues

def _load_ap_platforms() -> dict:
    """从 anti-patterns.yaml 加载每个 AP 的 platforms_applicable。
    返回 {ap_id: set(platforms)}，未声明的 AP 不在 dict 中（表示全平台通用）。
    """
    ap_yaml = Path(__file__).resolve().parent.parent / "data" / "anti-patterns.yaml"
    if not ap_yaml.exists():
        return {}
    text = ap_yaml.read_text(encoding='utf-8')
    ap_platforms = {}
    current_ap = None
    for line in text.split('\n'):
        m = re.match(r'^\s+- id:\s*(\S+)', line)
        if m:
            current_ap = m.group(1)
            continue
        if current_ap:
            m2 = re.match(r'^\s+platforms_applicable:\s*\[(.*?)\]', line)
            if m2:
                plats = {p.strip() for p in m2.group(1).split(',') if p.strip()}
                ap_platforms[current_ap] = plats
    return ap_platforms


# ── 反模式检查 ───────────────────────────────────────────
def check_anti_patterns(skill_path, fm_str: str, fm: dict, content: str, platform: str = None) -> list:
    """
    扫描 SKILL.md 中的已知反模式。
    
    参数:
      skill_path: skill 目录路径 (Path)
      fm_str: raw frontmatter 字符串
      fm: 解析后的 frontmatter dict
      content: SKILL.md 完整内容
      platform: 目标平台，None 则自动检测
    """
    if platform is None:
        platform = detect_platform(skill_path)
    
    profile = load_platform_profile(platform)
    exclude_ids = set(profile.get("anti_patterns", {}).get("exclude_ids", []))
    ap_platforms = _load_ap_platforms()  # {ap_id: set(platforms)}，None=全平台

    issues = []
    skill_path = Path(skill_path).expanduser().resolve()
    skill_name = skill_path.name

    # AP-001: 缺少 triggers
    if "AP-001" not in exclude_ids:
        if 'triggers' not in fm:
            issues.append({
                "id": "AP-001",
                "severity": "HIGH",
                "check": "SKILL.md frontmatter 中缺少 triggers 字段",
                "fix": '在 frontmatter 中添加 `triggers: ["关键词1", "关键词2"]`',
                "reason": "缺少触发词会导致 skill 无法被自动匹配加载",
            })

    # AP-002: 缺少 L0_trigger
    if "AP-002" not in exclude_ids:
        tb = fm.get('token_budget', {})
        if isinstance(tb, dict) and not tb.get('L0_trigger'):
            issues.append({
                "id": "AP-002",
                "severity": "MEDIUM",
                "check": "token_budget 中缺少 L0_trigger 字段",
                "fix": "添加 `L0_trigger: 200` 到 token_budget 中",
                "reason": "L0_trigger 控制触发词匹配阶段的 token 分配",
            })

    # AP-003: 缺少 template
    if "AP-003" not in exclude_ids:
        if not fm.get('template'):
            issues.append({
                "id": "AP-003",
                "severity": "MEDIUM",
                "check": "SKILL.md frontmatter 中缺少 template 字段",
                "fix": '添加 `template: basic` 或多场景/数据驱动对应值',
                "reason": "template 字段帮助审计工具选择正确的检查维度",
            })

    # AP-004: 缺少 token_budget（兼容嵌套 YAML：简单解析器会将嵌套键展平为顶层键）
    if "AP-004" not in exclude_ids:
        has_token_budget = (
            fm.get('token_budget') or  # 直接存在
            fm.get('L0_trigger') or     # 嵌套 YAML 展平后的子键
            'token_budget:' in fm_str   # raw frontmatter 中存在
        )
        if not has_token_budget:
            issues.append({
                "id": "AP-004",
                "severity": "MEDIUM",
                "check": "SKILL.md frontmatter 中缺少 token_budget 字段",
                "fix": "添加四级预算声明（L0_trigger/L1_core/L2_deep/hard_cap）",
                "reason": "缺少 Token 预算声明会影响上下文分配优化",
            })

    # AP-005: 缺少 hard_cap
    if "AP-005" not in exclude_ids:
        tb = fm.get('token_budget', {})
        if isinstance(tb, dict) and tb and not tb.get('hard_cap'):
            issues.append({
                "id": "AP-005",
                "severity": "LOW",
                "check": "token_budget 中缺少 hard_cap 字段",
                "fix": "添加 `hard_cap: 10000` 到 token_budget",
                "reason": "hard_cap 作为安全上限防止上下文溢出",
            })

    # AP-006: 重复 trigger
    if "AP-006" not in exclude_ids:
        triggers = fm.get('triggers', [])
        if isinstance(triggers, list):
            seen = set()
            for t in triggers:
                t_lower = t.lower().strip()
                if t_lower in seen:
                    issues.append({
                        "id": "AP-006",
                        "severity": "LOW",
                        "check": f"触发词 '{t}' 在 triggers 中重复出现",
                        "fix": "移除重复的触发词条目",
                        "reason": "重复触发词浪费匹配资源且可能导致日志噪音",
                    })
                    break
                seen.add(t_lower)

    # AP-007: 凭证泄露检测
    if "AP-007" not in exclude_ids:
        credential_patterns = [
            (r'(?i)(api[_-]?key|apikey|secret|token|password|passwd)\s*[:=]\s*[\'"][^\'"]{8,}[\'"]', "API Key/Token 硬编码"),
            (r'(?i)(sk-[a-zA-Z0-9]{20,})', "OpenAI API Key 格式"),
            (r'(?i)(ghp_[a-zA-Z0-9]{36})', "GitHub Personal Access Token"),
            (r'(?i)(AKIA[0-9A-Z]{16})', "AWS Access Key"),
        ]
        for pattern, desc in credential_patterns:
            if re.search(pattern, content):
                issues.append({
                    "id": "AP-007",
                    "severity": "HIGH",
                    "check": f"检测到可能的凭证泄露: {desc}",
                    "fix": "立即移除硬编码凭证，改用环境变量或配置文件",
                    "reason": "凭证泄露是严重安全隐患，可能导致账户被盗用",
                })
                break

    # AP-008: sudo / 危险命令检测
    if "AP-008" not in exclude_ids:
        dangerous = [
            r'\bsudo\b', r'\brm\s+-rf\b', r'\bchmod\s+777\b',
            r'\bcurl\b.*\|\s*(ba)?sh\b', r'\bwget\b.*\|\s*(ba)?sh\b',
            r'\bdd\s+if=', r'\bmkfs\.', r'\b:(){ :\|:& };:',
        ]
        for pattern in dangerous:
            if re.search(pattern, content):
                issues.append({
                    "id": "AP-008",
                    "severity": "HIGH",
                    "check": f"检测到潜在危险命令模式: {pattern}",
                    "fix": "避免在 skill 中硬编码 sudo/危险 shell 命令，使用白名单机制",
                    "reason": "skill 中的危险命令可能被恶意利用或在非预期环境执行",
                })
                break

    # AP-009: SKILL.md 过大
    if "AP-009" not in exclude_ids:
        lines = content.count('\n') + 1  # +1: count('\n') 统计换行符，行数=换行符+1
        if lines > 500:
            estimated_tokens = lines * 8
            severity = "MEDIUM" if estimated_tokens > 8000 else "LOW"
            issues.append({
                "id": "AP-009",
                "severity": severity,
                "check": f"SKILL.md 过长 ({lines} 行, ~{estimated_tokens}t)，可能超出合理 token 预算",
                "fix": "参考 quality-audit Token 预算合规维度确认。如已通过（15/15），此告警可忽略",
                "reason": "过长的 SKILL.md 会导致每次触发都加载大量不需要的内容",
            })

    # AP-010: 硬编码路径检测（platforms_applicable: openclaw/hermes/universal）
    ap010_applicable = ap_platforms.get("AP-010")
    if "AP-010" not in exclude_ids and (ap010_applicable is None or platform in ap010_applicable):
        found_labels = []

        # 平台专属路径检测
        hardcoded_patterns = _dir_to_regex_patterns(platform)
        for pattern in hardcoded_patterns:
            if re.search(pattern, content):
                found_labels.append(pattern)

        # 通用硬编码路径检测
        generic_patterns = [
            (r'/Users/\w+/', '/Users/xxx/'),
            (r'/home/\w+/', '/home/xxx/'),
            (r'C:\\Users\\', 'C:\\Users\\'),
            (r'~/\.\w+/skills/', '~/.xxx/skills/'),
            (r'~/.workbuddy/skills/', '~/.workbuddy/skills/'),
        ]
        for gp_raw, gp_label in generic_patterns:
            if re.search(gp_raw, content):
                found_labels.append(gp_label)

        # 排除 skill 自身所在平台目录的合法引用
        if found_labels:
            skill_dir_expanded = os.path.expanduser(str(skill_path))
            found_labels = [
                label for label in found_labels
                if not skill_dir_expanded.startswith(os.path.expanduser(label))
            ]

            if found_labels:
                issues.append({
                    "id": "AP-010",
                    "severity": "MEDIUM",
                    "check": "检测到硬编码路径模式，降低可移植性",
                    "fix": "使用相对路径或可配置的路径变量替代硬编码绝对路径",
                    "reason": "硬编码路径降低 skill 的可移植性",
                    "detail": f"匹配: {', '.join(dict.fromkeys(found_labels))}",
                })

    # AP-011: 缺少 README.md
    if "AP-011" not in exclude_ids:
        readme = skill_path / 'README.md'
        if not readme.exists():
            issues.append({
                "id": "AP-011",
                "severity": "MEDIUM",
                "check": "缺少 README.md 文件",
                "fix": "创建 README.md 包含 skill 概述、适用场景、安装说明",
                "reason": "README 是用户了解 skill 的第一入口",
            })

    # AP-012: triggers 中不含中文关键词（对中文平台）
    if "AP-012" not in exclude_ids:
        triggers = fm.get('triggers', [])
        if isinstance(triggers, list) and triggers:
            has_cjk = any(re.search(r'[\u4e00-\u9fff]', str(t)) for t in triggers)
            if not has_cjk:
                issues.append({
                    "id": "AP-012",
                    "severity": "LOW",
                    "check": "triggers 列表中缺少中文关键词",
                    "fix": "添加至少一个中文触发词以提高中文用户的匹配率",
                    "reason": "纯英文触发词可能无法匹配中文用户的自然语言查询",
                })

    # AP-013: SPEC/DESIGN 跨文件一致性（v3.14 合并架构：若无 SPEC.md，跳过此检查）
    if "AP-013" not in exclude_ids:
        spec = skill_path / 'SPEC.md'
        design = skill_path / 'DESIGN.md'
        if spec.exists() and design.exists():
            with open(spec, 'r', encoding='utf-8') as f:
                spec_content = f.read()
            with open(design, 'r', encoding='utf-8') as f:
                design_content = f.read()
            # 检查版本一致性
            sv = re.search(r'[vV]ersion[:\s]*([\d.]+)', spec_content)
            dv = re.search(r'[vV]ersion[:\s]*([\d.]+)', design_content)
            if sv and dv and sv.group(1) != dv.group(1):
                issues.append({
                    "id": "AP-013",
                    "severity": "MEDIUM",
                    "check": f"SPEC.md ({sv.group(1)}) 与 DESIGN.md ({dv.group(1)}) 版本不一致",
                    "fix": "同步 SPEC.md 和 DESIGN.md 的版本号",
                    "reason": "契约文档版本不一致会导致开发和审计的混乱",
                })

    # AP-014: description 过短（< 80 字符影响 SkillHub 上架展示）
    if "AP-014" not in exclude_ids:
        desc = fm.get("description", "")
        if desc and len(desc) < 80:
            issues.append({
                "id": "AP-014",
                "severity": "MEDIUM",
                "check": f"description 长度 {len(desc)} < 80，影响 SkillHub 上架展示和搜索发现",
                "fix": "将 description 扩展至 80-200 字，包含核心功能、适用场景、关键特性",
                "reason": "过短的 description 降低可发现性和吸引力",
            })

    # AP-015: description 为长单行字符串，非 YAML 块标量（> 或 |）
    # 检测原始 frontmatter 字符串（非解析后的值），因为 > 块标量解析后天然是单行
    if "AP-015" not in exclude_ids:
        desc_val = fm.get("description", "")
        if desc_val and isinstance(desc_val, str) and len(str(desc_val)) > 120:
            # 检查原始 fm_str 中是否使用了块标量格式（description: > 或 | 后跟缩进行）
            import re as _re
            is_block_scalar = bool(_re.search(r'^description\s*:\s*[>|]\s*$', fm_str, _re.MULTILINE))
            if not is_block_scalar:
                issues.append({
                    "id": "AP-015",
                    "severity": "MEDIUM",
                    "check": f"description 为长单行字符串 ({len(str(desc_val))} 字符)，未使用 YAML 块标量（> 或 |），部分平台可能解析失败",
                    "fix": "将 frontmatter 的 description 改为多行折叠格式（description: >），避免单行过长导致安装错误",
                    "reason": "长单行 YAML 值可能超过部分解析器的行长度限制，导致 skill 安装失败",
                })

    # AP-017: 缺少作者署名
    if "AP-017" not in exclude_ids:
        if not fm.get("author"):
            issues.append({
                "id": "AP-017",
                "severity": "LOW",
                "check": "SKILL.md frontmatter 中缺少 author 字段（署名）",
                "fix": "在 frontmatter 中添加 `author: 你的署名`（公众号/作者名）",
                "reason": "缺少署名，skill 来源不可追溯",
                "ask_user": True,
            })

    # AP-018: 过期内容或死代码
    if "AP-018" not in exclude_ids:
        issues.extend(_check_stale_content(skill_path, fm, content))

    # AP-019: README/CHANGELOG 强制同步
    if "AP-019" not in exclude_ids:
        issues.extend(_check_forced_doc_sync(skill_path, fm))

    # AP-020: description 缺少 Use when 场景触发语
    if "AP-020" not in exclude_ids:
        desc = fm.get("description", "")
        if desc and not any(kw in desc.lower() for kw in ["use when", "当…时", "适用场景"]):
            issues.append({
                "id": "AP-020",
                "severity": "MEDIUM",
                "check": "description 缺少 Use when 场景触发语，降低 AI 自动匹配精度",
                "fix": "在 description 末尾追加 'Use when {场景1}, {场景2}, or {场景3}。'",
                "reason": "description 仅描述功能未说明使用场景，skill 可能无法被正确触发",
            })

    # AP-021: 正文缺少 Output 输出模板段
    if "AP-021" not in exclude_ids:
        body_has_output = bool(re.search(
            r'^##\s+(Output|输出格式|输出模板)', content, re.MULTILINE | re.IGNORECASE
        ))
        if not body_has_output:
            issues.append({
                "id": "AP-021",
                "severity": "MEDIUM",
                "check": "正文缺少 Output 输出模板段，AI 输出格式可能不稳定",
                "fix": "添加 '## Output' 章节 + ``` 代码块包裹输出示例",
                "reason": "明确输出模板确保每次执行结果格式一致",
            })

    # AP-022: description 含版本史堆积（≥2 个旧版本号）
    if "AP-022" not in exclude_ids:
        desc = fm.get("description", "")
        if desc and isinstance(desc, str):
            # 检测 description 中是否塞入多个 vX.Y.Z 版本号（排除当前版本）
            current_ver = fm.get("version", "")
            ver_matches = re.findall(r'v\d+\.\d+(?:\.\d+)?', desc)
            # 过滤掉当前版本引用和 CHANGELOG 链接
            old_vers = [v for v in ver_matches if v != current_ver and v != f"v{current_ver}"]
            if len(old_vers) >= 2:
                issues.append({
                    "id": "AP-022",
                    "severity": "MEDIUM",
                    "check": f"description 含 {len(old_vers)} 个旧版本号 ({', '.join(old_vers[:3])})——版本史应放 CHANGELOG，description 保持功能/场景触发语",
                    "fix": "将旧版本特性描述移至 CHANGELOG.md，description 仅保留当前核心能力和触发场景（建议 ≤3 句）",
                    "reason": "版本史堆积增加触发噪音，后续迭代会持续膨胀。description 应是稳定的功能+场景摘要",
                })

    # AP-023: 输出文件约定未声明（与 AP-021 互补：一个管文件路径，一个管内容格式）
    if "AP-023" not in exclude_ids:
        # Step 1: 检测 body 是否涉及文件产出
        body = fm_str + "\n" + content  # frontmatter 也检查，覆盖 description 中的声明
        output_keywords = [
            r'(生成|导出|保存|输出|写入|下载)\s*(?:报告|文件|CSV|JSON|Markdown|代码|配置|图片|图表|数据|文档|Excel)',
            r'write\s+(?:to\s+)?(?:file|output|report|csv|json|markdown|config|code)',
            r'(export|save|generate|create|output|download|produce)\s+(?:a\s+)?(?:file|report|csv|json|markdown|config|code|image|data|document)',
            r'写(?:入|出|到)\s*(?:文件|报告|CSV|JSON|配置|数据)',
            r'导出(?:为|到|成)',
            r'生成(?:一个|一份|文件|报告)',
        ]
        has_file_output = any(re.search(kw, body, re.IGNORECASE) for kw in output_keywords)
        
        if has_file_output:
            # Step 2: 检查是否有输出文件约定声明
            convention_declared = bool(re.search(
                r'^##\s*(输出文件约定|文件输出约定|Output\s+File\s+Convention)',
                content, re.MULTILINE | re.IGNORECASE
            ))
            
            if not convention_declared:
                issues.append({
                    "id": "AP-023",
                    "severity": "MEDIUM",
                    "check": "skill 涉及文件产出，但未声明输出文件约定（目录/命名/格式/错误输出方式）",
                    "fix": "添加 '## 输出文件约定' 章节，明确：输出目录、文件命名规则、文件格式、错误输出方式，并给出路径示例。示例格式见 DESIGN 收尾确认模板",
                    "reason": "未声明的输出约定导致 AI 每次文件落地行为不一致，用户无法预期文件位置和命名",
                })

    # AP-024: 危险 shell 调用（CRITICAL）
    if "AP-024" not in exclude_ids:
        body = content.lower()
        dangerous_shell = [
            r'bash\s+-c',
            r'eval\s+["\x27 ]',
            r'exec\(',
            r'os\.system',
            r'subprocess\.',
            r'shell\s*=\s*true',
            r'\$\([^)]+\)',
        ]
        for pat in dangerous_shell:
            if re.search(pat, body):
                issues.append({
                    "id": "AP-024",
                    "severity": "CRITICAL",
                    "check": f"SKILL.md 正文含危险 shell 调用模式: {pat}",
                    "fix": "移除直接 shell 调用，改用平台安全执行接口。如确需 shell，声明安全边界和用户确认流程",
                    "reason": "恶意 skill 可通过 shell 调用在用户环境执行任意代码",
                })
                break  # 命中一个即告警，不重复

    # AP-025: 网络调用模式（MEDIUM）
    if "AP-025" not in exclude_ids:
        body = content.lower()
        network_patterns = [
            r'curl\s',
            r'wget\s',
            r'\bfetch\(',
            r'requests\.(get|post)',
            r'urlopen',
            r'socket\.connect',
        ]
        for pat in network_patterns:
            if re.search(pat, body):
                issues.append({
                    "id": "AP-025",
                    "severity": "MEDIUM",
                    "check": f"SKILL.md 正文含网络调用模式: {pat}",
                    "fix": "改用平台安全网络接口或声明数据来源。如确需网络调用，声明安全边界和用户确认流程",
                    "reason": "skill 可通过网络调用下载并执行未审查代码",
                })
                break

    # AP-026: 文件系统越界（HIGH）
    if "AP-026" not in exclude_ids:
        body = content.lower()
        fs_patterns = [
            r'~/\.(?:ssh|aws|kube|config)',
            r'/etc/(?:passwd|shadow)',
            r'chmod\s+777',
            r'rm\s+-rf\s+/',
        ]
        for pat in fs_patterns:
            if re.search(pat, body):
                issues.append({
                    "id": "AP-026",
                    "severity": "HIGH",
                    "check": f"SKILL.md 正文含文件系统越界模式: {pat}",
                    "fix": "限制文件操作范围为 skill 工作目录。如确需访问外部路径，声明安全边界和用户确认流程",
                    "reason": "恶意 skill 可通过文件越界窃取凭证或破坏系统",
                })
                break

    return issues


def _dir_to_regex_patterns(platform: str) -> list:
    """AP-010 适配器：将平台 skill_dir 模式转为正则"""
    patterns = get_skill_dir_patterns(platform)
    regex_patterns = []
    for p in patterns:
        expanded = str(Path(p).expanduser())
        escaped = re.escape(expanded)
        regex_patterns.append(escaped)
    return regex_patterns


# ── 跨引用检查 ──────────────────────────────────────────
def _check_cross_references(skill_dir: Path) -> list:
    """检查跨文件引用的一致性"""
    issues = []
    skill_dir = Path(skill_dir).expanduser().resolve()
    skill_md = skill_dir / 'SKILL.md'
    if not skill_md.exists():
        return issues

    with open(skill_md, 'r', encoding='utf-8') as f:
        content = f.read()

    # 检查引用的 references/ 文件是否存在
    refs = re.findall(r'references/[\w./-]+\.md', content)
    for ref in refs:
        ref_path = skill_dir / ref
        if not ref_path.exists():
            issues.append({
                "id": "cross_reference_missing",
                "severity": "MEDIUM",
                "check": f"SKILL.md 引用但文件不存在: {ref}",
                "fix": f"创建 {ref} 或从 SKILL.md 中移除引用",
                "reason": "断开的引用链接会让用户点击后遇到 404",
            })
    return issues


def _check_downstream_sync(skill_dir: Path) -> list:
    """AP-016: 检测 SKILL.md 修改后 README/DESIGN 是否可能未同步。

    通过比较 mtime（修改时间）实现：若 SKILL.md 比下游文件更新 > 5 分钟，
    提示开发者检查这些文件是否需要同步更新。
    """
    issues = []
    skill_dir = Path(skill_dir).expanduser().resolve()
    skill_md = skill_dir / 'SKILL.md'
    if not skill_md.exists():
        return issues

    skill_mtime = skill_md.stat().st_mtime
    downstream = {
        'README.md': '使用说明（方式/功能清单/核心概念）',
        'DESIGN.md': '设计决策（版本号/文件树）',
    }
    gap_threshold = 300  # 5 分钟，避免同会话编辑的 mtime 竞态

    for filename, description in downstream.items():
        fpath = skill_dir / filename
        if not fpath.exists():
            continue
        f_mtime = fpath.stat().st_mtime
        if skill_mtime - f_mtime > gap_threshold:
            issues.append({
                "id": "AP-016",
                "severity": "MEDIUM",
                "check": f"SKILL.md 修改后 {filename} 可能未同步更新（{description}）",
                "fix": f"检查 {filename} 是否需要同步 SKILL.md 的最新变更",
                "reason": "SKILL.md 变更后，README/DESIGN 中的功能描述、设计决策、文件树应保持同步",
            })

    return issues


def _run_count_match(rule: dict, skill_dir: Path) -> list:
    """执行 count_match 规则：磁盘文件数 = 文档声明数"""
    import glob as globlib
    import fnmatch
    issues = []
    source_pat = rule.get("source", "")
    exclude_pat = rule.get("exclude", "")
    target_file = rule.get("target", "SKILL.md")
    match_re = rule.get("match", "")

    disk_files = []
    for f in globlib.glob(str(skill_dir / source_pat)):
        if exclude_pat and fnmatch.fnmatch(f, str(skill_dir / exclude_pat)):
            continue
        if os.path.isfile(f):
            disk_files.append(f)
    disk_count = len(disk_files)

    target = skill_dir / target_file
    if not target.exists():
        return issues
    content = target.read_text(encoding="utf-8", errors="ignore")
    match = re.search(match_re, content)
    if not match:
        issues.append({
            "id": "count_match", "severity": "MEDIUM",
            "check": f"{target_file} 中未匹配到声明模式 '{match_re}'",
            "fix": f"在 {target_file} 中添加匹配 '{match_re}' 的声明",
            "reason": "自定义规则 count_match 匹配失败",
        })
        return issues
    declared = int(match.group(1))

    if disk_count != declared:
        issues.append({
            "id": "count_match", "severity": "MEDIUM",
            "check": f"文件数({disk_count}) ≠ {target_file}声明({declared})",
            "fix": f"更新 {target_file} 中的数量声明为 {disk_count}",
            "reason": f"source={source_pat} disk={disk_count} declared={declared}",
        })
    return issues


def _run_crossref_rule(rule: dict, skill_dir: Path) -> list:
    """执行 cross_reference 规则：磁盘中每个实体名在目标文档段落中出现"""
    import fnmatch
    issues = []
    source_dir = rule.get("source", "")
    exclude_pat = rule.get("exclude", "")
    target_file = rule.get("target", "SKILL.md")
    sections = rule.get("sections", [])

    target = skill_dir / target_file
    if not target.exists():
        return issues
    target_content = target.read_text(encoding="utf-8", errors="ignore")

    section_text = ""
    if sections:
        lines = target_content.split("\n")
        in_section = False
        for line in lines:
            for sec in sections:
                if sec in line:
                    in_section = True
                    section_text += line + "\n"
                    break
            else:
                if in_section:
                    section_text += line + "\n"
                if in_section and (line.strip().startswith("#") or line.strip().startswith("---")):
                    in_section = False
    else:
        section_text = target_content

    src_path = skill_dir / source_dir
    if not src_path.exists():
        return issues
    disk_names = []
    for f in sorted(src_path.glob("*.md")):
        if exclude_pat and fnmatch.fnmatch(f.name, exclude_pat):
            continue
        disk_names.append(f.stem)

    for name in disk_names:
        # 检查原名 + 别名（如果配置了）
        aliases = rule.get("aliases", {}).get(name, [])
        check_names = [name] + (aliases if isinstance(aliases, list) else [aliases])
        if not any(n in section_text for n in check_names):
            issues.append({
                "id": "cross_reference", "severity": "MEDIUM",
                "check": f"'{name}' 未在 {target_file} 指定段落中出现",
                "fix": f"在 {target_file} 的 {', '.join(sections)} 段落中添加 '{name}'",
                "reason": "磁盘文件存在但文档引用缺失",
            })
    return issues


def _run_content_count(rule: dict, skill_dir: Path) -> list:
    """执行 content_count 规则：源文件中匹配次数 = 目标文档声明数"""
    issues = []
    source_file = rule.get("source", "")
    source_re = rule.get("source_match", "")
    target_file = rule.get("target", "SKILL.md")
    target_re = rule.get("target_match", "")

    # 源文件匹配计数
    src = skill_dir / source_file
    if not src.exists():
        return issues
    content = src.read_text(encoding="utf-8", errors="ignore")
    source_count = len(re.findall(source_re, content))

    # 目标声明
    tgt = skill_dir / target_file
    if not tgt.exists():
        return issues
    tgt_content = tgt.read_text(encoding="utf-8", errors="ignore")
    match = re.search(target_re, tgt_content)
    if not match:
        return issues
    declared = int(match.group(1))

    if source_count != declared:
        issues.append({
            "id": "content_count", "severity": "MEDIUM",
            "check": f"{source_file} 实际({source_count}) ≠ {target_file}声明({declared})",
            "fix": f"更新 {target_file} 中的声明为 {source_count}，或调整 {source_file}",
            "reason": f"source_count={source_count} declared={declared}",
        })
    return issues


def validate(skill_dir: str, strict: bool = False, platform: str = None, channel: str = "full", vitality: bool = False) -> dict:
    """对 skill 目录执行全面验证。
    
    vitality=True 时额外执行退化检测（文件引用完整性 + 脚本语法健康）。
    参数:
      skill_dir: skill 根目录路径
      strict: 若为 True，MEDIUM 级别也视为失败
      platform: 目标平台（workbuddy|openclaw|hermes|universal），None 则自动检测
      channel: 通道（lightweight | full），轻量通道跳过 SPEC/DESIGN/CHANGELOG 相关检查
    
    返回: {"success": bool, "issues": list, "platform": str, "channel": str, "stats": dict, ...}
    """
    skill_path = Path(skill_dir).expanduser().resolve()
    if not skill_path.exists():
        return {
            "success": False,
            "issues": [{"id": "fatal", "severity": "CRITICAL",
                        "check": f"目录不存在: {skill_path}", "fix": "提供正确的 skill 目录路径",
                        "reason": "无法验证不存在的目录"}],
            "platform": "unknown", "stats": {"total": 1, "critical": 1, "high": 0, "medium": 0, "low": 0},
        }

    # Auto-detect platform if not specified
    if platform is None:
        platform = detect_platform(skill_path)

    profile = load_platform_profile(platform)
    exclude_ids = set(profile.get("anti_patterns", {}).get("exclude_ids", []))

    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        return {
            "success": False,
            "issues": [{"id": "fatal", "severity": "CRITICAL",
                        "check": f"SKILL.md 不存在于 {skill_path}",
                        "fix": "创建 SKILL.md 文件", "reason": "SKILL.md 是 skill 的入口文件，必须存在"}],
            "platform": platform,
            "stats": {"total": 1, "high": 0, "medium": 0, "low": 0, "critical": 1},
        }

    with open(skill_md, 'r', encoding='utf-8') as f:
        content = f.read()

    fm_str, fm = extract_frontmatter(skill_md)

    # 执行所有检查（每个 extend 独立 try，避免单点崩全崩）
    all_issues = []

    try:
        all_issues.extend(_check_version_consistency(fm, skill_path))
    except Exception as e:
        all_issues.append({
            "id": "fatal", "severity": "CRITICAL",
            "check": "版本一致性检查失败",
            "fix": str(e),
            "reason": "_check_version_consistency 执行异常",
        })

    try:
        # 轻量通道：跳过文件表检查（轻量 Skill 的文件结构更精简，不强制声明文件表）
        if channel != "lightweight":
            all_issues.extend(_check_file_table(skill_path, content))
    except Exception as e:
        all_issues.append({
            "id": "fatal", "severity": "CRITICAL",
            "check": "文件表检查失败",
            "fix": str(e),
            "reason": "_check_file_table 执行异常",
        })

    try:
        all_issues.extend(check_anti_patterns(skill_path, fm_str, fm, content, platform))
    except Exception as e:
        all_issues.append({
            "id": "fatal", "severity": "CRITICAL",
            "check": "反模式扫描失败",
            "fix": str(e),
            "reason": "check_anti_patterns 执行异常",
        })

    try:
        all_issues.extend(_check_trigger_hygiene(skill_path, fm))
    except Exception as e:
        all_issues.append({
            "id": "fatal", "severity": "CRITICAL",
            "check": "触发词卫生检查失败",
            "fix": str(e),
            "reason": "_check_trigger_hygiene 执行异常",
        })

    try:
        all_issues.extend(_check_data_source_declared(skill_path, content))
    except Exception as e:
        all_issues.append({
            "id": "fatal", "severity": "CRITICAL",
            "check": "数据源声明检查失败",
            "fix": str(e),
            "reason": "_check_data_source_declared 执行异常",
        })

    try:
        all_issues.extend(_check_cross_references(skill_path))
    except Exception as e:
        all_issues.append({
            "id": "fatal", "severity": "CRITICAL",
            "check": "交叉引用检查失败",
            "fix": str(e),
            "reason": "_check_cross_references 执行异常",
        })

    try:
        all_issues.extend(_check_downstream_sync(skill_path))
    except Exception as e:
        all_issues.append({
            "id": "fatal", "severity": "CRITICAL",
            "check": "下游同步检查失败",
            "fix": str(e),
            "reason": "_check_downstream_sync 执行异常",
        })

    # ── 自定义一致性规则 (.consistency.yml) ──
    consistency_file = skill_path / ".consistency.yml"
    if consistency_file.exists():
        # 读取原始内容，检查是否有实际生效的规则（非纯注释模板）
        raw_text = consistency_file.read_text(encoding='utf-8')
        has_active_rules = any(
            line.strip() and not line.strip().startswith('#')
            for line in raw_text.split('\n')
        )
        if not has_active_rules:
            pass  # 纯注释模板，静默跳过
        else:
            try:
                import yaml
                rules = yaml.safe_load(raw_text)
                if rules and "custom_rules" in rules:
                    for rule in rules["custom_rules"]:
                        rtype = rule.get("type")
                        if rtype == "count_match":
                            all_issues.extend(_run_count_match(rule, skill_path))
                        elif rtype == "cross_reference":
                            all_issues.extend(_run_crossref_rule(rule, skill_path))
                        elif rtype == "content_count":
                            all_issues.extend(_run_content_count(rule, skill_path))
            except ModuleNotFoundError:
                # PyYAML 未安装 → 静默跳过。用户如需自定义一致性规则，自行 pip install pyyaml
                pass
            except Exception as e:
                all_issues.append({
                    "id": "custom_consistency",
                    "severity": "MEDIUM",
                    "check": ".consistency.yml 执行失败",
                    "fix": str(e),
                    "reason": "自定义一致性规则异常",
                })

    # ── 退化检测（--vitality 时）──
    if vitality:
        try:
            all_issues.extend(_check_vitality(skill_path))
        except Exception as e:
            all_issues.append({
                "id": "fatal", "severity": "CRITICAL",
                "check": "退化检测失败",
                "fix": str(e),
                "reason": "_check_vitality 执行异常",
            })

    # 统计
    stats = {"total": len(all_issues), "high": 0, "medium": 0, "low": 0, "critical": 0}
    for issue in all_issues:
        sev = issue.get("severity", "LOW").upper()
        if sev == "CRITICAL":
            stats["critical"] += 1
        elif sev == "HIGH":
            stats["high"] += 1
        elif sev == "MEDIUM":
            stats["medium"] += 1
        else:
            stats["low"] += 1

    # 判断成功/失败：HIGH 以上必失败，MEDIUM 在 strict 模式下也失败
    has_high = stats.get("high", 0) > 0 or stats.get("critical", 0) > 0
    has_medium = stats.get("medium", 0) > 0
    success = not has_high and (not has_medium or not strict)

    # strict 模式：嵌入 self-audit（引用完整性/配置活性/测试覆盖/保鲜度/纪律）
    result = {
        "success": success,
        "issues": all_issues,
        "platform": platform,
        "channel": channel,
        "stats": stats,
        "skill_dir": str(skill_path),
        "semantic_check": {
            "description": "语义一致性检查（请 LLM 执行）：交叉读取 DESIGN.md / README.md / l2-l3-workflow.md（如存在）/ CHANGELOG.md，逐段确认其中的阶段数、数字、交付物清单、功能描述与 SKILL.md 一致。不一致项请报告。",
            "files": ["DESIGN.md", "README.md", "l2-l3-workflow.md", "CHANGELOG.md"],
            "reference": "SKILL.md"
        },
    }
    if strict:
        try:
            import importlib.util
            sa_path = Path(__file__).resolve().parent / "self-audit.py"
            spec = importlib.util.spec_from_file_location("self_audit", str(sa_path))
            sa_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(sa_module)
            self_audit_result = sa_module.audit(str(skill_path), sck_mode=False)
            result["self_audit"] = self_audit_result
        except Exception as e:
            result["self_audit"] = {"success": False, "error": str(e)}
    return result


def _check_stale_content(skill_dir: Path, fm: dict, content: str) -> list:
    """AP-018: 检测过期内容与死代码。"""
    issues = []
    skill_dir = Path(skill_dir).expanduser().resolve()
    fm_version = str(fm.get('version', '')).strip()
    if not fm_version:
        return issues

    # 检查1: references/ .md 文件头独立版本声明
    refs_dir = skill_dir / "references"
    if refs_dir.exists():
        for md_file in refs_dir.rglob("*.md"):
            try:
                text = md_file.read_text(encoding="utf-8")
            except Exception:
                continue
            m = re.search(r'^>\s*版本[：:]\s*v?([\d.]+)', text, re.MULTILINE)
            if m and m.group(1) != fm_version:
                issues.append({
                    "id": "AP-018",
                    "severity": "MEDIUM",
                    "check": f"{md_file.relative_to(skill_dir)} 声明版本 {m.group(1)}，SKILL.md 为 {fm_version}",
                    "fix": f"更新或移除 {md_file.relative_to(skill_dir)} 中的独立版本声明",
                    "reason": "独立版本声明应与 SKILL.md 同步",
                })

    # 检查2: 文档引用但文件不存在
    for doc_name in ["SKILL.md", "README.md", "DESIGN.md"]:
        doc_path = skill_dir / doc_name
        if not doc_path.exists():
            continue
        try:
            doc_text = doc_path.read_text(encoding="utf-8")
        except Exception:
            continue
        refs = re.findall(r'`?(references/[\w\/-]+\.md)`?', doc_text)
        for ref in refs:
            if not (skill_dir / ref).exists():
                issues.append({
                    "id": "AP-018",
                    "severity": "HIGH",
                    "check": f"{doc_name} 引用 {ref} 但文件不存在",
                    "fix": f"创建 {ref} 或从 {doc_name} 中移除引用",
                    "reason": "断开的文件引用会导致加载失败",
                })

    # 检查3: references/ 下孤立文件 — 跳过（需要多格式L2解析器，vNext）
    # 当前 SKILL.md 的 L2 列表使用简写格式（如"cross-cutting / rubrics"不带前缀和扩展名），
    # 需要更智能的解析器才能可靠匹配。此检查暂时关闭。 

    return issues


def _check_forced_doc_sync(skill_dir: Path, fm: dict) -> list:
    """AP-019: README/CHANGELOG 必须随 SKILL.md 同步更新。"""
    import datetime
    issues = []
    skill_dir = Path(skill_dir).expanduser().resolve()
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return issues

    skill_mtime = skill_md.stat().st_mtime
    gap_threshold = 300
    today_str = datetime.date.today().isoformat()

    changelog = skill_dir / "CHANGELOG.md"
    has_today_entry = False
    if changelog.exists():
        cl_text = changelog.read_text(encoding="utf-8")
        has_today_entry = today_str in cl_text

    for target_name in ["README.md", "CHANGELOG.md"]:
        target = skill_dir / target_name
        if not target.exists():
            continue
        if skill_mtime - target.stat().st_mtime > gap_threshold:
            if target_name == "CHANGELOG.md" and has_today_entry:
                continue
            issues.append({
                "id": "AP-019",
                "severity": "HIGH",
                "check": f"SKILL.md 修改后 {target_name} 未同步更新",
                "fix": f"同步 {target_name} 的功能描述/文件树/变更记录",
                "reason": "SKILL.md 变更后，下游文档必须同步，否则用户看到的是过时信息",
            })

    return issues


def _check_data_source_declared(skill_dir: Path, content: str) -> list:
    """检测数据依赖是否仍为模板占位状态（配合模板中的「validate 报 LOW 级警告」承诺）"""
    issues = []
    # 模板占位特征：同时出现未勾选的 checkbox + 必须声明的提示语
    has_warning = "⚠️ 不声明数据依赖" in content or "🔒 必须声明" in content
    has_unchecked = "- [ ]" in content and "数据依赖" in content
    if has_warning and has_unchecked:
        issues.append({
            "id": "DATA-001",
            "severity": "LOW",
            "check": "SKILL.md 数据依赖声明仍为模板占位状态（未勾选、未删除提示语）",
            "fix": "勾选数据依赖类型（内置/本地/网络/API），删除「⚠️ 不声明数据依赖」提示语",
            "reason": "未声明的数据依赖使 skill 可移植性不可知——换一个环境可能因缺少数据源而失败",
        })
    return issues


def _check_trigger_hygiene(skill_dir: Path, fm: dict) -> list:
    """触发词卫生检查：空/过短/高频碰撞词 → 警告。
    AP-001 已覆盖「缺少 triggers 字段」→ 此处只检测字段存在但内容为空。"""
    issues = []
    triggers = fm.get("triggers", [])
    if not isinstance(triggers, list):
        triggers = []

    # TRIG-001: triggers 字段存在但列表为空（与 AP-001「字段缺失」互补，避免双重报警）
    if "triggers" in fm and not triggers:
        issues.append({
            "id": "TRIG-001",
            "severity": "HIGH",
            "check": "SKILL.md frontmatter 中 triggers 字段存在但为空列表",
            "fix": "在 triggers: [] 中添加至少一个触发短语（如 '创建 skill'），或删除空字段让 AP-001 接手",
            "reason": "显式空列表表示开发者知道该字段但未填充——这比字段缺失更糟（明知该填却不填）",
        })
        return issues

    if not triggers:
        return issues  # triggers 字段完全缺失 → 由 AP-001 报告

    # 过短触发词检测（< 3 字符 → 太泛）
    short_triggers = [t for t in triggers if len(t) < 3]
    if short_triggers:
        issues.append({
            "id": "TRIG-002",
            "severity": "MEDIUM",
            "check": f"触发词过短（< 3 字符）：{', '.join(repr(t) for t in short_triggers)}",
            "fix": "短触发词容易和系统指令/其他 skill 碰撞。建议改为 ≥ 3 个字符的描述性短语",
            "reason": f"短触发词（如 '做'、'帮'）触发精度极低，会和大量其他 skill 抢路由",
        })

    # 高频碰撞词检测：只对单触发词或极短组合（< 6 字符）做碰撞检测
    # 多词触发词（如 "create skill"）即使含高频词，整体组合已有足够特异性
    HIGH_COLLISION_WORDS = {
        "帮助", "帮我", "做", "搞", "弄", "来", "去", "改", "修", "查",
        "生成", "创建", "写", "读", "分析", "处理", "运行",
        "help", "do", "make", "create", "run", "fix", "check", "test"
    }
    collision_triggers = []
    for t in triggers:
        t_clean = t.strip()
        # 只检测：1) 单字触发词 = 碰撞词  2) 两字短组合 = 碰撞词开头
        if t_clean in HIGH_COLLISION_WORDS:
            collision_triggers.append(t)
        elif len(t_clean) <= 5 and any(
            t_clean.startswith(w) for w in HIGH_COLLISION_WORDS
            if len(w) >= 2 or (len(w) == 1 and len(t_clean) <= 3)
        ):
            # 短触发词（≤5字符）且以碰撞词开头 → 仍然太泛
            collision_triggers.append(t)
    # 去重
    collision_triggers = list(set(collision_triggers))
    if collision_triggers:
        issues.append({
            "id": "TRIG-003",
            "severity": "LOW",
            "check": f"触发词使用了高频碰撞词：{', '.join(repr(t) for t in collision_triggers[:5])}",
            "fix": "高频碰撞词容易被其他 skill 抢断。建议用更具体的触发短语（如 'review this pull request' 代替 'review'）",
            "reason": "触发词越具体，路由越精准。高频词可能导致你的 skill 在错误场景被激活，或正确场景被其他 skill 抢走",
        })

    return issues


def _check_vitality(skill_dir: Path) -> list:
    """退化检测：检查文件引用有效性 + 脚本语法健康。
    
    返回退化警告列表（空 = 健康）。
    """
    issues = []
    skill_dir = Path(skill_dir).expanduser().resolve()
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return issues

    # 1. 文件引用完整性：SKILL.md 中引用的 references/ 文件是否存在
    content = skill_md.read_text(encoding="utf-8")
    refs = re.findall(r'references/[\w./-]+\.md', content)
    for ref in refs:
        ref_path = skill_dir / ref
        if not ref_path.exists():
            issues.append({
                "id": "VITAL-001",
                "severity": "HIGH",
                "check": f"退化：引用的文件已丢失: references/{ref.split('references/')[-1]}",
                "fix": f"恢复 {ref} 或从 SKILL.md 移除引用",
                "reason": "文件丢失后 skill 加载可能失败或行为异常",
            })

    # 2. 脚本语法检查：scripts/ 下所有 .py 文件能否通过编译
    scripts_dir = skill_dir / "scripts"
    if scripts_dir.exists():
        for py_file in scripts_dir.glob("*.py"):
            try:
                with open(py_file, 'r') as f:
                    compile(f.read(), str(py_file), 'exec')
            except SyntaxError as e:
                issues.append({
                    "id": "VITAL-002",
                    "severity": "HIGH",
                    "check": f"退化：脚本语法错误: {py_file.name}",
                    "fix": f"修复 {py_file.name} 第 {e.lineno} 行: {e.msg}",
                    "reason": "语法错误会导致 skill 功能完全不可用",
                })

    return issues


# ── 输出格式化 ──────────────────────────────────────────
def _format_report(result: dict) -> str:
    """将验证结果格式化为终端彩色报告"""
    lines = []
    success = result["success"]
    stats = result["stats"]
    platform = result.get("platform", "unknown")

    status_icon = "✅" if success else "❌"
    lines.append(f"\n{status_icon} 验证{'通过' if success else '失败'}")
    lines.append(f"   平台: {platform}  |  通道: {result.get('channel', 'full')}")
    lines.append(f"   统计: Critical: {stats.get('critical', 0)}, High: {stats.get('high', 0)}, "
                 f"Medium: {stats.get('medium', 0)}, Low: {stats.get('low', 0)}")
    lines.append("")

    if not result.get("issues"):
        lines.append("无问题发现。")

    # self-audit 结果（strict 模式）
    sa = result.get("self_audit")
    if sa:
        lines.append("")
        lines.append("--- Self-Audit ---")
        if sa.get("error"):
            lines.append(f"❌ self-audit 执行失败: {sa['error']}")
        else:
            sm = sa.get("summary", {})
            lines.append(f"  结果: {'✅ 通过' if sm.get('passed') else '⚠️ 发现问题'}  ({sm.get('checks_passed', 0)}/{sm.get('checks_total', 0)} 项通过，{sm.get('total_issues', 0)} 个问题)")
            for c in sa.get("checks", []):
                icon = "✅" if c.get("passed") else "⚠️"
                lines.append(f"  {icon} {c['check']}")
                for iss in c.get("issues", []):
                    lines.append(f"    - {iss.get('detail', iss)}")
        lines.append("")
        lines.append("（语义一致性检查见 result.semantic_check 字段）")
        lines.append("")
        return "\n".join(lines)
    for i, issue in enumerate(result["issues"], 1):
        sev = issue.get("severity", "LOW")
        lines.append(f"[{sev}] #{i} {issue.get('id', 'unknown')}")
        lines.append(f"  检查: {issue.get('check', 'N/A')}")
        lines.append(f"  修复: {issue.get('fix', 'N/A')}")
        lines.append(f"  原因: {issue.get('reason', 'N/A')}")
        lines.append("")
    lines.append("（语义一致性检查见 result.semantic_check 字段）")
    lines.append("")
    return "\n".join(lines)


# ── CLI 入口 ────────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python3 scripts/validate.py <skill目录路径> [--json] [--platform workbuddy|openclaw|hermes|universal] [--channel lightweight|full]")
        print("示例:")
        print("      python3 scripts/validate.py ~/.workbuddy/skills/my-skill/")
        print("      python3 scripts/validate.py ~/.openclaw/skills/my-skill/ --platform openclaw")
        print("      python3 scripts/validate.py ~/.workbuddy/skills/my-skill/ --channel lightweight")
        sys.exit(1)

    skill_dir = sys.argv[1]
    use_json = "--json" in sys.argv
    strict = "--strict" in sys.argv
    exit_zero = "--exit-zero" in sys.argv
    vitality = "--vitality" in sys.argv
    platform = None
    channel = "full"
    for i, arg in enumerate(sys.argv):
        if arg == '--platform' and i + 1 < len(sys.argv):
            platform = sys.argv[i + 1]
        if arg == '--channel' and i + 1 < len(sys.argv):
            channel = sys.argv[i + 1]

    result = validate(skill_dir, strict=strict, platform=platform, channel=channel, vitality=vitality)

    if use_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(_format_report(result))

    sys.exit(0 if (result["success"] or exit_zero) else 1)
