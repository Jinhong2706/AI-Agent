"""
@generated-by AI: lovli
@generated-date 2026-04-02

回放阶段本地工具
包含：SearchReport、ReportAgg、SearchResponse、TwoEnvReplayResultSearch、ExecuteReplay、GetReplayTaskInfo、
      TaskList、DiffConfig、SetDiffConfig、
      QueryEditRuleList、CreateEditRule、UpdateEditRule、DeleteEditRule、EditRuleCheck、
      GetFlow2SceneTaskList、GenerateTestPlanByTrafficData
"""
from __future__ import annotations  # added by AI wenning

import json
import logging
from typing import Any

from .base import (
    HttpCaller,
    get_app_server_detail,
    get_default,
    get_default_nano_time_range,
    get_default_str_time_range,
    get_env_name_by_project_id,
    get_perf_auth_headers,
    get_url,
    get_user_context,
    make_tool_definition,
    registry,
    resolve_logreplay_prereqs,
    # API 路径常量
    API_REPORT_SEARCH,
    API_REPORT_AGG,
    API_RECORD_SEARCH_RESPONSE,
    API_REPLAY_SEARCH,  # added by AI: lovli
    API_EXECUTE_REPLAY,
    API_GET_REPLAY_TASK_INFO,
    API_TASK_LIST,
    API_DIFF_CONFIG,
    API_SET_DIFF_CONFIG,
    API_QUERY_EDIT_RULE_LIST,
    API_EDIT_RULE_CHECK,
    API_CREATE_EDIT_RULE,
    API_UPDATE_EDIT_RULE,
    API_DELETE_EDIT_RULE,
    API_GET_FLOW2_SCENE_TASK_LIST,
    API_CREATE_FLOW2_SCENE,
)

logger = logging.getLogger(__name__)


# ===================== SearchReport =====================

# === AI Generated Code Start lovli===

SEARCH_REPORT_DEF = make_tool_definition(
    name="SearchReport",
    description="回放报告详细查看",
    parameters={
        "type": "object",
        "properties": {
            "app_server_name": {"type": "string", "description": "服务名称，格式 app.server"},
            "task_id": {"type": "integer", "description": "任务ID"},
            "api_name": {"type": "string", "description": "接口名"},
            "result": {"type": "integer", "description": "diff结果，1：成功，2：错误，3：失败"},
            "error_field": {"type": "string", "description": "错误字段名"},
            "reason": {"type": "string", "description": "错误原因"},
            "trace_id": {"type": "string", "description": "TraceID"},
            "page": {"type": "integer", "description": "页码"},
            "page_size": {"type": "integer", "description": "每页大小"},
            "mock_aspect_flag": {"type": "string", "description": "切面mock失败标识"},
            "replay_tag": {
                "type": "object",
                "additionalProperties": {"type": "string"},
                "description": "回放数据tag",
            },
            "includes": {"type": "array", "items": {"type": "string"}, "description": "返回字段包含"},
            "excludes": {"type": "array", "items": {"type": "string"}, "description": "返回字段排除"},
            "regexp_fields": {
                "type": "array",
                "items": {"type": "string"},
                "description": "正则检索字段，支持：api_name、error_field、reason",
            },
        },
        "required": ["app_server_name", "task_id"],
    },
)


async def execute_search_report(input_args: dict[str, Any]) -> str:
    """回放报告详细查看"""
    app_server_name = input_args["app_server_name"]
    _module_id, auth_headers, uctx = await resolve_logreplay_prereqs(app_server_name)

    request_body = {
        "base_req": {"username": uctx["user_id"]},
        "page_req": {
            "page": input_args.get("page", 1),
            "page_size": input_args.get("page_size", 20),
        },
        "task_id": input_args.get("task_id"),
        "api_name": input_args.get("api_name", ""),
        "result": input_args.get("result", 0),
        "error_field": input_args.get("error_field", ""),
        "reason": input_args.get("reason", ""),
        "trace_id": input_args.get("trace_id", ""),
        "mock_aspect_flag": input_args.get("mock_aspect_flag", ""),
        "replay_tag": input_args.get("replay_tag", {}),
        "includes": input_args.get("includes", []),
        "excludes": input_args.get("excludes", []),
        "regexp_fields": input_args.get("regexp_fields", []),
    }

    caller = HttpCaller()
    result = await caller.call(
        request_body=request_body,
        host=get_url("logreplay"),
        path=API_REPORT_SEARCH,
        extra_headers=auth_headers,
    )
    return json.dumps(result, ensure_ascii=False)

# === AI Generated Code End lovli===


# ===================== ReportAgg =====================

# === AI Generated Code Start lovli===

REPORT_AGG_DEF = make_tool_definition(
    name="ReportAgg",
    description="回放报告聚合查询",
    parameters={
        "type": "object",
        "properties": {
            "app_server_name": {"type": "string", "description": "服务名称，格式 app.server"},
            "type": {
                "type": "integer",
                "description": "聚合类型：0-Default，1-APIName，2-ErrorField，3-Reason，4-TraceID，5-ReplayTag",
                "enum": [0, 1, 2, 3, 4, 5],
            },
            "task_id": {"type": "integer", "description": "回放任务ID"},
            "api_name": {"type": "string", "description": "接口名"},
            "result": {"type": "integer", "description": "diff结果"},
            "error_field": {"type": "string", "description": "字段名"},
            "trace_id": {"type": "string", "description": "TraceID"},
            "mock_aspect_flag": {"type": "string", "description": "切面mock失败标识"},
            "replay_tag": {
                "type": "object",
                "additionalProperties": {"type": "string"},
                "description": "回放数据tag",
            },
            "tag_agg": {"type": "array", "items": {"type": "string"}, "description": "回放tag聚合字段"},
        },
        "required": ["app_server_name", "type", "task_id"],
    },
)


async def execute_report_agg(input_args: dict[str, Any]) -> str:
    """回放报告聚合查询"""
    app_server_name = input_args["app_server_name"]
    _module_id, auth_headers, uctx = await resolve_logreplay_prereqs(app_server_name)

    request_body = {
        "base_req": {"username": uctx["user_id"]},
        "type": input_args.get("type"),
        "task_id": input_args.get("task_id"),
        "api_name": input_args.get("api_name", ""),
        "result": input_args.get("result", 0),
        "error_field": input_args.get("error_field", ""),
        "trace_id": input_args.get("trace_id", ""),
        "mock_aspect_flag": input_args.get("mock_aspect_flag", ""),
        "replay_tag": input_args.get("replay_tag", {}),
        "tag_agg": input_args.get("tag_agg", []),
    }

    caller = HttpCaller()
    result = await caller.call(
        request_body=request_body,
        host=get_url("logreplay"),
        path=API_REPORT_AGG,
        extra_headers=auth_headers,
    )
    return json.dumps(result, ensure_ascii=False)

# === AI Generated Code End lovli===


# ===================== SearchResponse =====================

# === AI Generated Code Start lovli===

SEARCH_RESPONSE_DEF = make_tool_definition(
    name="SearchResponse",
    description=(
        "查询【普通回放（单环境）】单条流量录制和回放响应比对结果（录制 vs 回放）。"
        "适用场景与双环境回放（TwoEnvReplayResultSearch）的判定规则详见 references/replay.md。"
    ),
    parameters={
        "type": "object",
        "properties": {
            "app_server_name": {"type": "string", "description": "服务名称，格式 app.server"},
            "trace_id": {"type": "string", "description": "TraceID"},
            "task_id": {"type": "integer", "description": "回放任务ID"},
            "needDiff": {"type": "boolean", "description": "是否需要比对"},
            "module_id": {"type": "string", "description": "模块ID"},
            "flow_type": {"type": "integer", "description": "流量类型，默认0：流量，1：用例"},
        },
        "required": ["app_server_name", "trace_id", "task_id"],
    },
)


async def execute_search_response(input_args: dict[str, Any]) -> str:
    """查询单条流量录制和回放响应比对结果"""
    app_server_name = input_args["app_server_name"]
    module_id, auth_headers, uctx = await resolve_logreplay_prereqs(app_server_name)

    request_body = {
        "base_req": {"username": uctx["user_id"]},
        "trace_id": input_args["trace_id"],
        "task_id": input_args["task_id"],
        "needDiff": input_args.get("needDiff", False),
        "module_id": input_args.get("module_id", module_id),
        "flow_type": input_args.get("flow_type", 0),
    }

    caller = HttpCaller()
    result = await caller.call(
        request_body=request_body,
        host=get_url("logreplay"),
        path=API_RECORD_SEARCH_RESPONSE,
        extra_headers=auth_headers,
    )
    return json.dumps(result, ensure_ascii=False)

# === AI Generated Code End lovli===


# ===================== TwoEnvReplayResultSearch =====================

# === AI Generated Code Start lovli===

TWO_ENV_REPLAY_RESULT_SEARCH_DEF = make_tool_definition(
    name="TwoEnvReplayResultSearch",
    description=(
        "查询【双环境回放】单条流量响应：按 task_id + trace_id 返回同一流量在两个目标环境上的回放响应（环境 A vs 环境 B）。"
        "适用场景与普通回放（SearchResponse）的判定规则详见 references/replay.md。"
    ),
    parameters={
        "type": "object",
        "properties": {
            "app_server_name": {"type": "string", "description": "服务名称，格式 app.server"},
            "task_id": {"type": "integer", "description": "回放任务ID，必填"},
            "trace_id": {"type": "string", "description": "流量 Trace ID，必填"},
            "commit_id": {"type": "string", "description": "Git提交ID（可选）"},
            "api_name": {"type": "string", "description": "接口名（可选）"},
            "status": {"type": "integer", "description": "回放结果（可选，对应 pb 中的 Status 枚举）"},
            "reasons": {
                "type": "array",
                "items": {"type": "string"},
                "description": "响应对比结果列表（可选，支持批量查询）",
            },
            "start_time": {"type": "number", "description": "起始时间（可选）"},
            "end_time": {"type": "number", "description": "结束时间（可选）"},
            "includes": {
                "type": "array",
                "items": {"type": "string"},
                "description": "返回字段包含。默认 [target, response]：target 表示双环境的两个不同 IP:Port，response 为回放响应结构化数据",
            },
            "excludes": {
                "type": "array",
                "items": {"type": "string"},
                "description": "返回字段排除（可选）",
            },
        },
        "required": ["app_server_name", "task_id", "trace_id"],
    },
)


async def execute_two_env_replay_result_search(input_args: dict[str, Any]) -> str:
    """双环境回放结果查询：按 task_id + trace_id 查询双环境响应数据"""
    app_server_name = input_args["app_server_name"]
    module_id, auth_headers, uctx = await resolve_logreplay_prereqs(app_server_name)

    request_body = {
        "base_req": {"username": uctx["user_id"]},
        # 双环境回放每条 trace 对应两条响应记录，固定 page=1、page_size=2
        "page_req": {"page": 1, "page_size": 2},
        "module_id": module_id,
        "task_id": input_args["task_id"],
        "trace_id": input_args["trace_id"],
        "commit_id": input_args.get("commit_id", ""),
        "api_name": input_args.get("api_name", ""),
        "status": input_args.get("status", 0),
        "reasons": input_args.get("reasons", []),
        "start_time": input_args.get("start_time", 0),
        "end_time": input_args.get("end_time", 0),
        # 默认只返回 target 与 response，便于查看双环境回放响应对比
        "includes": input_args.get("includes", ["target", "response"]),
        "excludes": input_args.get("excludes", []),
    }

    caller = HttpCaller()
    result = await caller.call(
        request_body=request_body,
        host=get_url("logreplay"),
        path=API_REPLAY_SEARCH,
        extra_headers=auth_headers,
    )
    return json.dumps(result, ensure_ascii=False)

# === AI Generated Code End lovli===


# ===================== 直接回放报告链接拼接 =====================

# === AI Generated Code Start lovli===

async def _build_direct_replay_report_url(
    s_id: int, task_id: int, project_id: str, group_id: str,
) -> str:
    """
    拼接直接回放报告的 Web 链接。
    通过 getEnvNameByProjectId 接口动态获取业务英文名（envName），
    然后拼接完整路径：{domain}/oneapitest/{envName}#/newApiManage/trpcReplayReport?...

    Args:
        s_id: 服务 ID（数字类型，来自 app_server_detail.id）
        task_id: 直接回放任务 ID（数字类型，来自 ExecuteReplay 返回的 task_id）
        project_id: 项目 ID（来自鉴权上下文）
        group_id: 组 ID（来自鉴权上下文）

    Returns:
        完整的回放报告 URL 字符串
    """
    base_url = get_default("direct_replay_domain", "")
    if not base_url:
        logger.warning(
            "direct_replay_domain not configured in config.json defaults, "
            "report URL will be empty"
        )
        return ""

    try:
        env_name = await get_env_name_by_project_id(project_id)
    except Exception as e:
        logger.warning(f"获取 envName 失败: {e}，报告链接将缺少业务路径")
        return ""

    return (
        f"{base_url}/oneapitest/{env_name}#/newApiManage/trpcReplayReport"
        f"?sId={s_id}&taskId={task_id}"
        f"&projectId={project_id}&groupId={group_id}"
    )

# === AI Generated Code End lovli===


# ===================== ExecuteReplay =====================

EXECUTE_REPLAY_DEF = make_tool_definition(
    name="ExecuteReplay",
    description="执行流量回放任务",
    parameters={
        "type": "object",
        "properties": {
            "app_server_name": {"type": "string", "description": "服务名称，格式 app.server"},
            "commit_id": {"type": "string", "description": "录制流量的协议版本号"},
            "number": {"type": "integer", "description": "回放请求个数，默认100"},
            "rate": {"type": "integer", "description": "回放速率，默认100"},
            "api_list": {"type": "array", "items": {"type": "string"}, "description": "回放接口列表"},
            "addr": {
                "type": "object",
                "description": "目标地址映射，key为service名称",
                "additionalProperties": {
                    "type": "object",
                    "properties": {
                        "addr": {"type": "array", "items": {"type": "string"}, "description": "目标地址列表"},
                    },
                },
            },
            "trace_id_list": {"type": "array", "items": {"type": "string"}, "description": "trace_id列表"},
            "start_time": {"type": "number", "description": "开始时间戳（纳秒）"},
            "end_time": {"type": "number", "description": "结束时间戳（纳秒）"},
            "replay_type": {"type": "integer", "description": "回放类型，默认0；1表示只发不比"},
            "service_name": {"type": "string", "description": "服务名"},
            "instance_name": {"type": "string", "description": "实例名"},
            "env": {"type": "string", "description": "回放流量的环境"},
            "select_target_by_commit_id": {"type": "boolean", "description": "是否按commit_id强制选目标"},
            "diffy_dockers": {"type": "array", "items": {"type": "string"}, "description": "diffy对照容器"},
            "disable_white": {"type": "boolean", "description": "是否允许白名单流量"},
            "all_filters": {"type": "array", "items": {"type": "string"}, "description": "统一过滤条件"},
            "replay_env_tag": {
                "type": "boolean",
                "description": (
                    "双环境回放标记。true 表示本次为双环境回放（需在 addr.default_target.addr 传入两个目标地址），"
                    "对应 GetReplayTaskInfo/TaskList 返回中 replay_show_type == '0_1'；"
                    "false 或不传则为普通回放。该值决定阶段 4 查询单条 diff 时使用 SearchResponse 还是 TwoEnvReplayResultSearch，详见 references/replay.md"
                ),
            },
            "is_devnet": {"type": "boolean", "description": "是否devnet"},
            "rules": {
                "type": "object",
                "description": "流量编辑规则，key/value都是字符串",
                "additionalProperties": {"type": "string"},
            },
            "process_timeout": {"type": "integer", "description": "数据处理超时秒数，默认30s"},
            "is_async_report": {"type": "boolean", "description": "是否异步上报"},
            "polaris_name": {"type": "string", "description": "北极星寻址名"},
            "flow_type": {"type": "integer", "description": "流量类型，默认0流量，1用例"},
            "req_rewrite": {"type": "array", "items": {"type": "string"}, "description": "临时编辑规则"},
            "is_async_replay": {"type": "boolean", "description": "是否异步回放"},
            "frequency": {"type": "integer", "description": "回放频率，单位100ms"},
            "get_target_type": {"type": "integer", "description": "目标选择类型"},
        },
        "required": ["app_server_name"],
    },
)


async def execute_execute_replay(input_args: dict[str, Any]) -> str:
    """执行流量回放任务"""
    _apply_execute_replay_defaults(input_args)

    app_server_name = input_args["app_server_name"]
    module_id, auth_headers, uctx = await resolve_logreplay_prereqs(app_server_name)

    # === AI Generated Code Start lovli===
    # 获取 server_id 用于拼接报告链接
    detail = await get_app_server_detail(app_server_name)
    server_id = detail.get("app_server_detail", {}).get("id", 0)
    # === AI Generated Code End lovli===

    request_body = {**input_args, "base_req": {"username": uctx["user_id"]}, "module_id": module_id, "src": "skill"}



    caller = HttpCaller()
    result = await caller.call(
        request_body=request_body,
        host=get_url("logreplay"),
        path=API_EXECUTE_REPLAY,
        extra_headers=auth_headers,
    )

    # === AI Generated Code Start lovli===
    # 在响应中追加 report_url 字段
    task_id = result.get("task_id", 0)
    result["report_url"] = await _build_direct_replay_report_url(
        s_id=server_id,
        task_id=task_id,
        project_id=uctx["project_id"],
        group_id=uctx["group_id"],
    )
    # === AI Generated Code End lovli===

    return json.dumps(result, ensure_ascii=False)


# ===================== GetReplayTaskInfo =====================

GET_REPLAY_TASK_INFO_DEF = make_tool_definition(
    name="GetReplayTaskInfo",
    description="查询回放任务状态和统计信息",
    parameters={
        "type": "object",
        "properties": {
            "app_server_name": {"type": "string", "description": "服务名称，格式 app.server"},
            "task_id": {"type": "integer", "description": "任务ID"},
        },
        "required": ["app_server_name", "task_id"],
    },
)


async def execute_get_replay_task_info(input_args: dict[str, Any]) -> str:
    """查询回放任务状态和统计信息"""
    app_server_name = input_args["app_server_name"]
    _module_id, auth_headers, uctx = await resolve_logreplay_prereqs(app_server_name)

    # === AI Generated Code Start lovli===
    # 获取 server_id 用于拼接报告链接
    detail = await get_app_server_detail(app_server_name)
    server_id = detail.get("app_server_detail", {}).get("id", 0)
    # === AI Generated Code End lovli===

    request_body = {
        "base_req": {"username": uctx["user_id"]},
        "task_id": input_args["task_id"],
    }



    caller = HttpCaller()
    result = await caller.call(
        request_body=request_body,
        host=get_url("logreplay"),
        path=API_GET_REPLAY_TASK_INFO,
        extra_headers=auth_headers,
    )

    # === AI Generated Code Start lovli===
    # 在响应中追加 report_url 字段
    result["report_url"] = await _build_direct_replay_report_url(
        s_id=server_id,
        task_id=input_args["task_id"],
        project_id=uctx["project_id"],
        group_id=uctx["group_id"],
    )
    # === AI Generated Code End lovli===

    return json.dumps(result, ensure_ascii=False)


# ===================== TaskList =====================

TASK_LIST_DEF = make_tool_definition(
    name="TaskList",
    description="分页查询回放任务列表",
    parameters={
        "type": "object",
        "properties": {
            "app_server_name": {"type": "string", "description": "服务名称，格式 app.server"},
            "page": {"type": "integer", "description": "页码，默认1"},
            "page_size": {"type": "integer", "description": "每页数量，默认20"},
            "operator": {"type": "string", "description": "任务启动人"},
            "status": {
                "type": "array",
                "items": {"type": "integer"},
                "description": "任务状态过滤：0默认 1初始化 2成功 3进行中 4数据处理中 5失败 6中止",
            },
            "comment": {"type": "string", "description": "任务备注过滤"},
            "start_time": {"type": "string", "description": "开始时间"},
            "end_time": {"type": "string", "description": "结束时间"},
            "task_id": {"type": "string", "description": "任务ID过滤"},
        },
        "required": ["app_server_name"],
    },
)


async def execute_task_list(input_args: dict[str, Any]) -> str:
    """分页查询回放任务列表"""
    _apply_task_list_defaults(input_args)

    app_server_name = input_args["app_server_name"]
    module_id, auth_headers, uctx = await resolve_logreplay_prereqs(app_server_name)

    request_body = {
        "base_req": {"username": uctx["user_id"]},
        "page_req": {
            "page": input_args.get("page", 1),
            "page_size": input_args.get("page_size", 20),
        },
        "module_id": module_id,
        "operator": input_args.get("operator", ""),
        "status": input_args.get("status", []),
        "comment": input_args.get("comment", ""),
        "start_time": input_args.get("start_time", ""),
        "end_time": input_args.get("end_time", ""),
        "task_id": input_args.get("task_id", ""),
    }



    caller = HttpCaller()
    result = await caller.call(
        request_body=request_body,
        host=get_url("logreplay"),
        path=API_TASK_LIST,
        extra_headers=auth_headers,
    )
    return json.dumps(result, ensure_ascii=False)


# ===================== DiffConfig =====================

DIFF_CONFIG_DEF = make_tool_definition(
    name="DiffConfig",
    description="查询指定接口的diff配置",
    parameters={
        "type": "object",
        "properties": {
            "app_server_name": {"type": "string", "description": "服务名称，格式 app.server"},
            "api_name": {"type": "string", "description": "接口名"},
        },
        "required": ["app_server_name", "api_name"],
    },
)


async def execute_diff_config(input_args: dict[str, Any]) -> str:
    """查询指定接口的diff配置"""
    app_server_name = input_args["app_server_name"]
    module_id, auth_headers, uctx = await resolve_logreplay_prereqs(app_server_name)

    request_body = {
        "base_req": {"username": uctx["user_id"]},
        "module_id": module_id,
        "api_name": input_args["api_name"],
    }



    caller = HttpCaller()
    result = await caller.call(
        request_body=request_body,
        host=get_url("logreplay"),
        path=API_DIFF_CONFIG,
        extra_headers=auth_headers,
    )
    return json.dumps(result, ensure_ascii=False)


# ===================== SetDiffConfig =====================

# === AI Generated Code Start lovli===

SET_DIFF_CONFIG_DEF = make_tool_definition(
    name="SetDiffConfig",
    description="设置指定接口的diff策略配置（白名单、黑名单、自定义策略、预处理策略、路径策略、自定义diff脚本等）",
    parameters={
        "type": "object",
        "properties": {
            "app_server_name": {"type": "string", "description": "服务名称，格式 app.server"},
            "api_name": {"type": "string", "description": "接口名"},
            "white_list": {
                "type": "array",
                "items": {"type": "string"},
                "description": "白名单字段列表",
            },
            "black_list": {
                "type": "array",
                "items": {"type": "string"},
                "description": "黑名单字段列表",
            },
            "custom_config": {
                "type": "object",
                "description": "自定义策略配置，key为字段名，value为策略对象{type, args}",
                "additionalProperties": {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string", "description": "策略类型"},
                        "args": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "策略参数，第一个参数为对比检查类型（如 default、regexp、floating、remainder、complex、=、<=、>= 等）",
                        },
                    },
                },
            },
            "parse_config": {
                "type": "object",
                "description": "预处理策略配置，key为字段名，value为策略对象{type, args}",
                "additionalProperties": {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string", "description": "策略类型"},
                        "args": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "策略参数",
                        },
                    },
                },
            },
            "script": {"type": "string", "description": "自定义diff脚本内容，当enable_script开关未开启时忽略此字段"},
            "enable_script": {
                "type": "integer",
                "description": "自定义脚本对比开关：1-打开，2-关闭",
                "enum": [1, 2],
            },
            "path_config": {
                "type": "array",
                "description": "路径策略配置列表",
                "items": {
                    "type": "object",
                    "properties": {
                        "RecordPath": {"type": "string", "description": "录制路径"},
                        "ReplayPath": {"type": "string", "description": "回放路径"},
                    },
                },
            },
        },
        "required": ["app_server_name", "api_name"],
    },
)


async def execute_set_diff_config(input_args: dict[str, Any]) -> str:
    """设置指定接口的diff策略配置"""
    app_server_name = input_args["app_server_name"]
    module_id, auth_headers, uctx = await resolve_logreplay_prereqs(app_server_name)

    request_body = {
        "base_req": {"username": uctx["user_id"]},
        "module_id": module_id,
        "api_name": input_args["api_name"],
        "white_list": input_args.get("white_list", []),
        "black_list": input_args.get("black_list", []),
        "custom_config": input_args.get("custom_config", {}),
        "parse_config": input_args.get("parse_config", {}),
        "script": input_args.get("script", ""),
        "enable_script": input_args.get("enable_script", 2),
        "path_config": input_args.get("path_config", []),
    }

    caller = HttpCaller()
    result = await caller.call(
        request_body=request_body,
        host=get_url("logreplay"),
        path=API_SET_DIFF_CONFIG,
        extra_headers=auth_headers,
    )
    return json.dumps(result, ensure_ascii=False)

# === AI Generated Code End lovli===


# ===================== QueryEditRuleList =====================

# === AI Generated Code Start lovli===

QUERY_EDIT_RULE_LIST_DEF = make_tool_definition(
    name="QueryEditRuleList",
    description="查询流量编辑规则列表（用于在回放前对请求/响应数据进行字段级编辑，如新增、修改、删除字段）。api_name 可选，不传则查询该服务下所有接口的编辑规则",
    parameters={
        "type": "object",
        "properties": {
            "app_server_name": {"type": "string", "description": "服务名称，格式 app.server"},
            "api_name": {"type": "string", "description": "接口名，可选。不传则查询该服务下所有接口的编辑规则"},
        },
        "required": ["app_server_name"],
    },
)


async def execute_query_edit_rule_list(input_args: dict[str, Any]) -> str:
    """查询流量编辑规则列表，api_name 可选"""
    app_server_name = input_args["app_server_name"]
    module_id, auth_headers, uctx = await resolve_logreplay_prereqs(app_server_name)

    request_body = {
        "base_req": {"username": uctx["user_id"]},
        "module_id": module_id,
        "api_name": input_args.get("api_name", ""),
    }

    caller = HttpCaller()
    result = await caller.call(
        request_body=request_body,
        host=get_url("logreplay"),
        path=API_QUERY_EDIT_RULE_LIST,
        extra_headers=auth_headers,
    )
    return json.dumps(result, ensure_ascii=False)

# === AI Generated Code End lovli===


# ===================== CreateEditRule =====================

# === AI Generated Code Start lovli===


def _derive_msg_name_from_api(api_name: str) -> str:
    """
    当调用方未显式提供 msg_name / message_name 时，从 api_name 末尾截取方法名作为默认值。
    后端不会对该字段做兜底，必须由工具层填入。

    截取规则：按 `/` 分隔取最后一段（同时去除首尾空白）。
    - `/trpc.app.server.xxx/Count` → `Count`
    - `Count`                       → `Count`
    - 空串或纯空白                   → ``（保持空串，交由后端校验）
    """
    if not api_name:
        return ""
    return api_name.strip().rsplit("/", 1)[-1]


CREATE_EDIT_RULE_DEF = make_tool_definition(
    name="CreateEditRule",
    description=(
        "为指定接口创建流量编辑规则。规则以接口（api_name）为粒度配置，每个接口对应一组 ItemRule。"
        "【强制流程】必须先调用 EditRuleCheck 对规则进行预览校验，预览通过后再调用本工具写入；"
        "若 EditRuleCheck 报错，必须先解决错误后再重新 Check，禁止直接创建。"
    ),
    parameters={
        "type": "object",
        "properties": {
            "app_server_name": {"type": "string", "description": "服务名称，格式 app.server"},
            "api_name": {
                "type": "string",
                "description": "接口名（可能带路径，如 /trpc.app.server.xxx/Count），必传",
            },
            "protocol": {
                "type": "string",
                "description": "协议名，如 trpc、http。**必传**：值来源为 RecordSearch 返回流量中的同名字段，或由用户显式指定，二者取其一",
            },
            "proto_version": {
                "type": "string",
                "description": "proto 版本号。**必传**：值来源为 RecordSearch 返回流量中的同名字段，或由用户显式指定，二者取其一",
            },
            "msg_name": {
                "type": "string",
                "description": (
                    "message name，即接口的方法名（例如 Count、QueryUser），不是带路径的 api_name。"
                    "**可选，唯一可不传的字段**——不填时工具会自动从 api_name 末尾截取方法名（按 `/` 分隔取最后一段）作为默认值；用户也可显式指定。"
                    "注意：RecordSearch 返回的流量中不包含此字段，不要试图从 RecordSearch 中读取"
                ),
            },
            "edit_enabled": {"type": "boolean", "description": "规则组是否启用，默认 true"},
            "rules": {
                "type": "array",
                "description": "具体的编辑规则列表（ItemRule）",
                "items": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "description": "编辑行为：add（新增）、update（修改，含普通替换与正则替换）、delete（删除）",
                            "enum": ["add", "update", "delete"],
                        },
                        "key": {
                            "type": "string",
                            "description": "JSON key 路径，例如 requestBody.user.name。详细规则见 references/editrule.md",
                        },
                        "value": {
                            "type": "string",
                            "description": "字段值。action=delete 时可填空串。支持动态函数占位符，详细规则见 references/editrule.md",
                        },
                        "type": {
                            "type": "string",
                            "description": "value 的数据类型",
                            "enum": ["string", "number", "boolean", "null", "undefined"],
                        },
                    },
                    "required": ["action", "key", "type"],
                },
            },
        },
        "required": [
            "app_server_name", "api_name", "protocol", "proto_version", "rules",
        ],
    },
)


async def execute_create_edit_rule(input_args: dict[str, Any]) -> str:
    """创建指定接口的流量编辑规则"""
    app_server_name = input_args["app_server_name"]
    module_id, auth_headers, uctx = await resolve_logreplay_prereqs(app_server_name)

    # === AI Generated Code Start lovli===
    # server_name 不对外暴露：logreplay 中该字段语义即服务名，直接使用 app_server_name 原值。
    # msg_name 后端不做兜底，工具层必须填入默认值：未显式传入时从 api_name 末尾截取方法名。
    api_name = input_args["api_name"]
    msg_name = input_args.get("msg_name") or _derive_msg_name_from_api(api_name)
    rule_body = {
        "moduleId": module_id,
        "apiName": api_name,
        "protocol": input_args.get("protocol", ""),
        "serverName": app_server_name,
        "protoVersion": input_args.get("proto_version", ""),
        "msgName": msg_name,
        "rules": input_args.get("rules", []),
        "editEnabled": input_args.get("edit_enabled", True),
    }
    # === AI Generated Code End lovli===

    request_body = {
        "base_req": {"username": uctx["user_id"]},
        "rule": rule_body,
    }

    caller = HttpCaller()
    result = await caller.call(
        request_body=request_body,
        host=get_url("logreplay"),
        path=API_CREATE_EDIT_RULE,
        extra_headers=auth_headers,
    )
    return json.dumps(result, ensure_ascii=False)


# ===================== UpdateEditRule =====================

UPDATE_EDIT_RULE_DEF = make_tool_definition(
    name="UpdateEditRule",
    description=(
        "更新已有流量编辑规则组的启用开关。仅修改 edit_enabled，不修改规则内容。"
        "id 通过 QueryEditRuleList 查询获得"
    ),
    parameters={
        "type": "object",
        "properties": {
            "app_server_name": {"type": "string", "description": "服务名称，格式 app.server"},
            "id": {"type": "integer", "description": "规则组 ID，通过 QueryEditRuleList 获取"},
            "edit_enabled": {"type": "boolean", "description": "是否启用"},
        },
        "required": ["app_server_name", "id", "edit_enabled"],
    },
)


async def execute_update_edit_rule(input_args: dict[str, Any]) -> str:
    """更新流量编辑规则组的启用开关"""
    app_server_name = input_args["app_server_name"]
    _module_id, auth_headers, uctx = await resolve_logreplay_prereqs(app_server_name)

    request_body = {
        "base_req": {"username": uctx["user_id"]},
        "id": input_args["id"],
        "edit_enabled": input_args["edit_enabled"],
    }

    caller = HttpCaller()
    result = await caller.call(
        request_body=request_body,
        host=get_url("logreplay"),
        path=API_UPDATE_EDIT_RULE,
        extra_headers=auth_headers,
    )
    return json.dumps(result, ensure_ascii=False)


# ===================== DeleteEditRule =====================

DELETE_EDIT_RULE_DEF = make_tool_definition(
    name="DeleteEditRule",
    description="删除指定的流量编辑规则组。id 通过 QueryEditRuleList 查询获得",
    parameters={
        "type": "object",
        "properties": {
            "app_server_name": {"type": "string", "description": "服务名称，格式 app.server"},
            "id": {"type": "integer", "description": "规则组 ID，通过 QueryEditRuleList 获取"},
        },
        "required": ["app_server_name", "id"],
    },
)


async def execute_delete_edit_rule(input_args: dict[str, Any]) -> str:
    """删除指定的流量编辑规则组"""
    app_server_name = input_args["app_server_name"]
    _module_id, auth_headers, uctx = await resolve_logreplay_prereqs(app_server_name)

    request_body = {
        "base_req": {"username": uctx["user_id"]},
        "id": input_args["id"],
    }

    caller = HttpCaller()
    result = await caller.call(
        request_body=request_body,
        host=get_url("logreplay"),
        path=API_DELETE_EDIT_RULE,
        extra_headers=auth_headers,
    )
    return json.dumps(result, ensure_ascii=False)


# ===================== EditRuleCheck =====================

EDIT_RULE_CHECK_DEF = make_tool_definition(
    name="EditRuleCheck",
    description=(
        "对指定接口的流量编辑规则进行预览校验：将规则应用到一条样例流量上，返回编辑前/编辑后的内容对比。"
        "不会真正写入规则，仅用于回放前确认规则是否符合预期。api_name 必传。"
        "【强制流程】用户希望创建流量编辑规则时，必须先调用本工具做预览校验，校验通过后再调用 "
        "CreateEditRule 写入；若本工具返回错误，必须先解决错误并重新 Check，不得直接 Create。"
    ),
    parameters={
        "type": "object",
        "properties": {
            "app_server_name": {"type": "string", "description": "服务名称，格式 app.server"},
            "api_name": {
                "type": "string",
                "description": "接口名（可能带路径，如 /trpc.app.server.xxx/Count），必传",
            },
            "protocol": {
                "type": "string",
                "description": "协议名，如 trpc、http。**必传**：值来源为 RecordSearch 返回流量中的同名字段，或由用户显式指定，二者取其一",
            },
            "proto_version": {
                "type": "string",
                "description": "proto 版本号。**必传**：值来源为 RecordSearch 返回流量中的同名字段，或由用户显式指定，二者取其一",
            },
            "message_name": {
                "type": "string",
                "description": (
                    "message name，即接口的方法名（等同于 CreateEditRule 里的 msg_name，"
                    "只是本接口后端入参字段叫 message_name）。"
                    "**可选，唯一可不传的字段**——不填时工具会自动从 api_name 末尾截取方法名（按 `/` 分隔取最后一段）作为默认值；用户也可显式指定。"
                    "注意：RecordSearch 返回的流量中不包含此字段，不要试图从 RecordSearch 中读取"
                ),
            },
            "rules": {
                "type": "array",
                "description": "待校验的编辑规则列表（ItemRule），结构与 CreateEditRule 中 rules 相同",
                "items": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["add", "update", "delete"],
                            "description": "编辑行为",
                        },
                        "key": {"type": "string", "description": "JSON key 路径，例如 requestBody.user.name。详细规则见 references/editrule.md"},
                        "value": {"type": "string", "description": "字段值。支持动态函数占位符，详细规则见 references/editrule.md"},
                        "type": {
                            "type": "string",
                            "enum": ["string", "number", "boolean", "null", "undefined"],
                            "description": "value 的数据类型",
                        },
                    },
                    "required": ["action", "key", "type"],
                },
            },
        },
        "required": [
            "app_server_name", "api_name", "protocol", "proto_version", "rules",
        ],
    },
)


async def execute_edit_rule_check(input_args: dict[str, Any]) -> str:
    """校验流量编辑规则，返回编辑前/编辑后的内容对比"""
    app_server_name = input_args["app_server_name"]
    module_id, auth_headers, uctx = await resolve_logreplay_prereqs(app_server_name)

    # === AI Generated Code Start lovli===
    # server_name 不对外暴露：直接使用 app_server_name 原值。
    # message_name 后端不做兜底，工具层必须填入默认值：未显式传入时从 api_name 末尾截取方法名。
    api_name = input_args["api_name"]
    message_name = input_args.get("message_name") or _derive_msg_name_from_api(api_name)
    request_body = {
        "base_req": {"username": uctx["user_id"]},
        "module_id": module_id,
        "api_name": api_name,
        "server_name": app_server_name,
        "proto_version": input_args.get("proto_version", ""),
        "message_name": message_name,
        "protocol": input_args.get("protocol", ""),
        "rules": input_args.get("rules", []),
    }
    # === AI Generated Code End lovli===

    caller = HttpCaller()
    result = await caller.call(
        request_body=request_body,
        host=get_url("logreplay"),
        path=API_EDIT_RULE_CHECK,
        extra_headers=auth_headers,
    )
    return json.dumps(result, ensure_ascii=False)

# === AI Generated Code End lovli===


# ===================== GetFlow2SceneTaskList（无前置依赖）=====================

GET_FLOW2_SCENE_TASK_LIST_DEF = make_tool_definition(
    name="GetFlow2SceneTaskList",
    description="获取流量转用例任务列表",
    parameters={
        "type": "object",
        "properties": {
            "uuid": {"type": "string", "description": "流量转用例任务UUID（可选），用于筛选指定任务"},
        },
        "required": [],
    },
)


async def execute_get_flow2_scene_task_list(input_args: dict[str, Any]) -> str:
    """获取流量转用例任务列表（原gRPC）"""
    uctx = await get_user_context()


    request_body = {
        "user_group_id": uctx["group_id"],
        "user_project_id": uctx["project_id"],
    }
    # 如果传入了uuid，构建 retrieve_data 筛选条件
    if input_args.get("uuid"):
        request_body["retrieve_data"] = [{
            "attr": {"key": "uuid", "name": "任务ID", "type": "input"},
            "values": [{"name": input_args["uuid"]}],
        }]

    caller = HttpCaller()
    result = await caller.call(
        request_body=request_body,
        host=get_url("utest_perf"),
        path=API_GET_FLOW2_SCENE_TASK_LIST,
        extra_headers=get_perf_auth_headers(),
    )
    return json.dumps(result, ensure_ascii=False)


# ===================== GenerateTestPlanByTrafficData =====================
# 前置依赖：GetAppServerDetailByName + GetCasKey
# 直接调用 CreateFlow2Scene，不再内部调用 RecordAgg/RecordSearch

# === AI Generated Code Start lovli===

GENERATE_TEST_PLAN_BY_TRAFFIC_DATA_DEF = make_tool_definition(
    name="GenerateTestPlanByTrafficData",
    description="使用流量数据生成测试场景用例。调用前应先通过 RecordAgg/RecordSearch 获取 commit_id、protocol 等流量字段",
    parameters={
        "type": "object",
        "properties": {
            "app_server_name": {"type": "string", "description": "服务名称，格式 app.server"},
            "api_name": {"type": "string", "description": "接口名，用于过滤特定流量"},
            "scene_name": {"type": "string", "description": "测试场景名称（可选）"},
            "start_time": {"type": "string", "description": "开始时间，格式 YYYY-MM-DD HH:MM:SS（可选）"},
            "end_time": {"type": "string", "description": "结束时间，格式 YYYY-MM-DD HH:MM:SS（可选）"},
            "max_count": {"type": "integer", "description": "最大流量数据条数，默认10"},
            "commit_id": {"type": "string", "description": "流量协议版本号，可从 RecordAgg commitId 维度获取"},
            "server_name": {"type": "string", "description": "logreplay server name（可选）"},
            "instance_name": {"type": "string", "description": "服务容器名称，可从 RecordAgg instanceName 维度获取（可选）"},
            "protocol": {"type": "string", "description": "协议类型（如 trpc、http），可从 RecordSearch 结果获取（可选）"},
            "traceIds": {"type": "string", "description": "链路ID，多个以 | 分割（可选）"},
            "dir_id": {"type": "integer", "description": "测试场景所在目录ID，默认-1（未分组）"},
            "export_filed_names": {
                "type": "array",
                "items": {"type": "string"},
                "description": "导出字段列表，可选值：request_header/request_body/response_header/response_body/trace_id/request_binary/request_metadata/response_metadata。默认前五个",
            },
            "label_uuid": {
                "type": "string",
                "description": "场景标签：flow2logreplay-流量转回放用例（默认）、flow2api-流量转接口测试用例、flow2perf-流量转压测用例、ai2scene-AI生成用例",
            },
            "all_filters": {
                "type": "array",
                "items": {"type": "string"},
                "description": "字段过滤条件（可选）",
            },
        },
        "required": ["app_server_name", "api_name"],
    },
)


async def execute_generate_test_plan_by_traffic_data(input_args: dict[str, Any]) -> str:
    """
    使用流量数据生成测试场景用例。
    对应 Go: generateTestPlanByFlow → doFlow2Scene

    链路（简化后）：
    1. resolve_logreplay_prereqs → module_id + auth_headers + uctx
    2. 直接调用 CreateFlow2Scene → 返回任务 uuid
    """
    _apply_generate_test_plan_defaults(input_args)

    app_server_name = input_args["app_server_name"]
    module_id, _auth_headers, uctx = await resolve_logreplay_prereqs(app_server_name)

    parts = app_server_name.split(".", 1)

    create_body = {
        "user_group_id": uctx["group_id"],
        "user_project_id": uctx["project_id"],
        "user_id": uctx["user_id"],
        "business_id": uctx["project_id"],
        "scene_name": input_args.get("scene_name", ""),
        "module_id": module_id,
        "server_name": input_args.get("server_name", ""),
        "start_time": input_args.get("start_time", ""),
        "end_time": input_args.get("end_time", ""),
        "analysis_type": 3,
        "traceIds": input_args.get("traceIds", ""),
        "max_count": input_args.get("max_count", 10),
        "commit_id": input_args.get("commit_id", ""),
        "instance_name": input_args.get("instance_name", ""),
        "protocol": input_args.get("protocol", ""),
        "app_name_en": parts[0],
        "module_name_en": parts[1] if len(parts) > 1 else "",
        "interface_name": input_args.get("api_name", ""),
        "dir_id": input_args.get("dir_id", -1),
        "export_filed_names": input_args.get("export_filed_names", [
            "request_header", "request_body",
            "response_header", "response_body", "trace_id",
        ]),
        "label_uuid": input_args.get("label_uuid", "flow2logreplay"),
        "label_group_uuid": "system-001",
        "all_filters": input_args.get("all_filters", []),
    }

    caller = HttpCaller()
    flow_result = await caller.call(
        request_body=create_body,
        host=get_url("utest_perf"),
        path=API_CREATE_FLOW2_SCENE,
        extra_headers=get_perf_auth_headers(),
    )
    return json.dumps(flow_result, ensure_ascii=False)

# === AI Generated Code End lovli===


# ===================== 默认值辅助函数 =====================


def _apply_page_size_defaults(
    args: dict[str, Any], page_key: str = "page", size_key: str = "page_size",
    default_page: int = 1, default_size: int = 20,
) -> None:
    if not args.get(page_key):
        args[page_key] = default_page
    if not args.get(size_key):
        args[size_key] = default_size


def _apply_execute_replay_defaults(args: dict[str, Any]) -> None:
    if not args.get("number"):
        args["number"] = 100
    if not args.get("rate"):
        args["rate"] = 100
    if not args.get("process_timeout"):
        args["process_timeout"] = 30
    s, e = get_default_nano_time_range()
    if not args.get("end_time"):
        args["end_time"] = e
    if not args.get("start_time"):
        args["start_time"] = s


def _apply_task_list_defaults(args: dict[str, Any]) -> None:
    if not args.get("page"):
        args["page"] = 1
    if not args.get("page_size"):
        args["page_size"] = 20
    s, e = get_default_str_time_range()
    if not args.get("end_time"):
        args["end_time"] = e
    if not args.get("start_time"):
        args["start_time"] = s


def _apply_generate_test_plan_defaults(args: dict[str, Any]) -> None:
    if not args.get("scene_name"):
        api_name = args.get("api_name", "unknown")
        args["scene_name"] = f"{api_name} 测试用例"
    if not args.get("max_count"):
        args["max_count"] = 10


# 注册工具
registry.register(SEARCH_REPORT_DEF, execute_search_report)
registry.register(REPORT_AGG_DEF, execute_report_agg)
registry.register(SEARCH_RESPONSE_DEF, execute_search_response)
# === AI Generated Code Start lovli===
registry.register(TWO_ENV_REPLAY_RESULT_SEARCH_DEF, execute_two_env_replay_result_search)
# === AI Generated Code End lovli===
registry.register(EXECUTE_REPLAY_DEF, execute_execute_replay)
registry.register(GET_REPLAY_TASK_INFO_DEF, execute_get_replay_task_info)
registry.register(TASK_LIST_DEF, execute_task_list)
registry.register(DIFF_CONFIG_DEF, execute_diff_config)
registry.register(SET_DIFF_CONFIG_DEF, execute_set_diff_config)
registry.register(QUERY_EDIT_RULE_LIST_DEF, execute_query_edit_rule_list)
# === AI Generated Code Start lovli===
registry.register(CREATE_EDIT_RULE_DEF, execute_create_edit_rule)
registry.register(UPDATE_EDIT_RULE_DEF, execute_update_edit_rule)
registry.register(DELETE_EDIT_RULE_DEF, execute_delete_edit_rule)
registry.register(EDIT_RULE_CHECK_DEF, execute_edit_rule_check)
# === AI Generated Code End lovli===
registry.register(GET_FLOW2_SCENE_TASK_LIST_DEF, execute_get_flow2_scene_task_list)
registry.register(GENERATE_TEST_PLAN_BY_TRAFFIC_DATA_DEF, execute_generate_test_plan_by_traffic_data)

