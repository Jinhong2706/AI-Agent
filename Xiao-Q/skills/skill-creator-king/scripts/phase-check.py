#!/usr/bin/env python3
"""Phase 完整性检查 — 在 Phase 过渡前验证前一 Phase 的产出物是否完备。

用法:
  python3 scripts/phase-check.py <skill-dir> --from-phase <N> --to-phase <M> [--channel lightweight|full]
  python3 scripts/phase-check.py <skill-dir> --phase <N> [--channel lightweight|full]    # 检查 Phase N 进入条件

Phase 过渡定义 (full):
  0→1  Pre-flight → Discuss:  SKILL.md 存在, frontmatter 有效
  1→2  Discuss → Design:      DESIGN.md 至少有一个非占位 REQ（v3.14+ SPEC 已合并入 DESIGN）+ Token 实测 + 数据源显式声明
  2→3  Design → Build:         DESIGN.md 冻结 (非占位 REQ+ADR) + ADR 有降级路径
  3→4  Build → Verify:         产出物就位 (scripts/非空, SKILL.md body 非骨架)
  4→5  Verify → Evolve:        validate.py 通过, quality-audit 分数 >= 门槛

Phase 过渡定义 (lightweight):
  0→1  Pre-flight → Discuss:  (同 full)
  1→2  Discuss → Design:      SKILL.md body 非骨架（轻量设计直接在 SKILL.md 中完成）
  2→3  Design → Build:         SKILL.md body 有实质内容 + scripts/ 非空
  3→4  Build → Verify:         (同 full)
  4→5  Verify → Evolve:        validate.py --channel lightweight 通过, quality-audit 分数 >= 轻量门槛

v1.0.0: 初始版本 (SCK v3.12.4)
"""

import argparse
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent

# ── Phase 过渡定义 ─────────────────────────────────────
PHASE_CHECKS = {
    "0→1": {
        "label": "Pre-flight → Discuss",
        "checks": [
            ("SKILL.md 存在", lambda d: (d / "SKILL.md").exists()),
            ("frontmatter 模板字段有效", "_check_frontmatter_template"),
        ],
    },
    "1→2": {
        "label": "Discuss → Design",
        "checks": [
            ("SPEC.md 或 DESIGN.md 存在", lambda d: (d / "SPEC.md").exists() or (d / "DESIGN.md").exists()),
            ("至少 1 个非占位 REQ", "_check_spec_non_placeholder"),
            ("Token 预算已实测（非全默认值）", "_check_token_budget_measured"),
            ("数据源已显式声明（非模板占位）", "_check_data_source_declared"),
        ],
    },
    "2→3": {
        "label": "Design → Build",
        "checks": [
            ("DESIGN.md 存在", lambda d: (d / "DESIGN.md").exists()),
            ("DESIGN.md 至少 1 个非占位 ADR", "_check_design_non_placeholder"),
            ("REQ 冻结（非占位）", "_check_spec_non_placeholder"),
        ],
    },
    "3→4": {
        "label": "Build → Verify",
        "checks": [
            ("scripts/ 有 .py 文件", lambda d: any((d / "scripts").glob("*.py")) if (d / "scripts").exists() else False),
            ("SKILL.md body 非骨架", "_check_skill_body_non_skeleton"),
        ],
    },
    "4→5": {
        "label": "Verify → Evolve",
        "checks": [
            ("validate.py 通过", "_check_validate_pass"),
            ("quality-audit 分数 >= 60%", "_check_quality_audit_min"),
        ],
    },
}

# 轻量通道 Phase 过渡定义（跳 SPEC/DESIGN/ADR 相关内容）
LIGHTWEIGHT_PHASE_CHECKS = {
    "0→1": {
        "label": "Pre-flight → Discuss (轻量)",
        "checks": [
            ("SKILL.md 存在", lambda d: (d / "SKILL.md").exists()),
            ("frontmatter 模板字段有效", "_check_frontmatter_template"),
        ],
    },
    "1→2": {
        "label": "Discuss → Design (轻量)",
        "checks": [
            ("SKILL.md body 非骨架", "_check_skill_body_non_skeleton"),
        ],
    },
    "2→3": {
        "label": "Design → Build (轻量)",
        "checks": [
            ("SKILL.md body 有实质内容", "_check_skill_body_meaningful"),
            ("scripts/ 有 .py 文件", lambda d: any((d / "scripts").glob("*.py")) if (d / "scripts").exists() else False),
        ],
    },
    "3→4": {
        "label": "Build → Verify (轻量)",
        "checks": [
            ("scripts/ 有 .py 文件", lambda d: any((d / "scripts").glob("*.py")) if (d / "scripts").exists() else False),
            ("SKILL.md body 非骨架", "_check_skill_body_non_skeleton"),
        ],
    },
    "4→5": {
        "label": "Verify → Evolve (轻量)",
        "checks": [
            ("validate.py --channel lightweight 通过", "_check_validate_lightweight_pass"),
            ("quality-audit 轻量分数 >= 60%", "_check_quality_audit_lightweight_min"),
        ],
    },
}


# ── 检查实现 ─────────────────────────────────────────

def _check_frontmatter_template(skill_dir: Path) -> bool:
    """检查 SKILL.md frontmatter 中的 template 字段是否有效"""
    try:
        content = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    except FileNotFoundError:
        return False
    import re
    m = re.search(r"template:\s*(\S+)", content)
    return m is not None and m.group(1) in ("basic", "multi-scene", "data-driven")


def _check_spec_non_placeholder(skill_dir: Path) -> bool:
    """SPEC.md（或合并架构下的 DESIGN.md）中至少有一个 REQ 不是「待定义」"""
    # v3.14+ 合并架构：SPEC 融入 DESIGN，优先读 SPEC，回退 DESIGN
    spec_file = skill_dir / "SPEC.md"
    design_file = skill_dir / "DESIGN.md"
    target = spec_file if spec_file.exists() else design_file
    try:
        content = target.read_text(encoding="utf-8")
    except FileNotFoundError:
        return False
    import re
    reqs = re.findall(r"### REQ-\d+:.*?\n(.*?)(?=\n###|\Z)", content, re.DOTALL)
    for req_body in reqs:
        if "待定义" not in req_body and req_body.strip():
            return True
    return False


def _check_design_non_placeholder(skill_dir: Path) -> bool:
    """DESIGN.md 中至少有一个 ADR 不是「待定义」"""
    try:
        content = (skill_dir / "DESIGN.md").read_text(encoding="utf-8")
    except FileNotFoundError:
        return False
    import re
    adrs = re.findall(r"### ADR-\d+:.*?\n(.*?)(?=\n###|\Z)", content, re.DOTALL)
    for adr_body in adrs:
        if "待定义" not in adr_body and adr_body.strip():
            return True
    return False


def _check_token_budget_measured(skill_dir: Path) -> bool:
    """Token 预算不能全是默认值（纯占位 = 未实测）"""
    try:
        content = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    except FileNotFoundError:
        return False
    import re
    # 检测 frontmatter token_budget 区段
    fm_match = re.search(r"token_budget:\s*\n((?:\s{2,}\w+:.*\n?)*)", content)
    if not fm_match:
        return True  # 没有 token_budget 声明 → 不算阻止，由 validate 报
    budget_block = fm_match.group(1)
    # 纯默认值模式：10000 是模板默认 hard_cap
    defaults = {"L0_trigger: 200", "L1_core: 1100", "L2_deep: 5000", "hard_cap: 10000"}
    declared = set()
    for line in budget_block.strip().split("\n"):
        line = line.strip()
        if line:
            declared.add(line)
    # 如果声明的值全是默认值 → 未实测
    all_default = len(declared) > 0 and all(d in defaults for d in declared)
    return not all_default


def _check_data_source_declared(skill_dir: Path) -> bool:
    """数据源必须显式声明（不能停留在模板占位状态）"""
    try:
        body = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    except FileNotFoundError:
        return False
    # 模板占位特征：同时出现未勾选的 checkbox + 「必须声明」提示
    has_placeholder_checklist = (
        "- [ ]" in body and ("数据依赖" in body or "数据源" in body)
        and ("🔒 必须声明" in body or "⚠️ 不声明数据依赖" in body)
    )
    # 如果有占位提示语还在 → 说明没改
    return not has_placeholder_checklist


def _check_adr_fallback(skill_dir: Path) -> bool:
    """至少一个 ADR 声明了降级路径（非占位符）"""
    design_file = skill_dir / "DESIGN.md"
    if not design_file.exists():
        return False
    try:
        content = design_file.read_text(encoding="utf-8")
    except FileNotFoundError:
        return False
    import re
    # 拆出所有 ADR 小节
    adrs = re.split(r"### ADR-\d+:", content)
    for adr in adrs:
        has_keyword = "降级" in adr or "fallback" in adr.lower() or "回退" in adr
        if not has_keyword:
            continue
        # 确认非占位符：去除 [___] 占位后检查是否有实质内容（≥ 30 字符）
        clean = re.sub(r'\[___\]', '', adr)
        clean = re.sub(r'待定义', '', clean)
        if len(clean.strip()) >= 30:
            return True
    return False


def _check_skill_body_non_skeleton(skill_dir: Path) -> bool:
    """SKILL.md body 不只是模板骨架（有实质内容）"""
    try:
        content = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    except FileNotFoundError:
        return False
    # 找 frontmatter 结束后的 body
    body = content.split("---\n", 2)
    if len(body) < 3:
        return False
    body = body[2].strip()
    # 骨架特征：只有 #{name} + {desc} + 空section
    lines = [l for l in body.split("\n") if l.strip() and not l.strip().startswith("#")]
    meaningful = [l for l in lines if not l.startswith("##") and len(l.strip()) > 5]
    return len(meaningful) >= 3


def _check_validate_pass(skill_dir: Path) -> bool:
    """运行 validate.py 检查是否通过"""
    validate_script = SCRIPT_DIR / "validate.py"
    if not validate_script.exists():
        return False  # 无法运行
    try:
        result = subprocess.run(
            [sys.executable, str(validate_script), str(skill_dir)],
            capture_output=True, text=True, timeout=30,
            cwd=str(SCRIPT_DIR.parent)
        )
        return result.returncode == 0
    except Exception:
        return False


def _check_skill_body_meaningful(skill_dir: Path) -> bool:
    """SKILL.md body 有实质内容（比「非骨架」更严格——要求至少 3 条有意义的行）"""
    try:
        content = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    except FileNotFoundError:
        return False
    # 找 frontmatter 结束后的 body
    body = content.split("---\n", 2)
    if len(body) < 3:
        return False
    body = body[2].strip()
    # 过滤空行和标题行，找有实质内容（>10 字符）的行
    lines = [l for l in body.split("\n") if l.strip() and not l.strip().startswith("#")]
    meaningful = [l for l in lines if len(l.strip()) > 10]
    return len(meaningful) >= 3


def _check_validate_lightweight_pass(skill_dir: Path) -> bool:
    """运行 validate.py --channel lightweight 检查是否通过"""
    validate_script = SCRIPT_DIR / "validate.py"
    if not validate_script.exists():
        return False
    try:
        result = subprocess.run(
            [sys.executable, str(validate_script), str(skill_dir), "--channel", "lightweight"],
            capture_output=True, text=True, timeout=30,
            cwd=str(SCRIPT_DIR.parent)
        )
        return result.returncode == 0
    except Exception:
        return False


def _check_quality_audit_lightweight_min(skill_dir: Path) -> bool:
    """运行 quality-audit.py --channel lightweight 检查分数 >= 60%"""
    audit_script = SCRIPT_DIR / "quality-audit.py"
    if not audit_script.exists():
        return False
    try:
        result = subprocess.run(
            [sys.executable, str(audit_script), str(skill_dir), "--json", "--channel", "lightweight"],
            capture_output=True, text=True, timeout=30,
            cwd=str(SCRIPT_DIR.parent)
        )
        import json
        data = json.loads(result.stdout)
        # 使用 percentage 字段（跨平台/通道一致），避免硬编码 max_score
        percentage = data.get("percentage", 0)
        return percentage >= 60
    except Exception:
        return False


def _check_quality_audit_min(skill_dir: Path) -> bool:
    """运行 quality-audit.py --channel full 检查分数 >= 60%"""
    audit_script = SCRIPT_DIR / "quality-audit.py"
    if not audit_script.exists():
        return False
    try:
        result = subprocess.run(
            [sys.executable, str(audit_script), str(skill_dir), "--json", "--channel", "full"],
            capture_output=True, text=True, timeout=30,
            cwd=str(SCRIPT_DIR.parent)
        )
        import json
        data = json.loads(result.stdout)
        percentage = data.get("percentage", 0)
        return percentage >= 60
    except Exception:
        return False


def _collect_design_review_context(skill_dir: Path) -> dict:
    """收集 DESIGN.md 上下文 + 4 个引导问题，供 LLM 进行建前设计审查。
    
    Returns: {"design_md": str, "skill_md_excerpt": str, "questions": [str]} 或 {}（无 DESIGN.md）
    """
    design_file = skill_dir / "DESIGN.md"
    skill_file = skill_dir / "SKILL.md"
    if not design_file.exists():
        return {}
    design_md = design_file.read_text(encoding="utf-8")
    skill_body = ""
    if skill_file.exists():
        raw = skill_file.read_text(encoding="utf-8")
        parts = raw.split("---", 2)
        skill_body = parts[2].strip() if len(parts) >= 3 else ""
    questions = [
        "设计闭合性：REQ 之间是否无重叠、无遗漏？是否存在隐含假设（如默认某工具可用）？",
        "Token 预算合理性：L0/L1/L2 的值是否有实测依据？hard_cap 是否与 L2_deep 一致？",
        "数据依赖完整性：声明的数据源是否可获取？是否有未声明的外部依赖？",
        "降级路径：每个依赖外部资源的功能，是否定义了该资源不可用时的行为？",
    ]
    return {"design_md": design_md[:4000], "skill_md_excerpt": skill_body[:1000], "questions": questions}


# ── 主逻辑 ───────────────────────────────────────────

def run_phase_check(skill_dir: str, from_phase: int, to_phase: int, channel: str = "full") -> dict:
    """运行 Phase 过渡检查。

    参数:
      skill_dir: skill 根目录路径
      from_phase: 起始 Phase
      to_phase: 目标 Phase
      channel: 通道（lightweight | full），轻量通道使用精简的检查清单

    Returns:
        {"passed": bool, "checks": [{"name": str, "passed": bool, "detail": str}], "label": str}
    """
    key = f"{from_phase}→{to_phase}"
    checks_dict = LIGHTWEIGHT_PHASE_CHECKS if channel == "lightweight" else PHASE_CHECKS
    transition = checks_dict.get(key)
    if transition is None:
        # 多步过渡：拆解为相邻步逐一检查
        if from_phase < to_phase and to_phase - from_phase > 1:
            all_checks = []
            all_labels = []
            all_passed = True
            for p in range(from_phase, to_phase):
                step_key = f"{p}→{p+1}"
                step = checks_dict.get(step_key)
                if step is None:
                    return {"passed": False, "checks": [], "label": f"未知步: {step_key}",
                            "error": f"过渡 {key} 中的 {step_key} 未定义"}
                d = Path(skill_dir).expanduser().resolve()
                if not d.exists():
                    return {"passed": False, "checks": [], "label": step["label"],
                            "error": f"Skill 目录不存在: {d}"}
                step_results = []
                for name, check_fn in step["checks"]:
                    if isinstance(check_fn, str):
                        fn = globals().get(check_fn)
                        if fn is None:
                            step_results.append({"name": name, "passed": False, "detail": f"内部错误: {check_fn} 未定义"})
                            all_passed = False
                            continue
                        ok = fn(d)
                    else:
                        ok = check_fn(d)
                    step_results.append({"name": name, "passed": ok, "detail": "✅" if ok else "❌ 未满足"})
                    if not ok:
                        all_passed = False
                all_checks.append({"step": step_key, "label": step["label"], "checks": step_results, "passed": all(r["passed"] for r in step_results)})
                all_labels.append(step["label"])
                if not all_checks[-1]["passed"]:
                    break  # 前一步失败则停止
            return {"passed": all_passed, "checks": all_checks, "label": f"多步: {' → '.join(all_labels)}"}
        return {"passed": False, "checks": [], "label": f"未知过渡: {key}",
                "error": f"支持的过渡: {', '.join(checks_dict.keys())}"}

    d = Path(skill_dir).expanduser().resolve()
    if not d.exists():
        return {"passed": False, "checks": [], "label": transition["label"],
                "error": f"Skill 目录不存在: {d}"}

    results = []
    all_passed = True
    for name, check_fn in transition["checks"]:
        if isinstance(check_fn, str):
            fn = globals().get(check_fn)
            if fn is None:
                results.append({"name": name, "passed": False, "detail": f"内部错误: 检查函数 {check_fn} 未定义"})
                all_passed = False
                continue
            ok = fn(d)
        else:
            ok = check_fn(d)
        detail = "✅" if ok else "❌ 未满足"
        results.append({"name": name, "passed": ok, "detail": detail})
        if not ok:
            all_passed = False

    result = {"passed": all_passed, "checks": results, "label": transition["label"]}
    # 2→3 全通道：注入设计审查上下文供 LLM 建前审查
    if key == "2→3" and channel == "full":
        ctx = _collect_design_review_context(d)
        if ctx:
            result["design_review"] = ctx
    return result


def main():
    parser = argparse.ArgumentParser(description="Phase 完整性检查")
    parser.add_argument("skill_dir", nargs="?", default=".", help="Skill 目录路径 (--list 时可省略)")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--phase", type=int, choices=range(0, 6),
                       help="检查进入此 Phase 的条件")
    group.add_argument("--from-phase", type=int, choices=range(0, 6),
                       help="起始 Phase", dest="from_phase")
    group.add_argument("--list", action="store_true", help="列出所有过渡")
    parser.add_argument("--to-phase", type=int, choices=range(1, 6),
                       help="目标 Phase", dest="to_phase")
    parser.add_argument("--json", action="store_true", help="JSON 输出")
    parser.add_argument("--channel", default="full", choices=["lightweight", "full"],
                        help="通道（lightweight 使用精简检查清单）")

    args = parser.parse_args()

    if args.list:
        print("Phase 过渡检查清单 (full):")
        for key, t in PHASE_CHECKS.items():
            print(f"  {key}  {t['label']}")
            for c in t["checks"]:
                print(f"    - {c[0]}")
        print("\nPhase 过渡检查清单 (lightweight):")
        for key, t in LIGHTWEIGHT_PHASE_CHECKS.items():
            print(f"  {key}  {t['label']}")
            for c in t["checks"]:
                print(f"    - {c[0]}")
        return

    # 非 --list 模式必须指定过渡
    if args.phase is not None:
        if args.phase == 0:
            print("✅ Phase 0 无前置条件（出发前确认）", file=sys.stderr)
            sys.exit(0)
        from_phase = args.phase - 1
        to_phase = args.phase
    elif args.from_phase is not None:
        from_phase = args.from_phase
        to_phase = args.to_phase
        if to_phase is None:
            parser.error("--from-phase 需要同时指定 --to-phase")
    else:
        parser.error("需要指定 --phase / --from-phase / --list 之一")

    result = run_phase_check(args.skill_dir, from_phase, to_phase, channel=args.channel)

    if args.json:
        import json
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"🔍 Phase 过渡检查: {result['label']}  (通道: {args.channel})")
        if "error" in result:
            print(f"   ❌ {result['error']}")
            sys.exit(1)
        for c in result["checks"]:
            # 多步过渡：每个 step 是嵌套结构 {label, checks: [{name, passed}], passed}
            if "checks" in c:
                step_icon = "✅" if c["passed"] else "❌"
                print(f"   {step_icon} {c['label']}")
                for sub in c["checks"]:
                    sub_icon = "✅" if sub["passed"] else "❌"
                    print(f"      {sub_icon} {sub['name']}")
            else:
                # 单步过渡：直接 {name, passed}
                icon = "✅" if c["passed"] else "❌"
                print(f"   {icon} {c['name']}")
        print(f"\n{'✅ 全部通过' if result['passed'] else '❌ 有未满足项'}")

    sys.exit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
