#!/usr/bin/env bash
# MiMo API (mimo-v2.5) 多模态调用工具 - Curl 版
#
# 用法:
#   bash mimo_api.sh image   <图片URL或本地路径> <问题> [--max-tokens N] [--timeout N]
#   bash mimo_api.sh images  <图片1> <图片2> [...] --question <问题> [--max-tokens N] [--timeout N]
#   bash mimo_api.sh video   <视频URL或本地路径> <问题> [--fps N] [--resolution default|max] [--max-tokens N] [--timeout N]
#   bash mimo_api.sh audio   <音频URL或本地路径> <问题> [--max-tokens N] [--timeout N]
#   bash mimo_api.sh mixed   --video <视频> --audio <音频> <问题> [--fps N] [--max-tokens N] [--timeout N]
#
# 通用参数:
#   --api-key KEY  MiMo API 密钥（也可通过环境变量 MIMO_API_KEY 设置）

set -euo pipefail

API_URL="${MIMO_API_BASE_URL:-https://api.xiaomimimo.com/v1}"
API_URL="${API_URL%/}/chat/completions"
MODEL="${MIMO_OMNI_MODEL:-mimo-v2.5}"

# ============================================================
# 工具函数
# ============================================================

die() { echo "错误: $*" >&2; exit 1; }

# 预先设置 MIMO_API_KEY 环境变量，或配置 ~/.openclaw/openclaw.json 中的 models.providers.xiaomi.apiKey

check_key() {
    if [[ -z "${MIMO_API_KEY:-}" ]]; then
        local _openclaw="$HOME/.openclaw/openclaw.json"
        if [[ -f "$_openclaw" ]]; then
            MIMO_API_KEY=$(python3 -c "
import json, sys
try:
    d = json.load(open('$_openclaw'))
    print(d['models']['providers']['xiaomi']['apiKey'])
except (KeyError, TypeError):
    sys.exit(1)
" 2>/dev/null) || true
        fi
    fi
    [[ -n "${MIMO_API_KEY:-}" ]] || die "未找到 MiMo API 密鑰。请设置环境变量 MIMO_API_KEY，或在 ~/.openclaw/openclaw.json 中配置 models.providers.xiaomi.apiKey"
}

# 判断是 URL 还是本地文件，本地文件转 data URI
resolve_source() {
    local src="$1"
    if [[ "$src" == http://* ]] || [[ "$src" == https://* ]] || [[ "$src" == data:* ]]; then
        echo "$src"
    else
        [[ -f "$src" ]] || die "文件不存在: $src"
        local ext="${src##*.}"
        ext="${ext,,}"
        local mime
        case "$ext" in
            jpg|jpeg) mime="image/jpeg" ;;
            png)      mime="image/png" ;;
            gif)      mime="image/gif" ;;
            webp)     mime="image/webp" ;;
            mp4)      mime="video/mp4" ;;
            webm)     mime="video/webm" ;;
            mov)      mime="video/quicktime" ;;
            wav)      mime="audio/wav" ;;
            mp3)      mime="audio/mpeg" ;;
            flac)     mime="audio/flac" ;;
            *)        mime="application/octet-stream" ;;
        esac
        local b64
        b64=$(base64 -w 0 "$src")
        echo "data:${mime};base64,${b64}"
    fi
}

# JSON 字符串转义
json_escape() {
    python3 -c "import json,sys; print(json.dumps(sys.stdin.read().strip()))" <<< "$1"
}

# 发送请求（用临时文件避免 ARG_MAX 限制）
# 用法: call_api <body_json> [timeout_seconds]
call_api() {
    local body="$1"
    local timeout="${2:-300}"
    local tmpfile
    tmpfile=$(mktemp /tmp/mimo_api_XXXXXX.json)
    trap "rm -f '$tmpfile'" RETURN
    echo "$body" > "$tmpfile"

    local start_time
    start_time=$(date +%s%N)

    local resp
    resp=$(curl -s --max-time "$timeout" "$API_URL" \
        -H "api-key: $MIMO_API_KEY" \
        -H "Content-Type: application/json" \
        -d @"$tmpfile")

    local end_time
    end_time=$(date +%s%N)
    local elapsed=$(( (end_time - start_time) / 1000000 ))
    local elapsed_s
    elapsed_s=$(awk "BEGIN{printf \"%.1f\", ${elapsed}/1000}")

    # 检查是否有 choices
    local has_choices
    has_choices=$(echo "$resp" | python3 -c "import json,sys; d=json.load(sys.stdin); print('yes' if 'choices' in d else 'no')" 2>/dev/null || echo "no")

    if [[ "$has_choices" == "yes" ]]; then
        echo "$resp" | python3 -c "
import json,sys
d=json.load(sys.stdin)
u=d.get('usage',{})
print(f'[${elapsed_s}s | prompt={u.get(\"prompt_tokens\",\"?\")}, completion={u.get(\"completion_tokens\",\"?\")}]', file=sys.stderr)
print(d['choices'][0]['message']['content'])
"
    else
        echo "API 错误 (${elapsed_s}s):" >&2
        echo "$resp" | python3 -c "import json,sys; print(json.dumps(json.load(sys.stdin), ensure_ascii=False, indent=2)[:500])" >&2
        exit 1
    fi
}

# ============================================================
# 子命令: image
# ============================================================
cmd_image() {
    local source="" question="" max_tokens=65536 timeout=300

    [[ $# -ge 2 ]] || die "用法: bash mimo_api.sh image <图片> <问题> [--max-tokens N] [--timeout N]"
    source="$1"; shift
    question="$1"; shift

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --max-tokens) max_tokens="$2"; shift 2 ;;
            --timeout) timeout="$2"; shift 2 ;;
            *) die "未知参数: $1" ;;
        esac
    done

    local url
    url=$(resolve_source "$source")
    local q_escaped
    q_escaped=$(json_escape "$question")

    local body
    body=$(cat <<EOF
{
  "model": "${MODEL}",
  "messages": [{"role": "user", "content": [
    {"type": "image_url", "image_url": {"url": $(json_escape "$url")}},
    {"type": "text", "text": ${q_escaped}}
  ]}],
  "max_completion_tokens": ${max_tokens}
}
EOF
)
    call_api "$body" "$timeout"
}

# ============================================================
# 子命令: images
# ============================================================
cmd_images() {
    local -a sources=()
    local question="" max_tokens=65536 timeout=300

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --question) question="$2"; shift 2 ;;
            --max-tokens) max_tokens="$2"; shift 2 ;;
            --timeout) timeout="$2"; shift 2 ;;
            *) sources+=("$1"); shift ;;
        esac
    done

    [[ ${#sources[@]} -ge 2 ]] || die "用法: bash mimo_api.sh images <图片1> <图片2> [...] --question <问题>"
    [[ -n "$question" ]] || die "缺少 --question 参数"

    # 构建 content 数组
    local content_items=""
    for src in "${sources[@]}"; do
        local url
        url=$(resolve_source "$src")
        content_items="${content_items}{\"type\": \"image_url\", \"image_url\": {\"url\": $(json_escape "$url")}},"
    done

    local q_escaped
    q_escaped=$(json_escape "$question")
    content_items="${content_items}{\"type\": \"text\", \"text\": ${q_escaped}}"

    local body
    body=$(cat <<EOF
{
  "model": "${MODEL}",
  "messages": [{"role": "user", "content": [${content_items}]}],
  "max_completion_tokens": ${max_tokens}
}
EOF
)
    call_api "$body" "$timeout"
}

# ============================================================
# 子命令: video
# ============================================================
cmd_video() {
    local source="" question="" fps=1 resolution="default" max_tokens=65536 timeout=300

    [[ $# -ge 2 ]] || die "用法: bash mimo_api.sh video <视频> <问题> [--fps N] [--resolution default|max] [--max-tokens N] [--timeout N]"
    source="$1"; shift
    question="$1"; shift

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --fps) fps="$2"; shift 2 ;;
            --resolution) resolution="$2"; shift 2 ;;
            --max-tokens) max_tokens="$2"; shift 2 ;;
            --timeout) timeout="$2"; shift 2 ;;
            *) die "未知参数: $1" ;;
        esac
    done

    local url
    url=$(resolve_source "$source")
    local q_escaped
    q_escaped=$(json_escape "$question")

    local body
    body=$(cat <<EOF
{
  "model": "${MODEL}",
  "messages": [{"role": "user", "content": [
    {
      "type": "video_url",
      "video_url": {"url": $(json_escape "$url")},
      "fps": ${fps},
      "media_resolution": "${resolution}"
    },
    {"type": "text", "text": ${q_escaped}}
  ]}],
  "max_completion_tokens": ${max_tokens}
}
EOF
)
    call_api "$body" "$timeout"
}

# ============================================================
# 子命令: audio
# ============================================================
cmd_audio() {
    local source="" question="" max_tokens=65536 timeout=300

    [[ $# -ge 2 ]] || die "用法: bash mimo_api.sh audio <音频> <问题> [--max-tokens N] [--timeout N]"
    source="$1"; shift
    question="$1"; shift

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --max-tokens) max_tokens="$2"; shift 2 ;;
            --timeout) timeout="$2"; shift 2 ;;
            *) die "未知参数: $1" ;;
        esac
    done

    local data
    data=$(resolve_source "$source")
    local q_escaped
    q_escaped=$(json_escape "$question")

    local body
    body=$(cat <<EOF
{
  "model": "${MODEL}",
  "messages": [{"role": "user", "content": [
    {"type": "input_audio", "input_audio": {"data": $(json_escape "$data")}},
    {"type": "text", "text": ${q_escaped}}
  ]}],
  "max_completion_tokens": ${max_tokens}
}
EOF
)
    call_api "$body" "$timeout"
}

# ============================================================
# 子命令: mixed (video + audio)
# ============================================================
cmd_mixed() {
    local video="" audio="" question="" fps=1 max_tokens=262144 timeout=600

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --video) video="$2"; shift 2 ;;
            --audio) audio="$2"; shift 2 ;;
            --fps) fps="$2"; shift 2 ;;
            --max-tokens) max_tokens="$2"; shift 2 ;;
            --timeout) timeout="$2"; shift 2 ;;
            *)
                if [[ -z "$question" ]]; then
                    question="$1"; shift
                else
                    die "未知参数: $1"
                fi
                ;;
        esac
    done

    [[ -n "$video" ]] || die "缺少 --video 参数"
    [[ -n "$audio" ]] || die "缺少 --audio 参数"
    [[ -n "$question" ]] || die "缺少问题参数"

    local video_url audio_data
    video_url=$(resolve_source "$video")
    audio_data=$(resolve_source "$audio")
    local q_escaped
    q_escaped=$(json_escape "$question")

    local body
    body=$(cat <<EOF
{
  "model": "${MODEL}",
  "messages": [{"role": "user", "content": [
    {"type": "video_url", "video_url": {"url": $(json_escape "$video_url")}, "fps": ${fps}},
    {"type": "input_audio", "input_audio": {"data": $(json_escape "$audio_data")}},
    {"type": "text", "text": ${q_escaped}}
  ]}],
  "max_completion_tokens": ${max_tokens}
}
EOF
)
    call_api "$body" "$timeout"
}

# ============================================================
# 入口
# ============================================================

# 解析密鑰并校验
check_key

[[ $# -ge 1 ]] || die "用法: bash mimo_api.sh [--api-key KEY] <image|images|video|audio|mixed> [参数...]
  bash mimo_api.sh image   <图片> <问题> [--max-tokens N]
  bash mimo_api.sh images  <图片1> <图片2> [...] --question <问题> [--max-tokens N]
  bash mimo_api.sh video   <视频> <问题> [--fps N] [--resolution default|max] [--max-tokens N]
  bash mimo_api.sh audio   <音频> <问题> [--max-tokens N]
  bash mimo_api.sh mixed   --video <视频> --audio <音频> <问题> [--fps N] [--max-tokens N]"

command="$1"; shift

case "$command" in
    image)  cmd_image "$@" ;;
    images) cmd_images "$@" ;;
    video)  cmd_video "$@" ;;
    audio)  cmd_audio "$@" ;;
    mixed)  cmd_mixed "$@" ;;
    *)      die "未知命令: $command (可用: image, images, video, audio, mixed)" ;;
esac
