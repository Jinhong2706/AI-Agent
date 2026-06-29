"""
@generated-by AI: lovli
@generated-date 2026-04-02

LogReplay 本地工具基础模块
提供 HTTP 调用、配置加载、工具注册、前置依赖解析（module_id / 鉴权 header）
"""
from __future__ import annotations  # added by AI wenning

import contextvars
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Optional
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

logger = logging.getLogger(__name__)

# 当前正在执行的工具名（由 ToolRunner.run 设置，HttpCaller.call 自动读取）
current_tool_name: contextvars.ContextVar[str] = contextvars.ContextVar("current_tool_name", default="")  # added by AI wenning

# 配置文件路径（相对于本文件所在目录的上级目录）
_CONFIG_PATH = Path(__file__).parent.parent / "config.json"
_config: Optional[dict] = None


def get_config() -> dict:
    """加载并缓存配置文件"""
    global _config
    if _config is None:
        with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
            _config = json.load(f)
    return _config


# === AI Generated Code Start wenning ===
def get_url(service: str) -> str:
    """
    从 config.json 的 urls 对象中获取服务 URL。

    Args:
        service: 服务名，可选值：logreplay / utest_perf / utest_topology / utest_user_center

    Returns:
        服务 URL 字符串

    Raises:
        ValueError: 未找到对应服务的 URL 配置
    """
    config = get_config()
    url = config.get("urls", {}).get(service, "")
    if url:
        return url
    raise ValueError(
        f"URL for service '{service}' not found in config.json. "
        f"Please set urls.{service} in config.json."
    )


def get_default(key: str, fallback: str = "") -> str:
    """
    从 config.json 的 defaults 对象中获取配置项。

    Args:
        key: 配置项名称，如 execution_group_id
        fallback: 默认值

    Returns:
        配置值字符串
    """
    config = get_config()
    return config.get("defaults", {}).get(key, "") or fallback
# === AI Generated Code End ===


# === AI Generated Code Start lovli===
# ===================== 响应校验器 =====================


class ResponseValidator:
    """
    业务响应校验器基类。

    不同后端接口的成功码字段和值各不相同，通过在 registry.register 时
    注入不同的 validator 实例来解耦校验逻辑。
    """

    def validate(self, data: dict) -> tuple[bool, str]:
        """
        校验业务响应是否成功。

        Args:
            data: 解析后的响应 dict

        Returns:
            (is_success, error_message)
            is_success 为 True 时 error_message 为空字符串
        """
        raise NotImplementedError


class LogReplayValidator(ResponseValidator):
    """
    标准 logreplay 接口校验器。
    成功条件：base_rsp.code == 100000
    """

    def validate(self, data: dict) -> tuple[bool, str]:
        base_rsp = data.get("base_rsp", {})
        code = base_rsp.get("code")
        if code is None:
            return True, ""  # 无 base_rsp.code，不做判断
        if code != 100000:
            msg = base_rsp.get("msg", f"业务错误码: {code}")
            return False, msg
        return True, ""


class LogReplayRetCodeValidator(ResponseValidator):
    """
    logreplay 特殊接口校验器（如 GetProtoInfoList）。
    成功条件：base_rsp.ret_code == 0
    """

    def validate(self, data: dict) -> tuple[bool, str]:
        base_rsp = data.get("base_rsp", {})
        ret_code = base_rsp.get("ret_code")
        if ret_code is None:
            return True, ""  # 无 ret_code，不做判断
        if ret_code != 0:
            msg = base_rsp.get("ret_msg", f"业务错误码: {ret_code}")
            return False, msg
        return True, ""


class UtestValidator(ResponseValidator):
    """
    utest 接口校验器。
    成功条件：顶层 code == 0
    """

    def validate(self, data: dict) -> tuple[bool, str]:
        code = data.get("code")
        if code is None:
            return True, ""
        if code != 0:
            msg = data.get("msg", f"业务错误码: {code}")
            return False, msg
        return True, ""


class AutoDetectValidator(ResponseValidator):
    """
    自动探测校验器（向后兼容的默认行为）。
    根据响应结构自动判断使用哪种校验逻辑，优先级从高到低：

    1. base_rsp 中有 ret_code → 按 ret_code==0 校验（如 GetProtoInfoList）
       注意：即使同层还有 code 字段也会被忽略，ret_code 优先级最高
    2. base_rsp 中有 code    → 按 code==100000 校验（标准 logreplay 接口）
    3. 顶层有 code（无 base_rsp）→ 按 code==0 校验（utest 接口）
    4. 以上都不匹配 → 视为成功

    如果某个接口的响应格式不符合以上任何模式，应在 register 时
    显式传入对应的 validator，而非依赖自动探测。
    """

    _logreplay = LogReplayValidator()
    _ret_code = LogReplayRetCodeValidator()
    _utest = UtestValidator()

    def validate(self, data: dict) -> tuple[bool, str]:
        base_rsp = data.get("base_rsp")
        if isinstance(base_rsp, dict):
            # ret_code 优先：同时有 ret_code 和 code 时只看 ret_code
            if "ret_code" in base_rsp:
                return self._ret_code.validate(data)
            return self._logreplay.validate(data)
        if "code" in data:
            return self._utest.validate(data)
        return True, ""


# 预设校验器实例，注册时直接引用
LOGREPLAY_VALIDATOR = LogReplayValidator()
LOGREPLAY_RET_CODE_VALIDATOR = LogReplayRetCodeValidator()
UTEST_VALIDATOR = UtestValidator()
AUTO_DETECT_VALIDATOR = AutoDetectValidator()

# === AI Generated Code End lovli===


# === AI Generated Code Start lovli===
def get_default_nano_time_range() -> tuple[float, float]:
    """获取默认时间范围（纳秒时间戳），最近 30 天"""
    now = datetime.now()
    end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=0)
    start_30 = (now - timedelta(days=30)).replace(hour=0, minute=0, second=0, microsecond=0)
    return start_30.timestamp() * 1e9, end_of_day.timestamp() * 1e9


def get_default_str_time_range() -> tuple[str, str]:
    """获取默认时间范围（字符串格式 YYYY-MM-DD HH:MM:SS），最近 30 天"""
    now = datetime.now()
    end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=0)
    start_30 = (now - timedelta(days=30)).replace(hour=0, minute=0, second=0, microsecond=0)
    fmt = "%Y-%m-%d %H:%M:%S"
    return start_30.strftime(fmt), end_of_day.strftime(fmt)
# === AI Generated Code End lovli===


class ToolRegistry:
    """本地工具注册中心"""

    def __init__(self):
        self._tools: list[dict] = []
        self._executors: dict[str, Callable] = {}
        self._validators: dict[str, "ResponseValidator"] = {}

    def register(
        self,
        tool_def: dict,
        executor: Callable,
        *,
        validator: Optional["ResponseValidator"] = None,
    ):
        """
        注册工具定义和执行函数

        Args:
            tool_def: 工具定义
            executor: 执行函数
            validator: 响应校验器，不传则使用默认校验器（自动探测）
        """
        name = tool_def["function"]["name"]
        self._tools.append(tool_def)
        self._executors[name] = executor
        if validator is not None:
            self._validators[name] = validator

    def get_tools(self) -> list[dict]:
        """获取所有已注册的工具定义"""
        return self._tools[:]

    def get_executor(self, name: str) -> Optional[Callable]:
        """根据工具名获取执行函数"""
        return self._executors.get(name)

    def get_validator(self, name: str) -> Optional["ResponseValidator"]:
        """根据工具名获取响应校验器，未注册则返回 None"""
        return self._validators.get(name)


# 全局工具注册中心
registry = ToolRegistry()


class HttpCaller:
    """统一的 HTTP 调用器（基于标准库 urllib）"""

    def __init__(
        self,
        host: str = "",
        path: str = "",
        headers: Optional[dict[str, str]] = None,
        timeout: int = 30,
    ):
        self.host = host
        self.path = path
        self.headers = headers or {"Content-Type": "application/json"}
        self.timeout = timeout

    async def call(
        self,
        request_body: dict[str, Any],
        host: Optional[str] = None,
        path: Optional[str] = None,
        extra_headers: Optional[dict[str, str]] = None,
    ) -> dict[str, Any]:
        """
        发起 HTTP POST 请求

        Args:
            request_body: 请求体（dict，自动序列化为 JSON）
            host: 覆盖默认 host
            path: 覆盖默认 path
            extra_headers: 额外的请求头

        Returns:
            响应体解析后的 dict

        Raises:
            ValueError: host 或 path 未设置
            HTTPError: HTTP 请求失败
            URLError: 网络连接失败
        """
        actual_host = host or self.host
        actual_path = path or self.path

        if not actual_host:
            raise ValueError("host is required")
        if not actual_path:
            raise ValueError("path is required")

        url = actual_host + actual_path

        headers = {**self.headers}
        if extra_headers:
            headers.update(extra_headers)

        # === AI Generated Code Start wenning ===
        # 自动注入 Logreplay-Skill 请求头（值为当前工具名）
        tool_name = current_tool_name.get()
        if tool_name:
            headers["Logreplay-Skill"] = tool_name
        # === AI Generated Code End ===

        data = json.dumps(request_body).encode("utf-8")
        req = Request(url, data=data, headers=headers, method="POST")

        with urlopen(req, timeout=self.timeout) as resp:
            resp_body = resp.read().decode("utf-8")
            result = json.loads(resp_body) if resp_body.strip() else {}

            # === AI Generated Code Start lovli===
            # 从响应头提取网关/tRPC 错误信息，用于报错时辅助排查
            gateway_error = _extract_gateway_error_headers(resp)
            if gateway_error:
                result["_gateway_error"] = gateway_error
                logger.warning(
                    "接口 %s 响应头包含错误信息: %s", actual_path, gateway_error,
                )
            # === AI Generated Code End lovli===

            return result


# === AI Generated Code Start lovli===
# logreplay 接口网关/tRPC 错误响应头名称
_GATEWAY_ERROR_HEADERS = (
    "Epp-Gateway-Code",
    "Epp-Gateway-Msg",
    "Trpc-Error-Msg",
    "Trpc-Func-Ret",
)

# 网关/tRPC 成功码（出现且等于该值表示成功，不视为错误）
_GATEWAY_SUCCESS_CODE = "100000"
# 需要按"存在且不等于成功码"判定的状态码字段
_GATEWAY_CODE_HEADERS = ("Epp-Gateway-Code", "Trpc-Func-Ret")


def _extract_gateway_error_headers(resp) -> Optional[dict[str, str]]:
    """
    从 HTTP 响应头中提取网关/tRPC 错误信息。

    判定规则：
    - 若 `Epp-Gateway-Code` / `Trpc-Func-Ret` 均不存在，视为无状态信息，直接返回 None。
    - 若上述字段存在且值等于成功码 `100000`，视为成功，返回 None。
    - 其他情况（字段存在且非成功码）才视为错误，连同 Msg 字段一并返回。

    Returns:
        错误时返回包含相关头信息的 dict；成功或无状态头时返回 None。
    """
    code_values = {
        name: resp.headers.get(name, "") for name in _GATEWAY_CODE_HEADERS
    }
    # 所有状态码字段都缺失 → 无从判断，直接放行
    if not any(code_values.values()):
        return None
    # 任一状态码字段存在且不为成功码 → 视为错误
    has_error = any(
        value and value != _GATEWAY_SUCCESS_CODE for value in code_values.values()
    )
    if not has_error:
        return None
    error_info: dict[str, str] = {}
    for header_name in _GATEWAY_ERROR_HEADERS:
        value = resp.headers.get(header_name, "")
        if value:
            error_info[header_name] = value
    return error_info if error_info else None
# === AI Generated Code End lovli===


def make_tool_definition(name: str, description: str, parameters: dict) -> dict:
    """构造标准的工具定义结构"""
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": parameters,
        },
    }


# ===================== API 路径常量（全局统一定义） =====================

# --- 鉴权 ---
API_AUTH_CHECK = "/utest-saas-user/utest/auth/checkAuth"

# --- Topology ---
API_GET_APP_SERVER_DETAIL_BY_NAME = "/protocol/utest/GetAppServerDetailByName"

# --- LogReplay CAS ---
API_GET_CAS_KEY = "/logreplay/trpc.logreplay.app_server.cas_service/GetCasKey"

# --- GoReplay 录制相关 ---
API_MULTI_GET_TASK_STATUS = "/logreplay/trpc.logreplay.goreplay_server.info_service/MultiGetTaskStatus"
API_GET_GOREPLAY_STATUS = "/logreplay/trpc.logreplay.goreplay_server.info_service/GetGoreplayStatus"
API_GET_GO_REPLAY_NODE_LIST = "/logreplay/trpc.logreplay.goreplay_server.info_service/GetAllProtoAndPort"
API_START_GO_REPLAY = "/logreplay/trpc.logreplay.goreplay_server.cmd_service/StartGoReplay"
API_GET_GO_REPLAY_EXEC_TASK = "/logreplay/trpc.logreplay.goreplay_server.info_service/GetGoReplayExecTask"
API_STOP_GO_REPLAY_TASK = "/logreplay/trpc.logreplay.goreplay_server.cmd_service/StopGoreplayTask"
API_GET_PROTO_INFO_LIST = "/logreplay/protocol/list"
API_GET_PROTOCOL_NAME = "/logreplay/trpc.logreplay.goreplay_server.info_service/GetProtocolName"

# --- tRPC 插件录制相关 ---
API_GET_TRPC_PLUGIN_INSTANCE_LIST = "/logreplay/trpc.logreplay.instance_server.instance_service/GetInstanceList"  # added by AI: lovli
API_UPDATE_TRPC_PLUGIN_CONFIG = "/logreplay/trpc.logreplay.instance_server.instance_service/UpdateConfig"  # added by AI: lovli

# --- 录制数据查询 ---
API_RECORD_AGG = "/logreplay/trpc.logreplay.data_server.Record/Agg"
API_RECORD_SEARCH = "/logreplay/trpc.logreplay.data_server.Record/Search"

# --- LogReplay 回放 ---
API_EXECUTE_REPLAY = "/logreplay/trpc.logreplay.replay_server.Replay/Replay"
API_GET_REPLAY_TASK_INFO = "/logreplay/trpc.logreplay.replay_server.Task/TaskInfo"
API_TASK_LIST = "/logreplay/trpc.logreplay.replay_server.Task/TaskList"

# --- LogReplay 报告 ---
API_REPORT_SEARCH = "/logreplay/trpc.logreplay.data_server.Report/Search"
API_REPORT_AGG = "/logreplay/trpc.logreplay.data_server.Report/Agg"
API_RECORD_SEARCH_RESPONSE = "/logreplay/trpc.logreplay.data_server.Record/SearchResponse"
# === AI Generated Code Start lovli===
# 双环境回放结果查询接口（按 task_id + trace_id 查回放响应，支持双 target 对比）
API_REPLAY_SEARCH = "/logreplay/trpc.logreplay.data_server.Replay/Search"
# === AI Generated Code End lovli===
API_DIFF_CONFIG = "/logreplay/trpc.logreplay.data_server.Rule/DiffConfig"
API_SET_DIFF_CONFIG = "/logreplay/trpc.logreplay.data_server.Rule/SetDiffConfig"  # added by AI: lovli

# --- LogReplay 流量编辑规则 ---
API_QUERY_EDIT_RULE_LIST = "/logreplay/trpc.logreplay.data_server.TrafficEdit/QueryEditRuleList"  # added by AI: lovli
# === AI Generated Code Start lovli===
API_EDIT_RULE_CHECK = "/logreplay/trpc.logreplay.data_server.TrafficEdit/EditRuleCheck"
API_CREATE_EDIT_RULE = "/logreplay/trpc.logreplay.data_server.TrafficEdit/CreateEditRule"
API_UPDATE_EDIT_RULE = "/logreplay/trpc.logreplay.data_server.TrafficEdit/UpdateEditRule"
API_DELETE_EDIT_RULE = "/logreplay/trpc.logreplay.data_server.TrafficEdit/DeleteEditRule"
# === AI Generated Code End lovli===

# --- Utest User Center（项目信息） ---
API_GET_ENV_NAME_BY_PROJECT_ID = "/utest-saas-user/ProjectTeamCtrl/getEnvNameByProjectId"  # added by AI: lovli

# --- Utest Perf（原 gRPC 接口转 HTTP） ---
API_GET_FLOW2_SCENE_TASK_LIST = "/perftestApp/api/getFlow2SceneTaskList"
API_CREATE_FLOW2_SCENE = "/perftestApp/api/createFlowToScene"

# 缓存鉴权结果，避免重复调用
_user_context: Optional[dict[str, str]] = None


async def auth_check() -> dict[str, str]:
    """
    使用 user_token + project_token 调用 UTEST_USER_CENTER 鉴权接口，
    获取 groupId / projectId / uid。

    对应 Go: hooks.AuthCheck() → AuthRspContent{GroupId, ProjectId, Uid}

    Returns:
        {"group_id": "...", "project_id": "...", "user_id": "..."}
    """
    config = get_config()
    auth_cfg = config.get("auth", {})
    user_token = auth_cfg.get("user_token", "")
    project_token = auth_cfg.get("project_token", "")

    if not user_token or not project_token:
        raise ValueError(
            "user_token and project_token must be configured in config.json auth section"
        )

    host = get_url("utest_user_center")

    # Go 中 token 是放在 header 里传给鉴权接口的（不是 body）
    caller = HttpCaller()
    result = await caller.call(
        request_body={},
        host=host,
        path=API_AUTH_CHECK,
        extra_headers={
            "user_token": user_token,
            "project_token": project_token,
        },
    )

    if result.get("code") != 0:
        raise RuntimeError(
            f"auth check failed: code={result.get('code')}, msg={result.get('msg')}"
        )

    data = result.get("data", {})
    return {
        "group_id": data.get("groupId", ""),
        "project_id": data.get("projectId", ""),
        "user_id": data.get("uid", ""),
    }


async def get_user_context() -> dict[str, str]:
    """
    获取用户上下文（group_id/project_id/user_id），首次调用时通过鉴权接口获取并缓存。

    对应 Go: hooks.GetAuthRspContent(ctx) → content.GroupId / content.ProjectId / content.Uid

    Returns:
        {"group_id": "...", "project_id": "...", "user_id": "..."}
    """
    global _user_context
    if _user_context is None:
        _user_context = await auth_check()
    return _user_context


# === AI Generated Code Start lovli===
# 缓存 envName 结果，避免重复调用
_env_name_cache: Optional[str] = None


async def get_env_name_by_project_id(project_id: str) -> str:
    """
    通过 projectId 调用 getEnvNameByProjectId 接口获取业务英文名（envName）。

    鉴权方式与 auth_check 一致，使用 user_token + project_token 放在请求头中。

    Args:
        project_id: 项目 ID

    Returns:
        envName 字符串（业务英文名）

    Raises:
        RuntimeError: 接口调用失败
    """
    global _env_name_cache
    if _env_name_cache is not None:
        return _env_name_cache

    config = get_config()
    auth_cfg = config.get("auth", {})
    user_token = auth_cfg.get("user_token", "")
    project_token = auth_cfg.get("project_token", "")

    if not user_token or not project_token:
        raise ValueError(
            "user_token and project_token must be configured in config.json auth section"
        )

    host = get_url("utest_user_center")

    caller = HttpCaller()
    result = await caller.call(
        request_body={"projectId": project_id},
        host=host,
        path=API_GET_ENV_NAME_BY_PROJECT_ID,
        extra_headers={
            "user_token": user_token,
            "project_token": project_token,
        },
    )

    state = result.get("state")
    if state is not None and state != 0:
        raise RuntimeError(
            f"getEnvNameByProjectId failed: state={state}, msg={result.get('msg', '')}"
        )

    env_name = result.get("data", "")
    if not env_name:
        raise RuntimeError(
            "getEnvNameByProjectId returned empty envName, "
            f"response: {result}"
        )

    _env_name_cache = env_name
    return env_name
# === AI Generated Code End lovli===


def get_perf_auth_headers() -> dict[str, str]:
    """
    构建 utest_perf 相关接口的鉴权 header。
    perf 接口（原 gRPC）使用 user_token / project_token 作为 header。

    Returns:
        {"user_token": "...", "project_token": "..."}
    """
    config = get_config()
    auth_cfg = config.get("auth", {})
    return {
        "user_token": auth_cfg.get("user_token", ""),
        "project_token": auth_cfg.get("project_token", ""),
    }


# ===================== 前置依赖：公共远程调用函数 =====================


async def get_app_server_detail(app_server_name: str) -> dict[str, Any]:
    """
    通过 app_server_name 调用 UTEST_TOPOLOGY 的 GetAppServerDetailByName 获取服务详情。

    对应 Go: resolveAppServerDetailByName()
    Go 中 base_req 需要传入 user_name 和 group_id（来自 content）。

    Returns:
        完整响应 dict，包含 app_server_detail.module_id / app_server_detail.uuid 等
    """
    # Go: appServerDetailByNameReq.BaseReq = {UserName: content.Uid, GroupId: content.GroupId}
    uctx = await get_user_context()

    caller = HttpCaller()
    result = await caller.call(
        request_body={
            "base_req": {
                "user_name": uctx["user_id"],
                "group_id": uctx["group_id"],
            },
            "app_server": app_server_name,
        },
        host=get_url("utest_topology"),
        path=API_GET_APP_SERVER_DETAIL_BY_NAME,
    )
    return result


def extract_module_id(detail: dict[str, Any]) -> str:
    """
    从 GetAppServerDetailByName 响应中提取 module_id，优先 module_id，fallback uuid。

    对应 Go: extractModuleID()
    """
    app_detail = detail.get("app_server_detail", {})
    module_id = app_detail.get("module_id", "")
    if not module_id:
        module_id = app_detail.get("uuid", "")
    return module_id


async def resolve_module_id(app_server_name: str) -> str:
    """
    一步到位：通过 app_server_name 获取 module_id。

    内部调用 get_app_server_detail + extract_module_id。
    """
    detail = await get_app_server_detail(app_server_name)
    return extract_module_id(detail)


async def get_cas_key(module_id: str, username: str = "") -> tuple[str, str]:
    """
    通过 module_id 调用 LogReplay 的 GetCasKey 接口获取 CAS 鉴权的 AppId 和 AppKey。

    对应 Go: resolveCasKey()
    注意：GetCasKey 接口本身也需要 user_token / project_token 鉴权 header。

    Returns:
        (app_id, app_key)
    """
    request_body: dict[str, Any] = {"module_id": module_id}
    if username:
        request_body["base_req"] = {"username": username}

    caller = HttpCaller()
    # === AI Generated Code Start lovli===
    # GetCasKey 接口需要在请求头中携带 user_token / project_token 进行鉴权
    result = await caller.call(
        request_body=request_body,
        host=get_url("utest_perf"),
        path=API_GET_CAS_KEY,
        extra_headers=get_perf_auth_headers(),
    )
    # === AI Generated Code End lovli===
    return result.get("id", ""), result.get("key", "")


async def resolve_auth_headers(module_id: str, username: str = "") -> dict[str, str]:
    """
    构建 logreplay 接口的鉴权请求头。
    通过 user_token + project_token 调用 GetCasKey 动态获取 AppId/AppKey。

    对应 Go: resolveHeaderInput() + resolveCasKey()

    Returns:
        鉴权 header dict，可直接传给 HttpCaller.call(extra_headers=...)
    """
    app_id, app_key = await get_cas_key(module_id, username)
    return {
        "AppId": app_id,
        "AppKey": app_key,
    }


async def resolve_logreplay_prereqs(
    app_server_name: str,
    username: Optional[str] = None,
) -> tuple[str, dict[str, str], dict[str, str]]:
    """
    一步到位的 LogReplay 前置依赖解析：
    1. auth_check → user_context (group_id/project_id/user_id)
    2. GetAppServerDetailByName → module_id
    3. GetCasKey → auth_headers (AppId/AppKey)

    大多数 logreplay 工具调用前都需要执行这一步。

    对应 Go: GetAuthRspContent + resolveAppServerDetailByName + resolveHeaderInput

    Args:
        app_server_name: 应用服务名称
        username: 指定用户名，如果提供则优先使用

    Returns:
        (module_id, auth_headers, user_context)
    """
    config = get_config()
    auth_cfg = config.get("auth", {})

    # 尝试获取用户上下文，如果失败则使用token信息构建
    try:
        uctx = await get_user_context()
    except Exception as e:
        logger.warning(f"获取用户上下文失败: {e}，使用token信息构建用户上下文")
        user_token = auth_cfg.get("user_token", "")
        project_token = auth_cfg.get("project_token", "")

        if username:
            user_id = username
        else:
            user_id = "admin"
            if user_token:
                user_id = f"token_user_{user_token[:8]}"

        uctx = {
            "user_id": user_id,
            "group_id": project_token or "",
            "project_id": project_token or "",
        }

    # 如果指定了用户名，覆盖用户上下文中的user_id
    if username:
        uctx["user_id"] = username

    # 获取 module_id
    try:
        module_id = await resolve_module_id(app_server_name)
    except Exception as e:
        logger.warning(f"获取module_id失败: {e}，使用默认值")
        module_id = "default_module"

    # 通过 CAS 获取鉴权 header
    try:
        auth_headers = await resolve_auth_headers(module_id, uctx["user_id"])
    except Exception as e:
        logger.warning(f"获取鉴权header失败: {e}，使用默认值")
        auth_headers = {}

    return module_id, auth_headers, uctx
