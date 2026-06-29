# -*- coding: utf-8 -*-
"""
记忆管家 V3.0 - 报告生成与打印
来源: memory_manager.py (HTML/report/print)
V3.0: 模块化重构
"""

import json
from datetime import datetime
from pathlib import Path

from .config import (
    VERSION, _, _LANG, get_colors,
    MEMORY_LARGE_SIZE_KB, RECENT_DAYS, OLD_DAYS, DEFAULT_CONFIG,
    load_config,
)


def print_report(result, format_type="text"):
    C = get_colors()
    if format_type == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    print(f"\n{C['bright']}{'='*50}{C['reset']}")
    print(f"{C['cyan']}\U0001f9e0 {_('memory_report')} V{VERSION}{C['reset']}")
    print(f"{C['bright']}{'='*50}{C['reset']}")
    print(f"\U0001f4c1 {_('workspace')}: {result.get('workspace', 'N/A')}")
    print(f"\u23f0 {_('timestamp')}: {result.get('timestamp', 'N/A')[:19]}")
    print()

    if "error" in result:
        print(f"{C['red']}\u274c {_('error')}: {result['error']}{C['reset']}")
        return

    stats = result.get("stats", {})
    print(f"\U0001f4ca {_('stats_overview')}:")
    print(f"   {_('total_files')}: {C['white']}{stats.get('total_files', 0)}{C['reset']}")
    print(f"   {_('total_usage')}: {C['yellow']}{stats.get('total_size_kb', 0):.2f} KB{C['reset']}")
    print(f"   {_('cleanable')}: {C['green']}{stats.get('cleanable_size_kb', 0):.2f} KB{C['reset']} ({stats.get('cleanable_files', 0)})")

    if "estimated_token_saving" in stats:
        print(f"   {_('estimated_token_saving')}: ~{C['magenta']}{stats['estimated_token_saving']}{C['reset']}")

    if result.get("files"):
        print(f"\n\U0001f4c8 {_('file_distribution_top10')}:")
        for i, f in enumerate(result["files"][:10], 1):
            if f.get("protected"):
                status = f"{C['red']}\U0001f512{C['reset']}"
            elif f.get("cleanable"):
                status = f"{C['green']}\U0001f5d1\ufe0f{C['reset']}"
            else:
                status = "\U0001f4c4"
            img = f" [{f.get('image_format')}]" if f.get("image_format") else ""
            print(f"   {status} {i}. {f['name'][:30]:30s} {f['size_kb']:>8.2f} KB {img}")

    if result.get("empty_dirs"):
        print(f"\n\U0001f4c2 {_('empty_dirs_count')} ({len(result['empty_dirs'])})")
        for d in result["empty_dirs"][:5]:
            print(f"   \u2022 {d}")
        if len(result["empty_dirs"]) > 5:
            print(f"   ... {_('and_more').format(count=len(result['empty_dirs'])-5)}")

    recs = result.get("recommendations", [])
    if recs:
        print(f"\n\U0001f4a1 {_('optimization_suggestions')}:")
        for r in recs:
            print(f"   {r}")

    if result.get("warning"):
        print(f"\n{C['yellow']}\u26a0\ufe0f  警告: {result['warning']}{C['reset']}")

    print(f"\n{C['bright']}{'='*50}{C['reset']}")


def print_memory_analysis(result, format_type="text"):
    if format_type == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    print(f"\n{'='*50}")
    print(f"\U0001f9e0 {_('memory_analysis')} V{VERSION}")
    print(f"{'='*50}")
    print(f"\U0001f4c1 {_('workspace')}: {result.get('workspace', 'N/A')}")
    print()

    if "error" in result:
        print(f"\u274c {_('error')}: {result['error']}")
        return

    stats = result.get("stats", {})
    print(f"\U0001f4ca {_('memory_status')}:")
    print(f"   {_('total_files')}: {stats.get('total_files', 0)}")
    print(f"   {_('total_usage')}: {stats.get('total_size_kb', 0):.2f} KB")

    if result.get("files"):
        print(f"\n\U0001f4dd {_('file_list')}:")
        for f in result["files"][:20]:
            age = f.get("age_days", 0)
            status = "\U0001f195" if age <= RECENT_DAYS else "\U0001f4c5" if age <= OLD_DAYS else "\U0001f4c1"
            clean = "\U0001f5d1\ufe0f" if f.get("cleanable") else "  "
            print(f"   {status}{clean} {f['name']:30s} {f['size_kb']:>7.2f}KB  {f['modified']} ({age}{_('days_ago')})")

        if len(result["files"]) > 20:
            print(f"   ... {_('and_more').format(count=len(result['files'])-20)} {_('files')}")

    recs = result.get("recommendations", [])
    if recs:
        print(f"\n\U0001f4a1 {_('suggestions')}:")
        for r in recs:
            print(f"   {r}")

    # P2-5: 显示跨引用关系
    xrefs = result.get("cross_references", {})
    if xrefs:
        total_xrefs = sum(len(v) for v in xrefs.values())
        print(f"\n\U0001f517 {_('cross_references_title')} ({total_xrefs}):")
        for src, targets in sorted(xrefs.items())[:15]:
            target_str = ", ".join(f"[[{t}]]" for t in targets[:5])
            if len(targets) > 5:
                target_str += f" ... (+{len(targets)-5})"
            print(f"   {src} \u2192 {target_str}")
        if len(xrefs) > 15:
            print(f"   ... {_('and_more').format(count=len(xrefs)-15)}")

    print(f"\n{'='*50}")


def print_preview(preview):
    print(f"\n{'='*50}")
    print(f"\U0001f9f9 {_('clean_preview')} {'[Preview]' if preview.get('dry_run') else ''}")
    print(f"{'='*50}")

    if "error" in preview:
        print(f"\u274c {_('error')}: {preview['error']}")
        return

    files = preview.get("files_to_clean", [])
    print(f"{_('will_delete_n_files').format(count=len(files))} ({preview.get('total_size_kb', 0):.1f} KB)")
    print(f"{_('estimated_token_saving')}: ~{preview.get('token_saving', 0)}")
    print()

    for i, f in enumerate(files[:20], 1):
        print(f"   [{i}] {f['name'][:40]:40s} {f['size_kb']:>7.2f} KB")

    if len(files) > 20:
        print(f"   ... {_('and_more').format(count=len(files)-20)} {_('files')}")

    print(f"\n{preview.get('message', '')}")
    print(f"\n{'='*50}")


def generate_memory_report(workspace_path):
    workspace = Path(workspace_path)
    workbuddy_dir = workspace / ".workbuddy"
    memory_dir = workbuddy_dir / "memory"

    total_files = 0
    total_size_kb = 0.0
    total_tokens = 0
    cache_size_kb = 0.0
    by_type = {_("report_type_push_label"): 0, _("report_type_personal_work_label"): 0, _("report_type_other_label"): 0}
    by_date = {}
    recent_files = []
    old_files = []

    config = load_config()
    _rules = config.get("_automation_rules", DEFAULT_CONFIG["_automation_rules"])
    _TYPE_MAP = {"push": _("report_type_push_label"), "personal_work": _("report_type_personal_work_label"), "other": _("report_type_other_label")}

    # 懒导入避免循环依赖
    from .clean import classify_content

    if memory_dir.exists():
        for md_file in sorted(memory_dir.glob("*.md")):
            if md_file.name in ["MEMORY.md", "memory.md"]:
                continue
            total_files += 1
            try:
                size_kb = md_file.stat().st_size / 1024
                total_size_kb += size_kb
                mtime = datetime.fromtimestamp(md_file.stat().st_mtime)
                date_key = mtime.strftime("%Y-%m-%d")

                try:
                    raw_type = classify_content(md_file, _rules)
                    content_type = _TYPE_MAP.get(raw_type, _("report_type_other_label"))
                except Exception:
                    content_type = _("report_type_other_label")

                if date_key not in by_date:
                    by_date[date_key] = []
                by_date[date_key].append({
                    "name": md_file.name,
                    "size_kb": round(size_kb, 1),
                    "type": content_type,
                    "date": mtime.strftime("%Y-%m-%d %H:%M")
                })

                by_type[content_type] += 1

                days_old = (datetime.now() - mtime).days
                if days_old <= 7:
                    recent_files.append(md_file.name)
                elif days_old > 30:
                    old_files.append(md_file.name)

            except OSError:
                pass

    stats_dir = workbuddy_dir / ".token_stats"
    if stats_dir.exists():
        for stat_file in stats_dir.glob("*.json"):
            cache_size_kb += stat_file.stat().st_size / 1024
            try:
                stat_data = json.loads(stat_file.read_text(encoding="utf-8"))
                if isinstance(stat_data, dict):
                    for key in ["input_tokens", "output_tokens", "total_tokens"]:
                        if key in stat_data:
                            try:
                                total_tokens += int(stat_data[key])
                            except (ValueError, TypeError):
                                pass
            except (json.JSONDecodeError, OSError, IOError, AttributeError):
                pass
    summary_dir = workbuddy_dir / ".summary"
    if summary_dir.exists():
        for f in summary_dir.glob("*.summary"):
            cache_size_kb += f.stat().st_size / 1024

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    msg = f"""
{'='*55}
\U0001f4cb {_('report_title')}
{_('generate_time')}: {now}
{'='*55}

\U0001f4ca 【{_('report_memory_usage_stats')}】
   \u251c\u2500 {_('report_file_count')}: {total_files}
   \u251c\u2500 {_('report_disk_usage')}: {total_size_kb:.1f} KB
   \u251c\u2500 {_('report_token_usage')}: {'约 {:,}'.format(total_tokens) if total_tokens > 0 else _('cache_reminder_token_no_data')}
   \u251c\u2500 {_('report_cache_size')}: {cache_size_kb:.1f} KB
   \u2502
   \u251c\u2500 \U0001f534 {_('report_type_push')}: {by_type[_('report_type_push_label')]}
   \u251c\u2500 \U0001f7e1 {_('report_type_personal_work')}: {by_type[_('report_type_personal_work_label')]}
   \u2514\u2500 \U0001f7e2 {_('report_type_other')}: {by_type[_('report_type_other_label')]}

\U0001f4c1 【{_('file_list')} ({_('by_date')})】
"""
    if by_date:
        for date_key in sorted(by_date.keys(), reverse=True)[:10]:
            files = by_date[date_key]
            days_ago = (datetime.now() - datetime.strptime(date_key, "%Y-%m-%d")).days
            age_tag = f"({days_ago}{_('days_ago')})" if days_ago > 0 else _("recent_7_days").split(" ")[0] if _LANG == "zh" else "(today)"
            msg += f"\n   \U0001f4c5 {date_key} {age_tag}\n"
            for f in files[:5]:
                _push_label = _("report_type_push_label")
                _pw_label = _("report_type_personal_work_label")
                type_icon = "\U0001f534" if f['type'] == _push_label else "\U0001f7e1" if f['type'] == _pw_label else "\U0001f7e2"
                msg += f"      {type_icon} {f['name']} ({f['size_kb']}KB)\n"
            if len(files) > 5:
                more_text = _("and_more").format(count=len(files)-5)
                msg += f"      ... {more_text}\n"
    else:
        no_data = _("no_files_to_clean")
        msg += f"\n   ({no_data})\n"

    msg += f"""
{'='*55}
\U0001f4a1 【{_('additional_info')}】
"""
    if recent_files:
        recent_label = _("recent_7_days")
        msg += f"   \u2022 {recent_label}: {len(recent_files)}\n"
    if old_files:
        old_label = _("older_than_30_days")
        msg += f"   \u2022 {old_label}: {len(old_files)}\n"
        rec_text = _("recommend_archive")
        msg += f"   \u2022 {rec_text}\n"
    if cache_size_kb > MEMORY_LARGE_SIZE_KB:
        run_clean = _("run_cache_clean")
        msg += f"   \u2022 {run_clean}\n"
    msg += f"""
   \u2022 memory_manager.py stats / auto-clean / summarize
{'='*55}
"""

    print(msg)

    return {
        "total_files": total_files,
        "total_size_kb": round(total_size_kb, 1),
        "total_tokens": total_tokens,
        "cache_size_kb": round(cache_size_kb, 1),
        "by_type": by_type,
        "by_date": by_date,
        "recent_files_count": len(recent_files),
        "old_files_count": len(old_files)
    }
