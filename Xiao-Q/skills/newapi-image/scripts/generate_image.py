#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "requests>=2.31.0",
# ]
# ///

import argparse
import base64
import json
import os
import re
import sys
import time
from typing import Any
from urllib.parse import urlencode
from urllib.parse import urlparse
from pathlib import Path

import requests
from model_config import ModelConfig


def load_local_env() -> None:
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue
        if value.startswith(("'", '"')) and value.endswith(("'", '"')) and len(value) >= 2:
            value = value[1:-1]
        os.environ.setdefault(key, value)


def build_openai_payload(args: argparse.Namespace, model: str) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "prompt": args.prompt,
        "model": model,
        "n": args.n,
        "size": args.size,
        "response_format": args.response_format,
    }
    if args.quality:
        payload["quality"] = args.quality
    if args.style:
        payload["style"] = args.style
    if args.user:
        payload["user"] = args.user
    return payload


def normalize_size_to_aspect_ratio(size: str) -> str:
    mapping = {
        "2048x2048": "1:1",
        "1024x1024": "1:1",
        "1024x1792": "9:16",
        "1792x1024": "16:9",
        "1536x1024": "3:2",
        "1024x1536": "2:3",
    }
    return mapping.get(size, "1:1")


def build_gemini_payload(args: argparse.Namespace) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "contents": [
            {
                "parts": [
                    {"text": args.prompt},
                ]
            }
        ],
        "generationConfig": {
            "responseModalities": ["IMAGE"],
        },
    }
    if args.size:
        payload["generationConfig"]["imageConfig"] = {
            "aspectRatio": normalize_size_to_aspect_ratio(args.size)
        }
    return payload


def resolve_model(args: argparse.Namespace) -> str:
    if args.mode == "aliyun":
        raise ValueError("Aliyun channel is not supported currently.")
    model = args.model or ModelConfig.DEFAULT_MODEL_BY_MODE.get(args.mode, "")
    if not model:
        raise ValueError(f"No default model for mode: {args.mode}")
    supported_models = ModelConfig.SUPPORTED_MODELS_BY_MODE.get(args.mode)
    if not supported_models or model not in supported_models:
        supported_text = ", ".join(sorted(supported_models or []))
        raise ValueError(f"Unsupported model for mode {args.mode}: {model}. Supported models: {supported_text}")
    return model


def parse_size_pixels(size: str) -> int:
    match = re.match(r"^(\d+)x(\d+)$", size.strip().lower())
    if not match:
        raise ValueError("Invalid size format. Use WIDTHxHEIGHT, for example: 2048x2048.")
    width = int(match.group(1))
    height = int(match.group(2))
    return width * height


def validate_size(size: str) -> None:
    pixels = parse_size_pixels(size)
    if pixels < ModelConfig.MIN_IMAGE_PIXELS:
        raise ValueError(
            f"Invalid size: {size}. Image size must be at least {ModelConfig.MIN_IMAGE_PIXELS} pixels."
        )


def print_available_models() -> None:
    print("AVAILABLE_MODELS:")
    print(f"- openai (default: {ModelConfig.DEFAULT_MODEL_BY_MODE['openai']})")
    for model in ModelConfig.OPENAI_MODELS:
        print(f"  - {model}")
    print(f"- gemini (default: {ModelConfig.DEFAULT_MODEL_BY_MODE['gemini']})")
    for model in ModelConfig.GEMINI_MODELS:
        print(f"  - {model}")
    print("- aliyun")
    print("  - not supported")


def resolve_request(args: argparse.Namespace, api_key: str, model: str) -> tuple[str, dict[str, str], dict[str, Any]]:
    base = args.base_url.rstrip("/")
    if args.mode == "openai":
        return (
            f"{base}/v1/images/generations",
            {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            build_openai_payload(args, model),
        )

    query = urlencode({"key": api_key})
    return (
        f"{base}/v1beta/models/{model}:generateContent?{query}",
        {
            "Content-Type": "application/json",
        },
        build_gemini_payload(args),
    )


def resolve_output_dir(args: argparse.Namespace) -> Path:
    default_dir = Path(__file__).resolve().parent.parent / "outputs"
    output_dir = Path(args.output_dir).expanduser() if args.output_dir else default_dir
    if not output_dir.is_absolute():
        output_dir = (Path.cwd() / output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def extension_from_mime_type(mime_type: str | None) -> str:
    mapping = {
        "image/png": ".png",
        "image/jpeg": ".jpg",
        "image/jpg": ".jpg",
        "image/webp": ".webp",
        "image/gif": ".gif",
        "image/bmp": ".bmp",
    }
    if not mime_type:
        return ".png"
    return mapping.get(mime_type.lower(), ".png")


def extension_from_url(image_url: str) -> str:
    path = urlparse(image_url).path.lower()
    for ext in [".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"]:
        if path.endswith(ext):
            return ".jpg" if ext == ".jpeg" else ext
    return ".png"


def save_image_bytes(image_bytes: bytes, output_dir: Path, suffix: str, ext: str) -> Path:
    timestamp = str(int(time.time() * 1000))
    file_path = output_dir / f"generated_{timestamp}_{suffix}{ext}"
    file_path.write_bytes(image_bytes)
    return file_path


def download_image(image_url: str, timeout: int) -> tuple[bytes, str | None]:
    response = requests.get(image_url, timeout=timeout)
    response.raise_for_status()
    content_type = response.headers.get("Content-Type")
    if content_type:
        content_type = content_type.split(";")[0].strip()
    return response.content, content_type


def decode_base64_image(data: str) -> bytes:
    try:
        return base64.b64decode(data, validate=True)
    except Exception:
        return base64.b64decode(data)


def print_openai_result(result: dict[str, Any], output_dir: Path, timeout: int) -> bool:
    data = result.get("data")
    if not isinstance(data, list) or not data:
        return False

    has_output = False
    for index, item in enumerate(data, start=1):
        if not isinstance(item, dict):
            continue
        if item.get("url"):
            image_url = item["url"]
            try:
                image_bytes, mime_type = download_image(image_url, timeout)
                ext = extension_from_url(image_url)
                if mime_type and mime_type.startswith("image/"):
                    ext = extension_from_mime_type(mime_type)
                file_path = save_image_bytes(image_bytes, output_dir, f"url_{index}", ext)
                print(f"MEDIA_FILE: {file_path}")
                has_output = True
            except Exception as error:
                print(f"ERROR: Failed to download image URL: {error}")
        elif item.get("b64_json"):
            try:
                image_bytes = decode_base64_image(item["b64_json"])
                file_path = save_image_bytes(image_bytes, output_dir, f"b64_{index}", ".png")
                print(f"MEDIA_FILE: {file_path}")
                has_output = True
            except Exception as error:
                print(f"ERROR: Failed to decode base64 image: {error}")
    return has_output


def print_gemini_result(result: dict[str, Any], output_dir: Path, timeout: int) -> bool:
    candidates = result.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        return False

    has_output = False
    image_index = 0
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        content = candidate.get("content")
        if not isinstance(content, dict):
            continue
        parts = content.get("parts")
        if not isinstance(parts, list):
            continue
        for part in parts:
            if not isinstance(part, dict):
                continue
            inline_data = part.get("inlineData") or part.get("inline_data")
            if isinstance(inline_data, dict):
                mime_type = inline_data.get("mimeType") or inline_data.get("mime_type") or ""
                data = inline_data.get("data")
                if isinstance(data, str) and mime_type.startswith("image/"):
                    try:
                        image_index += 1
                        image_bytes = decode_base64_image(data)
                        ext = extension_from_mime_type(mime_type)
                        file_path = save_image_bytes(image_bytes, output_dir, f"gemini_b64_{image_index}", ext)
                        print(f"MEDIA_FILE: {file_path}")
                        has_output = True
                    except Exception as error:
                        print(f"ERROR: Failed to decode Gemini base64 image: {error}")
            file_data = part.get("fileData") or part.get("file_data")
            if isinstance(file_data, dict):
                file_uri = file_data.get("fileUri") or file_data.get("file_uri")
                mime_type = file_data.get("mimeType") or file_data.get("mime_type") or ""
                if isinstance(file_uri, str) and file_uri and mime_type.startswith("image/"):
                    if file_uri.startswith("http://") or file_uri.startswith("https://"):
                        try:
                            image_index += 1
                            image_bytes, downloaded_mime_type = download_image(file_uri, timeout)
                            ext = extension_from_mime_type(mime_type)
                            if downloaded_mime_type and downloaded_mime_type.startswith("image/"):
                                ext = extension_from_mime_type(downloaded_mime_type)
                            file_path = save_image_bytes(image_bytes, output_dir, f"gemini_url_{image_index}", ext)
                            print(f"MEDIA_FILE: {file_path}")
                            has_output = True
                        except Exception as error:
                            print(f"ERROR: Failed to download Gemini file URI: {error}")
    return has_output


def generate_image(args: argparse.Namespace) -> None:
    if not args.prompt:
        print("ERROR: prompt is required unless --list-models is used.")
        sys.exit(1)

    try:
        validate_size(args.size)
    except ValueError as error:
        print(f"ERROR: {error}")
        sys.exit(1)

    base_url = (args.base_url or os.environ.get("NEWAPI_BASE_URL", "")).strip()
    if not base_url:
        print("ERROR: base URL is required. Provide via --base-url or NEWAPI_BASE_URL.")
        sys.exit(1)

    api_key = args.api_key or os.environ.get("NEWAPI_API_KEY")
    if not api_key:
        print("ERROR: API key is required. Provide via --api-key or NEWAPI_API_KEY.")
        sys.exit(1)

    try:
        model = resolve_model(args)
    except ValueError as error:
        print(f"ERROR: {error}")
        sys.exit(1)

    url, headers, payload = resolve_request(args, api_key, model)

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=args.timeout)
        response.raise_for_status()
        result = response.json()
    except requests.exceptions.RequestException as error:
        print(f"ERROR: API request failed: {error}")
        if hasattr(error, "response") and error.response is not None:
            print(f"Response body: {error.response.text}")
        sys.exit(1)
    except ValueError:
        print("ERROR: Response is not valid JSON.")
        sys.exit(1)

    output_dir = resolve_output_dir(args)
    if args.mode == "openai":
        has_output = print_openai_result(result, output_dir, args.timeout)
    else:
        has_output = print_gemini_result(result, output_dir, args.timeout)

    if not has_output:
        print(f"ERROR: No image output found. Full response: {json.dumps(result, ensure_ascii=False)}")
        sys.exit(1)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate images using NewAPI in openai/gemini/aliyun modes.")
    parser.add_argument("--mode", default=ModelConfig.DEFAULT_MODE, choices=["openai", "gemini", "aliyun"], help="Request mode")
    parser.add_argument("--list-models", action="store_true", help="List currently supported models and exit")
    parser.add_argument("--prompt", help="Text prompt for image generation")
    parser.add_argument("--base-url", help="NewAPI server base URL, e.g. https://your-newapi-server-address")
    parser.add_argument("--api-key", help="NewAPI API key")
    parser.add_argument("--model", help="Image model name")
    parser.add_argument("--n", type=int, default=1, help="Number of images to generate")
    parser.add_argument("--size", default=ModelConfig.DEFAULT_SIZE, help="Image size")
    parser.add_argument("--quality", help="Image quality, e.g. standard or hd")
    parser.add_argument("--style", help="Image style, e.g. vivid or natural")
    parser.add_argument("--response-format", default="url", choices=["url", "b64_json"], help="Response format")
    parser.add_argument("--user", help="End-user identifier")
    parser.add_argument("--timeout", type=int, default=60, help="Request timeout in seconds")
    parser.add_argument("--output-dir", help="Directory to save generated images")
    return parser.parse_args()


def main() -> None:
    load_local_env()
    args = parse_args()
    if args.list_models:
        print_available_models()
        return
    generate_image(args)


if __name__ == "__main__":
    main()
