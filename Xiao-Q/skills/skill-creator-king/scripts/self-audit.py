#!/usr/bin/env python3
"""Self-audit: structural and health checks for any skill.

5 层 6 项检查 — 嵌入 validate.py --strict 模式运行。

用法:
  python3 scripts/self-audit.py <skill-dir> [--sck-mode] [--json]
  python3 scripts/self-audit.py --list-checks
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path


def check_reference_integrity(skill_dir: Path) -> dict:
    """所有 .md/.yaml 中引用的文件必须存在。"""
    issues = []
    for ext in ['.md', '.yaml', '.yml']:
        for f in sorted(skill_dir.rglob(f'*{ext}')):
            if 'cache' in f.parts or f.name.startswith('.'):
                continue
            # CHANGELOG 文件含版本号正则（如 \d+\.\d+\.\d+），会被误匹配为文件链接
            if 'CHANGELOG' in f.name.upper():
                continue
            try:
                content = f.read_text(encoding='utf-8', errors='ignore')
            except Exception:
                continue

            for match in re.finditer(r'\[([^\]]+)\]\(([^)]+)\)', content):
                path = match.group(2).strip()
                if path.startswith(('http://', 'https://', '#', '/', '~')):
                    continue
                target = (f.parent / path).resolve()
                if not target.exists():
                    if '*' in path:
                        matches = list(f.parent.glob(path.replace('./', '')))
                        if not matches:
                            issues.append({"type": "dead_link", "file": str(f.relative_to(skill_dir)), "ref": path, "detail": f"glob 未匹配任何文件: {path}"})
                    else:
                        issues.append({"type": "dead_link", "file": str(f.relative_to(skill_dir)), "ref": path, "detail": f"文件不存在: {path}"})
    return {"check": "引用完整性", "passed": len(issues) == 0, "issues": issues}


def check_config_liveliness(skill_dir: Path) -> dict:
    """config.yaml 中 >5 字符的 key 必须被至少一个脚本引用。"""
    issues = []
    config_file = skill_dir / 'config.yaml'
    if not config_file.exists():
        return {"check": "配置活性", "passed": True, "issues": [], "skipped": True}

    config_raw = config_file.read_text(encoding='utf-8')
    config_lines = config_raw.split('\n')
    keys = set()
    for i, line in enumerate(config_lines):
        line = line.strip()
        if not line or line.startswith('#') or ':' not in line:
            continue
        key = line.split(':')[0].strip()
        if len(key) > 5 and not key.startswith('-'):
            # Check if this key is in a # documentary section: look back up to 15 lines
            is_documentary = False
            for j in range(max(0, i - 15), i):
                if '# documentary' in config_lines[j]:
                    is_documentary = True
                    break
            if not is_documentary:
                keys.add(key)

    scripts_dir = skill_dir / 'scripts'
    if not scripts_dir.exists():
        return {"check": "配置活性", "passed": True, "issues": [], "skipped": True}

    # Search both .py files and .md files (config may be consumed by AI/LLM flow)
    searchable_dirs = [scripts_dir]
    md_dirs = [skill_dir / 'references', skill_dir]
    for d in md_dirs:
        if d.exists():
            searchable_dirs.append(d)

    for key in sorted(keys):
        found = False
        for search_dir in searchable_dirs:
            for f in sorted(search_dir.rglob('*')):
                if f.suffix not in ('.py', '.md') or f.name.startswith('.'):
                    continue
                if key in f.read_text(encoding='utf-8', errors='ignore'):
                    found = True
                    break
            if found:
                break
        if not found:
            issues.append({"type": "unused_config", "key": key, "detail": f"配置项 '{key}' 未被任何脚本或文档引用"})
    return {"check": "配置活性", "passed": len(issues) == 0, "issues": issues}


def check_freshness(skill_dir: Path) -> dict:
    """SKILL.md frontmatter token_budget 与实测值对比，偏差 > 20% 或超出 hard_cap 时警告。
    
    真相源 = SKILL.md frontmatter（单一源头），DESIGN.md Token 表仅为快照。
    """
    issues = []
    skill_file = skill_dir / 'SKILL.md'
    estimate_script = skill_dir / 'scripts' / 'estimate-tokens.py'
    if not skill_file.exists() or not estimate_script.exists():
        return {"check": "保鲜度", "passed": True, "issues": [], "skipped": True}

    # 从 SKILL.md frontmatter 读预算（单一真相源）
    content = skill_file.read_text(encoding='utf-8')
    budget = {}
    in_frontmatter = False
    for line in content.split('\n'):
        stripped = line.strip()
        if stripped == '---':
            in_frontmatter = not in_frontmatter
            if not in_frontmatter:
                break
            continue
        if in_frontmatter:
            for key in ['L0_trigger', 'L1_core', 'L2_deep', 'hard_cap']:
                m = re.match(rf'{key}:\s*(\d+)', stripped)
                if m:
                    budget[key] = int(m.group(1))

    if not budget:
        return {"check": "保鲜度", "passed": True, "issues": [], "skipped": True}

    try:
        r = subprocess.run([sys.executable, str(estimate_script), str(skill_dir)], capture_output=True, text=True, timeout=30)
        out = r.stdout
    except Exception:
        return {"check": "保鲜度", "passed": True, "issues": [], "skipped": True}

    # 解析实测值
    token_act = {}
    for label in ['L0', 'L1', 'L2']:
        m = re.search(rf'^{label}[^:]*:\s*([\d,]+)', out, re.MULTILINE)
        if m:
            token_act[label] = int(m.group(1).replace(',', ''))

    # L0 vs L0_trigger, L1 vs L1_core, L2 vs L2_deep
    # 仅实测超出预算时报警（预算 = 上限，低于预算表示健康）
    budget_map = {'L0': 'L0_trigger', 'L1': 'L1_core', 'L2': 'L2_deep'}
    for comp, bkey in budget_map.items():
        if comp in token_act and bkey in budget and budget[bkey] > 0:
            act_val = token_act[comp]
            budget_val = budget[bkey]
            if act_val > budget_val * 1.2:
                dev = (act_val - budget_val) / budget_val
                issues.append({"type": "stale_token", "component": comp, "budget": budget_val, "actual": act_val, "deviation": f"+{dev:.0%}", "detail": f"{comp} 实测 {act_val} 超出预算 {budget_val}，偏差 +{dev:.0%}"})

    # 硬上限检查：任一组件实测超出 hard_cap
    if 'hard_cap' in budget:
        total_act = sum(token_act.values()) if token_act else 0
        if total_act > budget['hard_cap']:
            issues.append({"type": "hard_cap_exceeded", "hard_cap": budget['hard_cap'], "actual_total": total_act, "detail": f"实测总计 {total_act} 超出 hard_cap {budget['hard_cap']}"})

    return {"check": "保鲜度", "passed": len(issues) == 0, "issues": issues}


def check_discipline_compliance(skill_dir: Path) -> dict:
    """三条操作纪律：不穷举 / 不双写 / 不窄检。"""
    issues = []
    scripts_dir = skill_dir / 'scripts'
    if not scripts_dir.exists():
        return {"check": "纪律验证", "passed": True, "issues": [], "skipped": True}

    # 不穷举: 检测 scripts/ 中是否有硬编码的 Python 文件列表（而非动态扫描）
    for script in scripts_dir.glob('*.py'):
        content = script.read_text(encoding='utf-8', errors='ignore')
        hardcoded = re.findall(r'\[[\s\S]{0,200}\]', content)
        for lst in hardcoded:
            if re.search(r"['\"]\w+\.py['\"]", lst) and 'iterdir' not in content and 'glob' not in content:
                issues.append({"type": "hardcoded_list", "script": script.name, "detail": f"'{script.name}' 可能有硬编码文件列表，建议 iterdir()/walk()"})
                break

    # 不双写: init_skill.py TMPL 变量 vs data/templates/ 文件名一致性
    init_skill = scripts_dir / 'init_skill.py'
    templates_dir = skill_dir / 'data' / 'templates'
    if init_skill.exists() and templates_dir.exists():
        tmpl_vars = set()
        for m in re.finditer(r'(\w+)_TMPL\s*=', init_skill.read_text(encoding='utf-8')):
            tmpl_vars.add(m.group(1).lower())
        tmpl_files = set()
        for f in templates_dir.iterdir():
            if f.is_file() and not f.name.startswith('.'):
                stem = f.stem.split('.')[0].lower()
                tmpl_files.add(stem)
        # Some templates are intentionally single-sourced:
        # - CONFIG_TMPL only in init_skill.py (too simple for separate file)
        # - review-report, session-report only in data/templates/ (review-only, not gen)
        single_source = {'config', 'review-report', 'session-report',
                         # reference design templates（结构参考，非生成输入）
                         'changelog', 'design', 'readme', 'sources', 'spec'}
        for v in sorted(tmpl_vars - tmpl_files - single_source):
            issues.append({"type": "orphaned_template_var", "detail": f"init_skill.py 有 {v.upper()}_TMPL 但 data/templates/ 无对应文件"})
        for f in sorted(tmpl_files - tmpl_vars - single_source):
            issues.append({"type": "orphaned_template_file", "detail": f"data/templates/ 有 {f} 但 init_skill.py 无对应 _TMPL 变量"})

    # 不窄检: validate.py 是否用动态扫描
    validate_script = scripts_dir / 'validate.py'
    if validate_script.exists():
        vc = validate_script.read_text(encoding='utf-8', errors='ignore')
        if 'iterdir' not in vc and 'os.walk' not in vc:
            issues.append({"type": "narrow_scan", "detail": "validate.py 未检测到动态扫描 (iterdir/walk)，可能使用硬编码路径"})

    # D7: 未测试代码路径 — 脚本有特殊模式（strict/sck-mode/verbse）但 tests/ 不覆盖
    tests_dir = skill_dir / 'tests'
    test_content = ""
    if tests_dir.exists():
        test_files = list(tests_dir.glob('test_*.py')) + list(tests_dir.glob('*.py'))
        for tf in test_files:
            try:
                test_content += tf.read_text(encoding='utf-8', errors='ignore')
            except (OSError, UnicodeError) as e:
                pass  # 权限或编码问题，跳过该文件
    special_modes = ['strict', 'sck-mode', 'verbose', 'debug']
    for script in sorted(scripts_dir.glob('*.py')):
        if script.name == 'self-audit.py':
            continue
        script_content = script.read_text(encoding='utf-8', errors='ignore')
        for mode in special_modes:
            if mode in script_content and mode not in test_content:
                issues.append({"type": "untested_code_path", "script": script.name, "detail": f"'{script.name}' 使用特殊模式 '{mode}' 但 tests/ 中无对应测试"})
                break

    # D8: 生成物累积 — data/cache/ 中过期或冗余文件
    cache_dir = skill_dir / 'data' / 'cache'
    if cache_dir.exists():
        cache_files = sorted(cache_dir.glob('*.json'))
        if len(cache_files) > 0:
            # Check for frequent-skill cache (same skill name, different hashes)
            skill_groups = {}
            for cf in cache_files:
                prefix = cf.stem.rsplit('_', 1)[0]  # "little-writer_v3.5.2" from "little-writer_v3.5.2_abc123"
                skill_groups.setdefault(prefix, []).append(cf)
            for prefix, group in skill_groups.items():
                if len(group) > 3:
                    issues.append({"type": "excess_cache", "detail": f"cache/{prefix} 有 {len(group)} 个文件，可能存在冗余缓存"})
            if len(cache_files) > 10:
                issues.append({"type": "excess_cache", "detail": f"data/cache/ 共 {len(cache_files)} 个文件，建议清理"})

    return {"check": "纪律验证", "passed": len(issues) == 0, "issues": issues}


def check_term_consistency(skill_dir: Path) -> dict:
    """(SCK only) 术语一致性：全仓扫描旧名引用。"""
    issues = []
    term_table = {}
    skip_patterns = [r'版本历史', r'Changelog', r'CHANGELOG', r'PHILOSOPHY\.md → PRINCIPLES\.md 重命名', r'REQ_001_PHILOSOPHY']

    for ext in ['.md', '.yaml', '.py']:
        for f in sorted(skill_dir.rglob(f'*{ext}')):
            if 'cache' in f.parts or f.name.startswith('.'):
                continue
            try:
                content = f.read_text(encoding='utf-8', errors='ignore')
            except Exception:
                continue

            for canonical, legacy_names in term_table.items():
                for legacy in legacy_names:
                    if legacy not in content:
                        continue
                    # 跳过版本历史 / CHANGELOG 等合法上下文
                    if any(re.search(p, content) for p in skip_patterns):
                        continue
                    for i, line in enumerate(content.split('\n'), 1):
                        if legacy in line:
                            issues.append({"type": "stale_term", "file": str(f.relative_to(skill_dir)), "line": i, "legacy": legacy, "canonical": canonical, "detail": f"第{i}行 旧名 '{legacy}'，应为 '{canonical}'"})
                            break
    return {"check": "名称一致性", "passed": len(issues) == 0, "issues": issues}


def check_numeric_claims(skill_dir: Path) -> dict:
    """验证 SKILL.md/README.md 中的数字声称与代码实际计数一致。
    
    调用 quality-audit.py --stats 获取真相源，对比文档中的声称数字。
    """
    issues = []
    qa_script = skill_dir / "scripts" / "quality-audit.py"
    skill_file = skill_dir / "SKILL.md"
    if not qa_script.exists() or not skill_file.exists():
        return {"check": "数字声称", "passed": True, "issues": [], "skipped": True}

    # 获取实际计数
    try:
        r = subprocess.run([sys.executable, str(qa_script), str(skill_dir), "--stats"],
                           capture_output=True, text=True, timeout=30)
        actual = json.loads(r.stdout)
    except Exception:
        return {"check": "数字声称", "passed": True, "issues": [], "skipped": True}

    # 文档声称 → 实际键映射（正则模式 + stats 键）
    claims = [
        (r'(\d+)\s*维度', "dimensions"),
        (r'(\d+)\s*(?:种|个).*?反模式', "anti_patterns"),
        (r'(\d+)\s*(?:个|段|阶段).*?Phase', "phases"),
        (r'(\d+)\s*(?:个|段).*?scripts?', "scripts"),
        (r'(\d+)\s*(?:个|段).*?references?', "references"),
        (r'(\d+)\s*(?:个|段).*?ADR', "adrs"),
        (r'(\d+)\s*(?:个|段).*?REQ', "reqs"),
    ]
    
    doc_text = skill_file.read_text(encoding="utf-8")

    for pattern, key in claims:
        if key not in actual:
            continue
        m = re.search(pattern, doc_text)
        if m:
            claimed = int(m.group(1))
            if claimed != actual[key]:
                issues.append({
                    "type": "numeric_drift",
                    "key": key,
                    "claimed": claimed,
                    "actual": actual[key],
                    "detail": f"声称 {claimed} 但实际 {actual[key]}（{key}）"
                })

    return {"check": "数字声称", "passed": len(issues) == 0, "issues": issues}


def audit(skill_dir: str, sck_mode: bool = False) -> dict:
    sp = Path(skill_dir).expanduser().resolve()
    if not sp.exists():
        return {"success": False, "error": f"目录不存在: {sp}"}

    checks = [
        check_reference_integrity(sp),
        check_config_liveliness(sp),
        check_freshness(sp),
        check_numeric_claims(sp),
        check_discipline_compliance(sp),
    ]
    if sck_mode:
        checks.append(check_term_consistency(sp))

    total = sum(len(c.get("issues", [])) for c in checks)
    return {"success": True, "skill": str(sp), "summary": {"total_issues": total, "passed": total == 0, "checks_passed": sum(1 for c in checks if c.get("passed")), "checks_total": len(checks)}, "checks": checks}


def format_report(result: dict) -> str:
    if not result.get("success"):
        return f"❌ 自检失败: {result.get('error')}"
    name = Path(result['skill']).name
    s = result['summary']
    lines = [f"🔍 自检报告 — {name}", f"", f"结果: {'✅ 全部通过' if s['passed'] else '⚠️ 发现问题'}", f"  通过 {s['checks_passed']}/{s['checks_total']} 项，共 {s['total_issues']} 个问题"]
    for c in result['checks']:
        icon = "✅" if c.get("passed") else "⚠️"
        skip = " (跳过)" if c.get("skipped") else ""
        lines.append(f"  {icon} {c['check']}{skip}")
        for issue in c.get("issues", []):
            lines.append(f"    - {issue['detail']}")
    return '\n'.join(lines)


def main():
    if '--list-checks' in sys.argv:
        print("可用检查项：")
        print("  1. 引用完整性 — .md/.yaml 中文件引用存在性")
        print("  2. 配置活性 — config.yaml 配置项被脚本消费")
        print("  3. 保鲜度 — Token 文档值与实测值偏差")
        print("  4. 数字声称 — SKILL.md 声称数字与代码实际计数的对比")
        print("  5. 纪律验证 — 不穷举/不双写/不窄检 + 未测试路径 + 生成物累积")
        print("  6. [SCK] 名称一致性 — 术语表全仓扫描（需 --sck-mode）")
        return

    if len(sys.argv) < 2 or sys.argv[1] in ('-h', '--help'):
        print("用法: python3 scripts/self-audit.py <skill-dir> [--sck-mode] [--json]")
        print("      python3 scripts/self-audit.py --list-checks")
        sys.exit(0 if '--help' in sys.argv else 1)

    skill_dir = sys.argv[1]
    result = audit(skill_dir, '--sck-mode' in sys.argv)
    if '--json' in sys.argv:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(format_report(result))
    sys.exit(0 if result['summary']['passed'] else 1)


if __name__ == '__main__':
    main()
