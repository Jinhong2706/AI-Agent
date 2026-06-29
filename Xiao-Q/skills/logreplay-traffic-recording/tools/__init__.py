"""
@generated-by AI wenning
@generated-date 2026-04-02

LogReplay 本地工具包
导入所有工具模块以触发自动注册
"""
from __future__ import annotations  # added by AI wenning

# 导入各模块以触发 registry.register() 调用
from . import record  # noqa: F401  # 录制阶段工具
from . import replay  # noqa: F401  # 回放阶段工具
from .base import registry  # noqa: F401  # 工具注册中心
from .runner import ToolRunner, ToolCallResult  # noqa: F401  # 工具调用器


def get_all_tools() -> list[dict]:
    """获取所有已注册的本地工具定义"""
    return registry.get_tools()


def get_tool_executor(name: str):
    """根据工具名获取执行函数"""
    return registry.get_executor(name)


def create_runner(default_username: str = None) -> ToolRunner:
    """
    创建工具调用器实例（推荐入口）

    Args:
        default_username: 默认用户名，自动填充到 base_req.username

    Returns:
        ToolRunner 实例
    """
    return ToolRunner(default_username=default_username)


def main():
    """
    包级别命令行入口

    用法：
        python -m tools list
        python -m tools schema <tool_name>
        python -m tools call <tool_name> [json_args] [--username user]
    """
    from .runner import main as runner_main
    runner_main()
