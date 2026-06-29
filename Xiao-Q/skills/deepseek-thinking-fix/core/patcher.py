"""
Patcher — 保留模块（仅供内部调试）
====================================
此模块已弃用（deprecated），保留仅用于向后兼容。

安全审查结论：
  本技能不包含任何自动 monkey-patch 机制。
  所有修复通过 Hermes 插件 hook 系统（register()）实现。
  auto_patch / enable / disable 功能已完全移除。

使用方式（推荐）：
  from deepseek_thinking_fix import register
  register(ctx)  # 通过 Hermes 插件系统注册
"""

import logging

logger = logging.getLogger(__name__)

# 所有 monkey-patch 功能已移除
# 请使用 register() 通过 Hermes hook 系统启用本技能

ENABLE_MESSAGE = (
    "⚠️ auto-patch 功能已移除。请通过 Hermes 插件系统安装本技能：\n"
    "  1. 将本包放入 ~/.hermes/plugins/deepseek-thinking-fix/\n"
    "  2. 在 config.yaml 中启用：plugins: { enabled: [deepseek-thinking-fix] }\n"
    "  3. 重启 Hermes"
)


def enable():
    """已弃用。通过 Hermes 插件系统安装。"""
    logger.warning(ENABLE_MESSAGE)
    print(ENABLE_MESSAGE)
    return False


def disable():
    """已弃用。无需操作。"""
    logger.info("auto-patch 功能已移除，无需禁用")


def get_patch_status():
    """返回状态信息"""
    return {
        "patched": False,
        "note": "monkey-patch 功能已移除。通过 Hermes hook 系统运行。",
    }
