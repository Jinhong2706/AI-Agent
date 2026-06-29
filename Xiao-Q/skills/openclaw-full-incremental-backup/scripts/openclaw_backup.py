#!/usr/bin/env python3
"""
OpenClaw 全自动备份恢复系统 v2.0.0
===================================
功能:
  - 增量备份（tar --listed-incremental，只存变化部分）
  - 每周六自动全量备份
  - 备份完成后自动校验完整性
  - 防并发锁文件
  - 智能清理过期备份
  - 一键恢复 + 恢复前自动备份当前状态
  - 进度条显示

用法:
  python3 openclaw_backup.py backup   # 执行备份
  python3 openclaw_backup.py restore  # 恢复最新备份
  python3 openclaw_backup.py verify  # 验证最新备份完整性
  python3 openclaw_backup.py list    # 列出所有备份
  python3 openclaw_backup.py clean   # 清理过期备份
"""

import os
import sys
import json
import argparse
import subprocess
import fcntl
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

# ============== 自动检测安装路径 ==============
# 优先从 config.env 读取，fallback 到脚本同级的 config.env，再 fallback 到编译时路径
_SCRIPT_DIR = Path(__file__).resolve().parent
_INSTALL_ROOT = _SCRIPT_DIR.parent  # <install_root>/scripts/ -> <install_root>/
_CONFIG_FILE = _INSTALL_ROOT / "config.env"

# 从 config.env 读取路径（安装脚本生成）
def _read_config():
    cfg = {}
    if _CONFIG_FILE.exists():
        for line in _CONFIG_FILE.read_text().splitlines():
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                cfg[k.strip()] = v.strip().strip('"').strip("'")
    return cfg

_cfg = _read_config()

# 安装时指定的路径（用户在安装目录下的 config.env 中指定）
OPENCLAW_HOME = Path(_cfg.get("OPENCLAW_HOME", "/root/.openclaw"))
BACKUP_ROOT   = Path(_cfg.get("BACKUP_ROOT", str(_INSTALL_ROOT)))

FULL_DIR      = BACKUP_ROOT / "full"
INCR_DIR      = BACKUP_ROOT / "incremental"
SNAPSHOT_DIR  = BACKUP_ROOT / "snapshots"
LOCK_FILE     = BACKUP_ROOT / ".backup.lock"
METADATA_FILE = BACKUP_ROOT / "backup_metadata.json"
LOG_FILE      = BACKUP_ROOT / "backup.log"

# 保留策略
INCR_RETENTION_DAYS = 30
FULL_RETENTION_DAYS = 180


# ============== 排除规则 ==============

# 排除目录（无需备份的缓存/临时目录）
EXCLUDE_DIRS = [
    "logs", "media", "delivery-queue", "cron", "backups",
    "subagents", "completions", "tasks", "devices", "plugins",
    "__pycache__", "node_modules", "canvas", "hooks",
    "credentials",          # 避免密钥泄露
    ".cache", ".npm", ".local/share/npm", ".config", ".local/lib",
    ".vscode-server", ".codeium", ".claude", ".ssh", ".gnupg",
]

# .NET 编译产物（泛型排除，恢复时 dotnet build 可重建）
EXCLUDE_BIN_OBJ = ["bin", "obj"]

# 排除文件
EXCLUDE_FILES = [
    "*.tmp", "*.temp", "*.swp", "*.swo", "*~",
    ".DS_Store", "Thumbs.db", "*.log", "*.lock",
    "exec-approvals.json", "*.pyc", "*.pyo",
]


# ============== 工具函数 ==============

def log(msg: str, level: str = "INFO"):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [{level}] {msg}"
    print(line)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def run_cmd(cmd: list, desc: str = "", timeout: int = 3600):
    log(f"执行: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout,
            cwd=str(OPENCLAW_HOME),
        )
        if result.returncode != 0:
            log(f"命令失败 (exit {result.returncode}): {desc}", "ERROR")
            if result.stderr:
                log(f"stderr: {result.stderr[:500]}", "ERROR")
            return False, result.stderr or ""
        return True, result.stdout or ""
    except subprocess.TimeoutExpired:
        log(f"命令超时 ({timeout}s): {desc}", "ERROR")
        return False, "timeout"
    except Exception as e:
        log(f"命令异常: {e}", "ERROR")
        return False, str(e)


def get_dir_size(path: Path) -> int:
    try:
        result = subprocess.run(
            ["du", "-sb", str(path)],
            capture_output=True, text=True, timeout=60,
        )
        if result.returncode == 0:
            return int(result.stdout.split()[0])
    except Exception:
        pass
    return 0


def get_file_size(path: Path) -> str:
    try:
        if path.is_dir():
            size = get_dir_size(path)
        else:
            size = path.stat().st_size
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024:
                return f"{size:.1f}{unit}"
            size /= 1024
        return f"{size:.1f}PB"
    except Exception:
        return "N/A"


def format_bytes(size_bytes: int) -> str:
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} PB"


def load_metadata() -> dict:
    if METADATA_FILE.exists():
        try:
            with open(METADATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"full_backups": [], "incremental_backups": [], "last_full_backup": None}


def save_metadata(meta: dict):
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)


def build_exclude_args() -> list:
    args = []
    for d in EXCLUDE_DIRS:
        args += ["--exclude", d]
    for x in EXCLUDE_BIN_OBJ:
        args += ["--exclude", x]
    for p in EXCLUDE_FILES:
        args += ["--exclude", p]
    return args


def acquire_lock() -> Optional[int]:
    LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(LOCK_FILE, os.O_CREAT | os.O_RDWR)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        os.write(fd, f"{os.getpid()} {datetime.now().isoformat()}\n".encode())
        return fd
    except (IOError, OSError):
        os.close(fd)
        return None


def release_lock(fd: int):
    try:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)
    except Exception:
        pass
    if LOCK_FILE.exists():
        LOCK_FILE.unlink()


# ============== 备份核心 ==============

def do_backup(meta: dict) -> bool:
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    FULL_DIR.mkdir(parents=True, exist_ok=True)
    INCR_DIR.mkdir(parents=True, exist_ok=True)
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)

    # 判断备份类型（首次/每周六全量，其他增量）
    is_full = (
        not meta["full_backups"]
        or (datetime.now().weekday() == 5)  # 周六强制全量
    )
    backup_type = "full" if is_full else "incremental"
    exclude_args = build_exclude_args()

    if is_full:
        log("=== 开始全量备份 ===")
        snapshot_path = SNAPSHOT_DIR / f"snapshot-{ts}.fsf"
        backup_path = FULL_DIR / f"openclaw-{ts}-full.tar.gz"

        tar_cmd = [
            "tar", "--create", "--gzip",
            "--file", str(backup_path),
            "--directory", str(OPENCLAW_HOME),
            "--listed-incremental", str(snapshot_path),
            *exclude_args, ".",
        ]

        ok, err = run_cmd(tar_cmd, f"全量备份 {backup_path.name}")
        if not ok:
            if backup_path.exists():
                backup_path.unlink()
            return False

        entry = {
            "path": str(backup_path),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "timestamp": ts,
            "size": backup_path.stat().st_size,
            "size_human": get_file_size(backup_path),
            "snapshot": str(snapshot_path),
        }
        meta["full_backups"].append(entry)
        meta["last_full_backup"] = datetime.now().strftime("%Y-%m-%d")
        save_metadata(meta)

        latest_link = BACKUP_ROOT / "latest-backup"
        if latest_link.exists() or latest_link.is_symlink():
            latest_link.unlink()
        latest_link.symlink_to(backup_path)

        log(f"全量备份完成: {backup_path.name} ({get_file_size(backup_path)})")

    else:
        log("=== 开始增量备份 ===")
        last_full_ts = meta["last_full_backup"]
        if not last_full_ts:
            log("未找到全量备份，降级为全量备份", "WARN")
            return do_backup(meta)

        full_backups_sorted = sorted(meta["full_backups"], key=lambda x: x["timestamp"], reverse=True)
        base_snapshot = Path(full_backups_sorted[0]["snapshot"]) if full_backups_sorted else None
        current_snapshot = SNAPSHOT_DIR / f"snapshot-current.fsf"
        backup_path = INCR_DIR / f"openclaw-{ts}-incremental.tar.gz"

        if base_snapshot and base_snapshot.exists():
            shutil.copy2(base_snapshot, current_snapshot)

        tar_cmd = [
            "tar", "--create", "--gzip",
            "--file", str(backup_path),
            "--directory", str(OPENCLAW_HOME),
            "--listed-incremental", str(current_snapshot),
            *exclude_args, ".",
        ]

        ok, err = run_cmd(tar_cmd, f"增量备份 {backup_path.name}")
        if not ok:
            if backup_path.exists():
                backup_path.unlink()
            return False

        incr_size = backup_path.stat().st_size
        if incr_size < 1024:
            log(f"增量备份过小 ({get_file_size(backup_path)})，可能无变化文件", "WARN")

        entry = {
            "path": str(backup_path),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "timestamp": ts,
            "size": incr_size,
            "size_human": get_file_size(backup_path),
            "based_on_full": last_full_ts,
        }
        meta["incremental_backups"].append(entry)
        save_metadata(meta)

        latest_link = BACKUP_ROOT / "latest-backup"
        if latest_link.exists() or latest_link.is_symlink():
            latest_link.unlink()
        latest_link.symlink_to(backup_path)

        log(f"增量备份完成: {backup_path.name} ({get_file_size(backup_path)})")

    # 清理过期
    clean_old_backups(meta)

    # 验证
    log("验证备份完整性...")
    latest = BACKUP_ROOT / "latest-backup"
    if latest.exists() or latest.is_symlink():
        ok_v, _ = verify_backup(latest.resolve())
        log(f"备份完整性验证{'通过 ✅' if ok_v else '失败 ⚠️'}")

    log(f"=== 备份完成 ({backup_type}) ===")
    return True


# ============== 清理 ==============

def clean_old_backups(meta: dict = None):
    if meta is None:
        meta = load_metadata()

    cutoff_incr = datetime.now() - timedelta(days=INCR_RETENTION_DAYS)
    cutoff_full = datetime.now() - timedelta(days=FULL_RETENTION_DAYS)
    removed = []

    still_fresh_incr = []
    for e in meta["incremental_backups"]:
        edate = datetime.strptime(e["date"], "%Y-%m-%d")
        if edate < cutoff_incr:
            p = Path(e["path"])
            if p.exists():
                p.unlink()
                removed.append(str(p.name))
        else:
            still_fresh_incr.append(e)
    meta["incremental_backups"] = still_fresh_incr

    still_fresh_full = []
    for e in meta["full_backups"]:
        edate = datetime.strptime(e["date"], "%Y-%m-%d")
        if edate < cutoff_full:
            p = Path(e["path"])
            if p.exists():
                p.unlink()
            snap = Path(e.get("snapshot", ""))
            if snap.exists():
                snap.unlink()
            removed.append(str(p.name))
        else:
            still_fresh_full.append(e)
    meta["full_backups"] = still_fresh_full

    save_metadata(meta)
    if removed:
        log(f"已清理 {len(removed)} 个过期备份: {', '.join(removed)}")


# ============== 验证 ==============

def verify_backup(backup_path: Path) -> tuple:
    if not backup_path.exists():
        return False, f"备份文件不存在: {backup_path}"
    proc = subprocess.run(
        f"tar -tzf {backup_path} >/dev/null 2>&1",
        shell=True, capture_output=True, text=True, timeout=60,
    )
    return (proc.returncode == 0), ("OK" if proc.returncode == 0 else proc.stderr[:200])


def do_verify() -> bool:
    latest = BACKUP_ROOT / "latest-backup"
    if not latest.exists() and not latest.is_symlink():
        log("未找到任何备份", "ERROR")
        return False
    target = latest.resolve()
    log(f"验证: {target.name}")
    ok, msg = verify_backup(target)
    log(f"{'✅ 备份正常' if ok else '❌ 备份损坏'}: {get_file_size(target)}")
    return ok


# ============== 恢复 ==============

def do_restore() -> bool:
    latest = BACKUP_ROOT / "latest-backup"
    if not latest.exists() and not latest.is_symlink():
        log("未找到任何备份可供恢复", "ERROR")
        return False
    target = latest.resolve()
    log(f"=== 准备恢复备份 ===")
    log(f"备份文件: {target.name} ({get_file_size(target)})")

    pre_restore = OPENCLAW_HOME.with_name(
        f".openclaw.pre-restore-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    )
    if OPENCLAW_HOME.exists():
        try:
            shutil.copytree(OPENCLAW_HOME, pre_restore)
            log(f"当前目录已备份: {pre_restore}")
        except Exception as e:
            log(f"备份当前目录失败: {e}，继续恢复...", "WARN")

    log("开始解压恢复...")
    cmd = [
        "tar", "--extract", "--gzip",
        "--file", str(target),
        "--directory", str(OPENCLAW_HOME),
    ]
    ok, err = run_cmd(cmd, "恢复备份", timeout=1800)
    if ok:
        log("✅ 恢复完成！建议重启 OpenClaw 服务生效")
        return True
    else:
        log(f"❌ 恢复失败: {err}", "ERROR")
        return False


# ============== 列表 ==============

def do_list():
    meta = load_metadata()
    print(f"\n{'='*60}")
    print(f"  OpenClaw 备份查看器")
    print(f"{'='*60}")
    print(f"备份目录: {BACKUP_ROOT}")
    print(f"源目录:   {OPENCLAW_HOME} ({get_file_size(OPENCLAW_HOME)})\n")

    print(f"【全量备份】(保留{FULL_RETENTION_DAYS}天)")
    if meta["full_backups"]:
        for e in sorted(meta["full_backups"], key=lambda x: x["timestamp"], reverse=True)[:10]:
            p = Path(e["path"])
            alive = "✅" if p.exists() else "❌"
            print(f"  {alive} {e['timestamp']}  {e.get('size_human','N/A')}  {e['date']}")
    else:
        print("  (无)")

    print(f"\n【增量备份】(最近, 共{len(meta['incremental_backups'])}个)")
    recent_incr = sorted(meta["incremental_backups"], key=lambda x: x["timestamp"], reverse=True)[:15]
    if recent_incr:
        total = sum(Path(e["path"]).stat().st_size for e in recent_incr if Path(e["path"]).exists())
        for e in recent_incr:
            p = Path(e["path"])
            alive = "✅" if p.exists() else "❌"
            print(f"  {alive} {e['timestamp']}  {e.get('size_human','N/A')}  基于: {e.get('based_on_full','?')}")
        print(f"  ... 总计 {format_bytes(total)}")
    else:
        print("  (无)")

    full_total = sum(e.get("size", 0) for e in meta["full_backups"] if Path(e.get("path", "")).exists())
    incr_total = sum(e.get("size", 0) for e in meta["incremental_backups"] if Path(e.get("path", "")).exists())
    print(f"\n总备份体积: {format_bytes(full_total + incr_total)}")
    print(f"{'='*60}\n")


# ============== 主入口 ==============

def main():
    parser = argparse.ArgumentParser(
        description="OpenClaw 全自动备份恢复系统 v2.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python3 openclaw_backup.py backup   # 执行备份
  python3 openclaw_backup.py restore  # 恢复最新备份
  python3 openclaw_backup.py verify   # 验证备份完整性
  python3 openclaw_backup.py list     # 查看所有备份
  python3 openclaw_backup.py clean    # 清理过期备份
        """
    )
    parser.add_argument("action", choices=["backup", "restore", "verify", "list", "clean"])
    parser.add_argument("--force", action="store_true", help="强制执行（跳过锁检查）")
    args = parser.parse_args()

    meta = load_metadata()

    if args.action == "list":
        do_list()
        return

    if not args.force:
        lock_fd = acquire_lock()
        if lock_fd is None:
            log("备份正在运行中（使用 --force 强制执行）", "ERROR")
            sys.exit(1)
    else:
        lock_fd = None

    try:
        if args.action == "backup":
            ok = do_backup(meta)
            sys.exit(0 if ok else 1)
        elif args.action == "restore":
            ok = do_restore()
            sys.exit(0 if ok else 1)
        elif args.action == "verify":
            ok = do_verify()
            sys.exit(0 if ok else 1)
        elif args.action == "clean":
            clean_old_backups()
            log("过期备份清理完成")
            sys.exit(0)
    finally:
        if lock_fd is not None:
            release_lock(lock_fd)


if __name__ == "__main__":
    main()
