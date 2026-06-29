#!/usr/bin/env python3
"""
quality-audit.py — 16纬度 Skill 质量审计引擎
用法：python3 scripts/quality-audit.py <skill> [--channel lightweight|full] [--platform workbuddy|openclaw|hermes|universal] [--no-cache] [--json] [--llm-review] [--stats]

--stats: 输出内部计数（维度/反模式/脚本/References/ADR/REQ 等），JSON 格式。

输入：skill 目录路径
输出：结构化审计报告（JSON / 终端友好文本）

--llm-review: 收集所有文件上下文 + 4 个固定问题，注入 llm_review 字段。
  脚本不调用 LLM——由上层 AI Agent 读取 llm_review 上下文后回答 4 问，追加结果。
"""

import hashlib
import json
import re
import subprocess
import sys
import time
from pathlib import Path

# ── sys.path 设置（支持 from scripts.platform import ...）────────
SCRIPT_DIR = Path(__file__).resolve().parent
SCK_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCK_ROOT))

from scripts.platform import detect_platform, load_platform_profile, get_skill_dir_patterns, list_platforms
from scripts.yaml_utils import parse_yaml_text, extract_frontmatter_raw

# ── 常量 ────────────────────────────────────────────────────
CACHE_DIR = SCK_ROOT / "_cache"
AUDIT_YAML_PATH = SCK_ROOT / "data" / "checklists" / "audit.yaml"

def _get_sck_version() -> str:
    """从 SCK 自身 SKILL.md frontmatter 读取版本号（SSOT）。"""
    try:
        sck_skill_md = SCK_ROOT / "SKILL.md"
        if sck_skill_md.exists():
            fm = extract_frontmatter_raw(sck_skill_md)
            if fm:
                m = re.search(r'version:\s*["\']?([\d.]+)["\']?', fm)
                if m:
                    return m.group(1)
    except (OSError, ValueError, re.error):
        pass
    return "0.0.0"

def _load_lightweight_skip() -> set:
    """从 audit.yaml 加载轻量通道跳过维度列表（SSOT）。"""
    try:
        raw = AUDIT_YAML_PATH.read_text(encoding="utf-8")
        found = False
        skip_list = []
        for line in raw.split("\n"):
            if line.strip() == "lightweight_skip:":
                found = True
                continue
            if found:
                stripped = line.strip()
                if stripped.startswith("- "):
                    skip_list.append(stripped[2:].strip())
                elif stripped and not stripped.startswith("#"):
                    break
        return set(skip_list)
    except (OSError, ValueError):
        # Fallback：审计引擎自身加载失败时，返回空集（保守：全评）
        return set()

# ── 14纬度审计定义 ─────────────────────────────────────────
# id: 维度标识符, name: 显示名, weight: 满分权重, max_score: 维度满分
# category: 分类, description: 检查内容, manual: 是否需人工裁定
# v3.17.4: 17→14维——3组合并（cross_doc_sync/doc_quality/maintenance_hygiene）
AUDIT_DIMENSIONS = [
    {"id": "frontmatter_safety", "name": "Frontmatter 安全", "weight": 15, "max_score": 15,
     "category": "安全", "description": "YAML frontmatter 语法正确性、特殊字符转义、块标量使用"},
    {"id": "token_budget", "name": "Token 预算合规", "weight": 15, "max_score": 15,
     "category": "性能", "description": "L0_trigger/L1_core/L2_deep/hard_cap 四级预算定义完整性"},
    {"id": "file_completeness", "name": "文件完整性", "weight": 10, "max_score": 10,
     "category": "结构", "description": "SKILL.md 文件结构表与实际文件一致性"},
    # 合并 semantic_consistency(8) + readme_sync(8) + cross_doc_sync(8) = 24
    {"id": "cross_doc_sync", "name": "文档一致性", "weight": 24, "max_score": 24,
     "category": "一致性", "description": "跨文件声明/修改时间/内容一致性"},
    {"id": "trigger_coverage", "name": "触发覆盖", "weight": 8, "max_score": 8,
     "category": "可用性", "description": "triggers 覆盖主要使用场景的程度（需 AI 裁定）", "manual": True},
    {"id": "script_llm_boundary", "name": "脚本-LLM边界", "weight": 8, "max_score": 8,
     "category": "架构", "description": "脚本与 LLM 的职责边界清晰度（需 AI 裁定）", "manual": True},
    {"id": "l2_organization", "name": "L2深度组织", "weight": 8, "max_score": 8,
     "category": "架构", "description": "L2 深度参考文档的组织与可发现性（需 AI 裁定）", "manual": True},
    {"id": "anti_patterns", "name": "反模式扫描", "weight": 8, "max_score": 8,
     "category": "质量", "description": "anti-patterns.yaml 中定义的反模式检测"},
    {"id": "body_structure", "name": "正文结构完整性", "weight": 6, "max_score": 6,
     "category": "结构", "description": "Purpose/Context/Instructions/Output/Notes/Further Reading 六段完整度（需 AI 裁定）", "manual": True},
    {"id": "version_consistency", "name": "跨文件版本一致性", "weight": 4, "max_score": 4,
     "category": "一致性", "description": "非 SKILL.md 文件中的 vX.Y.Z 引用与当前版本一致（LLM 内部裁断，不输出逐条详情）", "manual": True},
    # 合并 template_compliance(4) + changelog_today(5) = 9
    {"id": "maintenance_hygiene", "name": "维护卫生", "weight": 9, "max_score": 9,
     "category": "维护", "description": "模板合规 + 当日 CHANGELOG 记录"},
    {"id": "data_sources", "name": "数据源规范", "weight": 4, "max_score": 4,
     "category": "数据", "description": "sources.yaml 格式与引用一致性"},
    {"id": "readme_quality", "name": "README 质量", "weight": 6, "max_score": 6,
     "category": "文档", "description": "README 完整性（版本/安装/使用/适合谁）（需 AI 裁定）", "manual": True},
    # design_quality(6) — PRINCIPLES 维度已移除
    {"id": "doc_quality", "name": "设计文档质量", "weight": 6, "max_score": 6,
     "category": "文档", "description": "DESIGN.md 完整性"},
]

# ── 内置 YAML 子集解析器 ─────────────────────────────────────

# _parse_simple_yaml / _coerce_value 已迁移至 yaml_utils.parse_yaml_text

# ── Frontmatter 提取 ───────────────────────────────────────

# _extract_frontmatter 已迁移至 yaml_utils.extract_frontmatter_raw

# ── 缓存 ──────────────────────────────────────────────────

def get_cache_key(skill_path: Path, version: str, platform: str = None) -> str:
    """生成缓存键，含所有关键文件 mtime 防静默过期
    
    v3.17.1 修复：除 SKILL.md 外，同时纳入 CHANGELOG/README/DESIGN
    的 mtime，避免只改非 SKILL.md 文件时命中旧缓存。
    """
    name = skill_path.name
    # 收集所有关键文件的 mtime，取最新值
    mtimes = []
    for fname in ["SKILL.md", "CHANGELOG.md", "README.md", "DESIGN.md"]:
        f = skill_path / fname
        if f.exists():
            mtimes.append(str(f.stat().st_mtime))
    content_mtime = max(mtimes) if mtimes else "0"
    platform = platform or "universal"
    short_hash = hashlib.md5(
        f"{skill_path}{version}{content_mtime}{platform}{_get_sck_version()}".encode()
    ).hexdigest()[:6]
    return f"{name}_v{version}_{platform}_{short_hash}"

def _read_cache(cache_key: str) -> dict | None:
    """读取缓存"""
    cache_file = CACHE_DIR / f"{cache_key}.json"
    if not cache_file.exists():
        return None
    try:
        data = json.loads(cache_file.read_text(encoding='utf-8'))
        # 缓存有效期 24h
        if time.time() - data.get("cached_at", 0) > 86400:
            return None
        return data
    except Exception:
        return None

def _write_cache(cache_key: str, data: dict) -> None:
    """写入缓存"""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / f"{cache_key}.json"
    cache_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

# ── 子进程调用 validate.py ──────────────────────────────────

def run_validate(skill_dir: Path, platform: str = None) -> dict:
    """调用 validate.py 获取详细验证结果"""
    cmd = [sys.executable, str(SCRIPT_DIR / "validate.py"), str(skill_dir), "--json"]
    if platform:
        cmd.extend(["--platform", platform])
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        # validate.py 发现问题时返回 exit 1，但 stdout 仍有有效 JSON
        if result.stdout.strip():
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError:
                pass
        return {"success": False, "issues": [], "error": result.stderr or result.stdout}
    except Exception as e:
        return {"success": False, "issues": [], "error": str(e)}

# ── Prechecks ─────────────────────────────────────────────────

def _run_prechecks(skill_path: Path, fm: str = None) -> list:
    """运行 frontmatter 和文件存在性等快速检查"""
    issues = []
    skill_md = skill_path / "SKILL.md"
    
    if not skill_md.exists():
        issues.append({"id": "no_skill_md", "severity": "CRITICAL", "message": "SKILL.md 不存在"})
        return issues

    # Frontmatter 安全
    content = skill_md.read_text(encoding='utf-8')
    if not content.startswith('---'):
        issues.append({"id": "fm_missing", "severity": "HIGH", "message": "SKILL.md 缺少 frontmatter 分隔符"})
    
    # 检查 YAML 块标量危险字符（复用传入的 fm，避免重复提取）
    if fm is None:
        fm = extract_frontmatter_raw(skill_md)
    if fm:
        if '\t' in fm:
            issues.append({"id": "fm_tabs", "severity": "HIGH", "message": "Frontmatter 含制表符，应使用空格"})
        # 检查未转义的特殊字符
        dangerous_chars = re.findall(r'["\']', fm)
        if len(dangerous_chars) % 2 != 0:
            issues.append({"id": "fm_quote", "severity": "MEDIUM", "message": "Frontmatter 引号不匹配"})

    return issues

# ── 14维度审计函数 ──────────────────────────────────────────

def audit_frontmatter_safety(skill_path: Path) -> dict:
    """维度1: Frontmatter 安全"""
    fm = extract_frontmatter_raw(skill_path / "SKILL.md")
    if not fm:
        return {"score": 0, "status": "fail", "note": "无 frontmatter 或解析失败"}
    
    score = 15
    deductions = []
    
    if '\t' in fm:
        deductions.append("含制表符")
        score -= 5
    if ':' not in fm:
        deductions.append("无有效 YAML 键值对")
        score = 0
    else:
        # 检查必需的 frontmatter 字段
        required = ["name", "description"]
        for field in required:
            if f"{field}:" not in fm:
                deductions.append(f"缺 {field} 字段")
                score -= 3
    
    score = max(0, score)
    status = "pass" if score >= 12 else ("warn" if score >= 7 else "fail")
    return {"score": score, "status": status, "note": "; ".join(deductions) if deductions else ""}

def audit_token_budget(skill_path: Path) -> dict:
    """维度2: Token 预算合规 — 声明值 vs 实测值对比"""
    fm = extract_frontmatter_raw(skill_path / "SKILL.md")
    if not fm:
        return {"score": 0, "status": "fail", "note": "无 frontmatter"}
    
    budget_fields = ["L0_trigger", "L1_core", "L2_deep", "hard_cap"]
    present = [f for f in budget_fields if f"{f}:" in fm]
    missing = [f for f in budget_fields if f"{f}:" not in fm]
    
    if len(present) == 0:
        # v3.21.1: pure language skills (no scripts/) don't need token budgets → skip
        scripts_dir = skill_path / "scripts"
        if not scripts_dir.exists() or not any(scripts_dir.iterdir()):
            return {"score": 15, "status": "skip", "note": "纯语言 skill（无 scripts/），Token 预算不适用"}
        return {"score": 0, "status": "fail", "note": "有 scripts/ 但未定义 Token 预算"}
    
    score = min(15, len(present) * 4)
    deductions = []
    
    # 提取声明值
    declared = {}
    for field in present:
        m = re.search(rf'{field}:\s*(\d+)', fm)
        if m:
            declared[field] = int(m.group(1))
    
    # 实测 SKILL.md 大小
    skill_md = skill_path / "SKILL.md"
    actual_chars = len(skill_md.read_text(encoding='utf-8')) if skill_md.exists() else 0
    actual_tokens = actual_chars // 3
    
    # 检查1: hard_cap 是否低于实测内容大小
    if "hard_cap" in declared and declared["hard_cap"] < actual_tokens:
        deductions.append(f"hard_cap({declared['hard_cap']}) < 实测({actual_tokens})")
        score -= 5
    
    # 检查2: 层级递进性 (L0 < L1 < L2 < hard_cap)
    level_order = ["L0_trigger", "L1_core", "L2_deep", "hard_cap"]
    declared_levels = [declared.get(k) for k in level_order if k in declared]
    if len(declared_levels) >= 2:
        for i in range(len(declared_levels) - 1):
            if declared_levels[i] is not None and declared_levels[i+1] is not None:
                if declared_levels[i] >= declared_levels[i+1]:
                    deductions.append(f"{level_order[i]}({declared_levels[i]}) >= {level_order[i+1]}({declared_levels[i+1]})")
                    score -= 2
    
    # 检查3: L2_deep 与 hard_cap 比例（L2 应 ≤ hard_cap * 0.8，留执行余量）
    if "L2_deep" in declared and "hard_cap" in declared:
        if declared["hard_cap"] > 0 and declared["L2_deep"] / declared["hard_cap"] > 0.8:
            deductions.append(f"L2_deep({declared['L2_deep']}) / hard_cap({declared['hard_cap']}) > 0.8")
            score -= 2
    
    score = max(0, score)
    status = "pass" if score >= 12 else ("warn" if score >= 7 else "fail")
    note = "; ".join(deductions) if deductions else (f"缺: {', '.join(missing)}" if missing else f"实测 {actual_tokens}t OK")
    return {"score": score, "status": status, "note": note}

def _load_scaffold_files(scaffold_name: str, platform: str = "universal") -> set:
    """加载 scaffold skill 的标准文件列表。

    从平台对应的 skill 目录递归获取所有文件（如 workbuddy → ~/.workbuddy/skills/）。
    禁用时返回空集合（无 scaffold 委托）。
    """
    if not scaffold_name:
        return set()

    # 根据平台获取 skill 目录模式，找到 scaffold 所在路径
    patterns = get_skill_dir_patterns(platform)
    scaffold_path = None
    for pat in patterns:
        candidate = Path(pat).expanduser() / scaffold_name
        if candidate.exists():
            scaffold_path = candidate
            break

    if scaffold_path is None:
        # 回退：遍历所有已知平台的 skill 目录
        for pid in list_platforms():
            patterns = get_skill_dir_patterns(pid)
            for pat in patterns:
                candidate = Path(pat).expanduser() / scaffold_name
                if candidate.exists():
                    scaffold_path = candidate
                    break
            if scaffold_path:
                break

    if scaffold_path is None:
        return set()
    if not scaffold_path.exists():
        return set()
    
    exclude_patterns = ['__pycache__', '_cache', '.DS_Store', '.gitkeep', '.git',
                        'data/review-history.jsonl',  # 审查历史是运行产物，非模板文件
                        ]
    files = set()
    for f in scaffold_path.rglob('*'):
        if f.is_file():
            skip = any(pat in str(f) for pat in exclude_patterns)
            if not skip:
                rel = str(f.relative_to(scaffold_path))
                files.add(rel)
    return files


def audit_file_completeness(skill_path: Path) -> dict:
    """维度3: 文件完整性"""
    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        return {"score": 0, "status": "fail", "note": "SKILL.md 不存在"}
    
    content = skill_md.read_text(encoding='utf-8')
    
    # 提取文件结构表中的文件列表
    table_files = set()
    in_table = False
    header_seen = False
    in_file_section = False
    for line in content.split('\n'):
        # 跟踪是否在 "文件" 相关章节下（容许多种写法）
        if line.strip().startswith('## ') and '文件' in line:
            in_file_section = True
        elif line.strip().startswith('## '):
            in_file_section = False
        
        if in_file_section and '|' in line and line.strip().startswith('|'):
            # 检测表头：本章节下的第一条 | 行即视为表头
            if not header_seen and not in_table:
                header_seen = True
                continue
            # 表头后的分隔行 --- 才触发收集
            if header_seen and '---' in line:
                in_table = True
                header_seen = False
                continue
            if in_table:
                parts = [p.strip() for p in line.split('|') if p.strip()]
                if parts:
                    fname = parts[0].strip('`').strip()
                    table_files.add(fname)
        # 大节标题或水平线时退出表格收集
        elif in_table and (line.strip().startswith('## ') or line.strip() == '---'):
            in_table = False
    
    # 委托模式：SKILL.md 无文件表时，先确认声明了委托，再信任 README 树形结构（与 validate.py 同策略）
    if not table_files and re.search(r'文件结构.*(?:详见|见|参考).*README\.md', content, re.DOTALL):
        readme = skill_path / "README.md"
        if readme.exists():
            r_content = readme.read_text(encoding='utf-8')
            if re.search(r'[├└]──', r_content):
                return {"score": 10, "status": "pass", "note": "委托至 README.md（含树形结构）"}
    
    # 获取实际文件（排除隐藏文件、缓存、版本控制目录）
    actual_files = set()
    exclude_patterns = ['__pycache__', '_cache', '.DS_Store', '.gitkeep', '.git', 'node_modules', '.gitignore', '__pycache__']
    for f in skill_path.rglob('*'):
        if f.is_file():
            skip = any(pat in str(f) for pat in exclude_patterns)
            if not skip:
                rel = str(f.relative_to(skill_path))
                actual_files.add(rel)
    
    # ── scaffold 委托 ──
    # 如果 SKILL.md 声明了 scaffold，跳过 scaffold 的标准文件，只检查增量文件
    fm_raw = extract_frontmatter_raw(skill_md)  # 传 Path，非 content 字符串
    fm = parse_yaml_text(fm_raw) if fm_raw else {}
    scaffold_name = fm.get("scaffold")
    scaffold_files = _load_scaffold_files(scaffold_name, platform=detect_platform(skill_path)) if scaffold_name else set()
    if scaffold_files:
        actual_files = actual_files - scaffold_files
    
    # 比较
    missing_from_table = actual_files - table_files
    score = max(0, 10 - len(missing_from_table) * 2)
    status = "pass" if score >= 8 else "warn"
    note = f"表缺: {', '.join(sorted(missing_from_table)[:3])}" if missing_from_table else ""
    return {"score": score, "status": status, "note": note}

def audit_trigger_coverage(skill_path: Path, manual_score: int = None) -> dict:
    """维度5: 触发覆盖（需 AI 裁定）"""
    fm = extract_frontmatter_raw(skill_path / "SKILL.md")
    
    # 尝试内联数组格式: triggers: [a, b, c]
    inline = re.search(r'triggers:\s*\[([^\]]*)\]', fm)
    if inline:
        trigger_count = len([t.strip() for t in inline.group(1).split(',') if t.strip()])
    else:
        # Fallback: 多行 - 格式
        triggers = re.findall(r'triggers:\s*\n((?:\s+-.*\n?)*)', fm)
        trigger_count = len(re.findall(r'^\s+-', triggers[0] if triggers else "", re.MULTILINE))
    
    if manual_score is not None:
        return {"score": manual_score, "status": "manual", "note": "AI 裁定"}
    
    # v3.21.1: 0 triggers is not a defect — some skills use context matching
    score = min(8, trigger_count * 2) if trigger_count > 0 else 8
    status = "manual"
    note = f"{trigger_count} 个触发器" + ("（内联数组）" if inline else "（多行列表）") + "，待 AI 裁定"
    return {"score": score, "status": status, "note": note}

def audit_script_llm_boundary(skill_path: Path, manual_score: int = None) -> dict:
    """维度6: 脚本-LLM边界（需 AI 裁定）"""
    if manual_score is not None:
        return {"score": manual_score, "status": "manual", "note": "AI 裁定"}
    return {"score": 8, "status": "manual", "note": "待 AI 裁定脚本与 LLM 的职责边界"}

def audit_l2_organization(skill_path: Path, manual_score: int = None) -> dict:
    """维度7: L2深度组织（需 AI 裁定）"""
    refs_dir = skill_path / "references"
    ref_count = len(list(refs_dir.glob("*.md"))) if refs_dir.exists() else 0
    
    if manual_score is not None:
        return {"score": manual_score, "status": "manual", "note": "AI 裁定"}
    
    score = min(8, ref_count * 2)
    status = "manual"
    return {"score": score, "status": status, "note": f"references/ 含 {ref_count} 个文档，待 AI 裁定"}

def audit_anti_patterns(skill_path: Path, validate_result: dict = None) -> dict:
    """维度8: 反模式扫描"""
    if validate_result and "issues" in validate_result:
        ap_issues = [i for i in validate_result["issues"] if i.get("id","").startswith("AP-")]
        score = max(0, 8 - len(ap_issues) * 2)
        status = "pass" if score >= 6 else "warn"
        return {"score": score, "status": status, "note": f"命中 {len(ap_issues)} 个反模式"}
    
    return {"score": 8, "status": "pass", "note": "无 validate 数据，假定无问题"}

def audit_body_structure(skill_path: Path, manual_score: int = None) -> dict:
    """维度: 正文结构完整性（需 AI 裁定）"""
    content = (skill_path / "SKILL.md").read_text(encoding="utf-8")

    if manual_score is not None:
        return {"score": manual_score, "status": "manual", "note": "AI 裁定"}

    # 检查六段存在性（中英文 heading 均支持）
    sections = {
        "Purpose": bool(re.search(r'^##\s+Purpose', content, re.MULTILINE)),
        "Context": bool(re.search(r'^##\s+Context', content, re.MULTILINE)),
        "Instructions": bool(re.search(r'^##\s+(Instructions|工作流|步骤)', content, re.MULTILINE)),
        "Output": bool(re.search(r'^##\s+(Output|输出格式|输出模板)', content, re.MULTILINE)),
        "Notes": bool(re.search(r'^##\s+(Notes|注意事项)', content, re.MULTILINE)),
        "Further Reading": bool(re.search(r'(Further Reading|延伸阅读|参考)', content)),
    }
    found = sum(1 for v in sections.values() if v)
    score = min(6, found)

    missing = [k for k, v in sections.items() if not v]
    note = f"六段完整度 {found}/6" + (f"，缺失: {', '.join(missing)}" if missing else " ✅")
    return {"score": score, "status": "manual", "note": note}

def audit_version_consistency(skill_path: Path, manual_score: int = None) -> dict:
    """维度: 跨文件版本一致性（LLM 内部裁断，不输出详情）

    扫描所有 .md 文件中的 vX.Y.Z 引用，逐条自动预分类：
    - 版本历史行 / 注释性引用（如 "v3.12.0 新增"）→ 自动豁免
    - 无法自动判定的孤立版本号 → 仅输出到 note 供 LLM 内部裁断
    标准审计报告中只显示裁断结论，不 dump 逐条匹配上下文。
    """
    skill_md = skill_path / "SKILL.md"
    fm_version = None
    if skill_md.exists():
        content = skill_md.read_text(encoding="utf-8")
        m = re.search(r'^version:\s*["\']?([\d.]+)', content, re.MULTILINE)
        if m:
            fm_version = m.group(1)

    if manual_score is not None:
        return {"score": manual_score, "status": "manual", "note": "LLM 裁断完成"}

    if not fm_version:
        return {"score": 4, "status": "pass", "note": "SKILL.md 无版本号，跳过"}

    # 收集所有非匹配 vX.Y.Z
    findings = []
    for md_file in sorted(skill_path.glob("*.md")):
        if md_file.name == "SKILL.md":
            continue
        try:
            file_content = md_file.read_text(encoding="utf-8")
        except Exception:
            continue
        for m in re.finditer(r'v(\d+\.\d+\.\d+)\b', file_content):
            v = m.group(1)
            if v == fm_version:
                continue
            pos = m.start()
            ctx_start = max(0, pos - 80)
            ctx_end = min(len(file_content), pos + 60)
            ctx = file_content[ctx_start:ctx_end].replace('\n', '↵')
            line_num = file_content[:pos].count('\n') + 1
            findings.append({
                "file": md_file.name,
                "line": line_num,
                "version": f"v{v}",
                "context": ctx,
                "safe": False,
            })

    if not findings:
        return {"score": 4, "status": "pass", "note": "所有 vX.Y.Z 引用与 SKILL.md 一致 ✅"}

    # 自动预分类：注释性引用 / 版本历史行 → safe=True
    annotation_kw = ["新增", "引入", "合并", "修复", "优化", "升级", "迁移",
                     "加入", "排除", "支持", "订阅", "发布", "移除", "重构",
                     "added", "fixed", "changed", "removed", "merged",
                     "REQ-", "ADR-", "决策", "decision"]
    for f_item in findings:
        ctx_lower = f_item["context"].lower()
        is_annotation = any(kw in ctx_lower for kw in annotation_kw)
        is_header = f_item["context"].strip().startswith("## ")
        is_version_line = re.search(r'v\d+\.\d+\.\d+\s*[-–—]\s*\d{4}', f_item["context"])
        # 在 CHANGELOG / RELEASE-NOTES / DESIGN / 技术报告 中的版本引用视为安全
        # DESIGN.md 记录设计决策（含版本演进），technical-report.md 含版本历史表
        is_history_file = f_item["file"] in ("CHANGELOG.md", "RELEASE-NOTES.md", "DESIGN.md", "technical-report.md")
        # 文件树/行内注释：(v3.12.4)、← ... (v3.12.4) 等
        ver_digits = f_item["version"].lstrip("v")
        is_parenthetical = bool(re.search(r'[\(（]\s*v?' + re.escape(ver_digits), f_item["context"]))
        if is_version_line or is_annotation or is_history_file or is_header or is_parenthetical:
            f_item["safe"] = True

    safe_count = sum(1 for f in findings if f["safe"])
    suspicious = [f for f in findings if not f["safe"]]
    total = len(findings)

    if not suspicious:
        return {
            "score": 4, "status": "pass",
            "note": f"全部 {total} 条非匹配 vX.Y.Z 为注释性引用/版本历史行，自动豁免 ✅",
        }

    # note 仅写摘要，不输出逐条详情（LLM 裁断时自己调函数取 findings）
    note = f"v{fm_version} ≠ {total}条非匹配引用（{safe_count}条注释/历史自动豁免），{len(suspicious)}条待 LLM 内部裁断"

    score = max(0, 4 - len(suspicious))
    status = "manual" if len(suspicious) > 0 else "pass"
    return {"score": score, "status": status, "note": note}

def audit_template_compliance(skill_path: Path) -> dict:
    """维度9: 模板合规"""
    required_files = ["SKILL.md", "README.md", "CHANGELOG.md"]
    optional_files = ["DESIGN.md", "config.yaml"]
    
    present = [f for f in required_files if (skill_path / f).exists()]
    optional_present = [f for f in optional_files if (skill_path / f).exists()]
    
    score = min(4, len(present) * 1 + len(optional_present))
    status = "pass" if len(present) >= 3 else "warn"
    missing = [f for f in required_files if f not in present]
    note = f"缺: {', '.join(missing)}" if missing else f"+{len(optional_present)} 可选文件"
    return {"score": score, "status": status, "note": note}

def audit_data_sources(skill_path: Path) -> dict:
    """维度10: 数据源规范"""
    sources_yaml = skill_path / "data" / "sources.yaml"
    if not sources_yaml.exists():
        return {"score": 4, "status": "pass", "note": "无数据源（工具型 skill）"}
    
    try:
        sources = parse_yaml_text(sources_yaml.read_text(encoding='utf-8'))
        source_count = len(sources)
        score = min(4, source_count)
        status = "pass" if source_count > 0 else "warn"
        return {"score": score, "status": status, "note": f"{source_count} 个数据源"}
    except Exception as e:
        return {"score": 0, "status": "fail", "note": f"解析失败: {e}"}

def audit_readme_quality(skill_path: Path, manual_score: int = None) -> dict:
    """维度11: README 质量（需 AI 裁定，按 readme-standard.md 5 项评估）"""
    readme = skill_path / "README.md"
    if not readme.exists():
        return {"score": 0, "status": "fail", "note": "README.md 不存在"}
    
    if manual_score is not None:
        return {"score": manual_score, "status": "manual", "note": "AI 裁定"}
    
    content = readme.read_text(encoding='utf-8')
    
    # 按 SkillHub 发布标准检测 8 个章节（中英双语关键词）
    # 「快速开始」和「触发方式」为独立段落——前者说明上手方式，后者列举具体触发词
    checks = {
        "概述/标题": bool(re.search(r'^# ', content, re.MULTILINE)),
        "快速开始/怎么用": bool(re.search(r'(快速开始|怎么用|Quick Start|Getting Started|How to Use)', content, re.IGNORECASE)),
        "触发方式/触发词": bool(re.search(r'(触发方式|触发词|使用方式|Trigger|How to trigger)', content, re.IGNORECASE)),
        "核心能力/功能": bool(re.search(r'(核心能力|核心功能|主要功能|能力|Core|Features|Capabilities|What it does)', content, re.IGNORECASE)),
        "适合谁": bool(re.search(r'(适合谁|适用场景|目标用户|谁适合|为你准备|Who is this for|Target Audience|Use Cases)', content, re.IGNORECASE)),
        "边界与注意事项": bool(re.search(r'(边界|注意|限制|约束|不适用|不擅长|不能|Limitations|Caveats|Constraints|Not for)', content, re.IGNORECASE)),
        "资源引用": any(k in content for k in ["SKILL.md", "CHANGELOG.md", "CODEX.md"]),
        "文件结构": any(k in content for k in ["├──", "└──", "文件结构", "File Structure"]),
    }
    found = sum(1 for v in checks.values() if v)
    
    # 加分：推荐段落（已纳入 8 个主检查，不再额外加分）
    bonus = 0
    
    score = min(6, found)
    status = "manual"
    
    missing = [k for k, v in checks.items() if not v]
    note = f"覆盖 {found}/8 必须段（SkillHub标准）"
    if missing:
        note += f"（缺失: {', '.join(missing)}）"
    if bonus:
        note += f" +{bonus} 推荐段"
    note += "，待 AI 裁定"
    
    return {"score": score, "status": status, "note": note}

def audit_design_quality(skill_path: Path) -> dict:
    """维度16: DESIGN.md 质量 — 5 项自动检查（候选方案/架构/局限/决策/SKILL-DESIGN边界）"""
    design = skill_path / "DESIGN.md"
    if not design.exists():
        return {"score": 0, "status": "fail", "note": "DESIGN.md 不存在"}
    
    content = design.read_text(encoding='utf-8')
    checks = {
        "候选方案对比": bool(re.search(r'(候选方案|备选方案|方案对比|Alternatives|Trade-off|权衡)', content, re.IGNORECASE)),
        "架构总览": bool(re.search(r'(架构总览|架构图|架构决策|Architecture|Design.*Decision|系统架构|模块关系|```(?:mermaid|d2|ascii))', content, re.IGNORECASE)),
        "已知局限": bool(re.search(r'(已知局限|限制|Limitations|不适用|不擅长|Caveats|边界|不覆盖)', content, re.IGNORECASE)),
        "决策记录": bool(re.search(r'(^## 决策 \d+:|### 决策 \d+|### ADR-|### D-\d+|\*\*决策\*\*)', content, re.MULTILINE)),
        "SKILL-DESIGN边界": bool(re.search(r'(SKILL.*DESIGN|DESIGN.*SKILL|边界声明|分工|不在.*SKILL|不在.*DESIGN)', content, re.IGNORECASE)),
    }
    found = sum(1 for v in checks.values() if v)
    score = min(6, found + 1)  # +1 base score for existence
    status = "pass" if score >= 5 else ("warn" if score >= 3 else "fail")
    missing = [k for k, v in checks.items() if not v]
    note = f"覆盖 {found}/5 检查项"
    if missing:
        note += f"（缺失: {', '.join(missing)}）"
    return {"score": score, "status": status, "note": note}

def audit_semantic_consistency(skill_path: Path) -> dict:
    """维度12: 声明一致性"""
    spec = skill_path / "SPEC.md"
    design = skill_path / "DESIGN.md"
    
    # v3.14 合并架构：若仅有 DESIGN.md（无独立 SPEC.md），跳过跨文件检查
    if not design.exists():
        return {"score": 8, "status": "pass", "note": "无 SPEC/DESIGN"}
    if not spec.exists():
        # 合并架构：仅 DESIGN.md 承载所有内容，无需跨文件比较
        return {"score": 8, "status": "pass", "note": "合并架构（仅 DESIGN.md），跳过跨文件检查"}
    
    spec_content = spec.read_text(encoding='utf-8')
    design_content = design.read_text(encoding='utf-8')
    
    # 检查版本引用一致性
    # 优先匹配 HTML comment 标记 `<!-- version: X.X.X -->`
    spec_v = re.search(r'<!--\s*version:\s*([\d.]+)\s*-->', spec_content)
    design_v = re.search(r'<!--\s*version:\s*([\d.]+)\s*-->', design_content)
    
    issues = []
    if spec_v and design_v and spec_v.group(1) != design_v.group(1):
        issues.append(f"版本不一致: SPEC {spec_v.group(1)} vs DESIGN {design_v.group(1)}")
    elif not spec_v or not design_v:
        # Fallback: 从所有 v-pattern 中取版本号最大的（版本表最新在上，但文档内可能有旧注释干扰）
        spec_versions = re.findall(r'[vV]([\d.]+)', spec_content)
        design_versions = re.findall(r'[vV]([\d.]+)', design_content)
        if spec_versions and design_versions:
            def _semver_key(v):
                parts = v.split('.')
                return tuple(int(p) for p in parts)
            spec_latest = max(spec_versions, key=_semver_key)
            design_latest = max(design_versions, key=_semver_key)
            if spec_latest != design_latest:
                issues.append(f"版本不一致: SPEC {spec_latest} vs DESIGN {design_latest}")
    
    score = max(0, 8 - len(issues) * 4)
    status = "pass" if score >= 8 else "warn"
    return {"score": score, "status": status, "note": "; ".join(issues)}

def audit_readme_sync(skill_path: Path) -> dict:
    """维度13: README 同步 — 内容一致性检查（非 mtime 时序）"""
    readme = skill_path / "README.md"
    skill_md = skill_path / "SKILL.md"
    
    if not readme.exists():
        return {"score": 0, "status": "fail", "note": "README.md 不存在"}
    
    readme_content = readme.read_text(encoding='utf-8')
    issues = []
    
    # 检查1: README 版本声明与 SKILL.md frontmatter 版本一致
    if skill_md.exists():
        skill_content = skill_md.read_text(encoding='utf-8')
        fm_v = re.search(r'version:\s*["\']?([\d.]+)["\']?', skill_content)
        if fm_v:
            fm_version = fm_v.group(1)
            rv = re.search(r'(?:当前版本|Version|版本)[：:\s]*\*{0,2}v?([\d.]+)', readme_content, re.IGNORECASE)
            if rv and rv.group(1) != fm_version:
                issues.append(f"版本不一致: README {rv.group(1)} vs SKILL {fm_version}")
    
    # 检查2: 有文件树时，检查关键文件是否被提及
    if re.search(r'[├└]──', readme_content):
        key_files = ["SKILL.md", "README.md", "CHANGELOG.md"]
        missing = [f for f in key_files if f not in readme_content]
        if missing:
            issues.append(f"文件树缺: {', '.join(missing)}")
    
    if not issues:
        return {"score": 8, "status": "pass", "note": "内容同步"}
    
    score = max(0, 8 - len(issues) * 3)
    status = "pass" if score >= 6 else "warn"
    return {"score": score, "status": status, "note": "; ".join(issues)}

def audit_changelog_today(skill_path: Path) -> dict:
    """维度14: CHANGELOG 是否跟上 SKILL.md 版本

    判断信号：CHANGELOG 最新条目的版本号 vs SKILL.md frontmatter.version
    一致 → 已跟上；不一致 → 落后。
    零 mtime 依赖、零时区依赖、零假阳性。
    """
    changelog = skill_path / "CHANGELOG.md"
    if not changelog.exists():
        return {"score": 0, "status": "fail", "note": "CHANGELOG.md 不存在"}

    # 取 SKILL.md frontmatter.version
    skill_md = skill_path / "SKILL.md"
    fm_version = None
    if skill_md.exists():
        m = re.search(r'^version:\s*["\']?([\d.]+)', skill_md.read_text(encoding="utf-8"), re.MULTILINE)
        if m:
            fm_version = m.group(1)

    if not fm_version:
        return {"score": 5, "status": "pass", "note": "SKILL.md 无版本号，跳过 CHANGELOG 同步检查"}

    # CHANGELOG 最新条目（第一个 ## [x.y.z] 行）
    cl_content = changelog.read_text(encoding="utf-8")
    m = re.search(r'^##\s*\[([\d.]+)\]', cl_content, re.MULTILINE)
    if not m:
        return {"score": 0, "status": "warn", "note": "CHANGELOG 无版本条目"}

    cl_version = m.group(1)
    if cl_version == fm_version:
        return {"score": 5, "status": "pass", "note": f"CHANGELOG 最新 ({cl_version}) = SKILL.md ({fm_version}) ✅"}

    return {
        "score": 0,
        "status": "warn",
        "note": f"CHANGELOG 最新 ({cl_version}) 落后于 SKILL.md ({fm_version})",
    }


def audit_cross_doc_sync(skill_path: Path) -> dict:
    """维度15: 文档同步 — 检查五个核心文档间的内容一致性"""
    skill_md = skill_path / "SKILL.md"
    readme = skill_path / "README.md"
    tech_report = skill_path / "docs" / "technical-report.md"
    rules_md = skill_path / "references" / "rules.md"
    design_md = skill_path / "DESIGN.md"
    
    issues = []
    
    # ── 检查1: 模式数残留 — SKILL.md 当前的「N模式」在 README/tech-report 中必须一致 ──
    def count_modes(text: str) -> set:
        found = set()
        for n in range(1, 11):
            if f'{n}模式' in text or f'{n}种模式' in text:
                found.add(n)
        return found
    
    if skill_md.exists():
        skill_content = skill_md.read_text(encoding='utf-8')
        modes_in_skill = count_modes(skill_content)
    
        if modes_in_skill:
            latest_mode = max(modes_in_skill)
            
            if readme.exists():
                readme_content = readme.read_text(encoding='utf-8')
                modes_in_readme = count_modes(readme_content)
                if latest_mode not in modes_in_readme:
                    issues.append(f"README 未提及{latest_mode}模式")
                # 残留检查: 旧模式数不应出现
                for old_n in range(1, latest_mode):
                    if old_n in modes_in_readme:
                        issues.append(f"README 残留‘{old_n}模式’（当前为{latest_mode}模式）")
            
            if tech_report.exists():
                tech_content = tech_report.read_text(encoding='utf-8')
                modes_in_tech = count_modes(tech_content)
                if latest_mode not in modes_in_tech:
                    issues.append(f"技术报告 未提及{latest_mode}模式")
                for old_n in range(1, latest_mode):
                    if old_n in modes_in_tech:
                        issues.append(f"技术报告 残留‘{old_n}模式’（当前为{latest_mode}模式）")
    
    # ── 检查2: rules.md 版本号 → SKILL.md 文件结构表引用 ──
    if rules_md.exists() and skill_md.exists():
        rules_first = rules_md.read_text(encoding='utf-8').split('\n')[0]
        m = re.search(r'v([\d.]+)', rules_first)
        if m:
            rules_version = m.group(1)
            if rules_version not in skill_content:
                issues.append(f"SKILL.md 未引用 rules 版本 v{rules_version}")
    
    # ── 检查3: technical-report 版本号 vs SKILL frontmatter ──
    if tech_report.exists() and skill_md.exists():
        fm = extract_frontmatter_raw(skill_md)
        if fm:
            fm_m = re.search(r'version:\s*(\S+)', fm)
            if fm_m:
                skill_ver = fm_m.group(1)
                tech_content = tech_report.read_text(encoding='utf-8')
                # tech-report 第二行通常含版本号
                tech_lines = tech_content.split('\n')
                tech_ver_match = re.search(r'版本\s*([\d.]+)', '\n'.join(tech_lines[:5]))
                if tech_ver_match:
                    if tech_ver_match.group(1) != skill_ver:
                        issues.append(f"技术报告版本 {tech_ver_match.group(1)} ≠ SKILL {skill_ver}")
                elif skill_ver not in tech_content:
                    issues.append(f"技术报告 未引用版本 {skill_ver}")
    
    # ── 检查4: DESIGN.md 决策数 vs CHANGELOG 版本条目数（粗略关联）─
    if design_md.exists():
        design_content = design_md.read_text(encoding='utf-8')
        design_decisions = len(re.findall(r'(^## 决策 \d+:|### 决策 \d+|### ADR-|### D-\d+)', design_content, re.MULTILINE))
        # 只做软检查: DESIGN 有内容就通过
        if design_decisions == 0:
            issues.append("DESIGN.md 无决策条目")
    
    score = max(0, 8 - len(issues) * 2)
    status = "pass" if score >= 6 else ("warn" if score >= 3 else "fail")
    note = "; ".join(issues) if issues else "五文档内容一致"
    return {"score": score, "status": status, "note": note}


# ── 维度审计函数映射 ──────────────────────────────────────
# ── 合并维度函数 ─────────────────────────────────────────

def audit_cross_doc_sync_merged(skill_path: Path) -> dict:
    """合并 semantic_consistency + readme_sync + cross_doc_sync
    （版本一致性已迁移至独立 dimension: version_consistency，LLM 裁断）"""
    s = audit_semantic_consistency(skill_path)
    r = audit_readme_sync(skill_path)
    c = audit_cross_doc_sync(skill_path)
    score = s.get("score", 0) + r.get("score", 0) + c.get("score", 0)
    max_score = 24
    status = "pass" if score >= 20 else ("warn" if score >= 14 else "fail")
    notes = []
    for r_ in [s, r, c]:
        if r_.get("note"):
            notes.append(r_["note"])
    return {"score": score, "max_score": max_score, "status": status, "note": "; ".join(notes)}


def audit_maintenance_hygiene(skill_path: Path) -> dict:
    """合并 template_compliance + changelog_today"""
    t = audit_template_compliance(skill_path)
    c = audit_changelog_today(skill_path)
    score = t.get("score", 0) + c.get("score", 0)
    max_score = 9
    status = "pass" if score >= 7 else ("warn" if score >= 5 else "fail")
    notes = []
    for r in [t, c]:
        if r.get("note"):
            notes.append(r["note"])
    return {"score": score, "max_score": max_score, "status": status, "note": "; ".join(notes)}


def audit_doc_quality(skill_path: Path) -> dict:
    """仅 DESIGN.md 质量（PRINCIPLES 维度已移除）"""
    return audit_design_quality(skill_path)


# ── 维度函数映射 ─────────────────────────────────────────

AUDIT_FUNCTIONS = {
    "frontmatter_safety": audit_frontmatter_safety,
    "token_budget": audit_token_budget,
    "file_completeness": audit_file_completeness,
    "cross_doc_sync": audit_cross_doc_sync_merged,
    "trigger_coverage": audit_trigger_coverage,
    "script_llm_boundary": audit_script_llm_boundary,
    "l2_organization": audit_l2_organization,
    "anti_patterns": audit_anti_patterns,
    "body_structure": audit_body_structure,
    "version_consistency": audit_version_consistency,
    "maintenance_hygiene": audit_maintenance_hygiene,
    "data_sources": audit_data_sources,
    "readme_quality": audit_readme_quality,
    "doc_quality": audit_doc_quality,
}


# ── Rubric 加载 ───────────────────────────────────────────

def _load_rubrics() -> dict:
    """从 audit.yaml 加载手动维度的评分 Rubric（状态机解析，支持 4 层嵌套）
    
    Returns:
        {dim_id: [{score: int, criteria: str}, ...]}
    """
    if not AUDIT_YAML_PATH.exists():
        return {}
    
    text = AUDIT_YAML_PATH.read_text(encoding='utf-8')
    rubrics = {}
    current_dim = None
    in_rubric = False
    current_rubric_item = None
    
    for line in text.split('\n'):
        stripped = line.strip()
        indent = len(line) - len(line.lstrip(' '))
        
        # 维度 ID: 缩进 2 的 "- id: xxx"
        if indent == 2 and stripped.startswith('- id:'):
            current_dim = stripped.split(':', 1)[1].strip()
            in_rubric = False
            current_rubric_item = None
            continue
        
        # rubric 开始: 缩进 4 的 "rubric:"
        if indent == 4 and stripped == 'rubric:':
            if current_dim:
                rubrics[current_dim] = []
            in_rubric = True
            continue
        
        # rubric item 开始: 缩进 6 的 "- score: N"
        if in_rubric and indent == 6 and stripped.startswith('- score:'):
            try:
                score = int(stripped.split(':', 1)[1].strip())
            except ValueError:
                score = 0
            current_rubric_item = {"score": score, "criteria": ""}
            rubrics.setdefault(current_dim, []).append(current_rubric_item)
            continue
        
        # rubric item criteria: 缩进 8 的 "criteria: ..."
        if in_rubric and current_rubric_item is not None and indent == 8 and stripped.startswith('criteria:'):
            criteria = stripped.split(':', 1)[1].strip().strip('"').strip("'")
            current_rubric_item["criteria"] = criteria
            continue
        
        # 退出 rubric 区域
        if in_rubric and indent <= 4 and not stripped.startswith('- score:') and not stripped.startswith('criteria:'):
            in_rubric = False
            current_rubric_item = None
    
    return rubrics


# ── 主审计函数 ──────────────────────────────────────────────

def audit(
    skill_dir: str,
    channel: str = "full",
    no_cache: bool = False,
    manual_scores: dict = None,
    platform: str = None,
    llm_review: bool = False,
) -> dict:
    """
    对指定 skill 执行全维度质量审计。

    参数:
        skill_dir: skill 目录路径
        channel: "lightweight" | "full"
        no_cache: 跳过缓存
        manual_scores: 手动评分 {dim_id: score}
        platform: 目标平台（None=自动检测）

    返回:
        dict 包含总分、维度结果、缓存信息等
    """
    skill_path = Path(skill_dir).expanduser().resolve()
    
    if not skill_path.exists():
        raise FileNotFoundError(f"目录不存在: {skill_dir}")
    
    skill_name = skill_path.name
    
    # ── 自动检测平台 ──
    if platform is None:
        platform = detect_platform(skill_path)
    
    # ── 加载平台 profile ──
    platform_profile = load_platform_profile(platform)
    platform_quality = platform_profile.get("quality", {})
    platform_skip = set(platform_quality.get("skip_dimensions", []))
    
    # ── 版本号 ──
    fm = extract_frontmatter_raw(skill_path / "SKILL.md")
    m = re.search(r'version:\s*["\']?([\d.]+)["\']?', fm) if fm else None
    version = m.group(1) if m else "0.0.0"
    
    # ── 缓存检查 ──
    cache_key = get_cache_key(skill_path, version, platform)
    if not no_cache and channel != "lightweight":
        cached = _read_cache(cache_key)
        if cached:
            cached["_cache_hit"] = True
            return cached
    
    # ── Prechecks（传入已提取的 fm，避免重复提取）──
    prechecks = _run_prechecks(skill_path, fm)
    
    # ── validate 结果 ──
    validate_result = run_validate(skill_path, platform)
    
    # ── 计算跳跃集合 ──
    skip_dims = set()
    lightweight_skip = set()  # 轻量通道跳过维度（需记录来源以便生成区分性 note）
    if channel == "lightweight":
        lightweight_skip = _load_lightweight_skip()
        skip_dims = lightweight_skip | platform_skip
    else:
        skip_dims = platform_skip
    
    # ── 各维度审计 ──
    dimension_results = []
    total_score = 0
    total_weight = 0
    manual_count = 0
    manual_pending = []
    
    # 加载手动维度 Rubric
    rubrics = _load_rubrics()
    
    for dim in AUDIT_DIMENSIONS:
        did = dim["id"]
        
        # 生成区分性 skip note
        if did in lightweight_skip and did in platform_skip:
            skip_note = f"轻量通道 + 平台 {platform} 跳过"
        elif did in lightweight_skip:
            skip_note = "轻量通道跳过"
        else:
            skip_note = f"平台 {platform} 不适用此维度"
        
        # 跳过维度
        if did in skip_dims:
            dimension_results.append({
                "id": did,
                "name": dim["name"],
                "score": dim["max_score"],
                "max_score": dim["max_score"],
                "weight": dim["weight"],
                "status": "skipped",
                "category": dim["category"],
                "note": skip_note,
            })
            continue
        
        # 执行审计
        audit_fn = AUDIT_FUNCTIONS.get(did)
        if not audit_fn:
            dimension_results.append({
                "id": did, "name": dim["name"], "score": 0, "max_score": dim["max_score"],
                "weight": dim["weight"], "status": "error", "category": dim["category"],
                "note": "审计函数未实现",
            })
            continue
        
        is_manual = dim.get("manual", False)
        
        try:
            if is_manual and manual_scores and did in manual_scores:
                result = audit_fn(skill_path, manual_score=manual_scores[did])
            elif did == "anti_patterns":
                result = audit_fn(skill_path, validate_result)
            else:
                result = audit_fn(skill_path)
        except Exception as e:
            result = {"score": 0, "status": "error", "note": str(e)}
        
        dim_result = {
            "id": did,
            "name": dim["name"],
            "score": result.get("score", 0),
            "max_score": dim["max_score"],
            "weight": dim["weight"],
            "status": result.get("status", "unknown"),
            "category": dim["category"],
            "note": result.get("note", ""),
        }
        # 注入 Rubric（手动维度）
        if is_manual and did in rubrics:
            dim_result["rubric"] = rubrics[did]
        dimension_results.append(dim_result)
        
        if result.get("status") in ("manual",):
            manual_count += 1
            manual_pending.append({"id": did, "name": dim["name"]})
        
        total_score += result.get("score", 0)
        total_weight += dim["weight"]
    
    # ── 评分与等级 ──
    # 注意：skipped 维度的得分不计入 total_score，但维度已跳过
    # 重新计算实际总分（仅计入非跳过维度）
    actual_score = sum(
        d.get("score", 0) for d in dimension_results 
        if d.get("status") not in ("skipped", "error")
    )
    actual_weight = sum(
        d.get("weight", 0) for d in dimension_results 
        if d.get("status") not in ("skipped", "error")
    )
    
    max_possible = sum(d["max_score"] for d in AUDIT_DIMENSIONS)
    
    if actual_weight > 0:
        percentage = actual_score / actual_weight * 100 if actual_weight > 0 else 0
    else:
        percentage = 0
    
    # ── 防作弊完整性检查 ──
    integrity_checks = []
    
    # 检查1: Precheck 严重问题 vs 高分的矛盾
    high_severity_prechecks = [p for p in prechecks if p.get("severity") in ("CRITICAL", "HIGH")]
    if high_severity_prechecks and percentage >= 85:
        integrity_checks.append({
            "type": "precheck_score_mismatch",
            "severity": "HIGH",
            "message": f"有 {len(high_severity_prechecks)} 个 HIGH/CRITICAL 预检问题但总分 {percentage:.0f}%，可能存在评分虚高"
        })
    
    # 检查2: 反模式命中数 vs anti_patterns 维度得分
    ap_issues = [i for i in validate_result.get("issues", []) if i.get("id", "").startswith("AP-")]
    ap_dim = next((d for d in dimension_results if d["id"] == "anti_patterns"), None)
    if ap_dim and len(ap_issues) >= 3 and ap_dim.get("score", 0) >= ap_dim.get("max_score", 8) * 0.75:
        integrity_checks.append({
            "type": "ap_score_inconsistency",
            "severity": "MEDIUM",
            "message": f"命中 {len(ap_issues)} 个反模式但 anti_patterns 维度得分偏高 ({ap_dim['score']}/{ap_dim['max_score']})"
        })
    
    # 检查3: 全维度满分检测
    non_manual_dims = [d for d in dimension_results 
                       if d.get("status") not in ("manual", "skipped", "error")]
    perfect_dims = [d for d in non_manual_dims if d.get("score", 0) == d.get("max_score", 0)]
    if len(non_manual_dims) > 0 and len(perfect_dims) == len(non_manual_dims):
        integrity_checks.append({
            "type": "all_perfect_auto",
            "severity": "LOW",
            "message": f"全部 {len(non_manual_dims)} 个自动评分维度均满分，请人工复核是否存在评分规则过于宽松"
        })
    
    # 检查4: 手动维度全部自动给满分（无 manual_scores 输入时）
    manual_dims = [d for d in dimension_results if d.get("status") == "manual"]
    if manual_dims and not manual_scores:
        max_manual = [d for d in manual_dims if d.get("score", 0) == d.get("max_score", 0)]
        if len(max_manual) == len(manual_dims):
            integrity_checks.append({
                "type": "all_manual_max",
                "severity": "MEDIUM",
                "message": f"全部 {len(manual_dims)} 个手动维度自动给满分，需 AI 裁定后确认"
            })
    
    # 等级判定
    if percentage >= 90:
        grade = "A"
        grade_meaning = "优秀"
    elif percentage >= 75:
        grade = "B"
        grade_meaning = "良好"
    elif percentage >= 60:
        grade = "C"
        grade_meaning = "及格"
    else:
        grade = "D"
        grade_meaning = "需改进"
    
    # ── Token 统计 ──
    token_actual = 0
    token_budget = {}
    skill_md_path = skill_path / "SKILL.md"
    if skill_md_path.exists():
        content = skill_md_path.read_text(encoding='utf-8')
        token_actual = len(content) // 3  # 粗略估算
        # 从 frontmatter 提取预算
        if fm:
            for field in ["L0_trigger", "L1_core", "L2_deep", "hard_cap"]:
                m = re.search(rf'{field}:\s*(\d+)', fm)
                if m:
                    token_budget[field] = int(m.group(1))
    
    result = {
        "success": True,
        "skill": skill_name,
        "version": version,
        "channel": channel,
        "platform": platform,
        "total_score": actual_score,
        "total_weight": actual_weight,
        "max_possible": max_possible,
        "percentage": round(percentage, 1),
        "grade": grade,
        "grade_meaning": grade_meaning,
        "dimensions": dimension_results,
        "manual_pending": manual_pending,
        "prechecks": prechecks,
        "integrity_checks": integrity_checks,
        "token_actual": token_actual,
        "token_budget": token_budget,
        "validate_issues": validate_result.get("issues", []),
        "cached_at": time.time(),
        "sck_version": _get_sck_version(),
    }

    # ── LLM Review 上下文注入（--llm-review 时）──
    if llm_review:
        result["llm_review"] = collect_llm_review_context(skill_path)
    
    # ── 写入审查历史（长期记忆，非缓存）──
    if channel == "full":
        _append_review_history(result, dimension_results, ap_issues, prechecks, manual_dims)
    
    # ── 写入缓存 ──
    if not no_cache and channel != "lightweight":
        _write_cache(cache_key, result)
    
    return result


# ── LLM Review 上下文收集 ──────────────────────────────────

LLM_REVIEW_QUESTIONS = [
    {
        "id": "Q1",
        "title": "语义漂移",
        "question": (
            "SKILL.md 中声称的数字（如「18 个风格」「15 条原则」「20 大 V」）"
            "与对应列表的实际计数是否一致？"
            "逐项列出版本号中的声称为 N 但实际为 M 的情况。"
        ),
    },
    {
        "id": "Q2",
        "title": "术语一致性",
        "question": (
            "同一概念在不同文件（SKILL.md / README.md / DESIGN.md / CHANGELOG.md）中是否有不同叫法？"
            "例如「Lightweight」vs「轻量」、「N 阶段」vs「N 步骤」。"
            "只列不一致的叫法，不列同义正常表述。"
        ),
    },
    {
        "id": "Q3",
        "title": "集成完整性",
        "question": (
            "SKILL.md 工作流中新增的子节（如 auto-test / LLM 语义审查）"
            "是否在 Phase 4 总览表、L2/L3 执行表中被明确提及？"
            "是否在 Output 输出模板中有对应行？"
            "列出任何在正文中存在但未在总览/Output 模板中提及的子节。"
        ),
    },
    {
        "id": "Q4",
        "title": "残余痕迹",
        "question": (
            "SKILL.md 正文中是否有单篇文章/单次会话的具体残留？"
            "信号包括：具体文章标题残留、单次会话的临时上下文、"
            "日期/时间戳残留、一次性任务的具名引用。"
            "列出所有疑似残余的具体文本和位置，判断是否应抽象为通用规则。"
        ),
    },
]


def collect_llm_review_context(skill_path: Path) -> dict:
    """收集 LLM review 所需的全部文件上下文 + 4 个结构化问题。

    返回：
        {
            "questions": [...],        # 4 个固定问题
            "files": {                 # 关键文件内容（截断）
                "SKILL.md": "<前 8000 字符>",
                "README.md": "<全文>",
                ...
            },
            "extracted_signals": {     # 脚本预提取的信号，辅助 LLM 判断
                "numeric_claims": [...],   # SKILL.md 中的数字声称
                "subsection_list": [...],  # Phase 4 的子节列表
                "overview_mentions": [...],# 总览表中提到的小节
            }
        }
    """
    context = {
        "questions": LLM_REVIEW_QUESTIONS,
        "files": {},
        "extracted_signals": {},
    }

    # ── 收集关键文件内容 ──
    key_files = ["SKILL.md", "README.md", "DESIGN.md", "CHANGELOG.md"]
    for fname in key_files:
        fpath = skill_path / fname
        if fpath.exists():
            raw = fpath.read_text(encoding="utf-8")
            # SKILL.md 截断到 12000 字符（避免 token 爆炸）
            if fname == "SKILL.md":
                context["files"][fname] = raw[:12000] + ("\n\n[... truncated ...]" if len(raw) > 12000 else "")
            else:
                context["files"][fname] = raw

    # 收集 references/ 下的 .md 文件（各截断到 3000 字符）
    refs_dir = skill_path / "references"
    if refs_dir.exists():
        context["files"]["_references"] = {}
        for ref_file in sorted(refs_dir.glob("*.md"))[:20]:  # 最多 20 个文件
            raw = ref_file.read_text(encoding="utf-8")
            context["files"]["_references"][ref_file.name] = raw[:3000] + (
                "\n\n[... truncated ...]" if len(raw) > 3000 else ""
            )

    # ── 预提取信号 ──

    # 信号 1：数字声称（匹配「N 个|大 V|条|模式|阶段|项」）
    skill_content = context["files"].get("SKILL.md", "")
    numeric_claims = []
    for m in re.finditer(
        r'(\d+)\s*(?:个|大\s*V|条|模式|阶段|项|维度|种|篇)',
        skill_content
    ):
        ctx_start = max(0, m.start() - 40)
        ctx_end = min(len(skill_content), m.end() + 40)
        ctx = skill_content[ctx_start:ctx_end].replace('\n', '↵')
        numeric_claims.append({
            "claimed": int(m.group(1)),
            "context": ctx,
        })
    context["extracted_signals"]["numeric_claims"] = numeric_claims

    # 信号 2：Phase 4 的子节列表（提取审校段中的所有 ### 标题）
    phase4_match = re.search(
        r'## Phase 4[^\n]*\n(.*?)(?=\n## (?:Phase [56]|Phase \d|Output|Notes|\Z))',
        skill_content, re.DOTALL
    )
    subsections = []
    if phase4_match:
        for m in re.finditer(r'^###\s+(.+)', phase4_match.group(1), re.MULTILINE):
            subsections.append(m.group(1).strip())
    context["extracted_signals"]["phase4_subsections"] = subsections

    # 信号 3：总览表/执行表中提到的小节名
    overview_mentions = []
    # 查找 Phase 4 总览表（包含 L1/L2/L3 行的表格）
    for m in re.finditer(
        r'\|\s*\*?\*?L[123].*?\|\s*(.+?)\s*\|',
        phase4_match.group(1) if phase4_match else skill_content,
        re.IGNORECASE
    ):
        overview_mentions.append(m.group(1).strip())
    context["extracted_signals"]["overview_mentions"] = overview_mentions

    # 信号 4：疑似单篇文章残余（具体文章标题模式）
    residual_candidates = []
    for m in re.finditer(
        r'「([^」]{2,40})」|[""]([^""]{5,40})["\"]',
        skill_content
    ):
        text = m.group(1) or m.group(2)
        # 跳过明显是技术术语的
        if any(kw in text for kw in ["skill", "md", "yaml", "json", "Phase", "L1", "L2"]):
            continue
        residual_candidates.append(text)
    context["extracted_signals"]["residual_candidates"] = residual_candidates[:30]

    # 信号 5: SKILL.md 总行数（辅助判断文件膨胀）
    context["extracted_signals"]["skill_md_line_count"] = skill_content.count('\n') + 1

    return context


def _append_review_history(result: dict, dimension_results: list, ap_issues: list, prechecks: list, manual_dims: list) -> None:
    """追加审查记录到 review-history.jsonl（长期记忆，跨会话可消费）。

    记录维度：
    - 身份: skill/version/grade
    - 全貌: 逐维得分 + 分类得分 → 消费时定位系统性弱点
    - 问题: 反模式 ID 列表 + 预检严重度分布 + 关键发现摘要
    - 上下文: 平台/通道/SCK版本/日期
    """
    history_file = SCK_ROOT / "data" / "review-history.jsonl"
    try:
        warn_dims = [d for d in dimension_results if d.get("status") in ("warn", "fail")]
        fail_dims = [d for d in dimension_results if d.get("status") == "fail"]

        # 逐维得分
        dim_scores = {
            d["id"]: d.get("score", 0)
            for d in dimension_results if d.get("status") not in ("skipped", "error")
        }

        # 分类得分汇总
        category_scores = {}
        for d in dimension_results:
            if d.get("status") in ("skipped", "error"):
                continue
            cat = d.get("category", "其他")
            if cat not in category_scores:
                category_scores[cat] = {"score": 0, "max": 0}
            category_scores[cat]["score"] += d.get("score", 0)
            category_scores[cat]["max"] += d.get("max_score", 0)

        # 反模式 ID 列表
        ap_ids = [i.get("id", "") for i in ap_issues]

        # 预检严重度分布
        precheck_severity = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for p in prechecks:
            sev = p.get("severity", "LOW")
            precheck_severity[sev] = precheck_severity.get(sev, 0) + 1

        record = {
            "skill": result["skill"],
            "version": result["version"],
            "score": result["total_score"],
            "max_score": result["max_possible"],
            "percentage": result["percentage"],
            "grade": result["grade"],
            "date": time.strftime("%Y-%m-%d"),
            "reviewer": "quality-audit",
            "channel": result.get("channel", "full"),
            "platform": result.get("platform", "universal"),
            "sck_version": result.get("sck_version", "0.0.0"),
            "warn_count": len(warn_dims),
            "fail_count": len(fail_dims),
            "key_findings": [
                f"[{d['status']}] {d['name']}: {d.get('note', '')}"
                for d in warn_dims + fail_dims
            ],
            "ap_ids": ap_ids,
            "dimension_scores": dim_scores,
            "category_scores": category_scores,
            "precheck_severity": precheck_severity,
            "manual_pending_count": len(manual_dims),
        }

        history_file.parent.mkdir(parents=True, exist_ok=True)
        with open(history_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except (OSError, IOError):
        pass  # 静默失败：审查历史写入不影响审计主流程


# ── 报告格式化 ──────────────────────────────────────────────

def format_report(result: dict) -> str:
    """格式化审计报告为终端友好的文本"""
    lines = []
    plat = result.get("platform", "universal")
    
    lines.append(f"\n{'='*60}")
    lines.append(f"  Skill Quality Audit Report")
    lines.append(f"  Skill: {result['skill']}  v{result['version']}")
    lines.append(f"  Platform: {plat}  |  Channel: {result['channel']}")
    lines.append(f"  Score: {result['total_score']}/{result['total_weight']}  "
                 f"({result['percentage']}%)  Grade: {result['grade']} ({result['grade_meaning']})")
    lines.append(f"  SCK Coach: v{_get_sck_version()}")
    lines.append(f"{'='*60}\n")
    
    # Prechecks
    if result.get("prechecks"):
        lines.append("⚠️  Prechecks:")
        for p in result["prechecks"]:
            lines.append(f"  [{p['severity']}] {p['message']}")
        lines.append("")
    
    # Dimensions
    lines.append(f"{'Dimension':<30} {'Score':<8} {'Status':<10} Note")
    lines.append("-" * 80)
    for dim in result.get("dimensions", []):
        score_str = f"{dim.get('score', 0)}/{dim.get('max_score', 0)}"
        status = dim.get('status', '?')
        if status == 'skipped':
            status_icon = '⊘'
        elif status == 'pass':
            status_icon = '✅'
        elif status == 'manual':
            status_icon = '👤'
        elif status == 'warn':
            status_icon = '⚠️'
        elif status == 'fail':
            status_icon = '❌'
        else:
            status_icon = '?'
        
        note = dim.get('note', '')[:40]
        lines.append(f"  {dim['name']:<28} {score_str:<8} {status_icon} {status:<8} {note}")
    
    lines.append("-" * 80)
    
    # Warnings
    warns = [d for d in result.get("dimensions", []) if d.get("status") in ("warn", "fail")]
    if warns:
        lines.append(f"\n⚠️  {len(warns)} 维度需要关注")
    manual = result.get("manual_pending", [])
    if manual:
        lines.append(f"👤 {len(manual)} 维度待 AI 裁定: {', '.join(m['id'] for m in manual)}")
    
    lines.append("")
    return "\n".join(lines)


def compute_stats(skill_path: Path) -> dict:
    """计算 skill 的内部计数，供 self-audit 数字声称验证使用。
    
    返回 {dimensions, anti_patterns, scripts, references, adrs, reqs}
    无对应文件时值 = 0，不报错。
    """
    stats = {}
    
    # 维度数
    stats["dimensions"] = len(AUDIT_DIMENSIONS)
    
    # 反模式数
    ap_file = skill_path / "data" / "anti-patterns.yaml"
    if ap_file.exists():
        ap_content = ap_file.read_text(encoding="utf-8")
        stats["anti_patterns"] = len(re.findall(r'^\s+- id: AP-', ap_content, re.MULTILINE))
    else:
        stats["anti_patterns"] = 0
    
    # 脚本数
    scripts_dir = skill_path / "scripts"
    stats["scripts"] = len(list(scripts_dir.glob("*.py"))) if scripts_dir.exists() else 0
    
    # references 文档数
    refs_dir = skill_path / "references"
    stats["references"] = len(list(refs_dir.glob("*.md"))) if refs_dir.exists() else 0
    
    # ADR 数
    design_file = skill_path / "DESIGN.md"
    if design_file.exists():
        dc = design_file.read_text(encoding="utf-8")
        stats["adrs"] = len(re.findall(r'^### ADR-\d+', dc, re.MULTILINE))
        stats["reqs"] = len(re.findall(r'^### REQ-\d+', dc, re.MULTILINE))
    else:
        stats["adrs"] = 0
        stats["reqs"] = 0
    
    return stats


# ── CLI 入口 ────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python3 scripts/quality-audit.py <skill> [--channel lightweight|full] [--platform workbuddy|openclaw|hermes|universal] [--no-cache] [--json] [--llm-review]")
        sys.exit(1)
    
    skill_dir = sys.argv[1]
    
    # 解析参数
    # 自动检测通道：存在 SPEC.md 或 DESIGN.md → full，否则 lightweight
    channel = "lightweight"  # 默认轻量
    if (Path(skill_dir) / "SPEC.md").exists() or (Path(skill_dir) / "DESIGN.md").exists():
        channel = "full"
    no_cache = False
    use_json = False
    platform = None
    manual_scores = {}
    llm_review = None  # None = 未显式设置，按通道默认
    
    i = 2
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == "--channel" and i + 1 < len(sys.argv):
            channel = sys.argv[i + 1]
            i += 2
        elif arg == "--platform" and i + 1 < len(sys.argv):
            platform = sys.argv[i + 1]
            i += 2
        elif arg == "--no-cache":
            no_cache = True
            i += 1
        elif arg == "--json":
            use_json = True
            i += 1
        elif arg == "--llm-review":
            llm_review = True
            no_cache = True  # LLM review 上下文变化，必须跳过缓存
            i += 1
        elif arg == "--no-llm-review":
            llm_review = False
            i += 1
        elif arg == "--stats":
            # Print internal counts and exit
            print(json.dumps(compute_stats(Path(skill_dir)), ensure_ascii=False, indent=2))
            sys.exit(0)
        elif arg == "--score" and i + 2 < len(sys.argv):
            dim_id = sys.argv[i + 1]
            score = int(sys.argv[i + 2])
            manual_scores[dim_id] = score
            i += 3
        else:
            i += 1
    
    # 全通道默认开启 LLM 审查（可通过 --no-llm-review 关闭 / --llm-review 显式开启）
    if llm_review is None:
        llm_review = (channel == "full")
    if llm_review:
        no_cache = True  # LLM 审查需要最新上下文
    
    try:
        result = audit(skill_dir, channel, no_cache, manual_scores, platform, llm_review)
        
        if use_json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(format_report(result))
        
        # 退出码
        if result["percentage"] < 60:
            sys.exit(1)
    except Exception as e:
        print(f"❌ 审计失败: {e}", file=sys.stderr)
        sys.exit(2)
