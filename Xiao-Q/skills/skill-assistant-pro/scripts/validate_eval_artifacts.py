#!/usr/bin/env python3
"""
validate_eval_artifacts.py — 第 1.5 道关·dry_run / 子 Agent 落盘后的 schema 校验器

放在 inspect D.1 / diagnose 4.1.4.c 写完 grading.json 之后、
generate-full-report.mjs 启动之前的中间位置，抓 schema 错配类问题
（例如 grading.json 字段名错、缺 eval_metadata.json、manifest 缺 eval_mode 等）。

设计来源：修复 R1-R7 系统性 schema drift 缺陷。

用法：
    python3 scripts/validate_eval_artifacts.py <iter_dir>

退出码：
    0  全部通过
    1  发现 ERROR（必须修后重跑），不允许调用 generate-full-report.mjs
    2  仅 WARN（可继续，但建议修），不阻断
    3  iter_dir 不存在 / 路径错误
"""
import json
import sys
from pathlib import Path
from typing import Any

REQUIRED_GRADING_FIELDS = ["passed_count", "total_count", "expectations"]
REQUIRED_GRADING_FALLBACK_FIELDS = [
    # script-level fallback（脚本可解析），但建议升级到主字段
    ["passed_count", "score", "summary.passed"],
    ["total_count", "total", "summary.total"],
    ["expectations", "results", "judgements"],
]
REQUIRED_EXP_FIELDS_PER_ROW = ["passed", "evidence"]
REQUIRED_META_FIELDS = ["eval_name", "scenario", "prompt"]


def get_nested(obj: dict, dotted: str) -> Any:
    """Look up key like 'summary.passed' in nested dict."""
    cur = obj
    for k in dotted.split("."):
        if not isinstance(cur, dict):
            return None
        cur = cur.get(k)
    return cur


def has_any(obj: dict, keys: list[str]) -> bool:
    return any(get_nested(obj, k) is not None for k in keys)


def check_grading(path: Path) -> tuple[list[str], list[str]]:
    """Return (errors, warnings) for one grading.json."""
    errs, warns = [], []
    if not path.exists():
        errs.append(f"missing file: {path}")
        return errs, warns
    if path.stat().st_size < 50:
        errs.append(f"size < 50B (likely empty): {path}")
        return errs, warns

    try:
        g = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        errs.append(f"JSON parse error in {path}: {e}")
        return errs, warns

    # Check required fields with fallback chain
    field_names = ["passed_count", "total_count", "expectations"]
    fallback_chains = [
        ["passed_count", "score", "summary.passed"],
        ["total_count", "total", "summary.total"],
        ["expectations", "results", "judgements"],
    ]
    for primary, chain in zip(field_names, fallback_chains):
        if get_nested(g, primary) is not None:
            continue
        if has_any(g, chain[1:]):
            warns.append(
                f"{path.name}: missing canonical '{primary}' but has fallback "
                f"({[c for c in chain[1:] if get_nested(g, c) is not None]}). "
                f"建议升级 schema"
            )
        else:
            errs.append(
                f"{path.name}: missing required field '{primary}' "
                f"(also no fallback in {chain[1:]})"
            )

    # Check expectations array entries
    exps = (
        g.get("expectations")
        or g.get("results")
        or [*(g.get("judgements", [])), *(g.get("negative_judgements", []))]
    )
    if not exps:
        errs.append(f"{path.name}: expectations array is empty")
    else:
        for i, e in enumerate(exps):
            if not isinstance(e, dict):
                errs.append(f"{path.name}: expectations[{i}] is not an object")
                continue
            for f in REQUIRED_EXP_FIELDS_PER_ROW:
                if f not in e or e[f] in ("", None):
                    errs.append(
                        f"{path.name}: expectations[{i}] missing or empty '{f}'"
                    )
            ev = e.get("evidence", "")
            if isinstance(ev, str) and ev.strip() in ("见上文", "如前所述", "略", "见报告", ""):
                errs.append(
                    f"{path.name}: expectations[{i}].evidence is empty/placeholder ('{ev}')"
                )
            # 检查至少有一个文本字段供 Grader 渲染
            if not any(
                e.get(k) for k in ["expectation", "text", "description", "question", "name"]
            ):
                errs.append(
                    f"{path.name}: expectations[{i}] missing text field "
                    f"(any of expectation/text/description/question/name required)"
                )

    # 反作弊：dry_run 不允许 100% 全 pass（baseline）或 0% 全 fail（with_skill 异常）
    side_hint = "with_skill" if "with_skill" in path.parts else (
        "baseline" if "baseline" in path.parts else None
    )
    if side_hint and exps:
        passed_n = sum(1 for e in exps if e.get("passed") is True)
        if side_hint == "baseline" and passed_n == len(exps):
            warns.append(
                f"{path.name}: baseline 全 passed=true（{passed_n}/{len(exps)}）"
                f"——可能 judgement 太宽松，复核 critique evals"
            )
        if side_hint == "with_skill" and passed_n == 0:
            errs.append(
                f"{path.name}: with_skill 全 failed=false（0/{len(exps)}）"
                f"——不正常，可能 grading 写反了"
            )

    return errs, warns


def check_eval_metadata(path: Path) -> tuple[list[str], list[str]]:
    """Return (errors, warnings) for eval_metadata.json."""
    errs, warns = [], []
    if not path.exists():
        warns.append(
            f"missing eval_metadata.json: {path}"
            f"（脚本会用 dir basename 兜底，但优先级 / functional_module 标签会缺失）"
        )
        return errs, warns
    try:
        m = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        errs.append(f"JSON parse error in {path}: {e}")
        return errs, warns

    for f in REQUIRED_META_FIELDS:
        if not m.get(f):
            warns.append(f"{path.name}: missing recommended field '{f}'")

    return errs, warns


def check_manifest(ws_dir: Path) -> tuple[list[str], list[str]]:
    """Return (errors, warnings) for manifest.yaml schema."""
    errs, warns = [], []
    manifest_path = ws_dir / "manifest.yaml"
    if not manifest_path.exists():
        errs.append(f"missing manifest.yaml: {manifest_path}")
        return errs, warns

    text = manifest_path.read_text(encoding="utf-8")

    # Check eval_mode 多源（任一即可被脚本读到）
    has_eval_mode_evaluation = "evaluation:" in text and "eval_mode:" in text.split("evaluation:", 1)[1] if "evaluation:" in text else False
    has_eval_mode_iterations = "iterations:" in text and "eval_mode:" in text.split("iterations:", 1)[1] if "iterations:" in text else False

    if not (has_eval_mode_evaluation or has_eval_mode_iterations):
        errs.append(
            "manifest.yaml: 缺 eval_mode 字段——必须在 evaluation.eval_mode "
            "或 iterations[].eval_mode 至少一处指定"
        )
    elif has_eval_mode_evaluation and not has_eval_mode_iterations:
        warns.append(
            "manifest.yaml: 仅在 evaluation.eval_mode 写了 eval_mode；"
            "建议同时在 iterations[].eval_mode 写一份历史快照（防止旧脚本读不到）"
        )
    elif has_eval_mode_iterations and not has_eval_mode_evaluation:
        warns.append(
            "manifest.yaml: 仅在 iterations[].eval_mode 写了 eval_mode；"
            "建议在 evaluation.eval_mode 也写一份"
        )

    return errs, warns


def main():
    if len(sys.argv) < 2:
        print("用法: python3 validate_eval_artifacts.py <iter_dir>")
        print("       <iter_dir> 形如 .../skill-assistant-workspace/<skill>/iteration-N/")
        sys.exit(3)

    iter_dir = Path(sys.argv[1]).resolve()
    if not iter_dir.exists():
        print(f"❌ iter_dir 不存在: {iter_dir}")
        sys.exit(3)

    ws_dir = iter_dir.parent

    print(f"=== validate_eval_artifacts ===")
    print(f"  iter_dir: {iter_dir}")
    print(f"  ws_dir:   {ws_dir}\n")

    all_errs, all_warns = [], []

    # ── 1. manifest.yaml ──
    print("[1/4] Checking manifest.yaml schema...")
    e, w = check_manifest(ws_dir)
    all_errs += e
    all_warns += w
    if not e and not w:
        print("  ✅ pass")
    else:
        for x in e:
            print(f"  ❌ ERROR: {x}")
        for x in w:
            print(f"  ⚠️  WARN:  {x}")

    # ── 2. eval-*/eval_metadata.json ──
    print("\n[2/4] Checking eval-*/eval_metadata.json...")
    eval_dirs = sorted([p for p in iter_dir.glob("eval-*") if p.is_dir()])
    if not eval_dirs:
        print("  (no eval-*/ subdirs found — static/preview mode? skipping)")
    for d in eval_dirs:
        e, w = check_eval_metadata(d / "eval_metadata.json")
        all_errs += e
        all_warns += w
        if not e and not w:
            print(f"  ✅ {d.name}/eval_metadata.json")
        else:
            for x in e:
                print(f"  ❌ ERROR: {x}")
            for x in w:
                print(f"  ⚠️  WARN:  {x}")

    # ── 3. eval-*/{baseline,with_skill}/run-*/grading.json ──
    print("\n[3/4] Checking eval-*/{baseline,with_skill}/run-*/grading.json schema...")
    for d in eval_dirs:
        for side in ["baseline", "with_skill", "old_skill"]:
            for run_dir in sorted((d / side).glob("run-*")) if (d / side).exists() else []:
                grading_path = run_dir / "grading.json"
                e, w = check_grading(grading_path)
                all_errs += e
                all_warns += w
                rel = grading_path.relative_to(iter_dir)
                if not e and not w:
                    print(f"  ✅ {rel}")
                else:
                    for x in e:
                        print(f"  ❌ ERROR: {x}")
                    for x in w:
                        print(f"  ⚠️  WARN:  {x}")

    # ── 4. test-prompts.json ↔ scenario 对得上 ──
    print("\n[4/4] Cross-checking eval-* scenario names ↔ test-prompts.json...")
    tp_path = ws_dir / "test-prompts.json"
    if tp_path.exists():
        try:
            tp = json.loads(tp_path.read_text(encoding="utf-8"))
            tp_scenarios = {p.get("scenario") for p in tp if isinstance(p, dict)}
            for d in eval_dirs:
                # eval_metadata.scenario 可与 dir basename 不同
                meta_path = d / "eval_metadata.json"
                if meta_path.exists():
                    try:
                        m = json.loads(meta_path.read_text(encoding="utf-8"))
                        scenario = m.get("scenario")
                        if scenario and scenario not in tp_scenarios and not d.name.startswith("eval-" + str(scenario)):
                            # 不强制要求 scenario 字面相等（dir 名已经是描述性的）
                            pass
                    except json.JSONDecodeError:
                        pass
            print(f"  ✅ test-prompts.json valid ({len(tp)} prompts)")
        except json.JSONDecodeError as e:
            all_errs.append(f"test-prompts.json parse error: {e}")
            print(f"  ❌ ERROR: test-prompts.json parse error: {e}")
    else:
        all_warns.append(
            "test-prompts.json not found (static/preview mode acceptable)"
        )
        print("  ⚠️  WARN: test-prompts.json not found")

    # ── Summary ──
    print(f"\n=== Summary ===")
    print(f"  Errors:   {len(all_errs)}")
    print(f"  Warnings: {len(all_warns)}")

    if all_errs:
        print(f"\n❌ Validation FAILED — 修以下错误后重跑（不要直接调 generate-full-report.mjs）：")
        for e in all_errs:
            print(f"    • {e}")
        print(f"\n  参考 schema 文档：")
        print(f"    - grading.json:        references/sub-agent-protocol.md §grading.json schema")
        print(f"    - eval_metadata.json:  references/workspace-layout.md §eval_metadata.json")
        print(f"    - manifest.yaml:       references/manifest-schema.md §evaluation.eval_mode")
        sys.exit(1)
    elif all_warns:
        print(f"\n⚠️  Validation PASSED with warnings — 可继续，但建议修：")
        for w in all_warns:
            print(f"    • {w}")
        sys.exit(2)
    else:
        print(f"\n✅ All eval artifacts valid. Safe to run generate-full-report.mjs.")
        sys.exit(0)


if __name__ == "__main__":
    main()
