"""
@generated-by AI: lovli
@generated-date 2026-04-02

录制阶段本地工具
包含：MultiGetTaskStatus、GetGoReplayStatus、RecordAgg、RecordSearch、
      GetGoReplayNodeList、StartGoReplay、GetGoReplayExecTask、
      StopGoReplayTask、GetProtoInfoList、GetProtocolName
"""
from __future__ import annotations  # added by AI wenning

import base64
import json
import logging
from typing import Any, Optional

from .base import (
    HttpCaller,
    get_default_nano_time_range,
    get_default_str_time_range,
    get_url,
    get_user_context,
    make_tool_definition,
    registry,
    resolve_logreplay_prereqs,
    LOGREPLAY_RET_CODE_VALIDATOR,
    # API 路径常量
    API_MULTI_GET_TASK_STATUS,
    API_GET_GOREPLAY_STATUS,
    API_RECORD_AGG,
    API_RECORD_SEARCH,
    API_GET_GO_REPLAY_NODE_LIST,
    API_START_GO_REPLAY,
    API_GET_GO_REPLAY_EXEC_TASK,
    API_STOP_GO_REPLAY_TASK,
    API_GET_PROTO_INFO_LIST,
    API_GET_PROTOCOL_NAME,
    API_GET_TRPC_PLUGIN_INSTANCE_LIST,
    API_UPDATE_TRPC_PLUGIN_CONFIG,
)

logger = logging.getLogger(__name__)


# ===================== MultiGetTaskStatus =====================

# === AI Generated Code Start lovli===

MULTI_GET_TASK_STATUS_DEF = make_tool_definition(
    name="MultiGetTaskStatus",
    description="批量获取goreplay录制任务状态",
    parameters={
        "type": "object",
        "properties": {
            "app_server_name": {"type": "string", "description": "服务名称，格式 app.server"},
            "task_ids": {
                "type": "array",
                "items": {"type": "string"},
                "description": "任务 id 数组",
            },
        },
        "required": ["app_server_name", "task_ids"],
    },
)


async def execute_multi_get_task_status(input_args: dict[str, Any]) -> str:
    """批量获取goreplay录制任务状态"""
    app_server_name = input_args["app_server_name"]
    _module_id, auth_headers, uctx = await resolve_logreplay_prereqs(app_server_name)

    request_body = {
        "base_req": {"username": uctx["user_id"]},
        "task_ids": input_args.get("task_ids", []),
    }

    caller = HttpCaller()
    result = await caller.call(
        request_body=request_body,
        host=get_url("logreplay"),
        path=API_MULTI_GET_TASK_STATUS,
        extra_headers=auth_headers,
    )
    return json.dumps(result, ensure_ascii=False)

# === AI Generated Code End lovli===


# ===================== GetGoReplayStatus =====================

# === AI Generated Code Start lovli===

GET_GOREPLAY_STATUS_DEF = make_tool_definition(
    name="GetGoReplayStatus",
    description="获取goreplay录制任务状态",
    parameters={
        "type": "object",
        "properties": {
            "app_server_name": {"type": "string", "description": "服务名称，格式 app.server"},
            "ipAndPorts": {
                "type": "array",
                "items": {"type": "string"},
                "description": "IP和端口数组",
            },
            "agent_ids": {
                "type": "array",
                "items": {"type": "string"},
                "description": "agent id 数组",
            },
        },
        "required": ["app_server_name"],
    },
)


async def execute_get_goreplay_status(input_args: dict[str, Any]) -> str:
    """获取goreplay录制任务状态"""
    app_server_name = input_args["app_server_name"]
    _module_id, auth_headers, uctx = await resolve_logreplay_prereqs(app_server_name)

    request_body = {
        "base_req": {"username": uctx["user_id"]},
        "ipAndPorts": input_args.get("ipAndPorts", []),
        "agent_ids": input_args.get("agent_ids", []),
    }

    caller = HttpCaller()
    result = await caller.call(
        request_body=request_body,
        host=get_url("logreplay"),
        path=API_GET_GOREPLAY_STATUS,
        extra_headers=auth_headers,
    )
    return json.dumps(result, ensure_ascii=False)

# === AI Generated Code End lovli===


# ===================== RecordAgg =====================

RECORD_AGG_DEF = make_tool_definition(
    name="RecordAgg",
    description="按条件聚合查询录制流量",
    parameters={
        "type": "object",
        "properties": {
            "app_server_name": {"type": "string", "description": "服务名称，格式 app.server"},
            "page": {"type": "integer", "description": "页码，默认1"},
            "page_size": {"type": "integer", "description": "每页数量，默认20"},
            "commit_id": {"type": "string", "description": "流量协议版本id"},
            "start_time": {"type": "number", "description": "开始时间戳（纳秒）"},
            "end_time": {"type": "number", "description": "结束时间戳（纳秒）"},
            "api_names": {"type": "array", "items": {"type": "string"}, "description": "接口名列表"},
            "trace_ids": {"type": "array", "items": {"type": "string"}, "description": "TraceID列表"},
            "service_name": {"type": "string", "description": "服务名"},
            "instance_name": {"type": "string", "description": "实例名"},
            "protocol": {"type": "string", "description": "协议"},
            "p_trace_id": {"type": "string", "description": "父Trace ID"},
            "agg_names": {
                "type": "array",
                "items": {"type": "string"},
                "description": "聚合字段列表，可为commitId,instanceName,serviceName,apiName,traceId",
            },
            "env": {"type": "string", "description": "环境名"},
            "all_filters": {"type": "array", "items": {"type": "string"}, "description": "统一过滤条件"},
            "no_need_routing": {"type": "boolean", "description": "是否不需要routing"},
            "flow_types": {"type": "array", "items": {"type": "integer"}, "description": "流量类型列表"},
        },
        "required": ["app_server_name", "agg_names"],
    },
)


async def execute_record_agg(input_args: dict[str, Any]) -> str:
    """按条件聚合查询录制流量"""
    _apply_record_agg_defaults(input_args)

    # 前置依赖：获取 module_id + 鉴权 header + 用户上下文
    app_server_name = input_args["app_server_name"]
    module_id, auth_headers, uctx = await resolve_logreplay_prereqs(app_server_name)

    # 构建实际请求体（注入 module_id，按 Go convertRecordAggInputToReq 构造 base_req/page_req）
    request_body = {
        "base_req": {"username": uctx["user_id"]},
        "page_req": {
            "page": input_args.get("page", 1),
            "page_size": input_args.get("page_size", 20),
        },
        "module_id": module_id,
        "commit_id": input_args.get("commit_id", ""),
        "start_time": input_args.get("start_time"),
        "end_time": input_args.get("end_time"),
        "api_names": input_args.get("api_names", []),
        "trace_ids": input_args.get("trace_ids", []),
        "service_name": input_args.get("service_name", ""),
        "instance_name": input_args.get("instance_name", ""),
        "protocol": input_args.get("protocol", ""),
        "p_trace_id": input_args.get("p_trace_id", ""),
        "agg_names": input_args.get("agg_names", ["apiName"]),
        "env": input_args.get("env", ""),
        "all_filters": input_args.get("all_filters", []),
        "no_need_routing": input_args.get("no_need_routing", False),
        "flow_types": input_args.get("flow_types", []),
    }

    caller = HttpCaller()
    result = await caller.call(
        request_body=request_body,
        host=get_url("logreplay"),
        path=API_RECORD_AGG,
        extra_headers=auth_headers,
    )
    return json.dumps(result, ensure_ascii=False)


# ===================== RecordSearch =====================

RECORD_SEARCH_DEF = make_tool_definition(
    name="RecordSearch",
    description="按条件检索录制流量明细",
    parameters={
        "type": "object",
        "properties": {
            "app_server_name": {"type": "string", "description": "服务名称，格式 app.server"},
            "page": {"type": "integer", "description": "页码，默认1"},
            "page_size": {"type": "integer", "description": "每页数量，默认20"},
            "commit_id": {"type": "string", "description": "流量协议版本id"},
            "start_time": {"type": "number", "description": "开始时间戳（纳秒）"},
            "end_time": {"type": "number", "description": "结束时间戳（纳秒）"},
            "api_names": {"type": "array", "items": {"type": "string"}, "description": "接口名列表"},
            "trace_ids": {"type": "array", "items": {"type": "string"}, "description": "TraceID列表"},
            "includes": {"type": "array", "items": {"type": "string"}, "description": "返回字段包含"},
            "excludes": {"type": "array", "items": {"type": "string"}, "description": "返回字段排除"},
            "service_name": {"type": "string", "description": "服务名"},
            "instance_name": {"type": "string", "description": "实例名"},
            "protocol": {"type": "string", "description": "协议"},
            "p_trace_id": {"type": "string", "description": "父Trace ID"},
            "only_body": {"type": "boolean", "description": "只返回requestBody"},
            "with_sub_record": {"type": "boolean", "description": "包含下游请求"},
            "all_filters": {"type": "array", "items": {"type": "string"}, "description": "统一过滤条件"},
            "no_need_routing": {"type": "boolean", "description": "是否不需要routing"},
            "flow_type": {"type": "integer", "description": "流量类型，默认0：流量，1：用例"},
        },
        "required": ["app_server_name"],
    },
)


async def execute_record_search(input_args: dict[str, Any]) -> str:
    """按条件检索录制流量明细"""
    _apply_record_search_defaults(input_args)

    app_server_name = input_args["app_server_name"]
    module_id, auth_headers, uctx = await resolve_logreplay_prereqs(app_server_name)

    # 构建实际请求体（按 Go convertRecordSearchInputToReq 构造 base_req/page_req）
    request_body = {
        "base_req": {"username": uctx["user_id"]},
        "page_req": {
            "page": input_args.get("page", 1),
            "page_size": input_args.get("page_size", 20),
        },
        "module_id": module_id,
        "commit_id": input_args.get("commit_id", ""),
        "start_time": input_args.get("start_time"),
        "end_time": input_args.get("end_time"),
        "api_names": input_args.get("api_names", []),
        "trace_ids": input_args.get("trace_ids", []),
        "includes": input_args.get("includes", []),
        "excludes": input_args.get("excludes", []),
        "service_name": input_args.get("service_name", ""),
        "instance_name": input_args.get("instance_name", ""),
        "protocol": input_args.get("protocol", ""),
        "p_trace_id": input_args.get("p_trace_id", ""),
        "only_body": input_args.get("only_body", False),
        "with_sub_record": input_args.get("with_sub_record", False),
        "all_filters": input_args.get("all_filters", []),
        "no_need_routing": input_args.get("no_need_routing", False),
        "flow_type": input_args.get("flow_type", 0),
    }

    caller = HttpCaller()
    result = await caller.call(
        request_body=request_body,
        host=get_url("logreplay"),
        path=API_RECORD_SEARCH,
        extra_headers=auth_headers,
    )
    _decode_record_search_base64_fields(result)
    return json.dumps(result, ensure_ascii=False)


# === AI Generated Code Start wenning ===
def _decode_record_search_base64_fields(result: Any) -> None:
    """将 RecordSearch 响应中的 request / response 从 base64 解码为字符串。

    - 仅对 result.data[].request、result.data[].response 进行原地解码
    - 解码失败（非合法 base64 或非 UTF-8）时保持原值，避免影响其他字段
    """
    if not isinstance(result, dict):
        return
    data = result.get("data")
    if not isinstance(data, list):
        return
    for item in data:
        if not isinstance(item, dict):
            continue
        for field in ("request", "response"):
            value = item.get(field)
            if not isinstance(value, str) or not value:
                continue
            try:
                item[field] = base64.b64decode(value).decode("utf-8", errors="replace")
            except (ValueError, TypeError):
                # 非合法 base64，保留原值
                continue
# === AI Generated Code End ===


# ===================== GetGoReplayNodeList =====================

GET_GO_REPLAY_NODE_LIST_DEF = make_tool_definition(
    name="GetGoReplayNodeList",
    description="获取指定服务的GoReplay节点列表",
    parameters={
        "type": "object",
        "properties": {
            "app_server_name": {"type": "string", "description": "服务名称，格式 app.server"},
        },
        "required": ["app_server_name"],
    },
)


async def execute_get_go_replay_node_list(input_args: dict[str, Any]) -> str:
    """获取指定服务的GoReplay节点列表"""
    app_server_name = input_args["app_server_name"]
    module_id, auth_headers, uctx = await resolve_logreplay_prereqs(app_server_name)

    # Go 中会将 app_server_name 拆为 app + server
    parts = app_server_name.split(".", 1)
    request_body = {
        "base_req": {"username": uctx["user_id"]},
        "app": parts[0],
        "server": parts[1] if len(parts) > 1 else "",
        "module_id": module_id,
    }

    caller = HttpCaller()
    result = await caller.call(
        request_body=request_body,
        host=get_url("logreplay"),
        path=API_GET_GO_REPLAY_NODE_LIST,
        extra_headers=auth_headers,
    )
    return json.dumps(result, ensure_ascii=False)


# ===================== StartGoReplay =====================

START_GO_REPLAY_DEF = make_tool_definition(
    name="StartGoReplay",
    description="启动GoReplay录制任务",
    parameters={
        "type": "object",
        "properties": {
            "app_server_name": {"type": "string", "description": "服务名称，格式 app.server"},
            "container_name_params": {
                "type": "object",
                "description": "容器到录制参数的映射，key为容器名",
                "additionalProperties": {
                    "type": "object",
                    "properties": {
                        "is_without_static_go_replay": {
                            "type": "boolean",
                            "description": "是否非静态goreplay，默认false",
                        },
                        "go_replay_params": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "ip_port": {"type": "string", "description": "抓包地址 ip:port"},
                                    "protocol": {"type": "string", "description": "协议"},
                                    "protocol_service_version": {"type": "string", "description": "协议版本"},
                                    "is_udp": {"type": "boolean", "description": "是否UDP，默认false"},
                                    "is_agent": {"type": "boolean", "description": "是否Agent，默认false"},
                                    "flux_switch": {"type": "integer", "description": "流量转用例开关，0关1开"},
                                    "verbose": {"type": "integer", "description": "日志等级，默认1"},
                                    "extend": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "description": "扩展参数。可用值：--output-logreplay-record-limit（录制条数上限）",
                                    },
                                    "record_time": {"type": "integer", "description": "定时录制时长（小时），默认6"},
                                    "only_one_process": {
                                        "type": "boolean",
                                        "description": "单容器单进程开关，默认false",
                                    },
                                },
                            },
                        },
                    },
                },
            },
        },
        "required": ["app_server_name", "container_name_params"],
    },
)


async def execute_start_go_replay(input_args: dict[str, Any]) -> str:
    """启动GoReplay录制任务"""
    app_server_name = input_args["app_server_name"]
    module_id, auth_headers, uctx = await resolve_logreplay_prereqs(app_server_name)

    # === AI Generated Code Start lovli===
    # protocol_service_name 与 app_server_name 一致，不由大模型传入，由代码统一注入，避免大模型传错
    container_name_params = input_args.get("container_name_params") or {}
    if isinstance(container_name_params, dict):
        for _container_name, container_cfg in container_name_params.items():
            if not isinstance(container_cfg, dict):
                continue
            go_replay_params = container_cfg.get("go_replay_params") or []
            if not isinstance(go_replay_params, list):
                continue
            for param in go_replay_params:
                if isinstance(param, dict):
                    param["protocol_service_name"] = app_server_name
    # === AI Generated Code End lovli===

    # Go 中会将 app_key 注入请求体、拆分 app/server、设置 source、user
    parts = app_server_name.split(".", 1)
    request_body = {
        **input_args,
        "base_req": {"username": uctx["user_id"]},
        "module_id": module_id,
        "user": uctx["user_id"],
        "app": parts[0],
        "server": parts[1] if len(parts) > 1 else "",
        "source": "skill",
        "app_key": auth_headers.get("AppKey", ""),
    }

    caller = HttpCaller()
    result = await caller.call(
        request_body=request_body,
        host=get_url("logreplay"),
        path=API_START_GO_REPLAY,
        extra_headers=auth_headers,
    )
    output = _convert_start_go_replay_output(result)
    return json.dumps(output or result, ensure_ascii=False)


def _convert_start_go_replay_output(result: dict[str, Any]) -> Optional[dict[str, Any]]:
    """将 StartGoReplay 原始响应转换为与 MCP 一致的精简输出。"""
    task_result = result.get("task_result")
    if not isinstance(task_result, list) or not task_result:
        return None

    output_items: list[dict[str, Any]] = []
    for item in task_result:
        if not isinstance(item, dict):
            continue
        output_items.append(
            {
                "task_ids": item.get("task_ids") or item.get("goReplayTaskIds") or [],
                "container_name": item.get("container_name", ""),
                "error_code": item.get("error_code", 0),
                "msg": item.get("msg", ""),
            }
        )

    if not output_items:
        return None
    return {"task_result": output_items}



# ===================== GetGoReplayExecTask =====================

GET_GO_REPLAY_EXEC_TASK_DEF = make_tool_definition(
    name="GetGoReplayExecTask",
    description="获取GoReplay录制任务列表",
    parameters={
        "type": "object",
        "properties": {
            "app_server_name": {"type": "string", "description": "服务名称，格式 app.server"},
            "start_time": {"type": "string", "description": "开始时间 YYYY-MM-DD HH:mm:ss"},
            "end_time": {"type": "string", "description": "结束时间 YYYY-MM-DD HH:mm:ss"},
            "ip_port": {"type": "string", "description": "IP端口过滤"},
            "page": {"type": "integer", "description": "页码，默认1"},
            "page_size": {"type": "integer", "description": "每页数量，默认20"},
            "status": {"type": "array", "items": {"type": "integer"}, "description": "状态过滤列表"},
            "user": {"type": "string", "description": "用户名"},
        },
        "required": ["app_server_name"],
    },
)


async def execute_get_go_replay_exec_task(input_args: dict[str, Any]) -> str:
    """获取GoReplay录制任务列表"""
    _apply_get_go_replay_exec_task_defaults(input_args)

    app_server_name = input_args["app_server_name"]
    module_id, auth_headers, uctx = await resolve_logreplay_prereqs(app_server_name)

    # Go: if input.User == "" { input.User = content.Uid }
    if not input_args.get("user"):
        input_args["user"] = uctx["user_id"]

    request_body = {
        "base_req": {"username": uctx["user_id"]},
        "page_req": {
            "page": input_args.get("page", 1),
            "page_size": input_args.get("page_size", 20),
        },
        "module_id": module_id,
        "start_time": input_args.get("start_time", ""),
        "end_time": input_args.get("end_time", ""),
        "ip_port": input_args.get("ip_port", ""),
        "status": input_args.get("status", []),
        "user": input_args.get("user", ""),
    }



    caller = HttpCaller()
    result = await caller.call(
        request_body=request_body,
        host=get_url("logreplay"),
        path=API_GET_GO_REPLAY_EXEC_TASK,
        extra_headers=auth_headers,
    )
    return json.dumps(result, ensure_ascii=False)


# ===================== StopGoReplayTask =====================

STOP_GO_REPLAY_TASK_DEF = make_tool_definition(
    name="StopGoReplayTask",
    description="停止正在执行的goreplay录制任务",
    parameters={
        "type": "object",
        "properties": {
            "app_server_name": {"type": "string", "description": "服务名称，格式 app.server"},
            "task_id": {"type": "string", "description": "任务ID"},
        },
        "required": ["app_server_name", "task_id"],
    },
)


async def execute_stop_go_replay_task(input_args: dict[str, Any]) -> str:
    """停止正在执行的goreplay录制任务"""
    app_server_name = input_args["app_server_name"]
    module_id, auth_headers, uctx = await resolve_logreplay_prereqs(app_server_name)

    request_body = {
        "base_req": {"username": uctx["user_id"]},
        "task_id": input_args["task_id"],
    }



    caller = HttpCaller()
    result = await caller.call(
        request_body=request_body,
        host=get_url("logreplay"),
        path=API_STOP_GO_REPLAY_TASK,
        extra_headers=auth_headers,
    )
    return json.dumps(result, ensure_ascii=False)


# ===================== GetProtoInfoList =====================

GET_PROTO_INFO_LIST_DEF = make_tool_definition(
    name="GetProtoInfoList",
    description="获取指定服务的协议信息列表（主要获取协议版本号commit_id）",
    parameters={
        "type": "object",
        "properties": {
            "app_server_name": {"type": "string", "description": "服务名称，格式 app.server"},
            "get_type": {"type": "integer", "description": "获取类型，0-获取全部信息，1-获取最新信息"},
        },
        "required": ["app_server_name"],
    },
)


async def execute_get_proto_info_list(input_args: dict[str, Any]) -> str:
    """获取指定服务的协议信息列表"""
    app_server_name = input_args["app_server_name"]
    _module_id, auth_headers, _uctx = await resolve_logreplay_prereqs(app_server_name)

    request_body = {
        "app_server_name": app_server_name,
        "get_type": input_args.get("get_type", 0),
    }



    caller = HttpCaller()
    result = await caller.call(
        request_body=request_body,
        host=get_url("logreplay"),
        path=API_GET_PROTO_INFO_LIST,
        extra_headers=auth_headers,
    )
    return json.dumps(result, ensure_ascii=False)


# ===================== GetProtocolName =====================

GET_PROTOCOL_NAME_DEF = make_tool_definition(
    name="GetProtocolName",
    description="获取具体的协议类型名称（一般在获取GoreplayNodeList后调用）",
    parameters={
        "type": "object",
        "properties": {
            "app_server_name": {"type": "string", "description": "服务名称，格式 app.server"},
            "docker_name": {"type": "string", "description": "容器名称"},
            "service_name": {"type": "string", "description": "项目中单一服务名"},
            "env": {"type": "string", "description": "环境"},
        },
        "required": ["app_server_name", "docker_name", "service_name", "env"],
    },
)


async def execute_get_protocol_name(input_args: dict[str, Any]) -> str:
    """获取具体的协议类型名称"""
    app_server_name = input_args["app_server_name"]
    _module_id, auth_headers, uctx = await resolve_logreplay_prereqs(app_server_name)

    parts = app_server_name.split(".", 1)
    request_body = {
        "base_req": {"username": uctx["user_id"]},
        "service_name": input_args["service_name"],
        "env": input_args["env"],
        "app": parts[0],
        "server": parts[1] if len(parts) > 1 else "",
        "container_name": input_args["docker_name"],
    }



    caller = HttpCaller()
    result = await caller.call(
        request_body=request_body,
        host=get_url("logreplay"),
        path=API_GET_PROTOCOL_NAME,
        extra_headers=auth_headers,
    )
    return json.dumps(result, ensure_ascii=False)


# ===================== GetTrpcPluginInstanceList =====================

# === AI Generated Code Start lovli===

GET_TRPC_PLUGIN_INSTANCE_LIST_DEF = make_tool_definition(
    name="GetTrpcPluginInstanceList",
    description="获取tRPC插件录制方式的节点实例列表（通过trpc插件方式录制时使用，区别于GoReplay录制方式）",
    parameters={
        "type": "object",
        "properties": {
            "app_server_name": {"type": "string", "description": "服务名称，格式 app.server"},
            "onlyReplay": {"type": "boolean", "description": "是否只返回回放节点，默认false"},
        },
        "required": ["app_server_name"],
    },
)


async def execute_get_trpc_plugin_instance_list(input_args: dict[str, Any]) -> str:
    """获取tRPC插件录制方式的节点实例列表"""
    app_server_name = input_args["app_server_name"]
    module_id, auth_headers, uctx = await resolve_logreplay_prereqs(app_server_name)

    request_body = {
        "base_req": {"username": uctx["user_id"]},
        "module_id": module_id,
        "onlyReplay": input_args.get("onlyReplay", False),
    }

    caller = HttpCaller()
    result = await caller.call(
        request_body=request_body,
        host=get_url("logreplay"),
        path=API_GET_TRPC_PLUGIN_INSTANCE_LIST,
        extra_headers=auth_headers,
    )
    return json.dumps(result, ensure_ascii=False)

# === AI Generated Code End lovli===


# ===================== UpdateTrpcPluginConfig =====================

# === AI Generated Code Start lovli===

UPDATE_TRPC_PLUGIN_CONFIG_DEF = make_tool_definition(
    name="UpdateTrpcPluginConfig",
    description="更新tRPC插件节点配置（用于开启/关闭录制或回放，修改录制参数等）。调用前【必须】先通过 GetTrpcPluginInstanceList 获取节点列表。list 允许多个不同 docker_name 的 info，但同一 docker_name 只能放一个 info（默认取命中的第一条 Instance 的 info）；config 为单对象，默认取查询结果 list 第一个元素的 config 作为基础，仅覆盖需要修改的字段。log_level 默认 4(Info，取值 2=Error/3=Warn/4=Info/5=Debug)；recordLimitSpeed 默认 10。过滤器 config.filters 仅支持 APINameFilter/RequestFieldFilter/MessageFieldFilter/QQliveHeadUnmarshalFilter 四种，每种最多一个；开启 APINameFilter 时必须填 api_whitelist，开启 RequestFieldFilter 时必须填 field_whitelist，否则后端拒绝录制所有请求",
    parameters={
        "type": "object",
        "properties": {
            "app_server_name": {"type": "string", "description": "服务名称，格式 app.server"},
            "list": {
                "type": "array",
                "description": "要更新的节点 Info 列表，元素来自 GetTrpcPluginInstanceList 返回的 instance.info。允许包含多个不同 docker_name 的 info，但同一 docker_name 只能放一个 info（默认取命中的第一条 Instance 的 info）",
                "items": {
                    "type": "object",
                    "properties": {
                        "module_id": {"type": "string", "description": "模块ID"},
                        "docker_env": {"type": "string", "description": "容器环境"},
                        "docker_name": {"type": "string", "description": "容器名"},
                        "ip": {"type": "string", "description": "IP地址"},
                        "service_name": {"type": "string", "description": "服务名"},
                        "port": {"type": "integer", "description": "端口"},
                        "commit_id": {"type": "string", "description": "git commit id"},
                        "commit_msg": {"type": "string", "description": "git commit msg"},
                        "sdk_version": {"type": "string", "description": "sdk版本"},
                        "update_time": {"type": "string", "description": "更新时间"},
                        "app_name": {"type": "string", "description": "业务名"},
                        "module_name": {"type": "string", "description": "模块名"},
                        "repo_url": {"type": "string", "description": "仓库地址"},
                        "lang": {"type": "string", "description": "模块语言"},
                        "platform": {"type": "string", "description": "发布平台"},
                        "protocol": {"type": "string", "description": "服务协议"},
                        "filters": {"type": "array", "items": {"type": "string"}, "description": "可用过滤器列表"},
                        "sdk_type": {"type": "string", "description": "接入类型"},
                        "aspects": {"type": "array", "items": {"type": "string"}, "description": "可用切面配置列表"},
                        "full_set_name": {"type": "string", "description": "set名"},
                    },
                },
            },
            "config": {
                "type": "object",
                "description": "节点配置对象（不是数组）。默认取 GetTrpcPluginInstanceList 返回的 list 第一个元素的 config 作为基础，仅覆盖需要修改的字段。enable=true 开启录制/回放，is_replay_server=false 为录制模式，is_replay_server=true 为回放模式",
                "properties": {
                    "is_replay_server": {"type": "boolean", "description": "是否为回放服务器，false=录制模式（启动录制），true=回放模式（将节点设置成回放模式）"},
                    "type": {"type": "integer", "description": "节点类型"},
                    "enable": {"type": "boolean", "description": "录制回放总开关，true=开启，false=关闭"},
                    "write_content_log": {"type": "boolean", "description": "记录请求内容到日志"},
                    "log_level": {"type": "integer", "description": "根日志等级。2=Error，3=Warn，4=Info，5=Debug。默认 4（Info）"},
                    "api_whitelist": {"type": "array", "items": {"type": "string"}, "description": "录制的接口白名单。开启 APINameFilter 时必填，否则后端拒绝录制所有请求"},
                    "cpu_usage_threshold": {"type": "number", "description": "CPU占用阈值百分比"},
                    "recordLimitSpeed": {"type": "integer", "description": "录制速度限制(次/秒)，<0表示不录制。默认 10"},
                    "rise_quickly": {"type": "boolean", "description": "录制速率快速上升开关"},
                    "state": {"type": "string", "description": "状态（none|record|replay|bench）"},
                    "aspect_attribute": {"type": "object", "additionalProperties": {"type": "string"}, "description": "切面特性"},
                    "field_whitelist": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {"path": {"type": "string"}, "value": {"type": "string"}},
                        },
                        "description": "请求字段过滤白名单。开启 RequestFieldFilter 时必填，否则后端拒绝录制所有请求。每项格式 {path: 请求字段路径, value: 匹配值}",
                    },
                    "filters": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {
                                    "type": "string",
                                    "enum": [
                                        "APINameFilter",
                                        "RequestFieldFilter",
                                        "MessageFieldFilter",
                                        "QQliveHeadUnmarshalFilter",
                                    ],
                                    "description": "过滤器名称。仅支持以下 4 种：APINameFilter(接口名过滤，常用，需配合 api_whitelist)、RequestFieldFilter(请求字段过滤，常用，需配合 field_whitelist)、MessageFieldFilter、QQliveHeadUnmarshalFilter",
                                },
                                "enable": {"type": "boolean", "description": "过滤器开关"},
                                "ext": {"type": "object", "additionalProperties": {"type": "string"}, "description": "附加信息"},
                            },
                        },
                        "description": "过滤器配置（可选，数组最多 4 个元素，每种过滤器最多只能出现一次）。开启 APINameFilter 必须同时填 api_whitelist；开启 RequestFieldFilter 必须同时填 field_whitelist，否则后端会拒绝录制所有请求",
                    },
                    "filter_relation": {"type": "integer", "description": "过滤器关系，1全与，2全或"},
                    "mem_usage_threshold": {"type": "number", "description": "内存占用阈值百分比"},
                    "is_whitelist_must_record": {"type": "boolean", "description": "白名单流量一定录制"},
                    "enable_not_whitelist": {"type": "boolean", "description": "是否录制非白名单流量"},
                    "net_work_band_with_threshold": {"type": "number", "description": "网络带宽阈值(Mb)"},
                    "block_device_write_ps": {"type": "number", "description": "块设备每秒写MB"},
                    "block_device_read_ps": {"type": "number", "description": "块设备每秒读MB"},
                    "global_aspect": {"type": "boolean", "description": "是否启用全局切面配置"},
                    "cron_expression": {"type": "string", "description": "定时开启录制开关"},
                    "duration": {"type": "integer", "description": "定时开关开启时间"},
                },
            },
            "pnconfig": {
                "type": "object",
                "description": "perfMetrics 插件节点配置（可选），基于现有配置覆盖修改",
                "properties": {
                    "log_level": {"type": "integer", "description": "日志级别"},
                    "enable_cpu_threshold": {"type": "integer", "description": "触发pprof采集cpu阈值(%)"},
                    "enable_mem_threshold": {"type": "integer", "description": "触发pprof采集mem阈值(%)"},
                    "disable_cpu_threshold": {"type": "integer", "description": "告警失效cpu阈值"},
                    "disable_mem_threshold": {"type": "integer", "description": "告警失效mem阈值"},
                    "enable_trace": {"type": "boolean", "description": "是否开启trace profile采集"},
                    "rsp_timeout_threshold": {"type": "integer", "description": "接口请求超时时间阈值"},
                    "rsp_timeout_rate_threshold": {"type": "integer", "description": "接口请求超时率阈值"},
                },
            },
            "sdk_type": {"type": "string", "description": "接入类型，默认 trpc_tracing_logreplay"},
            "set_name": {
                "type": "array",
                "items": {"type": "string"},
                "description": "set名列表（可选）",
            },
        },
        "required": ["app_server_name", "list", "config"],
    },
)


def _normalize_trpc_plugin_update_payload(input_args: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """规范化 tRPC 插件更新入参。

    规则：
    - list 允许多个不同 docker_name 的 info；同一 docker_name 仅保留第一条 info（去重）。
    - 若误传完整 Instance（含 info/config），自动抽取 info；同时记录 list 第一个元素的 config 作为默认基础。
    - config 必须是单对象（非数组）。若未显式传入或为空，则使用 list 第一个元素携带的 config 作为默认。
    - 隐性默认值：log_level 缺省为 4（Info）；recordLimitSpeed 缺省为 10。
    """
    raw_list = input_args.get("list", [])
    normalized_list: list[dict[str, Any]] = []
    seen_docker_names: set[str] = set()
    default_config: dict[str, Any] = {}

    if isinstance(raw_list, list):
        for item in raw_list:
            if not isinstance(item, dict):
                continue
            info = item.get("info") if isinstance(item.get("info"), dict) else item
            if not isinstance(info, dict):
                continue
            docker_name = info.get("docker_name")
            if isinstance(docker_name, str) and docker_name:
                if docker_name in seen_docker_names:
                    continue
                seen_docker_names.add(docker_name)
            normalized_list.append(info)
            # 仅以 list 第一个元素携带的 config 作为默认基础
            if not default_config and isinstance(item.get("config"), dict):
                default_config = item["config"]

    config = input_args.get("config")
    if not isinstance(config, dict) or not config:
        config = dict(default_config) if default_config else {}
    else:
        # 显式传入的 config 与默认 config 合并：以显式值为准，未指定字段保留默认
        merged: dict[str, Any] = dict(default_config) if default_config else {}
        merged.update(config)
        config = merged

    # 隐性默认值
    if config.get("log_level") in (None, 0, ""):
        config["log_level"] = 4
    if config.get("recordLimitSpeed") in (None, "",):
        config["recordLimitSpeed"] = 10

    return normalized_list, config


async def execute_update_trpc_plugin_config(input_args: dict[str, Any]) -> str:
    """更新tRPC插件节点配置（录制/回放开关、参数等）"""
    app_server_name = input_args["app_server_name"]
    module_id, auth_headers, uctx = await resolve_logreplay_prereqs(app_server_name)
    update_list, config = _normalize_trpc_plugin_update_payload(input_args)

    request_body = {
        "base_req": {"username": uctx["user_id"]},
        "module_id": module_id,
        "list": update_list,
        "config": config,
        "sdk_type": input_args.get("sdk_type", "trpc_tracing_logreplay"),
    }


    # 可选字段：仅在用户传入时添加
    if "pnconfig" in input_args:
        request_body["pnconfig"] = input_args["pnconfig"]
    if "set_name" in input_args:
        request_body["set_name"] = input_args["set_name"]

    caller = HttpCaller()
    result = await caller.call(
        request_body=request_body,
        host=get_url("logreplay"),
        path=API_UPDATE_TRPC_PLUGIN_CONFIG,
        extra_headers=auth_headers,
    )
    return json.dumps(result, ensure_ascii=False)

# === AI Generated Code End lovli===


# ===================== 默认值辅助函数 =====================


def _apply_record_agg_defaults(args: dict[str, Any]) -> None:
    if not args.get("page"):
        args["page"] = 1
    if not args.get("page_size"):
        args["page_size"] = 20
    s, e = get_default_nano_time_range()
    if not args.get("end_time"):
        args["end_time"] = e
    if not args.get("start_time"):
        args["start_time"] = s
    if not args.get("agg_names"):
        args["agg_names"] = ["apiName", "commitId", "protocol", "instanceName"]


def _apply_record_search_defaults(args: dict[str, Any]) -> None:
    if not args.get("page"):
        args["page"] = 1
    if not args.get("page_size"):
        args["page_size"] = 20
    s, e = get_default_nano_time_range()
    if not args.get("end_time"):
        args["end_time"] = e
    if not args.get("start_time"):
        args["start_time"] = s


def _apply_get_go_replay_exec_task_defaults(args: dict[str, Any]) -> None:
    if not args.get("page"):
        args["page"] = 1
    if not args.get("page_size"):
        args["page_size"] = 20
    s, e = get_default_str_time_range()
    if not args.get("end_time"):
        args["end_time"] = e
    if not args.get("start_time"):
        args["start_time"] = s


# 注册工具
registry.register(MULTI_GET_TASK_STATUS_DEF, execute_multi_get_task_status)
registry.register(GET_GOREPLAY_STATUS_DEF, execute_get_goreplay_status)
registry.register(RECORD_AGG_DEF, execute_record_agg)
registry.register(RECORD_SEARCH_DEF, execute_record_search)
registry.register(GET_GO_REPLAY_NODE_LIST_DEF, execute_get_go_replay_node_list)
registry.register(START_GO_REPLAY_DEF, execute_start_go_replay)
registry.register(GET_GO_REPLAY_EXEC_TASK_DEF, execute_get_go_replay_exec_task)
registry.register(STOP_GO_REPLAY_TASK_DEF, execute_stop_go_replay_task)
registry.register(GET_PROTO_INFO_LIST_DEF, execute_get_proto_info_list, validator=LOGREPLAY_RET_CODE_VALIDATOR)
registry.register(GET_PROTOCOL_NAME_DEF, execute_get_protocol_name)
registry.register(GET_TRPC_PLUGIN_INSTANCE_LIST_DEF, execute_get_trpc_plugin_instance_list)
registry.register(UPDATE_TRPC_PLUGIN_CONFIG_DEF, execute_update_trpc_plugin_config)
