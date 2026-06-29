# -*- coding: utf-8 -*-
"""
记忆管家 V3.0 - Token预算检查、统计与哈希计算
来源: memory_manager.py (hash/token/trends)
V3.0: 模块化重构
"""

import hashlib
import json
import os
import tempfile
from datetime import datetime, date, timedelta
from pathlib import Path

from .config import VERSION, DEFAULT_DAILY_BUDGET, TOKEN_ALERT_RATIO, TOKEN_WARN_RATIO, _


def compute_content_hash(file_path):
    """计算文件内容SHA256哈希"""
    try:
        with open(file_path, 'rb') as f:
            return hashlib.sha256(f.read(50 * 1024)).hexdigest()
    except (OSError, IOError, PermissionError):
        return ""


def get_token_stats_dir(workspace_path):
    base_path = Path(workspace_path).resolve()
    stats_dir = base_path / ".workbuddy" / ".token_stats"
    stats_dir.mkdir(parents=True, exist_ok=True)
    return stats_dir


def record_token_usage(workspace_path, tokens, operation="load"):
    stats_dir = get_token_stats_dir(workspace_path)
    today = datetime.now().date().isoformat()
    stats_file = stats_dir / (today + ".json")
    stats = {"date": today, "operations": {}} if not stats_file.exists() else json.loads(
        stats_file.read_text(encoding="utf-8"))
    if operation not in stats["operations"]:
        stats["operations"][operation] = {"count": 0, "tokens": 0}
    stats["operations"][operation]["count"] += 1
    stats["operations"][operation]["tokens"] += tokens
    # 原子性写入：先写临时文件再 rename，防止并发丢数据
    try:
        fd, tmp_path = tempfile.mkstemp(dir=str(stats_dir), suffix=".tmp")
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, str(stats_file))
    except (OSError, IOError):
        # 原子写入失败时回退到直接写入
        stats_file.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    return stats


def token_check(workspace_path, budget=DEFAULT_DAILY_BUDGET):
    workspace = Path(workspace_path).resolve()
    stats_dir = workspace / ".workbuddy" / ".token_stats"
    today = date.today().isoformat()
    today_file = stats_dir / f"{today}.json"

    today_tokens = 0
    if today_file.exists():
        try:
            data = json.loads(today_file.read_text(encoding="utf-8"))
            for op in data.get("operations", {}).values():
                today_tokens += int(op.get("tokens", 0))
        except (json.JSONDecodeError, OSError, KeyError):
            pass

    ratio = today_tokens / max(budget, 1)

    if ratio >= TOKEN_ALERT_RATIO:
        level, emoji, message = "red", "🔴", _("token_alert").format(today=today_tokens, budget=budget, pct=ratio*100)
    elif ratio >= TOKEN_WARN_RATIO:
        level, emoji, message = "yellow", "🟡", _("token_warn").format(today=today_tokens, budget=budget, pct=ratio*100)
    else:
        level, emoji, message = "green", "🟢", _("token_ok").format(today=today_tokens, budget=budget, pct=ratio*100)

    return {
        "today": today,
        "today_tokens": today_tokens,
        "budget": budget,
        "ratio": round(ratio, 2),
        "level": level,
        "emoji": emoji,
        "message": message,
        "note": _("token_estimated_note"),
    }


def token_trends(workspace_path, period="week", days_back=None):
    """聚合 Token 消耗趋势（按周/月）

    Args:
        workspace_path: 工作空间路径
        period: "week" | "month" | "daily"
        days_back: 回溯天数，默认 7(week)/30(month)/14(daily)

    Returns:
        dict: {period, days_back, daily: [{date, tokens, operations}],
               aggregated: [{label, tokens, operations_count}], totals}
    """
    workspace = Path(workspace_path).resolve()
    stats_dir = workspace / ".workbuddy" / ".token_stats"

    if days_back is None:
        days_back = {"week": 7, "month": 30, "daily": 14}.get(period, 7)

    cutoff = date.today() - timedelta(days=days_back)

    # 1. 逐日读取
    daily = []
    total_tokens = 0
    total_ops = 0

    if stats_dir.exists():
        for stat_file in sorted(stats_dir.glob("*.json")):
            try:
                file_date = date.fromisoformat(stat_file.stem)
            except ValueError:
                continue
            if file_date < cutoff:
                continue

            day_tokens = 0
            day_ops = 0
            try:
                data = json.loads(stat_file.read_text(encoding="utf-8"))
                for op_data in data.get("operations", {}).values():
                    day_tokens += int(op_data.get("tokens", 0))
                    day_ops += int(op_data.get("count", 0))
            except (json.JSONDecodeError, OSError, KeyError, ValueError):
                continue

            daily.append({
                "date": file_date.isoformat(),
                "tokens": day_tokens,
                "operations_count": day_ops,
            })
            total_tokens += day_tokens
            total_ops += day_ops

    # 2. 按周期聚合
    aggregated = []
    if period == "daily":
        aggregated = daily
    elif period == "week":
        week_buckets = {}
        for d in daily:
            dt = date.fromisoformat(d["date"])
            week_start = dt - timedelta(days=dt.weekday())
            key = week_start.isoformat()
            if key not in week_buckets:
                week_buckets[key] = {"tokens": 0, "operations_count": 0}
            week_buckets[key]["tokens"] += d["tokens"]
            week_buckets[key]["operations_count"] += d["operations_count"]
        for key in sorted(week_buckets):
            aggregated.append({
                "label": f"{key} ~",
                "tokens": week_buckets[key]["tokens"],
                "operations_count": week_buckets[key]["operations_count"],
            })
    elif period == "month":
        month_buckets = {}
        for d in daily:
            dt = date.fromisoformat(d["date"])
            key = dt.strftime("%Y-%m")
            if key not in month_buckets:
                month_buckets[key] = {"tokens": 0, "operations_count": 0}
            month_buckets[key]["tokens"] += d["tokens"]
            month_buckets[key]["operations_count"] += d["operations_count"]
        for key in sorted(month_buckets):
            aggregated.append({
                "label": key,
                "tokens": month_buckets[key]["tokens"],
                "operations_count": month_buckets[key]["operations_count"],
            })

    avg_daily = total_tokens // max(len(daily), 1)

    return {
        "period": period,
        "days_back": days_back,
        "daily": daily,
        "aggregated": aggregated,
        "totals": {
            "days_with_data": len(daily),
            "total_tokens": total_tokens,
            "total_operations": total_ops,
            "avg_daily_tokens": avg_daily,
        },
    }
