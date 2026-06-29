#!/usr/bin/env python3
"""按模块别名统一执行 ADP 多模态能力。

示例：
    python3 scripts/adp_mcp.py list-aliases
    python3 scripts/adp_mcp.py image.hy run '{"Prompt":"一只白色小猫坐在木桌上，写实风格","Resolution":"1024:1024"}'
    python3 scripts/adp_mcp.py image.hy run --step submit '{"Prompt":"一只白色小猫坐在木桌上，写实风格","Resolution":"1024:1024"}'
    python3 scripts/adp_mcp.py image.hy run --step query '{"JobId":"123"}'
"""

from __future__ import annotations

import argparse
import base64 as _b64
import io
import json
import os
import sys
import time
from typing import Any

import requests


def _normalize_console_encoding() -> None:
    """在父进程 locale 不稳定时，强制标准输出保持 UTF-8。"""
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name)
        encoding = (stream.encoding or "").lower().replace("-", "")
        if encoding and encoding != "utf8":
            wrapped = io.TextIOWrapper(stream.buffer, encoding="utf-8", errors="replace")
            setattr(sys, stream_name, wrapped)


def _decode_id(encoded: str) -> str:
    """解码内嵌的 base64 标识。"""
    return _b64.b64decode(encoded).decode()


_normalize_console_encoding()


PLUGIN_ALIASES = {
    "image.hy": {
        "plugin_id": _decode_id("ZDQ2NzIwNjItZWQwNy00NWU1LWE0MTktYjlkOGViNWYwNDcz"),
        "label": "图片生成（3.0）",
    },
    "image.gi": {
        "plugin_id": _decode_id("MGZiYTc1NDEtZjQzYy00MGJkLWJlMzktMTA5NmViOGYyOTcx"),
        "label": "图片生成GI版",
    },
    "video.kling": {
        "plugin_id": _decode_id("YjM2NDRiY2ItNWFhMy00NDQ2LTg3N2MtZTUwMjliY2I1N2I3"),
        "label": "可灵视频生成",
    },
    "video.vidu": {
        "plugin_id": _decode_id("MzU1MDZhZWQtM2M3Ny00OGU4LThjNmItZmQyYzQ5YWIxNjFl"),
        "label": "VIDU视频生成",
    },
    "3d.hy": {
        "plugin_id": _decode_id("YmJlNWMzNWEtZmJmZC00NWZkLWJkOWUtZTAyYTNiODNhODQ3"),
        "label": "混元生3D（专业版）",
    },
}

IMAGE_HY_SUBMIT_TOOL = _decode_id("U3VibWl0VGV4dFRvSW1hZ2VKb2I=")
IMAGE_HY_QUERY_TOOL = _decode_id("UXVlcnlUZXh0VG9JbWFnZUpvYg==")
IMAGE_GI_SUBMIT_TOOL = _decode_id("U3VibWl0R0lJbWFnZUpvYg==")
IMAGE_GI_QUERY_TOOL = _decode_id("UXVlcnlHSUltYWdlSm9i")
VIDEO_KLING_TEXT_SUBMIT_TOOL = _decode_id("U3VibWl0S2xpbmdUZXh0VG9WaWRlb0pvYg==")
VIDEO_KLING_TEXT_QUERY_TOOL = _decode_id("UXVlcnlLbGluZ1RleHRUb1ZpZGVvSm9i")
VIDEO_KLING_IMAGE_SUBMIT_TOOL = _decode_id("U3VibWl0S2xpbmdJbWFnZVRvVmlkZW9Kb2I=")
VIDEO_KLING_IMAGE_QUERY_TOOL = _decode_id("UXVlcnlLbGluZ0ltYWdlVG9WaWRlb0pvYg==")
VIDEO_VIDU_TEXT_SUBMIT_TOOL = _decode_id("U3VibWl0VmlkdVRleHRUb1ZpZGVvSm9i")
VIDEO_VIDU_TEXT_QUERY_TOOL = _decode_id("UXVlcnlWaWR1VGV4dFRvVmlkZW9Kb2I=")
VIDEO_VIDU_IMAGE_SUBMIT_TOOL = _decode_id("U3VibWl0VmlkdUltYWdlVG9WaWRlb0pvYg==")
VIDEO_VIDU_IMAGE_QUERY_TOOL = _decode_id("UXVlcnlWaWR1SW1hZ2VUb1ZpZGVvSm9i")
THREE_D_HY_SUBMIT_TOOL = _decode_id("U3VibWl0SHVueXVhblRvM0RQcm9Kb2I=")
THREE_D_HY_QUERY_TOOL = _decode_id("UXVlcnlIdW55dWFuVG8zRFByb0pvYg==")
TERMINAL_SUCCESS_STATUSES = {"DONE", "SUCCESS", "SUCCEEDED", "COMPLETED", "FINISHED"}
TERMINAL_FAILURE_STATUSES = {"FAIL", "FAILED", "ERROR", "CANCELLED"}
RUNNING_STATUSES = {"WAIT", "RUN", "RUNNING", "PENDING", "QUEUEING", "PROCESSING"}

RUN_SPECS = {
    "image.hy": {
        "default_mode": "text2image",
        "modes": {
            "text2image": {"submit_tool": IMAGE_HY_SUBMIT_TOOL, "query_tool": IMAGE_HY_QUERY_TOOL, "query_id_field": "JobId"},
            "image2image": {"submit_tool": IMAGE_HY_SUBMIT_TOOL, "query_tool": IMAGE_HY_QUERY_TOOL, "query_id_field": "JobId"},
        },
    },
    "image.gi": {
        "default_mode": "text2image",
        "modes": {
            "text2image": {"submit_tool": IMAGE_GI_SUBMIT_TOOL, "query_tool": IMAGE_GI_QUERY_TOOL, "query_id_field": "JobId"},
            "image2image": {"submit_tool": IMAGE_GI_SUBMIT_TOOL, "query_tool": IMAGE_GI_QUERY_TOOL, "query_id_field": "JobId"},
        },
    },
    "video.kling": {
        "default_mode": "text2video",
        "modes": {
            "text2video": {"submit_tool": VIDEO_KLING_TEXT_SUBMIT_TOOL, "query_tool": VIDEO_KLING_TEXT_QUERY_TOOL, "query_id_field": "JobId"},
            "image2video": {"submit_tool": VIDEO_KLING_IMAGE_SUBMIT_TOOL, "query_tool": VIDEO_KLING_IMAGE_QUERY_TOOL, "query_id_field": "JobId"},
        },
    },
    "video.vidu": {
        "default_mode": "text2video",
        "modes": {
            "text2video": {"submit_tool": VIDEO_VIDU_TEXT_SUBMIT_TOOL, "query_tool": VIDEO_VIDU_TEXT_QUERY_TOOL, "query_id_field": "JobId"},
            "image2video": {"submit_tool": VIDEO_VIDU_IMAGE_SUBMIT_TOOL, "query_tool": VIDEO_VIDU_IMAGE_QUERY_TOOL, "query_id_field": "JobId"},
        },
    },
    "3d.hy": {
        "default_mode": "text23d",
        "modes": {
            "text23d": {"submit_tool": THREE_D_HY_SUBMIT_TOOL, "query_tool": THREE_D_HY_QUERY_TOOL, "query_id_field": "JobId"},
            "image23d": {"submit_tool": THREE_D_HY_SUBMIT_TOOL, "query_tool": THREE_D_HY_QUERY_TOOL, "query_id_field": "JobId"},
        },
    },
}


def resolve_alias(target: str) -> tuple[str, str]:
    alias = target.strip()
    if alias in PLUGIN_ALIASES:
        item = PLUGIN_ALIASES[alias]
        return item["plugin_id"], alias
    raise RuntimeError(f"unknown alias: {alias}")


def resolve_run_spec(alias: str, mode: str | None, step: str) -> tuple[str, str, str, str]:
    if alias not in RUN_SPECS:
        raise RuntimeError(f"alias does not support run: {alias}")

    spec = RUN_SPECS[alias]
    selected_mode = mode or spec["default_mode"]

    if selected_mode not in spec["modes"]:
        raise RuntimeError(f"unsupported mode for {alias}: {selected_mode}")

    if step == "query" and alias in {"video.kling", "video.vidu"} and mode is None:
        raise RuntimeError(f"{alias} 在 --step query 时需要显式传入 --mode")

    mode_spec = spec["modes"][selected_mode]
    return selected_mode, mode_spec["submit_tool"], mode_spec["query_tool"], mode_spec["query_id_field"]


def build_url(plugin_id: str) -> str:
    base_url = "https://adp.cloud.tencent.com/plugin/mcp"
    return f"{base_url}/{plugin_id}/mcp"


def _read_key_from_env_file(path: str) -> str:
    if not os.path.exists(path):
        return ""
    try:
        with open(path, "r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()
                if line.startswith("ADP_API_KEY="):
                    return line.split("=", 1)[1].strip().strip("'\"")
    except OSError:
        return ""
    return ""


def require_token() -> str:
    token = os.environ.get("ADP_API_KEY", "").strip()
    if token:
        return token

    for env_file in ("/etc/environment", os.path.expanduser("~/.env"), os.path.join(os.getcwd(), ".env")):
        token = _read_key_from_env_file(env_file)
        if token:
            return token

    raise RuntimeError("missing ADP_API_KEY")


def _parse_sse_body(body: str) -> Any:
    """从 SSE 文本中提取最后一段 JSON 数据。"""
    last_data: list[str] = []
    for chunk in body.split("\n\n"):
        data_lines = [line[5:].lstrip() for line in chunk.splitlines() if line.startswith("data:")]
        if data_lines:
            last_data = data_lines
    if not last_data:
        return None
    joined = "\n".join(last_data).strip()
    if not joined:
        return None
    try:
        return json.loads(joined)
    except json.JSONDecodeError:
        return None


def post_json(url: str, token: str, payload: dict[str, Any], session_id: str | None = None) -> tuple[dict[str, str], Any]:
    request_headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }
    if session_id:
        request_headers["Mcp-Session-Id"] = session_id

    body_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    try:
        response = requests.post(url, data=body_bytes, headers=request_headers, timeout=120)
    except requests.RequestException as exc:
        raise RuntimeError(f"request failed: {exc}") from exc

    headers: dict[str, str] = {
        "_status_line": f"HTTP/{response.raw.version / 10:.1f} {response.status_code}"
        if getattr(response, "raw", None) and getattr(response.raw, "version", None)
        else f"HTTP/1.1 {response.status_code}",
    }
    for key, value in response.headers.items():
        headers[key.lower()] = value

    body_text = response.text.strip()
    parsed: Any = {}
    if body_text:
        content_type = response.headers.get("Content-Type", "").lower()
        if "text/event-stream" in content_type:
            parsed = _parse_sse_body(body_text) or {}
        else:
            try:
                parsed = json.loads(body_text)
            except json.JSONDecodeError:
                sse_parsed = _parse_sse_body(body_text)
                parsed = sse_parsed if sse_parsed is not None else {"_raw_body": body_text}
    return headers, parsed


def attach_http_headers(payload: Any, headers: dict[str, str]) -> Any:
    if isinstance(payload, dict):
        payload["_http_headers"] = headers
        return payload
    return {
        "body": payload,
        "_http_headers": headers,
    }


def initialize(plugin_id: str) -> tuple[str, str | None, Any]:
    token = require_token()
    url = build_url(plugin_id)
    headers, payload = post_json(
        url,
        token,
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "clientInfo": {"name": "adp-skill", "version": "1.0.0"},
            },
        },
    )
    session_id = headers.get("mcp-session-id") if payload.get("result") else None
    return url, session_id, payload


def list_tools(plugin_id: str) -> Any:
    url, session_id, _ = initialize(plugin_id)
    token = require_token()
    headers, payload = post_json(
        url,
        token,
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
        session_id=session_id,
    )
    return attach_http_headers(payload, headers)


def call_tool(plugin_id: str, tool_name: str, arguments: dict[str, Any]) -> Any:
    url, session_id, _ = initialize(plugin_id)
    token = require_token()
    headers, payload = post_json(
        url,
        token,
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments},
        },
        session_id=session_id,
    )
    return attach_http_headers(payload, headers)


def walk_values(value: Any) -> Any:
    yield value
    if isinstance(value, dict):
        for child in value.values():
            yield from walk_values(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_values(child)
    elif isinstance(value, str):
        text = value.strip()
        if not text:
            return
        if (text.startswith("{") and text.endswith("}")) or (text.startswith("[") and text.endswith("]")):
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError:
                return
            yield from walk_values(parsed)


def find_first_key(payload: Any, candidate_keys: tuple[str, ...]) -> Any:
    for value in walk_values(payload):
        if isinstance(value, dict):
            for key in candidate_keys:
                if key in value:
                    return value[key]
    return None


def extract_job_id(payload: Any) -> str:
    value = find_first_key(payload, ("JobId", "jobId", "job_id", "TaskId", "taskId", "task_id"))
    if value is None:
        raise RuntimeError("submit 成功响应中未找到 JobId/TaskId")
    return str(value)


def extract_status(payload: Any) -> str:
    value = find_first_key(payload, ("Status", "status", "State", "state"))
    if value is not None:
        return str(value).strip().upper()

    job_status_code = find_first_key(payload, ("JobStatusCode", "jobStatusCode", "job_status_code"))
    if job_status_code is not None:
        code = str(job_status_code).strip()
        if code == "5":
            return "DONE"
        return code

    job_status_msg = find_first_key(payload, ("JobStatusMsg", "jobStatusMsg", "job_status_msg"))
    if job_status_msg is not None:
        text = str(job_status_msg).strip()
        if "完成" in text:
            return "DONE"
        return text.upper()

    return ""


def extract_urls(payload: Any) -> list[str]:
    urls: list[str] = []
    for value in walk_values(payload):
        if isinstance(value, str) and value.startswith(("http://", "https://")) and value not in urls:
            urls.append(value)
    return urls


def is_success_payload(payload: Any) -> bool:
    status = extract_status(payload)
    if status in TERMINAL_SUCCESS_STATUSES:
        return True
    return bool(extract_urls(payload)) and status not in TERMINAL_FAILURE_STATUSES


def is_failure_payload(payload: Any) -> bool:
    status = extract_status(payload)
    return status in TERMINAL_FAILURE_STATUSES or "error" in payload


def build_image_hy_output(job_id: str, submit_payload: Any, query_payload: Any) -> dict[str, Any]:
    return {
        "alias": "image.hy",
        "plugin_id": PLUGIN_ALIASES["image.hy"]["plugin_id"],
        "submit_tool": IMAGE_HY_SUBMIT_TOOL,
        "query_tool": IMAGE_HY_QUERY_TOOL,
        "job_id": job_id,
        "status": extract_status(query_payload) or "UNKNOWN",
        "final_output": {
            "urls": extract_urls(query_payload),
        },
        "raw_submit": submit_payload,
        "raw_query": query_payload,
    }


def build_async_output(alias: str, submit_tool: str, query_tool: str, job_id: str, submit_payload: Any, query_payload: Any) -> dict[str, Any]:
    return {
        "alias": alias,
        "plugin_id": PLUGIN_ALIASES[alias]["plugin_id"],
        "submit_tool": submit_tool,
        "query_tool": query_tool,
        "job_id": job_id,
        "status": extract_status(query_payload) or "UNKNOWN",
        "final_output": {
            "urls": extract_urls(query_payload),
        },
        "raw_submit": submit_payload,
        "raw_query": query_payload,
    }


def build_stage_output(alias: str, stage: str, submit_tool: str, submit_payload: Any, query_tool: str | None = None, job_id: str | None = None, query_payload: Any | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "alias": alias,
        "stage": stage,
        "submit_tool": submit_tool,
        "raw_submit": submit_payload,
    }
    if query_tool:
        payload["query_tool"] = query_tool
    if job_id:
        payload["job_id"] = job_id
    if query_payload is not None:
        payload["raw_query"] = query_payload
        status = extract_status(query_payload)
        if status:
            payload["status"] = status
    return payload


def has_external_access_error(payload: Any) -> bool:
    return isinstance(payload, dict) and payload.get("Code") is not None and payload.get("Msg") is not None


def run_async_pipeline(alias: str, submit_tool: str, query_tool: str, arguments: dict[str, Any], poll_interval: float, max_wait_seconds: float, query_id_field: str = "JobId") -> dict[str, Any]:
    plugin_id, _ = resolve_alias(alias)
    submit_payload = call_tool(plugin_id, submit_tool, arguments)
    if "error" in submit_payload or has_external_access_error(submit_payload):
        return build_stage_output(alias, "submit", submit_tool, submit_payload)

    try:
        job_id = extract_job_id(submit_payload)
    except RuntimeError as exc:
        result = build_stage_output(alias, "submit", submit_tool, submit_payload)
        result["error_message"] = str(exc)
        return result
    deadline = time.time() + max_wait_seconds
    last_query_payload: dict[str, Any] | None = None

    while True:
        query_payload = call_tool(plugin_id, query_tool, {query_id_field: job_id})
        last_query_payload = query_payload

        if "error" in query_payload or has_external_access_error(query_payload):
            return build_stage_output(alias, "query", submit_tool, submit_payload, query_tool=query_tool, job_id=job_id, query_payload=query_payload)

        if is_success_payload(query_payload):
            return build_async_output(alias, submit_tool, query_tool, job_id, submit_payload, query_payload)

        if is_failure_payload(query_payload):
            return build_stage_output(alias, "query", submit_tool, submit_payload, query_tool=query_tool, job_id=job_id, query_payload=query_payload)

        if time.time() >= deadline:
            return build_stage_output(alias, "timeout", submit_tool, submit_payload, query_tool=query_tool, job_id=job_id, query_payload=last_query_payload)

        time.sleep(poll_interval)


def run_submit_step(alias: str, submit_tool: str, arguments: dict[str, Any]) -> dict[str, Any]:
    plugin_id, _ = resolve_alias(alias)
    submit_payload = call_tool(plugin_id, submit_tool, arguments)
    if "error" in submit_payload or has_external_access_error(submit_payload):
        return build_stage_output(alias, "submit", submit_tool, submit_payload)
    result = build_stage_output(alias, "submit", submit_tool, submit_payload)
    try:
        result["job_id"] = extract_job_id(submit_payload)
    except RuntimeError as exc:
        result["error_message"] = str(exc)
    return result


def run_query_step(alias: str, query_tool: str, arguments: dict[str, Any]) -> dict[str, Any]:
    plugin_id, _ = resolve_alias(alias)
    query_payload = call_tool(plugin_id, query_tool, arguments)
    result = {
        "alias": alias,
        "stage": "query",
        "query_tool": query_tool,
        "raw_query": query_payload,
    }
    status = extract_status(query_payload)
    if status:
        result["status"] = status
    urls = extract_urls(query_payload)
    if urls:
        result["final_output"] = {"urls": urls}
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target_or_command", help="模块别名，或 list-aliases")
    parser.add_argument("action", nargs="?", help="run")
    parser.add_argument("rest", nargs=argparse.REMAINDER)
    args = parser.parse_args()

    if args.target_or_command == "list-aliases":
        return argparse.Namespace(command="list-aliases")

    target = args.target_or_command
    action = args.action
    if not action:
        raise RuntimeError("missing action: expected run")

    if action == "run":
        run_parser = argparse.ArgumentParser(prog=f"{PathLikeName()} {target} run")
        run_parser.add_argument("--mode")
        run_parser.add_argument("--step", choices=("submit", "query"), default="full")
        run_parser.add_argument("--poll-interval", type=float, default=3.0, help="query 轮询间隔，默认 3 秒")
        run_parser.add_argument("--max-wait-seconds", type=float, default=180.0, help="最长等待时间，默认 180 秒")
        run_parser.add_argument(
            "-f",
            "--arguments-file",
            help="从 JSON 文件读取参数（使用 - 表示从 stdin 读取）",
        )
        run_parser.add_argument(
            "arguments_json",
            nargs="?",
            help="参数 JSON 字符串；与 --arguments-file 二选一",
        )
        parsed = run_parser.parse_args(args.rest)
        if parsed.arguments_file and parsed.arguments_json is not None:
            raise RuntimeError("arguments_json 与 --arguments-file 互斥，不能同时提供")
        if not parsed.arguments_file and parsed.arguments_json is None:
            raise RuntimeError("必须提供 arguments_json 位置参数或 --arguments-file 文件路径")
        return argparse.Namespace(
            command="run",
            target=target,
            mode=parsed.mode,
            step=parsed.step,
            poll_interval=parsed.poll_interval,
            max_wait_seconds=parsed.max_wait_seconds,
            arguments_json=parsed.arguments_json,
            arguments_file=parsed.arguments_file,
        )

    raise RuntimeError(f"unknown action: {action}")


def PathLikeName() -> str:
    return "python3 scripts/adp_mcp.py"


def main() -> int:
    payload: Any = None
    try:
        args = parse_args()
        if args.command == "list-aliases":
            payload = {
                "aliases": [
                    {"alias": alias, "label": item["label"]}
                    for alias, item in PLUGIN_ALIASES.items()
                ]
            }
        elif args.command == "run":
            if args.arguments_file:
                if args.arguments_file == "-":
                    raw_json = sys.stdin.read()
                else:
                    with open(args.arguments_file, "r", encoding="utf-8") as fh:
                        raw_json = fh.read()
            else:
                raw_json = args.arguments_json
            arguments = json.loads(raw_json)
            if not isinstance(arguments, dict):
                raise RuntimeError("arguments_json must decode to a JSON object")
            mode, submit_tool, query_tool, query_id_field = resolve_run_spec(args.target, args.mode, args.step)
            if args.step == "submit":
                payload = run_submit_step(args.target, submit_tool, arguments)
            elif args.step == "query":
                payload = run_query_step(args.target, query_tool, arguments)
            else:
                payload = run_async_pipeline(args.target, submit_tool, query_tool, arguments, args.poll_interval, args.max_wait_seconds, query_id_field=query_id_field)
            if isinstance(payload, dict):
                payload.setdefault("_meta", {})
                payload["_meta"]["alias"] = args.target
                payload["_meta"]["mode"] = mode
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"error": str(exc)}, ensure_ascii=False, indent=2))
        return 1

    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
