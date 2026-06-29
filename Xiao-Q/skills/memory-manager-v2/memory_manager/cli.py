# -*- coding: utf-8 -*-
"""
记忆管家 V3.0 - CLI入口、诊断
来源: memory_manager.py (main/CLI/doctor)
V3.0: 模块化重构
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from .config import (
    VERSION, _, _LANG, set_lang, get_colors,
    MEMORY_VERY_MANY_FILES, MEMORY_VERY_LARGE_SIZE_KB,
    DEFAULT_CONFIG,
    init_i18n, load_config, save_config, clear_config_cache,
    _get_workspace_config_path,
)
from .core import analyze_memory, search_memory, load_memory, rank_memory
from .summarize import summarize_memory
from .cache import cache_clean, cache_reminder
from .clean import (
    auto_clean_memory, archive_old_memory, dedup_memory,
    generate_cleanup_preview, scan_workspace, execute_cleanup,
)
from .io import export_memories, import_memories, backup_memory, restore_backup
from .report import (
    generate_memory_report, print_memory_analysis, print_preview
)
from .token import token_check, token_trends, compute_content_hash
from .prompt import list_prompts, get_prompt, save_prompt, search_prompts

init_i18n()


def _configure_stdio():
    """Avoid UnicodeEncodeError on Windows consoles with legacy encodings."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(errors="replace")
            except (OSError, ValueError):
                pass


_configure_stdio()


def _is_interactive_tty():
    """检测当前是否为交互式终端（非管道/重定向）"""
    try:
        return sys.stdin.isatty()
    except AttributeError:
        return False


def _require_confirmation(prompt_msg, agree=False, force=False):
    """安全的确认机制"""
    if agree and _is_interactive_tty():
        return True
    if force:
        return True
    if not _is_interactive_tty():
        print(f"\n\U0001f6ab 安全拒绝: 非交互式终端无法执行破坏性操作")
        print(f"   提示: 请在交互式终端中运行，或使用 --force 标志跳过确认")
        return False
    print(prompt_msg)
    try:
        user_input = input().strip()
    except EOFError:
        return False
    return user_input == "同意"


def _scan_memory_dir(memory_path):
    """P0-1 优化：单次扫描同时产出 md_files / symlinks / 哈希 / 重复 / 大文件。

    旧实现里 doctor_diagnose 调了 4 次 memory_path.glob + 多次重复 stat，
    这里一次 rglob + 单次 stat 解决。
    Returns:
        dict 或 None（目录不存在）
    """
    if not memory_path.exists() or not memory_path.is_dir():
        return None

    md_files = []
    total_size = 0
    file_hashes = {}        # hash -> first file
    duplicate_cnt = 0
    symlink_files = []
    oversized = []

    for entry in memory_path.rglob("*.md"):
        try:
            if entry.is_symlink():
                symlink_files.append(entry.name)
                continue
            stat = entry.stat()  # 单次 stat，多处复用
        except OSError:
            continue

        # 仅顶层 *.md 计入"文件数量 + 总大小"
        if entry.parent == memory_path:
            md_files.append(entry)
            total_size += stat.st_size
        else:
            md_files.append(entry)  # 子目录也算入"文件数量"警告

        # 异常大文件（> 500KB）
        if stat.st_size > 500 * 1024:
            oversized.append(f"{entry.name} ({stat.st_size // 1024}KB)")

        # 顶层去重（避开 MEMORY.md 自身）
        if entry.parent == memory_path and entry.name != "MEMORY.md":
            try:
                h = compute_content_hash(entry)
                if h in file_hashes:
                    duplicate_cnt += 1
                else:
                    file_hashes[h] = entry
            except Exception:
                pass

    return {
        "md_files": md_files,
        "total_size_kb": total_size / 1024,
        "duplicate_cnt": duplicate_cnt,
        "symlink_files": symlink_files,
        "oversized": oversized,
    }


def doctor_diagnose(workspace_path):
    base_path = Path(workspace_path).resolve()
    result = {
        "version": VERSION,
        "timestamp": datetime.now().isoformat(),
        "issues": [],
        "warnings": [],
        "passed": [],
        "score": 100
    }

    memory_path = base_path / ".workbuddy" / "memory"
    if not memory_path.exists():
        result["issues"].append({"type": "error", "item": "memory_dir", "message": _("memory_dir_not_exist_detail")})
        result["score"] -= 30
    else:
        result["passed"].append({"item": "记忆目录", "status": "正常"})
        try:
            list(memory_path.iterdir())  # 权限检查（轻量）
            result["passed"].append({"item": "访问权限", "status": "正常"})
        except (PermissionError, OSError) as e:
            result["issues"].append(
                {"type": "error", "item": "access", "message": _("memory_access_denied").format(error=str(e))})
            result["score"] -= 20

    # ===== P0-1：单次扫描替代原 4 次 glob =====
    scan = _scan_memory_dir(memory_path) if memory_path.exists() else None
    if scan is not None:
        md_files = scan["md_files"]
        total_size = scan["total_size_kb"]
        dup_count = scan["duplicate_cnt"]
        symlink_files = scan["symlink_files"]
        oversized = scan["oversized"]

        if len(md_files) > MEMORY_VERY_MANY_FILES:
            result["warnings"].append({"item": "文件数量", "message": f"记忆文件较多({len(md_files)}个)，建议清理或归档"})
            result["score"] -= 5

        if total_size > MEMORY_VERY_LARGE_SIZE_KB:
            result["warnings"].append({"item": "存储大小", "message": f"记忆占用较大({total_size:.1f}KB)，可能影响Token消耗"})
            result["score"] -= 5

        if dup_count > 0:
            result["warnings"].append({
                "item": "重复文件",
                "message": f"发现约 {dup_count} 个重复文件，建议运行 'python memory_manager.py dedup' 执行去重"
            })

        if symlink_files:
            result["warnings"].append({
                "item": "符号链接",
                "message": f"记忆目录下发现 {len(symlink_files)} 个符号链接: {', '.join(symlink_files[:5])}，可能存在安全风险"
            })
            result["score"] -= 5
        else:
            result["passed"].append({"item": "符号链接", "status": "无异常"})

        if oversized:
            result["warnings"].append({
                "item": "异常大文件",
                "message": f"记忆文件异常大: {', '.join(oversized[:5])}，建议检查内容"
            })
            result["score"] -= 5

    config = load_config()
    if not config:
        result["issues"].append({"type": "warning", "item": "配置文件", "message": "配置文件为空或损坏"})
        result["score"] -= 10
    else:
        result["passed"].append({"item": "配置文件", "status": "正常"})

    bp_cfg = config.get("_backup_config", {})
    if bp_cfg.get("local_path"):
        backup_path = Path(bp_cfg["local_path"])
        if not backup_path.exists():
            result["warnings"].append({"item": "备份路径", "message": f"配置的备份路径不存在: {backup_path}"})
        else:
            result["passed"].append({"item": "备份路径", "status": "正常"})
    else:
        result["warnings"].append({"item": "备份路径", "message": "未配置备份路径，建议设置以防数据丢失"})

    sched_cfg = config.get("_schedule_config", {})
    if sched_cfg.get("enabled"):
        result["passed"].append({"item": "定时任务", "status": "已启用"})
        for task_name, task_cfg in sched_cfg.get("tasks", {}).items():
            if not task_cfg.get("enabled"):
                result["warnings"].append({"item": f"任务 {task_name}", "message": "任务已禁用"})
    else:
        result["warnings"].append({"item": "定时任务", "message": "定时任务未启用，建议设置自动清理"})

    summary_path = base_path / ".workbuddy" / ".summary"
    if summary_path.exists():
        summary_files = list(summary_path.glob("*.summary"))
        result["passed"].append({"item": "摘要缓存", "status": f"{len(summary_files)} 个缓存"})
    else:
        result["warnings"].append({"item": "摘要缓存", "message": "未生成摘要缓存，建议运行 summarize 命令"})

    # ---- 安全自检项 ----
    # 1) 模块完整性：检查核心模块文件是否存在且可导入
    core_modules = ["core", "config", "clean", "io", "report", "token", "summarize", "cache", "cli"]
    pkg_dir = Path(__file__).parent
    missing_modules = [m for m in core_modules if not (pkg_dir / f"{m}.py").exists()]
    if missing_modules:
        result["issues"].append({
            "type": "error", "item": "模块完整性",
            "message": f"缺失核心模块: {', '.join(missing_modules)}，Skill 可能被篡改或损坏"
        })
        result["score"] -= 15
    else:
        result["passed"].append({"item": "模块完整性", "status": f"{len(core_modules)} 个模块完整"})

    # 3) 配置值域检查：检测配置中是否存在异常值
    if config:
        value_issues = []
        retention = config.get("retention_days", 1)
        if retention <= 0:
            value_issues.append(f"retention_days={retention} (应 >=1)")
        remind_days = config.get("auto_remind_days", 5)
        if remind_days <= 0 or remind_days > 365:
            value_issues.append(f"auto_remind_days={remind_days} (应在 1-365)")
        if value_issues:
            result["warnings"].append({
                "item": "配置值域",
                "message": f"发现异常配置值: {'; '.join(value_issues)}"
            })
            result["score"] -= 5
        else:
            result["passed"].append({"item": "配置值域", "status": "正常"})

    result["score"] = max(0, result["score"])
    return result


def _handle_doctor(args):
    """处理 doctor 诊断命令"""
    C = get_colors()
    res = doctor_diagnose(args.workspace)
    print(f"\n{C['bright']}{'='*50}{C['reset']}")
    print(f"{C['cyan']}\U0001f50d 记忆管家 V{VERSION} - 诊断报告{C['reset']}")
    print(f"{'='*50}")
    print(f"\n\U0001f4ca 健康评分: {C['yellow']}{res['score']}/100{C['reset']}")

    if res["issues"]:
        print(f"\n{C['red']}\u274c 问题 ({len(res['issues'])} 个):{C['reset']}")
        for issue in res["issues"]:
            print(f"   \u2022 [{issue['type']}] {issue['item']}: {issue['message']}")

    if res["warnings"]:
        print(f"\n{C['yellow']}\u26a0\ufe0f  警告 ({len(res['warnings'])} 个):{C['reset']}")
        for warn in res["warnings"]:
            print(f"   \u2022 {warn['item']}: {warn['message']}")

    if res["passed"]:
        print(f"\n{C['green']}\u2705 正常 ({len(res['passed'])} 项):{C['reset']}")
        for item in res["passed"][:5]:
            print(f"   \u2713 {item['item']}: {item['status']}")
        if len(res["passed"]) > 5:
            print(f"   ... 还有 {len(res['passed'])-5} 项")

    print(f"\n{'='*50}")
    return res


def _handle_dedup(args):
    """处理 dedup 去重命令"""
    C = get_colors()
    res = dedup_memory(args.workspace, dry_run=not args.execute, delete_dup=args.execute)
    print("\n总文件: %d | 唯一: %d | 重复: %d | 可回收: %.1fKB" % (
        res.get("total_files", 0), res.get("unique_files", 0),
        res.get("duplicates_found", 0), res.get("space_saved_kb", 0)))
    if res.get("duplicate_groups"):
        print("\n重复组（前5组）:")
        for g in res["duplicate_groups"][:5]:
            print("  原始: %s (%s)" % (g["original"]["name"], g["original"]["modified"]))
            print("  重复: %s" % ", ".join(d["name"] for d in g["duplicates"]))
    if not args.execute and res.get("duplicates_found", 0) > 0:
        print("\n[提示] 使用 --execute 确认删除")
    elif args.execute and res.get("duplicates_found", 0) > 0:
        if _require_confirmation(
            f"\n{C['yellow']}\u26a0\ufe0f  将删除 {res['duplicates_found']} 个重复文件（不可恢复）{''}\n"
            f"{C['yellow']}回复「同意」确认删除:{''}",
            agree=getattr(args, 'agree', False),
            force=getattr(args, 'force', False),
        ):
            res = dedup_memory(args.workspace, dry_run=False, delete_dup=True)
            print(f"\n{C['green']}\u2705 已删除 {res['duplicates_found']} 个重复文件，释放 {res['space_saved_kb']:.1f}KB{''}")
        else:
            print(f"\n{C['yellow']}\u274c 已取消{''}")
    return res


def _handle_backup(args):
    """处理 backup 备份/恢复命令"""
    if args.restore:
        res = restore_backup(args.workspace, backup_path=args.path, dry_run=not args.execute)
        print("\n恢复结果: 已恢复文件数 = %d" % res.get("files_restored", 0))
    else:
        res = backup_memory(args.workspace, backup_path=args.path, dry_run=not args.execute)
        print("\n备份路径: %s | 新增: %d | 更新: %d | 大小: %.1fKB" % (
            res.get("backup_path", ""), res.get("files_copied", 0),
            res.get("files_updated", 0), res.get("total_size_kb", 0)))
    return res


def main():
    parser = argparse.ArgumentParser(
        description=f"记忆管家 V{VERSION} - WorkBuddy 记忆层管理专家",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python memory_manager.py analyze /path/to/workspace
  python memory_manager.py search "关键词" /path/to/workspace
  python memory_manager.py load /path/to/workspace --days 7
        """
    )

    parser.add_argument("--version", action="version", version=f"记忆管家 V{VERSION}")
    parser.add_argument("--lang", choices=["zh", "en"], default="zh", help="界面语言")

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    analyze_parser = subparsers.add_parser("analyze", help="分析记忆存储")
    analyze_parser.add_argument("workspace")
    analyze_parser.add_argument("--json", action="store_true", help="JSON格式输出")

    search_parser = subparsers.add_parser("search", help="搜索记忆")
    search_parser.add_argument("keyword")
    search_parser.add_argument("workspace")
    search_parser.add_argument("--tag", type=str, help="按标签过滤")
    search_parser.add_argument("--folder", type=str, help="按子目录过滤")
    search_parser.add_argument("--tfidf", action="store_true", help="启用 TF-IDF 语义搜索增强")

    load_parser = subparsers.add_parser("load", help="加载记忆")
    load_parser.add_argument("workspace")
    load_parser.add_argument("--mode", choices=["brief", "normal", "full"], default="normal")
    load_parser.add_argument("--days", type=int, help="只加载N天内的记忆")

    rank_parser = subparsers.add_parser("rank", help="记忆分级")
    rank_parser.add_argument("workspace")
    rank_parser.add_argument("--days", type=int, help="只分析N天内的文件")

    summarize_parser = subparsers.add_parser("summarize", help="生成摘要")
    summarize_parser.add_argument("workspace")

    report_parser = subparsers.add_parser("report", help="生成报告")
    report_parser.add_argument("workspace")

    cache_parser = subparsers.add_parser("cache-reminder", help="缓存提醒")
    cache_parser.add_argument("workspace")

    clean_cache_parser = subparsers.add_parser("cache-clean", help="清理缓存")
    clean_cache_parser.add_argument("workspace")
    clean_cache_parser.add_argument("--execute", action="store_true")
    clean_cache_parser.add_argument("--agree", action="store_true", help="跳过确认提示（需交互式终端）")
    clean_cache_parser.add_argument("--force", action="store_true", help="强制执行（允许非交互式终端）")

    clean_parser = subparsers.add_parser("clean", help="清理工作空间")
    clean_parser.add_argument("workspace")
    clean_parser.add_argument("--execute", action="store_true")
    clean_parser.add_argument("--agree", action="store_true", help="跳过确认提示（需交互式终端）")
    clean_parser.add_argument("--force", action="store_true", help="强制执行（允许非交互式终端）")

    archive_parser = subparsers.add_parser("archive", help="归档旧记忆")
    archive_parser.add_argument("workspace")
    archive_parser.add_argument("--days", type=int, default=30)
    archive_parser.add_argument("--execute", action="store_true")
    archive_parser.add_argument("--agree", action="store_true", help="跳过确认提示（需交互式终端）")
    archive_parser.add_argument("--force", action="store_true", help="强制执行（允许非交互式终端）")

    auto_clean_parser = subparsers.add_parser("auto-clean", help="差异清理")
    auto_clean_parser.add_argument("workspace")
    auto_clean_parser.add_argument("--filter", choices=["push", "personal_work", "other", "all"])
    auto_clean_parser.add_argument("--execute", action="store_true")
    auto_clean_parser.add_argument("--agree", action="store_true", help="跳过确认提示（需交互式终端）")
    auto_clean_parser.add_argument("--force", action="store_true", help="强制执行（允许非交互式终端）")

    export_parser = subparsers.add_parser("export", help="导出记忆")
    export_parser.add_argument("workspace")
    export_parser.add_argument("output")
    export_parser.add_argument("--encrypt", action="store_true", help="使用 AES-256-GCM 加密导出")
    export_parser.add_argument("--password", type=str, help="加密密码（也可通过环境变量 MEMORY_MANAGER_PASSWORD 设置）")

    import_parser = subparsers.add_parser("import", help="导入记忆")
    import_parser.add_argument("workspace")
    import_parser.add_argument("input")
    import_parser.add_argument("--confirm", action="store_true", help="确认导入记忆数据")

    config_parser = subparsers.add_parser("config", help="配置管理")
    config_parser.add_argument("workspace", nargs='?', default=None)
    config_parser.add_argument("--set-key", dest="key", type=str)
    config_parser.add_argument("--set-value", dest="value", type=str)

    token_parser = subparsers.add_parser("token-check", help="Token预算检查")
    token_parser.add_argument("workspace")

    trends_parser = subparsers.add_parser("token-trends", help="Token使用趋势(按日/周/月)")
    trends_parser.add_argument("workspace")
    trends_parser.add_argument("--period", choices=["daily", "week", "month"], default="week",
                               help="聚合周期: daily/week/month")
    trends_parser.add_argument("--days", type=int, default=None, help="回溯天数")

    scan_parser = subparsers.add_parser("scan", help="扫描工作空间")
    scan_parser.add_argument("workspace")

    # ---- V2.5+ 兼容命令 ----
    doctor_parser = subparsers.add_parser("doctor", help="诊断工具 - 检测配置异常和潜在问题")
    doctor_parser.add_argument("workspace")

    dedup_parser = subparsers.add_parser("dedup", help="基于内容哈希去重")
    dedup_parser.add_argument("workspace")
    dedup_parser.add_argument("--execute", action="store_true", help="执行去重")
    dedup_parser.add_argument("--agree", action="store_true", help="跳过确认提示（需交互式终端）")
    dedup_parser.add_argument("--force", action="store_true", help="强制执行（允许非交互式终端）")

    backup_parser = subparsers.add_parser("backup", help="备份/恢复")
    backup_parser.add_argument("workspace")
    backup_parser.add_argument("--path", type=str, help="备份目录")
    backup_parser.add_argument("--execute", action="store_true", help="执行备份")
    backup_parser.add_argument("--restore", action="store_true", help="从备份恢复")

    # ---- Prompt 模板管理 ----
    prompt_list_parser = subparsers.add_parser("prompt-list", help="列出Prompt模板")
    prompt_list_parser.add_argument("workspace")
    prompt_list_parser.add_argument("--tag", type=str, help="按标签过滤")

    prompt_get_parser = subparsers.add_parser("prompt-get", help="获取Prompt模板内容")
    prompt_get_parser.add_argument("name", help="模板名称")
    prompt_get_parser.add_argument("workspace")

    prompt_save_parser = subparsers.add_parser("prompt-save", help="保存Prompt模板")
    prompt_save_parser.add_argument("name", help="模板名称")
    prompt_save_parser.add_argument("workspace")
    prompt_save_parser.add_argument("--content", type=str, required=True, help="Prompt内容")
    prompt_save_parser.add_argument("--tags", type=str, help="标签（逗号分隔）")
    prompt_save_parser.add_argument("--description", type=str, default="", help="描述")
    prompt_save_parser.add_argument("--category", type=str, default="", help="分类/子目录")

    prompt_search_parser = subparsers.add_parser("prompt-search", help="搜索Prompt模板")
    prompt_search_parser.add_argument("workspace")
    prompt_search_parser.add_argument("--keyword", type=str, help="关键词")
    prompt_search_parser.add_argument("--tag", type=str, help="按标签过滤")

    args = parser.parse_args()

    if hasattr(args, 'lang') and args.lang:
        set_lang(args.lang)

    if not args.command:
        parser.print_help()
        return 1

    # ---- 兼容命令路由 ----
    if args.command == "doctor":
        _handle_doctor(args)
        return 0
    elif args.command == "dedup":
        _handle_dedup(args)
        return 0
    elif args.command == "backup":
        _handle_backup(args)
        return 0

    # ---- 核心命令路由 ----
    C = get_colors()
    if args.command == "analyze":
        result = analyze_memory(args.workspace)
        print_memory_analysis(result, format_type="json" if getattr(args, 'json', False) else "text")

    elif args.command == "search":
        tag = getattr(args, 'tag', None)
        folder = getattr(args, 'folder', None)
        use_tfidf = getattr(args, 'tfidf', False)
        result = search_memory(args.workspace, args.keyword, tag=tag, folder=folder, use_tfidf=use_tfidf)
        if getattr(args, 'json', False):
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            tag_info = f" [tag={tag}]" if tag else ""
            folder_info = f" [folder={folder}]" if folder else ""
            tfidf_info = " [tfidf]" if use_tfidf else ""
            print(f"\n{C['bright']}\U0001f50d 搜索结果: \"{args.keyword}\"{tag_info}{folder_info}{tfidf_info} ({result['total']} 个匹配){C['reset']}")
            for i, m in enumerate(result["matches"][:10], 1):
                tags_str = f" [{','.join(m['tags'])}]" if m.get('tags') else ""
                tfidf_str = f" TF-IDF:{m['tfidf_score']:.2f}" if m.get('tfidf_score') is not None else ""
                print(f"   [{i}] {m['file']}{tags_str} (评分:{m['score']}{tfidf_str}) {m['modified']}")

    elif args.command == "load":
        result = load_memory(args.workspace, mode=args.mode, days=getattr(args, 'days', None))
        if getattr(args, 'json', False):
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"\n{C['bright']}\U0001f4da 加载记忆 ({len(result['loaded'])} 个文件){C['reset']}")
            print(f"   预估Token: {result['total_tokens_estimate']}")
            for item in result["loaded"][:10]:
                print(f"   \u2022 {item['file']} ({item['type']}) {item.get('keywords', [])}")

    elif args.command == "rank":
        _handle_rank_display(args, C)

    elif args.command == "summarize":
        result = summarize_memory(args.workspace)
        print(f"\n\U0001f4dd 摘要生成完成: {len(result['summarized'])} 个文件")

    elif args.command == "report":
        generate_memory_report(args.workspace)

    elif args.command == "cache-reminder":
        cache_reminder(args.workspace)

    elif args.command == "cache-clean":
        agree = getattr(args, 'agree', False)
        force = getattr(args, 'force', False)
        cache_clean(args.workspace, dry_run=not getattr(args, 'execute', False),
                    confirm=agree or force or getattr(args, 'execute', False), cache_type='all')

    elif args.command == "clean":
        preview = generate_cleanup_preview(args.workspace, dry_run=True)
        print_preview(preview)

        if getattr(args, 'execute', False):
            if _require_confirmation(
                f"\n{C['yellow']}\u26a0\ufe0f  将永久删除 {len(preview.get('files_to_clean', []))} 个文件（不可恢复）{''}\n"
                f"{C['yellow']}回复「同意」确认删除:{''}",
                agree=getattr(args, 'agree', False),
                force=getattr(args, 'force', False),
            ):
                exec_result = execute_cleanup(args.workspace, confirm=True)
                print(f"\n{C['green']}\u2705 已删除 {exec_result['deleted_count']} 个文件，释放 {exec_result['deleted_size_kb']:.1f}KB{''}")
            else:
                print(f"\n{C['yellow']}\u274c 已取消{''}")

    elif args.command == "archive":
        confirm = getattr(args, 'execute', False) or getattr(args, 'agree', False) or getattr(args, 'force', False)
        result = archive_old_memory(args.workspace, args.days, confirm=confirm)
        print(f"\n归档结果: 已归档 {result['archived_count']} 个文件 ({result['archived_size_kb']:.1f}KB)")
        print(f"归档位置: {result['archive_path']}")

    elif args.command == "auto-clean":
        content_filter = getattr(args, 'filter', None)
        confirm_action = getattr(args, 'execute', False) or getattr(args, 'agree', False) or getattr(args, 'force', False)
        result = auto_clean_memory(args.workspace, dry_run=not confirm_action,
                                   content_filter=content_filter, confirm_action=confirm_action)

        print(f"\n{C['bright']}{'='*50}{C['reset']}")
        print(f"{C['cyan']}\U0001f9f9 {_('differential_auto_clean')}{C['reset']}")
        print(f"{'='*50}")
        print(f"\U0001f4ca 推送类(>1天强制清理): {result['clean_summary']['push_to_remind']} 个")
        print(f"\U0001f4ca 个人/工作(>5天提醒): {result['clean_summary']['personal_work_to_remind']} 个")
        print(f"\U0001f4ca 其他(>1天提醒): {result['clean_summary']['other_to_remind']} 个")

        total_remind = sum(result["clean_summary"].values())
        total_kept = len(result["kept_files"])

        if total_remind > 0:
            print(f"\n{C['yellow']}提醒清理 ({total_remind} 个文件):{''}")
            for f in result.get("remind_files", []):
                print(f"   \u2022 {f['name']} ({f['age_days']}天前) [{f['type']}]")
        print(f"\n{C['green']}保留 ({total_kept} 个文件):{''}")
        for f in result.get("kept_files", []):
            print(f"   \u2713 {f['name']} {f.get('reason', '')}")

    elif args.command == "export":
        encrypt = getattr(args, 'encrypt', False)
        password = getattr(args, 'password', None)
        result = export_memories(args.workspace, args.output, encrypt=encrypt, password=password)
        if "error" in result:
            print(f"\u274c {result['error']}")
        else:
            enc_label = " \U0001f512" if result.get('encrypted') else ""
            print(f"\u2705{enc_label} {result.get('message', '导出完成')} {result['exported_file']} ({result['size_kb']}KB)")

    elif args.command == "import":
        if not getattr(args, "confirm", False):
            print("[ERROR] import writes memory files. Re-run with --confirm after verifying the archive.")
            return 2
        result = import_memories(args.workspace, args.input)
        print(f"导入完成: {result.get('imported_files', 0)} 个文件, {result.get('imported_summaries', 0)} 个摘要")

    elif args.command == "config":
        config = load_config()
        if hasattr(args, 'key') and args.key and hasattr(args, 'value') and args.value:
            from .config import config_memory
            result = config_memory(args.workspace, key=args.key, value=args.value)
            print(f"\n配置已更新: {args.key} = {args.value}")
        else:
            print(f"\n当前配置:")
            for k, v in sorted(config.items()):
                print(f"  {k}: {v}")

    elif args.command == "token-check":
        result = token_check(args.workspace)
        print(f"\n{result['emoji']} {result['message']}")
        print(f"   今日消耗: {result['today_tokens']:,} tokens")
        print(f"   预算: {result['budget']:,} tokens")
        print(f"   使用率: {result['ratio']*100:.1f}%")

    elif args.command == "token-trends":
        period = getattr(args, 'period', 'week')
        days_back = getattr(args, 'days', None)
        result = token_trends(args.workspace, period=period, days_back=days_back)
        period_label = {"daily": "日", "week": "周", "month": "月"}.get(period, period)
        print(f"\n{C['cyan']}\U0001f4ca {_('token_trends_header').format(period=period_label)}{C['reset']}")
        print(f"{'='*50}")
        totals = result.get("totals", {})
        if totals.get("days_with_data", 0) == 0:
            print(f"   {_('token_trends_no_data')}")
        else:
            print(f"   {_('token_trends_total')}: {totals['total_tokens']:,} tokens")
            print(f"   {_('token_trends_daily_avg')}: {totals['avg_daily_tokens']:,} tokens")
            print(f"   {_('token_trends_ops')}: {totals['total_operations']:,}")
            print()
            for agg in result.get("aggregated", []):
                label = agg.get("label", "")
                tokens = agg.get("tokens", 0)
                ops = agg.get("operations_count", 0)
                bar_len = min(int(tokens / max(totals['avg_daily_tokens'], 1) * 10), 40)
                bar = "\u2588" * max(bar_len, 1)
                print(f"   {label:>12s} | {bar} {tokens:,} ({ops} ops)")
        print(f"{'='*50}")

    elif args.command == "scan":
        result = scan_workspace(args.workspace)
        from .report import print_report
        print_report(result)

    # ---- Prompt 模板管理 ----
    elif args.command == "prompt-list":
        result = list_prompts(args.workspace, tag=getattr(args, 'tag', None))
        if result["total"] == 0:
            print(f"\n{C['yellow']}\U0001f4cb 暂无Prompt模板{C['reset']}")
            print(f"   提示: 使用 prompt-save 保存第一个模板")
        else:
            print(f"\n{C['bright']}\U0001f4cb Prompt模板清单 ({result['total']} 个){C['reset']}")
            print(f"{'='*50}")
            for p in result["prompts"]:
                tags_str = f" [{','.join(p['tags'])}]" if p.get('tags') else ""
                desc = f" - {p['description']}" if p.get('description') else ""
                print(f"   \U0001f4dd {p['name']}{tags_str}{desc}")
                print(f"      版本:{p['version']} | 修改:{p['modified']} | {p['size_kb']:.1f}KB")

    elif args.command == "prompt-get":
        result = get_prompt(args.workspace, args.name)
        if not result.get("found"):
            print(f"\n{C['red']}\u274c {result.get('error', '未找到模板')}{C['reset']}")
        else:
            print(f"\n{C['bright']}\U0001f4dd {result['name']}{C['reset']}")
            tags_str = f" [{','.join(result['tags'])}]" if result.get('tags') else ""
            print(f"   标签:{tags_str} | 版本:{result['version']}")
            print(f"{'='*50}")
            print(result["content"])

    elif args.command == "prompt-save":
        tags = [t.strip() for t in args.tags.split(",")] if getattr(args, 'tags', None) else None
        result = save_prompt(
            args.workspace, args.name,
            content=args.content,
            tags=tags,
            description=getattr(args, 'description', ''),
            category=getattr(args, 'category', ''),
        )
        if result.get("saved"):
            print(f"\n{C['green']}\u2705 Prompt模板已保存: {result['name']} (v{result['version']}){C['reset']}")
            if result.get('tags'):
                print(f"   标签: [{', '.join(result['tags'])}]")
        else:
            print(f"\n{C['red']}\u274c 保存失败: {result.get('error', '未知错误')}{C['reset']}")

    elif args.command == "prompt-search":
        result = search_prompts(
            args.workspace,
            keyword=getattr(args, 'keyword', None),
            tag=getattr(args, 'tag', None),
        )
        if result["total"] == 0:
            print(f"\n{C['yellow']}\U0001f50d 未找到匹配的Prompt模板{C['reset']}")
        else:
            print(f"\n{C['bright']}\U0001f50d Prompt搜索结果 ({result['total']} 个){C['reset']}")
            for p in result["prompts"]:
                tags_str = f" [{','.join(p['tags'])}]" if p.get('tags') else ""
                score_str = f" (匹配:{p['score']})" if p.get('score') else ""
                print(f"   \U0001f4dd {p['name']}{tags_str}{score_str}")

    return 0


def _handle_rank_display(args, C=None):
    if C is None:
        C = get_colors()
    result = rank_memory(args.workspace, days=getattr(args, 'days', None))

    print(f"\n{C['bright']}{'='*50}{C['reset']}")
    print(f"{C['cyan']}\U0001f4ca 记忆文件重要性分级报告{C['reset']}")
    print(f"{C['bright']}{'='*50}{C['reset']}")

    core_items = result.get("core", [])
    normal_items = result.get("normal", [])
    cold_items = result.get("cold", [])

    if core_items:
        print(f"\n{C['green']}\U0001f534 核心记忆 ({len(core_items)} 个){C['reset']}")
        for i, item in enumerate(core_items[:10], 1):
            print(f"   [{i}] {item['file']} (评分:{item['score']:.1f})")
            if i >= 10 and len(core_items) > 10:
                print(f"   ... 还有 {len(core_items) - 10} 个")
                break

    if normal_items:
        print(f"\n{C['yellow']}\U0001f7e1 普通记忆 ({len(normal_items)} 个){C['reset']}")
        for i, item in enumerate(normal_items[:5], 1):
            print(f"   [{i}] {item['file']} (评分:{item['score']:.1f})")
        if len(normal_items) > 5:
            print(f"   ... 还有 {len(normal_items) - 5} 个")

    if cold_items:
        print(f"\n{C['cyan']}\U0001f7e2 冷记忆 ({len(cold_items)} 个){C['reset']}")
        for i, item in enumerate(cold_items[:5], 1):
            print(f"   [{i}] {item['file']} (评分:{item['score']:.1f})")
        if len(cold_items) > 5:
            print(f"   ... 还有 {len(cold_items) - 5} 个")

    if not any([core_items, normal_items, cold_items]):
        print(f"\n{C['yellow']}\U0001f4c2 记忆目录中暂无可用文件{C['reset']}")

    print(f"\n统计: 总计{result['stats'].get('total', 0)}个文件")
    print(f"{'=' * 50}")

    return result


if __name__ == "__main__":
    sys.exit(main())
