"""
Hermes Plugin: DeepSeek Thinking Fix v2.2
==========================================

Drop-in fix for DeepSeek V4 Flash/Pro thinking mode 400 error.

安装：
    1. 将本包放入 Hermes 插件目录
    2. 在 config.yaml 中启用
    3. 重启 Hermes

所有修复通过 Hermes 插件 hook 系统（register()）实现。
不包含任何 monkey-patch 或自动文件操作。
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger("plugin.deepseek_fix")

# ─────── 从 core 包导入 ───────
from .core.sanitizer import MessageSanitizer
from .core.persistence import PersistenceSanitizer


# ─────── Hermes 插件注册入口 ───────


def register(ctx):
    """
    Hermes 插件注册函数。
    安装所有 hooks 和 tools。
    """
    logger.info("🧠 DeepSeek Thinking Fix v2.2 loading...")

    # 注册 hooks
    ctx.register_hook("before_api_call", before_api_call_hook)
    ctx.register_hook("after_session_load", after_session_load_hook)
    ctx.register_hook("before_session_store", before_session_store_hook)

    # 注册 tools
    ctx.register_tool(
        name="deepseek_fix_status",
        description="Check DeepSeek Thinking Fix plugin status and stats",
        handler=handle_status,
        schema={"type": "object", "properties": {}},
    )

    ctx.register_tool(
        name="deepseek_fix_migrate",
        description="修复已损坏的 Hermes session 数据库中的 reasoning_content 字段。需要提供 db_path 参数。",
        handler=handle_migrate,
        schema={
            "type": "object",
            "properties": {
                "db_path": {
                    "type": "string",
                    "description": "Hermes session 数据库的完整路径（必填，不自动检测）",
                }
            },
            "required": ["db_path"],
        },
    )

    logger.info("✅ DeepSeek Thinking Fix v2.2 loaded successfully")


# ─────── Hooks ───────


def before_api_call_hook(
    ctx, messages: List[Dict], provider: str, model: str, thinking: bool, **kwargs
) -> Dict:
    """
    核心 hook：在所有 API 调用前清洗消息。

    解决：
    - #14933, #15353, #16137 tool-call 消息缺 reasoning_content → 回填
    - #17400 间歇性丢失 → deepcopy 防状态突变
    - #15748 跨厂商泄漏 → 非 thinking 模型移除 RC
    - #15700 thinking=off → 显式传入 disabled
    """
    sanitizer = MessageSanitizer(provider, model, thinking)
    clean_messages = sanitizer.sanitize_for_api(messages)

    params = dict(kwargs)
    if thinking is False:
        params["thinking"] = {"type": "disabled"}

    return {"messages": clean_messages, **params}


def after_session_load_hook(ctx, messages: List[Dict]) -> List[Dict]:
    """
    会话加载后 hook：修复 reasoning_content 字段。
    解决 #16844, #17825 持久化字段名不一致问题。
    """
    return [PersistenceSanitizer.deserialize(m) for m in messages]


def before_session_store_hook(ctx, messages: List[Dict]) -> List[Dict]:
    """
    会话存储前 hook：同时保留 reasoning 和 reasoning_content。
    """
    return [PersistenceSanitizer.serialize(m) for m in messages]


# ─────── Tools ───────


def handle_status(ctx) -> str:
    """查看插件状态"""
    from .core.sanitizer import THINKING_PROVIDERS

    lines = [
        "🧠 DeepSeek Thinking Fix v2.2 — Status",
        "═══════════════════════════════════",
        f"  Monitored providers: {', '.join(THINKING_PROVIDERS)}",
        "",
        "  ✅ Hooks installed:",
        "    • before_api_call — backfill reasoning_content",
        "    • after_session_load — restore reasoning_content",
        "    • before_session_store — preserve reasoning_content",
        "",
        "  ✅ Tools registered:",
        "    • /deepseek_fix_status — this screen",
        "    • /deepseek_fix_migrate <db_path> — repair corrupted DB",
        "",
        "  ⚠️ 安全说明：",
        "    • 不包含任何 monkey-patch",
        "    • 不自动检测或扫描文件系统",
        "    • DB 迁移工具需要用户主动指定 db_path",
        "    • 迁移前自动备份原库并记录审计日志",
        "",
        "  Covered issues:",
        "    #14933, #15353, #16137, #15741 — tool-call + plain assistant",
        "    #17400 — intermittent failure (deep-copy protection)",
        "    #15213 — cron/auxiliary paths",
        "    #16844, #17825 — session persistence",
        "    #15748 — cross-provider field cleanup",
        "    #17052 — stale reasoning prevention",
        "    #15700 — explicit thinking:disabled",
        "    #17212 — direct API thinking control",
    ]
    return "\n".join(lines)


def handle_migrate(ctx, db_path: str) -> str:
    """
    修复已损坏的 session 数据库。

    注意：db_path 参数为必填，不会自动扫描文件系统。
    用户需明确指定目标数据库的完整路径。
    """
    import os

    if not db_path:
        return (
            "❌ 请提供 db_path 参数。例如：\n"
            '  /deepseek_fix_migrate db_path=~/.hermes/data/hermes.db\n'
            '  注意：不会自动扫描或猜测数据库位置。'
        )

    # 展开用户目录
    db_path = os.path.expanduser(db_path)

    if not os.path.exists(db_path):
        return f"❌ 文件不存在: {db_path}"

    if not db_path.endswith(".db"):
        logger.warning(f"指定路径不是 .db 文件: {db_path}")

    # dry_run 参数从 kwargs 中读取（Hermes 工具调用支持）
    dry_run = getattr(ctx, 'dry_run', True)

    try:
        fixed, backup = PersistenceSanitizer.migrate_database(
            db_path, dry_run=dry_run, backup=True
        )
    except Exception as e:
        return f"❌ 迁移失败: {e}"

    if dry_run:
        return (
            f"🔍 [DRY RUN] 将修复 {fixed} 条消息。\n"
            f"确认执行请添加 dry_run=false 参数：\n"
            f'  /deepseek_fix_migrate db_path={db_path} dry_run=false'
        )

    msg = f"✅ 数据库迁移完成：修复了 {fixed} 条消息。"
    if backup:
        msg += f" 备份: {backup}"
    return msg
