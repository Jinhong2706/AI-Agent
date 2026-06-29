"""
@generated-by AI wenning
@generated-date 2026-04-02

LogReplay 工具调用器
提供统一的工具调用入口，封装工具查找、参数校验、执行和错误处理逻辑
"""
from __future__ import annotations  # added by AI wenning

import asyncio
import json
import logging
import time
from typing import Any, Optional

from .base import registry, AUTO_DETECT_VALIDATOR, current_tool_name

logger = logging.getLogger(__name__)


class ToolCallResult:
    """工具调用结果的统一封装"""

    def __init__(
        self,
        tool_name: str,
        success: bool,
        data: Any = None,
        error: Optional[str] = None,
        elapsed_ms: float = 0,
    ):
        self.tool_name = tool_name
        self.success = success
        self.data = data
        self.error = error
        self.elapsed_ms = elapsed_ms

    def to_dict(self) -> dict:
        """转换为字典"""
        result = {
            "tool_name": self.tool_name,
            "success": self.success,
            "elapsed_ms": round(self.elapsed_ms, 2),
        }
        if self.success:
            result["data"] = self.data
        else:
            result["error"] = self.error
        return result

    def to_json(self) -> str:
        """转换为 JSON 字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False)

    def __repr__(self) -> str:
        status = "OK" if self.success else "FAIL"
        return f"<ToolCallResult {self.tool_name} {status} {self.elapsed_ms:.0f}ms>"


class ToolRunner:
    """
    统一的工具调用器

    用法：
        runner = ToolRunner()

        # 异步调用
        result = await runner.run("MultiGetTaskStatus", {"task_ids": ["id1"]})

        # 同步调用
        result = runner.run_sync("MultiGetTaskStatus", {"task_ids": ["id1"]})

        # 批量调用
        results = await runner.run_batch([
            ("SearchReport", {"task_id": 123}),
            ("ReportAgg", {"type": 1, "task_id": 123}),
        ])
    """

    def __init__(self, default_username: Optional[str] = None):
        """
        初始化工具调用器

        Args:
            default_username: 默认用户名，自动填充到 base_req.username
        """
        self._default_username = default_username

    def list_tools(self) -> list[dict]:
        """
        列出所有已注册的工具

        Returns:
            工具定义列表，每项包含 name、description、required 字段
        """
        tools = registry.get_tools()
        summary = []
        for tool in tools:
            func = tool.get("function", {})
            params = func.get("parameters", {})
            summary.append({
                "name": func.get("name", ""),
                "description": func.get("description", ""),
                "required": params.get("required", []),
            })
        return summary

    def get_tool_schema(self, tool_name: str) -> Optional[dict]:
        """
        获取指定工具的完整 schema 定义

        Args:
            tool_name: 工具名称

        Returns:
            工具定义 dict，未找到返回 None
        """
        for tool in registry.get_tools():
            if tool.get("function", {}).get("name") == tool_name:
                return tool
        return None

    def validate_args(self, tool_name: str, args: dict) -> tuple[bool, Optional[str]]:
        """
        校验工具调用参数

        Args:
            tool_name: 工具名称
            args: 调用参数

        Returns:
            (是否合法, 错误信息)
        """
        schema = self.get_tool_schema(tool_name)
        if schema is None:
            return False, f"工具 '{tool_name}' 未注册"

        params = schema.get("function", {}).get("parameters", {})
        required_fields = params.get("required", [])

        # 校验必填参数
        missing = [f for f in required_fields if f not in args]
        if missing:
            return False, f"缺少必填参数: {', '.join(missing)}"

        return True, None

    def _inject_base_req(self, args: dict) -> dict:
        """
        自动注入 base_req.username（如果设置了默认用户名且参数中未提供）

        Args:
            args: 原始参数

        Returns:
            注入后的参数（不修改原始 dict）
        """
        if self._default_username is None:
            return args

        args = {**args}  # 浅拷贝，避免修改原始参数
        base_req = args.get("base_req", {})
        if not base_req.get("username"):
            base_req = {**base_req, "username": self._default_username}
            args["base_req"] = base_req

        return args

    async def run(
        self,
        tool_name: str,
        args: Optional[dict] = None,
        *,
        validate: bool = True,
        inject_username: bool = True,
    ) -> ToolCallResult:
        """
        异步调用指定工具

        Args:
            tool_name: 工具名称（必须与注册名完全一致）
            args: 调用参数
            validate: 是否在调用前校验参数（默认 True）
            inject_username: 是否自动注入 base_req.username（默认 True）

        Returns:
            ToolCallResult 调用结果
        """
        args = args or {}

        # 参数校验
        if validate:
            valid, err_msg = self.validate_args(tool_name, args)
            if not valid:
                return ToolCallResult(
                    tool_name=tool_name, success=False, error=err_msg
                )

        # 获取执行器
        executor = registry.get_executor(tool_name)
        if executor is None:
            return ToolCallResult(
                tool_name=tool_name,
                success=False,
                error=f"工具 '{tool_name}' 未注册或无执行器",
            )

        # 注入默认用户名
        if inject_username:
            args = self._inject_base_req(args)

        # 执行调用
        current_tool_name.set(tool_name)  # added by AI wenning
        start = time.monotonic()
        try:
            raw_result = await executor(args)
            elapsed = (time.monotonic() - start) * 1000

            # 解析 JSON 字符串结果
            if isinstance(raw_result, str):
                try:
                    data = json.loads(raw_result)
                except json.JSONDecodeError:
                    data = raw_result
            else:
                data = raw_result

            # === AI Generated Code Start lovli===
            # 业务层响应校验：优先使用注册时绑定的 validator，未绑定则自动探测
            if isinstance(data, dict):
                validator = registry.get_validator(tool_name) or AUTO_DETECT_VALIDATOR
                is_ok, error_msg = validator.validate(data)
                if not is_ok:
                    logger.warning(
                        "工具 %s 业务错误: %s", tool_name, error_msg,
                    )
                    return ToolCallResult(
                        tool_name=tool_name,
                        success=False,
                        data=data,
                        error=error_msg,
                        elapsed_ms=elapsed,
                    )
            # === AI Generated Code End lovli===

            logger.info("工具 %s 调用成功, 耗时 %.0fms", tool_name, elapsed)
            return ToolCallResult(
                tool_name=tool_name,
                success=True,
                data=data,
                elapsed_ms=elapsed,
            )

        except Exception as e:
            elapsed = (time.monotonic() - start) * 1000
            error_msg = f"{type(e).__name__}: {e}"
            logger.error("工具 %s 调用异常: %s", tool_name, error_msg)
            return ToolCallResult(
                tool_name=tool_name,
                success=False,
                error=error_msg,
                elapsed_ms=elapsed,
            )

    def run_sync(
        self,
        tool_name: str,
        args: Optional[dict] = None,
        **kwargs,
    ) -> ToolCallResult:
        """
        同步调用指定工具（内部创建事件循环执行异步调用）

        Args:
            tool_name: 工具名称
            args: 调用参数
            **kwargs: 传递给 run() 的其他参数

        Returns:
            ToolCallResult 调用结果
        """
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            # 已在事件循环中，创建新线程执行
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(
                    asyncio.run, self.run(tool_name, args, **kwargs)
                )
                return future.result()
        else:
            return asyncio.run(self.run(tool_name, args, **kwargs))

    async def run_batch(
        self,
        calls: list[tuple[str, Optional[dict]]],
        *,
        stop_on_error: bool = False,
        **kwargs,
    ) -> list[ToolCallResult]:
        """
        批量并发调用多个工具

        Args:
            calls: 调用列表，每项为 (tool_name, args) 元组
            stop_on_error: 遇到错误是否停止后续调用（默认 False，全部执行）
            **kwargs: 传递给 run() 的其他参数

        Returns:
            ToolCallResult 列表，顺序与 calls 一致
        """
        if stop_on_error:
            # 顺序执行，遇错停止
            results = []
            for tool_name, args in calls:
                result = await self.run(tool_name, args, **kwargs)
                results.append(result)
                if not result.success:
                    logger.warning(
                        "批量调用在 %s 处失败，停止后续调用", tool_name
                    )
                    break
            return results
        else:
            # 并发执行
            tasks = [
                self.run(tool_name, args, **kwargs)
                for tool_name, args in calls
            ]
            return await asyncio.gather(*tasks)


def main():
    """
    命令行入口，支持以下子命令：

        list                          列出所有已注册工具
        schema <tool_name>            查看指定工具的完整 schema
        call <tool_name> [json_args]  调用指定工具（参数为 JSON 字符串）

    用法：
        python -m tools list
        python -m tools schema SearchReport
        python -m tools call MultiGetTaskStatus '{"task_ids": ["id1"]}'
        python -m tools call ReportAgg '{"type": 1, "task_id": 123}' --username user1
        python -m tools call SearchReport -f input.json
        python -m tools call SearchReport '{"task_id": 123}' -o result.json
        python -m tools call SearchReport -f input.json -o result.json
    """
    import argparse
    import sys

    # 配置日志输出
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    parser = argparse.ArgumentParser(
        prog="logreplay-tools",
        description="LogReplay 本地工具命令行调用器",
    )
    parser.add_argument(
        "--username", "-u",
        default=None,
        help="默认用户名，自动填充到 base_req.username",
    )

    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # list 子命令
    subparsers.add_parser("list", help="列出所有已注册工具")

    # schema 子命令
    schema_parser = subparsers.add_parser("schema", help="查看指定工具的完整 schema")
    schema_parser.add_argument("tool_name", help="工具名称")

    # call 子命令
    call_parser = subparsers.add_parser("call", help="调用指定工具")
    call_parser.add_argument("tool_name", help="工具名称")
    call_parser.add_argument(
        "args_json",
        nargs="?",
        default="{}",
        help='调用参数（JSON 字符串），默认 "{}"',
    )
    # === AI Generated Code Start wenning ===
    call_parser.add_argument(
        "--input-file", "-f",
        default=None,
        help="从 JSON 文件读取调用参数（优先级高于 args_json）",
    )
    call_parser.add_argument(
        "--output-file", "-o",
        default=None,
        help="将调用结果输出到指定文件（JSON 格式）",
    )
    # === AI Generated Code End ===

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    runner = ToolRunner(default_username=args.username)

    if args.command == "list":
        tools = runner.list_tools()
        if not tools:
            print("暂无已注册工具")
            return
        print(f"已注册工具（共 {len(tools)} 个）：\n")
        for t in tools:
            required = ", ".join(t["required"]) if t["required"] else "无"
            print(f"  📌 {t['name']}")
            print(f"     描述: {t['description']}")
            print(f"     必填: {required}")
            print()

    elif args.command == "schema":
        schema = runner.get_tool_schema(args.tool_name)
        if schema is None:
            print(f"❌ 工具 '{args.tool_name}' 未找到")
            sys.exit(1)
        print(json.dumps(schema, indent=2, ensure_ascii=False))

    elif args.command == "call":
        # === AI Generated Code Start wenning ===
        # 从文件或命令行参数读取调用入参
        if args.input_file:
            try:
                with open(args.input_file, "r", encoding="utf-8") as f:
                    call_args = json.load(f)
            except FileNotFoundError:
                print(f"❌ 输入文件不存在: {args.input_file}")
                sys.exit(1)
            except json.JSONDecodeError as e:
                print(f"❌ 输入文件 JSON 解析失败: {e}")
                sys.exit(1)
        else:
            try:
                call_args = json.loads(args.args_json)
            except json.JSONDecodeError as e:
                print(f"❌ 参数 JSON 解析失败: {e}")
                sys.exit(1)

        result = runner.run_sync(args.tool_name, call_args)
        output_json = result.to_json()

        # 输出结果到文件或控制台
        if args.output_file:
            with open(args.output_file, "w", encoding="utf-8") as f:
                # 写入格式化的 JSON 便于阅读
                json.dump(result.to_dict(), f, ensure_ascii=False, indent=2)
            print(f"✅ 结果已写入: {args.output_file}")
        else:
            print(output_json)
        # === AI Generated Code End ===
        if not result.success:
            sys.exit(1)
