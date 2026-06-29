#!/usr/bin/env python3
"""
fetch_lanhu.py - 从蓝湖获取设计稿数据

用法:
    # 列出项目下所有设计图
    python scripts/fetch_lanhu.py --url "<LANHU_URL>"

    # 获取指定设计图数据（按序号或完整名称）
    python scripts/fetch_lanhu.py --url "<LANHU_URL>" --design 1 --download-images

    # 指定输出目录
    python scripts/fetch_lanhu.py --url "<LANHU_URL>" --design "首页" \\
        --download-images --output-dir ./my_output

Cookie 来源（优先级由高到低）:
    1. --cookie 参数
    2. LANHU_COOKIE 环境变量
    3. 当前目录或父目录的 .env 文件中的 LANHU_COOKIE
"""

import argparse
import asyncio
import json
import math
import io
import os
import re
import sys
import zipfile
from pathlib import Path
from urllib.parse import urlparse

# Windows 终端默认 GBK，强制 stdout/stderr 输出 UTF-8
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if sys.stderr.encoding and sys.stderr.encoding.lower() != "utf-8":
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import httpx

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

BASE_URL = "https://lanhuapp.com"
DDS_BASE_URL = "https://dds.lanhuapp.com"
HTTP_TIMEOUT = 60.0


# ==================== URL 解析 ====================

def parse_lanhu_url(url: str) -> dict:
    """
    解析蓝湖 URL，支持多种格式：
    1. 完整 URL: https://lanhuapp.com/web/#/item/project/stage?tid=...&pid=...
    2. 参数部分: ?tid=...&pid=...
    3. 纯参数: tid=...&pid=...
    """
    if url.startswith("http"):
        parsed = urlparse(url)
        fragment = parsed.fragment
        if not fragment:
            raise ValueError("Invalid Lanhu URL: missing fragment (#) part")
        url = fragment.split("?", 1)[1] if "?" in fragment else fragment

    if url.startswith("?"):
        url = url[1:]

    params = {}
    for part in url.split("&"):
        if "=" in part:
            k, v = part.split("=", 1)
            params[k.strip()] = v.strip()

    team_id = params.get("tid")
    project_id = params.get("pid")
    doc_id = params.get("docId") or params.get("image_id")

    if not project_id:
        raise ValueError("URL missing required param: pid (project_id)")
    if not team_id:
        raise ValueError("URL missing required param: tid (team_id)")

    return {"team_id": team_id, "project_id": project_id, "doc_id": doc_id}


# ==================== API 调用 ====================

def _make_client(cookie: str) -> httpx.AsyncClient:
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Referer": "https://lanhuapp.com/web/",
        "Accept": "application/json, text/plain, */*",
        "Cookie": cookie,
        "request-from": "web",
    }
    return httpx.AsyncClient(timeout=HTTP_TIMEOUT, headers=headers, follow_redirects=True)


async def get_design_list(client: httpx.AsyncClient, team_id: str, project_id: str) -> dict:
    """获取项目下所有设计图列表"""
    url = (
        f"{BASE_URL}/api/project/images"
        f"?project_id={project_id}&team_id={team_id}"
        f"&dds_status=1&position=1&show_cb_src=1"
    )
    resp = await client.get(url)
    resp.raise_for_status()
    data = resp.json()

    if data.get("code") != "00000":
        raise Exception(f"get_design_list failed: {data.get('msg', 'unknown error')}")

    project_data = data.get("data", {})
    images = project_data.get("images", [])

    designs = [
        {
            "index": i + 1,
            "id": img.get("id"),
            "name": img.get("name"),
            "width": img.get("width"),
            "height": img.get("height"),
            "url": img.get("url"),
            "update_time": img.get("update_time"),
        }
        for i, img in enumerate(images)
    ]

    return {
        "project_name": project_data.get("name"),
        "total": len(designs),
        "designs": designs,
    }


async def get_version_id(
    client: httpx.AsyncClient, project_id: str, team_id: str, image_id: str
) -> str:
    """通过 multi_info API 获取设计图的 latest_version（version_id）"""
    resp = await client.get(
        f"{BASE_URL}/api/project/multi_info",
        params={"project_id": project_id, "team_id": team_id, "img_limit": 500, "detach": 1},
    )
    resp.raise_for_status()
    data = resp.json()

    if data.get("code") != "00000":
        raise Exception(f"multi_info failed: {data.get('msg', 'unknown error')}")

    for img in (data.get("result") or {}).get("images") or []:
        if img.get("id") == image_id:
            vid = img.get("latest_version")
            if vid:
                return vid
            raise Exception(f"设计图 {image_id} 无 latest_version 字段")

    raise Exception(f"multi_info 中未找到 image_id={image_id}")


async def fetch_dds_schema(version_id: str, cookie: str) -> dict:
    """
    调用 DDS store_schema_revise 接口获取 Schema JSON。
    使用独立的 httpx 客户端，因为 DDS 域名不同于主站。
    """
    dds_headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://dds.lanhuapp.com/",
        "Cookie": cookie,
        "Authorization": "Basic dW5kZWZpbmVkOg==",
    }
    async with httpx.AsyncClient(
        timeout=HTTP_TIMEOUT, headers=dds_headers, follow_redirects=True
    ) as dds:
        resp = await dds.get(
            f"{DDS_BASE_URL}/api/dds/image/store_schema_revise",
            params={"version_id": version_id},
        )
        resp.raise_for_status()
        data = resp.json()

        if data.get("code") != "00000":
            raise Exception(f"store_schema_revise failed: {data.get('msg', 'unknown error')}")

        schema_url = (data.get("data") or {}).get("data_resource_url")
        if not schema_url:
            raise Exception("store_schema_revise did not return data_resource_url")

        schema_resp = await dds.get(schema_url)
        schema_resp.raise_for_status()
        return schema_resp.json()


def _extract_zip_url(data: dict) -> str | None:
    """从 code_package/task 响应的 data 字段中提取 ZIP 下载 URL"""
    OSS_BASE = "https://dds-online.oss-cn-beijing.aliyuncs.com/code_package_docker"

    # 直接包含 URL 的字段
    for key in ("download_url", "zip_url", "url", "file_url", "package_url"):
        val = data.get(key)
        if isinstance(val, str) and val.startswith("http"):
            return val

    # 通过 id / task_id 构造 URL
    task_id = data.get("id") or data.get("task_id") or data.get("package_id")
    if task_id:
        return f"{OSS_BASE}/code_package_{task_id}/LanhuProject.zip"

    return None


async def fetch_official_code(
    project_id: str,
    image_id: str,
    version_id: str,
    cookie: str,
    design_name: str = "LanhuProject",
    framework: str = "html",
) -> tuple[str, str]:
    """
    调用蓝湖代码生成 API，下载官方 HTML+CSS ZIP 包并返回解压后的内容。
    返回: (html_content, css_content)
    """
    dds_headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json;charset=UTF-8",
        "Origin": "https://dds.lanhuapp.com",
        "Referer": "https://dds.lanhuapp.com/",
        "Cookie": cookie,
        "Authorization": "Basic dW5kZWZpbmVkOg==",
    }

    payload = {
        "project_name": design_name,
        "framework": framework,
        "css_style": "CSS",
        "resource_data": [
            {
                "image_id": image_id,
                "project_id": project_id,
                "version_id": version_id,
            }
        ],
        "task_settings": {"remBase": "", "width": 375},
    }

    async with httpx.AsyncClient(
        timeout=HTTP_TIMEOUT, headers=dds_headers, follow_redirects=True
    ) as dds:
        # Step 1: 创建代码生成任务
        resp = await dds.post(
            f"{DDS_BASE_URL}/api/dds/code_package/task",
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()

        if data.get("code") != "00000":
            raise Exception(
                f"code_package/task failed: code={data.get('code')}, msg={data.get('msg', '')}\n"
                f"  response: {json.dumps(data, ensure_ascii=False)[:300]}"
            )

        result_data = data.get("data") or {}
        zip_url = _extract_zip_url(result_data)
        if not zip_url:
            raise Exception(
                f"无法从响应中提取 ZIP URL，data 字段: {json.dumps(result_data, ensure_ascii=False)[:300]}"
            )

        print(f"  → ZIP URL: {zip_url}", file=sys.stderr)

        # Step 2: 下载 ZIP（支持重试，应对异步任务未完成的情况）
        zip_bytes = await _download_zip_with_retry(zip_url)

    # Step 3: 解压提取 HTML + CSS
    return _extract_code_from_zip(zip_bytes)


async def _download_zip_with_retry(
    zip_url: str, max_retries: int = 8, interval: float = 3.0
) -> bytes:
    """下载 ZIP 文件，若任务尚未完成（404）则自动重试"""
    oss_headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Referer": "https://dds.lanhuapp.com/",
    }
    for attempt in range(1, max_retries + 1):
        async with httpx.AsyncClient(
            timeout=HTTP_TIMEOUT, headers=oss_headers, follow_redirects=True
        ) as oss:
            resp = await oss.get(zip_url)
            if resp.status_code == 200:
                return resp.content
            if resp.status_code == 404 and attempt < max_retries:
                print(
                    f"  ⏳ ZIP 尚未就绪，{interval}s 后重试 ({attempt}/{max_retries})...",
                    file=sys.stderr,
                )
                await asyncio.sleep(interval)
                continue
            resp.raise_for_status()

    raise Exception(f"ZIP 下载失败，已重试 {max_retries} 次: {zip_url}")


def _extract_code_from_zip(zip_bytes: bytes) -> tuple[str, str]:
    """从 ZIP 字节内容中提取所有 HTML 和 CSS 文件的文本"""
    html_parts: list[str] = []
    css_parts: list[str] = []

    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        for name in sorted(zf.namelist()):
            lower = name.lower()
            content = zf.read(name).decode("utf-8", errors="replace")
            if lower.endswith(".html"):
                html_parts.append(f"<!-- ===== {name} ===== -->\n{content}")
            elif lower.endswith(".css"):
                css_parts.append(f"/* ===== {name} ===== */\n{content}")

    return "\n\n".join(html_parts), "\n\n".join(css_parts)


def _normalize_version_id(version_obj: dict) -> str | None:
    """从版本对象中提取可比较的版本 ID。"""
    for key in ("id", "version_id", "versionId", "uuid"):
        val = version_obj.get(key)
        if val is not None and str(val).strip():
            return str(val)
    return None


async def get_sketch_json(
    client: httpx.AsyncClient,
    project_id: str,
    team_id: str,
    image_id: str,
    expected_version_id: str | None = None,
) -> dict:
    """获取原始 Sketch JSON（含完整设计标注数据，用于 Design Token 提取）"""
    resp = await client.get(
        f"{BASE_URL}/api/project/image",
        params={
            "dds_status": 1,
            "image_id": image_id,
            "team_id": team_id,
            "project_id": project_id,
        },
    )
    resp.raise_for_status()
    data = resp.json()

    if data.get("code") != "00000":
        raise Exception(f"get_sketch_json failed: {data.get('msg', 'unknown error')}")

    versions = (data.get("result") or {}).get("versions") or []
    if not versions:
        raise Exception("get_sketch_json 返回为空：未找到 versions")

    picked = versions[0]
    if expected_version_id:
        normalized_expected = str(expected_version_id)
        matched = next(
            (v for v in versions if _normalize_version_id(v) == normalized_expected),
            None,
        )
        if matched:
            picked = matched

    json_url = picked.get("json_url")
    if not json_url:
        raise Exception("get_sketch_json: 目标版本缺少 json_url")
    json_resp = await client.get(json_url)
    json_resp.raise_for_status()
    return json_resp.json()


# ==================== Design Token 提取 ====================

def extract_design_tokens(sketch_data: dict) -> str:
    """
    从 Sketch JSON 中提取高风险视觉元素的设计参数，输出紧凑文本供 AI 校验。
    只提取含渐变、非均匀圆角、描边、阴影、透明度的真实可见元素。
    """
    NOISE_TYPES = {"color", "gradient", "colorStop", "colorControl"}

    def _get_dimensions(obj: dict) -> tuple:
        frame = obj.get("ddsOriginFrame") or obj.get("layerOriginFrame") or {}
        x = frame.get("x", obj.get("left", 0)) or 0
        y = frame.get("y", obj.get("top", 0)) or 0
        w = frame.get("width", obj.get("width", 0)) or 0
        h = frame.get("height", obj.get("height", 0)) or 0
        return x, y, w, h

    def _simplify_fill(fill: dict) -> str | None:
        if not fill.get("isEnabled", True):
            return None
        fill_type = fill.get("fillType", 0)
        if fill_type == 0:
            color = fill.get("color", {})
            return f"solid({color.get('value', 'unknown')})"
        if fill_type == 1:
            gradient = fill.get("gradient", {})
            stops = gradient.get("colorStops", [])
            from_pt = gradient.get("from", {})
            to_pt = gradient.get("to", {})
            dx = to_pt.get("x", 0.5) - from_pt.get("x", 0.5)
            dy = to_pt.get("y", 0) - from_pt.get("y", 0)
            angle = math.degrees(math.atan2(dx, dy)) % 360
            parts = [
                f"{s.get('color', {}).get('value', 'unknown')} {(s.get('position', 0) * 100)}%"
                for s in stops
            ]
            return f"linear-gradient({angle}deg, {', '.join(parts)})"
        return None

    def _simplify_border(border: dict) -> str | None:
        if not border.get("isEnabled", True):
            return None
        color = border.get("color", {}).get("value", "unknown")
        thickness = border.get("thickness", 1)
        pos_map = {"内边框": "inside", "外边框": "outside", "中心边框": "center"}
        pos = pos_map.get(border.get("position", ""), border.get("position", "center"))
        return f"{thickness}px {pos} {color}"

    def _simplify_shadow(shadow: dict) -> str | None:
        if not shadow.get("isEnabled", True):
            return None
        color = shadow.get("color", {}).get("value", "unknown")
        x = shadow.get("offsetX", 0)
        y = shadow.get("offsetY", 0)
        blur = shadow.get("blurRadius", 0)
        spread = shadow.get("spread", 0)
        return f"{color} {x}px {y}px {blur}px {spread}px"

    def _has_only_transparent_solid(fills: list) -> bool:
        for f in fills:
            if not f.get("isEnabled", True):
                continue
            if f.get("fillType", 0) == 0:
                color = f.get("color", {})
                val = color.get("value", "")
                if "rgba" in val and ",0)" in val.replace(" ", ""):
                    continue
                if color.get("alpha", color.get("a", 1)) == 0:
                    continue
            return False
        return True

    def _is_high_risk(obj: dict) -> bool:
        obj_type = (obj.get("type") or obj.get("ddsType") or "").lower()
        if obj_type in NOISE_TYPES:
            return False
        _, _, w, h = _get_dimensions(obj)
        if w < 2 and h < 2:
            return False

        fills = obj.get("fills", [])
        if any(f.get("isEnabled", True) and f.get("fillType") == 1 for f in fills):
            return True
        if any(b.get("isEnabled", True) for b in obj.get("borders", [])):
            return True
        radius = obj.get("radius")
        if isinstance(radius, list) and len(set(radius)) > 1:
            return True
        opacity = obj.get("opacity")
        if opacity is not None and opacity < 100:
            if not _has_only_transparent_solid(fills) or obj.get("borders") or obj.get("shadows"):
                return True
        if any(s.get("isEnabled", True) for s in obj.get("shadows", [])):
            return True
        return False

    tokens = []

    def _walk(obj: dict, parent_path: str = ""):
        if not obj or not isinstance(obj, dict):
            return
        if not obj.get("isVisible", True):
            return

        name = obj.get("name", "")
        current_path = f"{parent_path}/{name}" if parent_path else name

        if _is_high_risk(obj):
            obj_type = obj.get("type") or obj.get("ddsType") or "unknown"
            x, y, w, h = _get_dimensions(obj)
            lines = [f'[{obj_type}] "{name}" @({int(x)},{int(y)}) {int(w)}x{int(h)}']
            if parent_path:
                lines[0] += f"  path: {current_path}"

            radius = obj.get("radius")
            if radius:
                if isinstance(radius, list):
                    lines.append(f"  radius: {radius[0] if len(set(radius)) == 1 else radius}")
                else:
                    lines.append(f"  radius: {radius}")

            for f in obj.get("fills", []):
                s = _simplify_fill(f)
                if s:
                    lines.append(f"  fill: {s}")

            for b in obj.get("borders", []):
                s = _simplify_border(b)
                if s:
                    lines.append(f"  border: {s}")

            opacity = obj.get("opacity")
            if opacity is not None and opacity < 100:
                lines.append(f"  opacity: {opacity}%")

            for sh in obj.get("shadows", []):
                s = _simplify_shadow(sh)
                if s:
                    lines.append(f"  shadow: {s}")

            tokens.append("\n".join(lines))

        for child in obj.get("layers", []):
            _walk(child, current_path)

    if sketch_data.get("artboard") and sketch_data["artboard"].get("layers"):
        for layer in sketch_data["artboard"]["layers"]:
            _walk(layer)
    elif sketch_data.get("info"):
        for item in sketch_data["info"]:
            _walk(item)
            for value in item.values():
                if isinstance(value, dict):
                    _walk(value)
                elif isinstance(value, list):
                    for v in value:
                        if isinstance(v, dict):
                            _walk(v)

    return "\n\n".join(tokens)


# ==================== 图片资源 ====================

def collect_image_urls_from_schema(schema: dict) -> list[str]:
    """
    从 Schema JSON 中递归收集所有远程图片 URL。
    覆盖 lanhuimage 节点的 data.value / props.src，
    以及 style.backgroundImage / style.background 中的 url(...)。
    """
    urls = []

    def _walk(node):
        if not isinstance(node, dict):
            return

        if node.get("type") == "lanhuimage":
            src = node.get("data", {}).get("value") or node.get("props", {}).get("src", "")
            if src and src.startswith("http"):
                urls.append(src)

        style = node.get("style", {})
        for bg_key in ("backgroundImage", "background"):
            bg = style.get(bg_key, "")
            if bg and "http" in bg:
                m = re.search(r"url\(['\"]?(https?://[^'\")\s]+)", bg)
                if m:
                    urls.append(m.group(1))

        for child in node.get("children", []):
            _walk(child)

    _walk(schema)
    return list(dict.fromkeys(urls))  # deduplicate, preserve order


async def download_file(client: httpx.AsyncClient, url: str, local_path: Path) -> bool:
    """下载单个文件，失败时静默返回 False"""
    try:
        local_path.parent.mkdir(parents=True, exist_ok=True)
        resp = await client.get(url)
        resp.raise_for_status()
        local_path.write_bytes(resp.content)
        return True
    except Exception as e:
        print(f"  ⚠ 下载失败 {url}: {e}", file=sys.stderr)
        return False


async def download_assets(
    client: httpx.AsyncClient, schema: dict, assets_dir: Path
) -> dict[str, str]:
    """
    下载 Schema 中所有图片资源到 assets_dir，返回 {本地相对路径: 远程URL} 映射表。
    """
    urls = collect_image_urls_from_schema(schema)
    mapping = {}

    for i, url in enumerate(urls, 1):
        path_part = urlparse(url).path
        suffix = Path(path_part).suffix
        if suffix.lower() not in {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp"}:
            suffix = ".png"
        local_name = f"img_{i}{suffix}"
        local_path = assets_dir / local_name
        ok = await download_file(client, url, local_path)
        if ok:
            mapping[f"./assets/slices/{local_name}"] = url

    return mapping


# ==================== CLI 入口 ====================

async def run(args):
    cookie = args.cookie or os.getenv("LANHU_COOKIE", "")
    if not cookie:
        print(
            "Error: 未提供 Cookie。请通过 --cookie 参数或 LANHU_COOKIE 环境变量提供。",
            file=sys.stderr,
        )
        sys.exit(1)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    params = parse_lanhu_url(args.url)
    team_id = params["team_id"]
    project_id = params["project_id"]

    async with _make_client(cookie) as client:
        # —— 列出所有设计图 ——
        design_data = await get_design_list(client, team_id, project_id)

        # —— 定位目标设计图 ——
        designs = design_data["designs"]
        target = None

        if args.design:
            if str(args.design).isdigit():
                n = int(args.design)
                target = next((d for d in designs if d["index"] == n), None)
            else:
                target = next((d for d in designs if d["name"] == args.design), None)

        # fallback: URL 中带有 image_id（无论是否传了 --design）
        if not target and params.get("doc_id"):
            target = next((d for d in designs if d["id"] == params["doc_id"]), None)

        if not target and not args.design:
            # 既没有 --design 也没有 image_id，打印列表供用户选择
            if args.list_full:
                print(json.dumps(design_data, ensure_ascii=False, indent=2))
            else:
                compact = {
                    "project_name": design_data.get("project_name"),
                    "total": design_data.get("total", 0),
                    "designs": [
                        {
                            "index": d.get("index"),
                            "name": d.get("name"),
                            "width": d.get("width"),
                            "height": d.get("height"),
                            "update_time": d.get("update_time"),
                        }
                        for d in design_data.get("designs", [])
                    ],
                }
                print(json.dumps(compact, ensure_ascii=False, indent=2))
            return

        if not target:
            print(
                f"Error: 未找到设计图 '{args.design}'\n"
                f"可用设计图: {[d['name'] for d in designs]}",
                file=sys.stderr,
            )
            sys.exit(1)

        image_id = target["id"]
        result = {"design": target}

        print(f"🔍 正在处理: {target['name']} (id={image_id})", file=sys.stderr)

        # —— 获取 Schema JSON ——
        print("  → 获取 version_id ...", file=sys.stderr)
        version_id = await get_version_id(client, project_id, team_id, image_id)

        print("  → 拉取 DDS Schema JSON ...", file=sys.stderr)
        schema = await fetch_dds_schema(version_id, cookie)

        schema_path = output_dir / f"{target['name']}.schema.json"
        schema_path.write_text(json.dumps(schema, ensure_ascii=False, indent=2), encoding="utf-8")
        result["schema_path"] = str(schema_path)
        print(f"  ✓ Schema JSON → {schema_path}", file=sys.stderr)

        # —— 获取 Sketch JSON + Design Tokens ——
        print("  → 拉取 Sketch JSON ...", file=sys.stderr)
        try:
            sketch = await get_sketch_json(
                client,
                project_id,
                team_id,
                image_id,
                expected_version_id=version_id,
            )
            tokens = extract_design_tokens(sketch)
            if tokens:
                tokens_path = output_dir / f"{target['name']}.tokens.txt"
                tokens_path.write_text(tokens, encoding="utf-8")
                result["tokens_path"] = str(tokens_path)
                print(f"  ✓ Design Tokens → {tokens_path}", file=sys.stderr)
            else:
                print("  ℹ Design Tokens: 无高风险属性", file=sys.stderr)
        except Exception as e:
            print(f"  ⚠ Sketch JSON 获取失败（Design Tokens 跳过）: {e}", file=sys.stderr)

        # —— 下载图片 ——
        if args.download_images:
            # 下载设计图原图
            if target.get("url"):
                img_path = output_dir / f"{target['name']}.png"
                print("  → 下载设计图原图 ...", file=sys.stderr)
                ok = await download_file(client, target["url"], img_path)
                if ok:
                    result["design_image_path"] = str(img_path)
                    print(f"  ✓ 设计图原图 → {img_path}", file=sys.stderr)

            # 下载 Schema 中引用的图片资源
            assets_dir = output_dir / "assets" / "slices"
            print("  → 下载 Schema 图片资源 ...", file=sys.stderr)
            mapping = await download_assets(client, schema, assets_dir)
            if mapping:
                result["image_mapping"] = mapping
                mapping_path = output_dir / f"{target['name']}.image_mapping.json"
                mapping_path.write_text(
                    json.dumps(mapping, ensure_ascii=False, indent=2), encoding="utf-8"
                )
                result["image_mapping_path"] = str(mapping_path)
                print(
                    f"  ✓ 图片资源 {len(mapping)} 个 → {assets_dir} (映射表: {mapping_path})",
                    file=sys.stderr,
                )

        # —— 下载官方代码包 ——
        if args.download_code:
            print("  → 下载官方代码包 ...", file=sys.stderr)
            try:
                html_content, css_content = await fetch_official_code(
                    project_id=project_id,
                    image_id=image_id,
                    version_id=version_id,
                    cookie=cookie,
                    design_name=target["name"],
                    framework=args.code_framework or "vue2",
                )
                if html_content:
                    html_path = output_dir / f"{target['name']}.official.html"
                    html_path.write_text(html_content, encoding="utf-8")
                    result["official_html_path"] = str(html_path)
                    print(f"  ✓ 官方代码 HTML → {html_path}", file=sys.stderr)
                if css_content:
                    css_path = output_dir / f"{target['name']}.official.css"
                    css_path.write_text(css_content, encoding="utf-8")
                    result["official_css_path"] = str(css_path)
                    print(f"  ✓ 官方代码 CSS  → {css_path}", file=sys.stderr)
            except Exception as e:
                print(f"  ⚠ 官方代码下载失败（已跳过）: {e}", file=sys.stderr)

    print(json.dumps(result, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(
        description="从蓝湖获取设计稿数据（Schema JSON + Design Tokens + 图片）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--url", required=True, help="蓝湖设计稿 URL（含 tid、pid 参数）")
    parser.add_argument("--cookie", help="蓝湖 Cookie（可选，优先于 LANHU_COOKIE 环境变量）")
    parser.add_argument(
        "--design",
        help="要获取的设计图：序号（如 1）或完整名称（如 '首页'）。不填则仅列出所有设计图。",
    )
    parser.add_argument(
        "--list-full",
        action="store_true",
        help="仅列出设计图时输出完整字段（含 id/url）。默认输出精简字段以减少上下文体积。",
    )
    parser.add_argument(
        "--download-images",
        action="store_true",
        help="下载设计图原图和 Schema 中引用的图片资源",
    )
    parser.add_argument(
        "--download-code",
        action="store_true",
        help="下载蓝湖官方生成的 HTML+CSS 代码包（用于结构参考，提升还原度）",
    )
    parser.add_argument(
        "--code-framework",
        default="vue2",
        choices=["vue2", "react"],
        help="官方代码包的框架类型（默认 vue2，可选 react）",
    )
    parser.add_argument("--output-dir", default="./lanhu_output", help="输出目录（默认 ./lanhu_output）")
    args = parser.parse_args()
    asyncio.run(run(args))


if __name__ == "__main__":
    main()
