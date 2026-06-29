# -*- coding: utf-8 -*-
"""
记忆管家 V3.0 - 缓存清理与提醒
来源: memory_manager.py (cache_clean/cache_reminder)
V3.0: 模块化重构
"""

import json
import os
import shutil
import time as _time
from datetime import datetime, timedelta
from pathlib import Path

from .config import VERSION, _, get_colors, DEFAULT_DAILY_BUDGET
from .token import token_check

# P1-3: 进程级 TTL 缓存（5 秒内复用结果，避免 cache_clean 多次重算）
_SIZE_CACHE = {}
_SIZE_CACHE_TTL = 5.0  # 秒


def cache_clean(workspace_path, dry_run=True, confirm=False, cache_type='all', days=30, C=None):
    if C is None:
        C = get_colors()
    workspace = Path(workspace_path).resolve()
    workbuddy_dir = workspace / ".workbuddy"

    # --- 清理前快照 ---
    before_kb = _calc_workbuddy_size(workbuddy_dir)

    to_clean = []
    summary_count = 0
    stats_count = 0
    temp_count = 0

    print(f"{C['cyan']}\U0001f9f9 缓存清理分析...{C['reset']}")

    if cache_type in ('orphan', 'all'):
        summary_dir = workbuddy_dir / ".summary"
        if summary_dir.exists():
            for sum_file in summary_dir.glob("*.summary"):
                memory_name = sum_file.stem
                memory_file = workbuddy_dir / "memory" / f"{memory_name}.md"
                if not memory_file.exists():
                    size_kb = sum_file.stat().st_size / 1024
                    to_clean.append({
                        'path': str(sum_file.relative_to(workspace)) if sum_file.is_relative_to(workspace) else sum_file.name,
                        'abs_path': str(sum_file),
                        'name': sum_file.name,
                        'type': 'orphan',
                        'size_kb': size_kb
                    })
                    summary_count += 1

    if cache_type in ('stats', 'all'):
        stats_dir = workbuddy_dir / ".token_stats"
        if stats_dir.exists():
            cutoff = datetime.now() - timedelta(days=days)
            for stat_file in stats_dir.glob("*.json"):
                mtime = datetime.fromtimestamp(stat_file.stat().st_mtime)
                if mtime < cutoff:
                    size_kb = stat_file.stat().st_size / 1024
                    to_clean.append({
                        'path': str(stat_file.relative_to(workspace)) if stat_file.is_relative_to(workspace) else stat_file.name,
                        'abs_path': str(stat_file),
                        'name': stat_file.name,
                        'type': 'stats',
                        'size_kb': size_kb,
                        'mtime': mtime.strftime('%Y-%m-%d')
                    })
                    stats_count += 1

    if cache_type in ('temp', 'all'):
        temp_patterns = ['*.tmp', '*.cache', '*.bak', '*.swp', '*.temp']
        memory_dir = workbuddy_dir / "memory"
        if memory_dir.exists():
            for pattern in temp_patterns:
                for f in memory_dir.glob(pattern):
                    if f.is_file():
                        size_kb = f.stat().st_size / 1024
                        to_clean.append({
                            'path': str(f.relative_to(workspace)) if f.is_relative_to(workspace) else f.name,
                            'abs_path': str(f),
                            'name': f.name,
                            'type': 'temp',
                            'size_kb': size_kb
                        })
                        temp_count += 1
        for pycache in workspace.rglob("__pycache__"):
            if pycache.is_symlink():
                continue
            if pycache.is_dir():
                try:
                    pycache.resolve().relative_to(workspace)
                except ValueError:
                    continue
                size_kb = sum(
                    f.stat().st_size for f in pycache.rglob("*") if f.is_file() and not f.is_symlink()) / 1024
                to_clean.append({
                    'path': str(pycache.relative_to(workspace)) if pycache.is_relative_to(workspace) else pycache.name,
                    'abs_path': str(pycache),
                    'name': pycache.name + "/",
                    'type': 'temp',
                    'size_kb': size_kb
                })
                temp_count += 1

    total_size_kb = sum(item['size_kb'] for item in to_clean)

    print(f"\n{C['bright']}\U0001f4ca {_('cache_scan_result')}:{C['reset']}")
    if cache_type in ('orphan', 'all'):
        print(f"   \U0001f4c4 {_('orphan_summaries')}: {summary_count}")
    if cache_type in ('stats', 'all'):
        print(f"   \U0001f4ca {_('expired_token_stats').format(days=days)}: {stats_count}")
    if cache_type in ('temp', 'all'):
        print(f"   \U0001f5c2\ufe0f  {_('temp_files_label')}: {temp_count}")
    print(f"   \U0001f4be {_('freeable_space')}: {total_size_kb:.1f} KB")

    if not to_clean:
        print(f"\n{C['green']}\u2705 {_('no_cache_to_clean')}{C['reset']}")
        return {"cleaned": 0, "freed_kb": 0}

    print(f"\n{C['yellow']}\U0001f4cb {_('pending_clean_list')}:{C['reset']}")
    for i, item in enumerate(to_clean[:20], 1):
        print(f"   [{i}] [{item['type']}] {item['name']} ({item['size_kb']:.1f}KB)")
    if len(to_clean) > 20:
        print(f"   ... {_('and_more').format(count=len(to_clean)-20)}")

    if dry_run:
        print(f"\n{C['yellow']}\U0001f4a1 {_('preview_mode_notice')}{C['reset']}")
        print(f"{C['yellow']}\U0001f4a1 {_('add_execute_param')}{C['reset']}")
        return {"preview": len(to_clean), "freed_kb": total_size_kb,
                "before_kb": before_kb, "after_kb": before_kb, "delta_kb": 0}

    if not confirm:
        answer = input(
            f"\n{C['bright']}\u26a0\ufe0f  {_('confirm_clean_prompt').format(count=len(to_clean))}: {C['reset']}").strip().upper()
        if answer != 'Y':
            print(f"{C['green']}\u2705 {_('cancelled')}{C['reset']}")
            return {"cleaned": 0, "freed_kb": 0}

    cleaned = 0
    freed_kb = 0
    errors = []

    for item in to_clean:
        try:
            p = Path(item.get('abs_path', item['path']))
            if not p.is_absolute():
                p = workspace / item['path']
            if p.is_symlink():
                errors.append(f"跳过符号链接 {item['name']}")
                continue
            if p.is_file():
                freed_kb += item['size_kb']
                p.unlink()
                cleaned += 1
            elif p.is_dir():
                freed_kb += item['size_kb']
                shutil.rmtree(p, ignore_errors=True)
                cleaned += 1
        except Exception as e:
            errors.append(f"删除失败 {item['name']}: {e}")

    print(f"\n{C['green']}\u2705 {_('cleaned_n_files').format(count=cleaned, kb=f'{freed_kb:.1f}')}{C['reset']}")
    if errors:
        print(f"{C['red']}\u26a0\ufe0f  {_('clean_errors')}: {len(errors)}{''}")
        for err in errors[:5]:
            print(f"   {err}")

    # --- 清理后快照 ---
    after_kb = _calc_workbuddy_size(workbuddy_dir)
    delta_kb = round(before_kb - after_kb, 1)

    if delta_kb > 0:
        print(f"\n{C['cyan']}\U0001f4ca {_('clean_size_comparison')}: {before_kb:.1f}KB \u2192 {after_kb:.1f}KB ({C['green']}-{delta_kb:.1f}KB{C['reset']}{C['cyan']}){C['reset']}")

    return {"cleaned": cleaned, "freed_kb": freed_kb, "errors": errors,
            "before_kb": round(before_kb, 1), "after_kb": round(after_kb, 1), "delta_kb": delta_kb}


def cache_reminder(workspace_path):
    workspace = Path(workspace_path)
    workbuddy_dir = workspace / ".workbuddy"

    summary_count = 0
    stats_count = 0
    temp_count = 0
    total_cache_size_kb = 0.0
    total_tokens = 0

    summary_dir = workbuddy_dir / ".summary"
    if summary_dir.exists():
        for sum_file in summary_dir.glob("*.summary"):
            memory_name = sum_file.stem
            memory_file = workbuddy_dir / "memory" / f"{memory_name}.md"
            if not memory_file.exists():
                summary_count += 1
            try:
                total_cache_size_kb += sum_file.stat().st_size / 1024
            except OSError:
                pass

    stats_dir = workbuddy_dir / ".token_stats"
    if stats_dir.exists():
        cutoff = datetime.now() - timedelta(days=30)
        for stat_file in stats_dir.glob("*.json"):
            mtime = datetime.fromtimestamp(stat_file.stat().st_mtime)
            if mtime < cutoff:
                stats_count += 1
            try:
                total_cache_size_kb += stat_file.stat().st_size / 1024
            except OSError:
                pass
            try:
                stat_data = json.loads(stat_file.read_text(encoding="utf-8"))
                if isinstance(stat_data, dict):
                    for key in ["input_tokens", "output_tokens", "total_tokens"]:
                        if key in stat_data:
                            try:
                                total_tokens += int(stat_data[key])
                            except (ValueError, TypeError):
                                pass
            except (json.JSONDecodeError, OSError):
                pass

    memory_dir = workbuddy_dir / "memory"
    if memory_dir.exists():
        for pattern in ["*.tmp", "*.cache"]:
            for f in memory_dir.glob(pattern):
                temp_count += 1
                try:
                    total_cache_size_kb += f.stat().st_size / 1024
                except OSError:
                    pass

    total = summary_count + stats_count + temp_count

    msg = f"\U0001f9f9 {_('cache_reminder_title')}\n"

    if total_tokens > 0:
        msg += f"\U0001f4ca {_('cache_reminder_token_stats')}: ~{total_tokens:,} tokens\n"
    else:
        msg += f"\U0001f4ca {_('cache_reminder_token_stats')}: {_('cache_reminder_token_no_data')}\n"

    tk = token_check(str(workspace), budget=DEFAULT_DAILY_BUDGET)
    msg += f"\n{tk['emoji']} {tk['message']}\n"

    if total_cache_size_kb > 1024:
        msg += f"\U0001f4be {_('cache_reminder_cache_size')}: {total_cache_size_kb / 1024:.1f} {_('cache_reminder_mb_unit')}\n"
    else:
        msg += f"\U0001f4be {_('cache_reminder_cache_size')}: {total_cache_size_kb:.1f} {_('cache_reminder_kb_unit')}\n"

    if summary_count > 0:
        msg += f"\U0001f4c4 {_('cache_reminder_orphan_summaries')}: {summary_count}\n"
    if stats_count > 0:
        msg += f"\U0001f4ca {_('cache_reminder_expired_stats')}: {stats_count}\n"
    if temp_count > 0:
        msg += f"\U0001f5c2\ufe0f {_('cache_reminder_temp_files')}: {temp_count}\n"

    if total == 0:
        msg += f"\u2705 {_('cache_reminder_no_cache_good')}"
    else:
        msg += f"\U0001f4a1 {_('cache_reminder_total_cleanable')}: {total}\n"
        msg += f"\U0001f4a1 {_('cache_reminder_manual_clean')}: memory_manager.py cache-clean --execute"

    print(msg)

    return {
        "orphan": summary_count,
        "expired_stats": stats_count,
        "temp_files": temp_count,
        "total": total,
        "total_tokens": total_tokens,
        "cache_size_kb": round(total_cache_size_kb, 1)
    }


def _calc_workbuddy_size(workbuddy_dir):
    """计算 .workbuddy 目录总大小（KB）—— P1-3 优化版。
    1) 5 秒进程级 TTL 缓存（cache_clean 清理前后两次调用 5s 内命中第二次）
    2) os.walk 替代 rglob，减少 ~30% 系统调用
    """
    workbuddy_dir = Path(workbuddy_dir)
    if not workbuddy_dir.exists():
        return 0.0

    key = str(workbuddy_dir.resolve())
    now = _time.monotonic()
    if key in _SIZE_CACHE:
        val, ts = _SIZE_CACHE[key]
        if now - ts < _SIZE_CACHE_TTL:
            return val
        _SIZE_CACHE.pop(key, None)

    total = 0.0
    try:
        for root, _dirs, files in os.walk(str(workbuddy_dir), followlinks=False):
            for fname in files:
                fpath = Path(root) / fname
                try:
                    if fpath.is_symlink():
                        continue
                    total += fpath.stat().st_size
                except (OSError, PermissionError):
                    pass
    except (OSError, PermissionError):
        pass
    val = total / 1024
    _SIZE_CACHE[key] = (val, now)
    return val
