#!/usr/bin/env python3
import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path


API_BASE = "https://api.apifox.com"
API_VERSION = "2024-03-28"
SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
CONFIG_PATH = SKILL_DIR / "config.json"
DEFAULT_OVERWRITE_BEHAVIOR = "OVERWRITE_EXISTING"
OVERWRITE_BEHAVIOR_ALIASES = {
    "OVERWRITE_EXISTING": {
        "OVERWRITE_EXISTING",
        "overwrite_existing",
        "overwrite",
        "覆盖",
        "覆盖现有",
        "覆盖已有",
        "覆盖现有接口",
        "覆盖已有接口",
        "覆盖现有模型",
        "覆盖已有模型",
    },
    "AUTO_MERGE": {
        "AUTO_MERGE",
        "auto_merge",
        "auto merge",
        "merge",
        "自动合并",
        "合并",
        "自动合并更改",
        "自动合并变更",
        "合并到现有接口",
        "合并到现有模型",
    },
    "KEEP_EXISTING": {
        "KEEP_EXISTING",
        "keep_existing",
        "keep existing",
        "keep",
        "skip",
        "保留",
        "保留现有",
        "保留已有",
        "跳过",
        "跳过变更",
        "跳过并保留",
        "跳过并保留现有接口",
        "跳过并保留现有模型",
    },
    "CREATE_NEW": {
        "CREATE_NEW",
        "create_new",
        "create new",
        "new",
        "创建",
        "创建新的",
        "新建",
        "创建新接口",
        "创建新模型",
        "保留现有并创建新的",
        "保留现有并创建新接口",
        "保留现有并创建新模型",
    },
}
DEFAULT_CONFIG = {
    "accessToken": "",
    "projectId": "",
}


def create_default_config_file() -> None:
    with open(CONFIG_PATH, "w", encoding="utf-8") as handle:
        json.dump(DEFAULT_CONFIG, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="将 OpenAPI 文档导入到 Apifox，并支持配置接口/模型重复项处理策略。"
    )
    parser.add_argument(
        "--input",
        required=True,
        help="待导入的 OpenAPI JSON 或 YAML 文件路径；传 `-` 表示从标准输入读取。",
    )
    parser.add_argument(
        "--project-id",
        default=None,
        help="Apifox 项目 ID。传入时优先级最高。",
    )
    parser.add_argument(
        "--access-token",
        default=None,
        help="Apifox access token。传入时优先级最高。",
    )
    parser.add_argument(
        "--module-id",
        type=int,
        default=None,
        help="可选，导入目标模块 ID。仅在传入时生效。",
    )
    parser.add_argument(
        "--target-endpoint-folder-id",
        type=int,
        default=None,
        help="可选，导入目标接口目录 ID。仅在传入时生效。",
    )
    parser.add_argument(
        "--endpoint-overwrite-behavior",
        default=None,
        help=(
            "可选，接口重复处理策略。支持 Apifox 枚举值，"
            "也支持中文描述，如“覆盖现有接口”“自动合并”“跳过并保留”“创建新的”。"
        ),
    )
    parser.add_argument(
        "--schema-overwrite-behavior",
        default=None,
        help=(
            "可选，数据模型重复处理策略。支持 Apifox 枚举值，"
            "也支持中文描述，如“覆盖现有模型”“自动合并”“跳过并保留”“创建新的”。"
        ),
    )
    return parser.parse_args()


def fail(message: str, exit_code: int = 1) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(exit_code)


def read_input(path: str) -> str:
    if path == "-":
        content = sys.stdin.read().strip()
        if not content:
            fail("标准输入内容为空。")
        return content

    if not os.path.exists(path):
        fail(f"输入文件不存在：{path}")

    with open(path, "r", encoding="utf-8") as handle:
        content = handle.read().strip()

    if not content:
        fail(f"输入文件为空：{path}")

    return content


def read_config() -> dict:
    if not CONFIG_PATH.exists():
        create_default_config_file()
        return dict(DEFAULT_CONFIG)

    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except json.JSONDecodeError as exc:
        fail(f"配置文件不是合法 JSON：{CONFIG_PATH}\n{exc}")


def resolve_setting(cli_value: str | None, config: dict, config_key: str, env_key: str) -> str | None:
    if cli_value:
        return cli_value

    config_value = config.get(config_key)
    if isinstance(config_value, str) and config_value.strip():
        return config_value.strip()

    env_value = os.environ.get(env_key)
    if env_value and env_value.strip():
        return env_value.strip()

    return None


def normalize_overwrite_behavior(value: str | None, field_name: str) -> str:
    if value is None:
        return DEFAULT_OVERWRITE_BEHAVIOR

    normalized = value.strip()
    if not normalized:
        return DEFAULT_OVERWRITE_BEHAVIOR

    normalized_upper = normalized.upper()
    if normalized_upper in OVERWRITE_BEHAVIOR_ALIASES:
        return normalized_upper

    normalized_lower = normalized.lower()
    normalized_compact = normalized_lower.replace("-", " ").replace("_", " ")

    for behavior, aliases in OVERWRITE_BEHAVIOR_ALIASES.items():
        alias_set = {alias.lower() for alias in aliases}
        if (
            normalized_lower in alias_set
            or normalized_compact in alias_set
            or normalized_lower.replace(" ", "") in {alias.replace(" ", "") for alias in alias_set}
        ):
            return behavior

    supported = ", ".join(OVERWRITE_BEHAVIOR_ALIASES.keys())
    fail(
        f"{field_name} 不支持该值：{value}。\n"
        f"支持直接传枚举值，或使用中文描述映射到以下枚举：{supported}"
    )


def build_request_body(
    openapi_text: str,
    module_id: int | None = None,
    target_endpoint_folder_id: int | None = None,
    endpoint_overwrite_behavior: str | None = None,
    schema_overwrite_behavior: str | None = None,
) -> bytes:
    options = {
        "endpointOverwriteBehavior": normalize_overwrite_behavior(
            endpoint_overwrite_behavior,
            "endpointOverwriteBehavior",
        ),
        "schemaOverwriteBehavior": normalize_overwrite_behavior(
            schema_overwrite_behavior,
            "schemaOverwriteBehavior",
        ),
        "updateFolderOfChangedEndpoint": False,
        "prependBasePath": False,
        "deleteUnmatchedResources": False,
    }

    if module_id is not None:
        options["moduleId"] = module_id

    if module_id is not None and target_endpoint_folder_id is not None:
        options["targetEndpointFolderId"] = target_endpoint_folder_id

    payload = {
        "input": openapi_text,
        "options": options,
    }
    return json.dumps(payload).encode("utf-8")


def post_import(
    project_id: str,
    access_token: str,
    openapi_text: str,
    module_id: int | None = None,
    target_endpoint_folder_id: int | None = None,
    endpoint_overwrite_behavior: str | None = None,
    schema_overwrite_behavior: str | None = None,
) -> dict:
    url = f"{API_BASE}/v1/projects/{project_id}/import-openapi"
    request = urllib.request.Request(
        url=url,
        data=build_request_body(
            openapi_text,
            module_id=module_id,
            target_endpoint_folder_id=target_endpoint_folder_id,
            endpoint_overwrite_behavior=endpoint_overwrite_behavior,
            schema_overwrite_behavior=schema_overwrite_behavior,
        ),
        method="POST",
        headers={
            "Content-Type": "application/json",
            "X-Apifox-Api-Version": API_VERSION,
            "Authorization": f"Bearer {access_token}",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        fail(
            f"Apifox 导入失败，HTTP {exc.code}。\n"
            f"响应内容：\n{error_body}"
        )
    except urllib.error.URLError as exc:
        fail(f"连接 Apifox 失败：{exc}")

    try:
        return json.loads(body)
    except json.JSONDecodeError:
        fail(f"Apifox 返回了非 JSON 响应：\n{body}")


def print_summary(result: dict) -> None:
    data = result.get("data") or {}
    counters = data.get("counters") or {}

    created = counters.get("endpointCreated", 0)
    updated = counters.get("endpointUpdated", 0)
    failed = counters.get("endpointFailed", 0)
    ignored = counters.get("endpointIgnored", 0)

    print("Apifox 导入完成。")
    print(f"endpointCreated={created}")
    print(f"endpointUpdated={updated}")
    print(f"endpointFailed={failed}")
    print(f"endpointIgnored={ignored}")

    if failed:
        print("存在接口导入失败，请检查下方完整响应。")

    print("\n完整响应：")
    print(json.dumps(result, ensure_ascii=False, indent=2))


def main() -> None:
    args = parse_args()
    config = read_config()
    access_token = resolve_setting(
        args.access_token, config, "accessToken", "APIFOX_ACCESS_TOKEN"
    )
    project_id = resolve_setting(
        args.project_id, config, "projectId", "APIFOX_PROJECT_ID"
    )

    if not access_token:
        fail(
            "缺少 accessToken。请先补充当前 skill 目录下的 config.json 后再继续：\n"
            f"{CONFIG_PATH}\n"
            '例如：{"accessToken":"your_access_token","projectId":"your_project_id"}',
            exit_code=2,
        )

    if not project_id:
        fail(
            "缺少 projectId。请先补充当前 skill 目录下的 config.json 后再继续：\n"
            f"{CONFIG_PATH}\n"
            '例如：{"accessToken":"your_access_token","projectId":"your_project_id"}',
            exit_code=2,
        )

    openapi_text = read_input(args.input)
    result = post_import(
        project_id,
        access_token,
        openapi_text,
        module_id=args.module_id,
        target_endpoint_folder_id=args.target_endpoint_folder_id,
        endpoint_overwrite_behavior=args.endpoint_overwrite_behavior,
        schema_overwrite_behavior=args.schema_overwrite_behavior,
    )
    print_summary(result)


if __name__ == "__main__":
    main()
