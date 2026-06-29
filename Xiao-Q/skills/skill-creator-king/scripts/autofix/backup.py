"""
backup.py — file backup + rollback engine.

Every autofix session:
  - Before fixing: copies affected files to _backups/<session_id>/
  - Rollback: reads trace.jsonl → restores from backup → deletes trace
"""

import os
import shutil
import json
import hashlib
import datetime
from pathlib import Path


def _session_backup_dir(skill_dir: str, session_id: str) -> Path:
    return Path(skill_dir) / "_backups" / session_id


def create_session_id() -> str:
    """Create a unique session ID: timestamp + short hash."""
    now = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    rand = os.urandom(4).hex()
    return f"{now}-{rand}"


def backup_files(skill_dir: str, session_id: str, file_paths: set) -> Path:
    """Copy current state of each file to _backups/<session_id>/.

    Deduplicates: if multiple fixers target the same file, backed up once.
    Returns backup directory path.
    """
    backup_dir = _session_backup_dir(skill_dir, session_id)
    backup_dir.mkdir(parents=True, exist_ok=True)

    for rel_path in file_paths:
        src = Path(skill_dir) / rel_path
        dst = backup_dir / rel_path
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.exists():
            shutil.copy2(src, dst)

    return backup_dir


def rollback_session(skill_dir: str, session_id: str) -> dict:
    """Restore all files from backup, then delete backup + trace.

    Returns: {"rolled_back": N, "files": [...]}
    """
    backup_dir = _session_backup_dir(skill_dir, session_id)
    if not backup_dir.exists():
        return {"rolled_back": 0, "files": [], "error": f"backup {session_id} not found"}

    restored = []
    for root, _, files in os.walk(backup_dir):
        for f in files:
            rel = Path(root) / f
            rel_path = rel.relative_to(backup_dir)
            target = Path(skill_dir) / rel_path
            shutil.copy2(str(rel), str(target))
            restored.append(str(rel_path))

    # Clean up backup dir and trace
    shutil.rmtree(backup_dir)
    trace_file = Path(skill_dir) / "_backups" / f"{session_id}.trace.jsonl"
    if trace_file.exists():
        trace_file.unlink()

    return {"rolled_back": len(restored), "files": restored}


def list_sessions(skill_dir: str) -> list:
    """List all rollback-able sessions in _backups/."""
    backup_root = Path(skill_dir) / "_backups"
    if not backup_root.exists():
        return []

    sessions = []
    for entry in backup_root.iterdir():
        if entry.is_dir() and not entry.name.endswith(".trace"):
            # Check if trace exists
            trace_file = backup_root / f"{entry.name}.trace.jsonl"
            sessions.append({
                "session_id": entry.name,
                "has_trace": trace_file.exists(),
                "file_count": sum(1 for _ in entry.rglob("*") if _.is_file()),
            })
    return sorted(sessions, key=lambda s: s["session_id"], reverse=True)
