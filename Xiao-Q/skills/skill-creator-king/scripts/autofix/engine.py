#!/usr/bin/env python3
"""
engine.py — autofix safety harness.

Does NOT do the fixing itself — LLM handles that.
This harness does three things:
  1. Parse validate.py issues into structured output for LLM consumption
  2. Backup files before LLM fixes (so we can rollback)
  3. Re-run validate after LLM fixes to verify no damage

Usage:
  python3 scripts/autofix/engine.py <skill_dir>         # issues report
  python3 scripts/autofix/engine.py <skill_dir> --backup # create backup
  python3 scripts/autofix/engine.py <skill_dir> --verify <session_id>  # verify after fix
  python3 scripts/autofix/engine.py --rollback <session_id> --skill <skill_dir>
  python3 scripts/autofix/engine.py --list-sessions --skill <skill_dir>
"""

import json
import os
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SCK_ROOT = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(SCK_ROOT))

from scripts.autofix.backup import (
    create_session_id, backup_files, rollback_session, list_sessions,
)


def _run_cmd(cmd: list, cwd: str = None) -> dict:
    result = subprocess.run(
        cmd, capture_output=True, text=True, timeout=60,
        cwd=cwd or str(SCK_ROOT),
    )
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"error": "not_json", "stdout": result.stdout[:500],
                "stderr": result.stderr[:500]}


def scan(skill_dir: str) -> dict:
    """Run validate.py and return structured issues."""
    cmd = [sys.executable, str(SCK_ROOT / "scripts" / "validate.py"),
           skill_dir, "--json"]
    data = _run_cmd(cmd)
    return {
        "skill_dir": skill_dir,
        "issue_count": len(data.get("issues", [])),
        "issues": data.get("issues", []),
    }


def backup(skill_dir: str) -> dict:
    """Create a backup session for all files in the skill."""
    session_id = create_session_id()
    skill_path = Path(skill_dir)
    files = [f.name for f in skill_path.iterdir()
             if f.is_file() and not f.name.startswith(".")
             and f.name != "sessions.log"
             and not f.name.endswith(".pyc")
             and not f.name.endswith(".trace.jsonl")]
    backup_files(skill_dir, session_id, set(files))
    return {"session_id": session_id, "files_backed_up": len(files)}


def verify(skill_dir: str, session_id: str) -> dict:
    """After LLM fixes, re-validate and report. Returns clean or damaged."""
    issues = scan(skill_dir)
    cmd = [sys.executable, str(SCK_ROOT / "scripts" / "quality-audit.py"),
           skill_dir, "--no-cache", "--json"]
    qa = _run_cmd(cmd)

    return {
        "session_id": session_id,
        "issues_after": issues["issue_count"],
        "score": qa.get("total_score", "?"),
        "grade": qa.get("grade", "?"),
        "clean": issues["issue_count"] == 0,
        "issues": issues["issues"],
    }


def main():
    args = sys.argv[1:]

    if not args:
        print("Usage: engine.py <skill_dir>")
        print("       engine.py <skill_dir> --backup")
        print("       engine.py <skill_dir> --verify <session_id>")
        print("       engine.py --rollback <session_id> --skill <skill_dir>")
        print("       engine.py --list-sessions --skill <skill_dir>")
        sys.exit(1)

    if "--rollback" in args:
        idx = args.index("--rollback")
        session_id = args[idx + 1]
        skill_idx = args.index("--skill") if "--skill" in args else -1
        skill_dir = args[skill_idx + 1] if skill_idx >= 0 else os.getcwd()
        result = rollback_session(skill_dir, session_id)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return

    if "--list-sessions" in args:
        skill_idx = args.index("--skill") if "--skill" in args else -1
        skill_dir = args[skill_idx + 1] if skill_idx >= 0 else os.getcwd()
        sessions = list_sessions(skill_dir)
        print(json.dumps(sessions, indent=2, ensure_ascii=False))
        return

    skill_dir = args[0]

    if "--backup" in args:
        result = backup(skill_dir)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return

    if "--verify" in args:
        idx = args.index("--verify")
        session_id = args[idx + 1]
        result = verify(skill_dir, session_id)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return

    # Default: scan mode
    result = scan(skill_dir)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
