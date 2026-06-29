"""
@generated-by AI wenning
@generated-date 2026-04-02

允许通过 python -m tools 直接调用

用法：
    python -m tools list
    python -m tools schema <tool_name>
    python -m tools call <tool_name> [json_args] [--username user]
    python -m tools call <tool_name> -f input.json [-o result.json]
"""
from __future__ import annotations  # added by AI wenning

# 导入包以触发工具注册
from . import record  # noqa: F401
from . import replay  # noqa: F401
from .runner import main

if __name__ == "__main__":
    main()
