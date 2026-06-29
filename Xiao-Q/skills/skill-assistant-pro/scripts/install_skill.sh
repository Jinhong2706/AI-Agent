#!/usr/bin/env bash
#
# install_skill.sh — 安装 GitHub Skill 到指定目录，生成 _skill_meta.json
#
# 用法:
#   bash install_skill.sh <github_url> <skill_name> [target_dir] [options]
#
# 参数:
#   github_url      — GitHub 仓库 URL (如 https://github.com/owner/repo)
#   skill_name      — Skill 名称 (如 my-skill)
#   target_dir      — 安装目标目录 (默认: .cursor/skills)
#
# 选项:
#   --skip-audit    — 跳过安全扫描
#   --no-telemetry  — 不向 skills.sh 上报安装事件
#   --channel <ch>  — 标记发现该 Skill 的搜索渠道 (如 skills.sh, github)
#   --force         — 已安装时直接覆盖，不提示
#
# 示例:
#   bash install_skill.sh https://github.com/anthropics/skills pdf-editor
#   bash install_skill.sh https://github.com/obra/superpowers requesting-code-review .cursor/skills --channel skills.sh

set -euo pipefail

SKIP_AUDIT=false
NO_TELEMETRY=false
FORCE=false
CHANNEL="unknown"
POSITIONAL=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --skip-audit)   SKIP_AUDIT=true; shift ;;
    --no-telemetry) NO_TELEMETRY=true; shift ;;
    --force)        FORCE=true; shift ;;
    --channel)      CHANNEL="${2:-unknown}"; shift 2 ;;
    *)              POSITIONAL+=("$1"); shift ;;
  esac
done

GITHUB_URL="${POSITIONAL[0]:?用法: bash install_skill.sh <github_url> <skill_name> [target_dir] [options]}"
SKILL_NAME="${POSITIONAL[1]:?用法: bash install_skill.sh <github_url> <skill_name> [target_dir] [options]}"
TARGET_DIR="${POSITIONAL[2]:-.cursor/skills}"

# ─── P0: 名称清理（sanitizeName）─────────────────────────────────────
sanitize_name() {
  local name="$1"
  local sanitized
  sanitized=$(echo "$name" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9._]+/-/g; s/^[.\-]+//; s/[.\-]+$//')
  sanitized="${sanitized:0:255}"
  echo "${sanitized:-unnamed-skill}"
}

SAFE_NAME=$(sanitize_name "${SKILL_NAME}")
if [ "${SAFE_NAME}" != "${SKILL_NAME}" ]; then
  echo "⚠️  名称已清理: '${SKILL_NAME}' → '${SAFE_NAME}'"
  SKILL_NAME="${SAFE_NAME}"
fi

# ─── P0: 路径安全校验（isPathSafe）───────────────────────────────────
SKILL_DEST="${TARGET_DIR}/${SKILL_NAME}"
RESOLVED_TARGET=$(cd "${TARGET_DIR}" 2>/dev/null && pwd || echo "${TARGET_DIR}")
RESOLVED_DEST=$(echo "${RESOLVED_TARGET}/${SKILL_NAME}")

if [[ ! "${RESOLVED_DEST}" == "${RESOLVED_TARGET}/"* ]]; then
  echo "🚨 路径安全校验失败：疑似路径穿越攻击"
  echo "   目标目录: ${RESOLVED_TARGET}"
  echo "   解析路径: ${RESOLVED_DEST}"
  exit 1
fi

# ─── P1: 已安装覆盖检测 ──────────────────────────────────────────────
if [ -d "${SKILL_DEST}" ] && [ -f "${SKILL_DEST}/SKILL.md" ]; then
  EXISTING_VERSION=""
  EXISTING_DATE=""
  EXISTING_CHANNEL=""
  if [ -f "${SKILL_DEST}/_skill_meta.json" ] && command -v python3 &>/dev/null; then
    EXISTING_VERSION=$(python3 -c "import json; m=json.load(open('${SKILL_DEST}/_skill_meta.json')); print(m.get('version','?'))" 2>/dev/null || echo "?")
    EXISTING_DATE=$(python3 -c "import json; m=json.load(open('${SKILL_DEST}/_skill_meta.json')); print(m.get('installedAt','?')[:10])" 2>/dev/null || echo "?")
    EXISTING_CHANNEL=$(python3 -c "import json; m=json.load(open('${SKILL_DEST}/_skill_meta.json')); print(m.get('channel','?'))" 2>/dev/null || echo "?")
  fi

  if [ "${FORCE}" = "true" ]; then
    echo "⚠️  已存在 ${SKILL_NAME} (v${EXISTING_VERSION}, ${EXISTING_DATE})，--force 覆盖安装"
  else
    echo "⚠️  ${SKILL_NAME} 已安装："
    echo "   版本: ${EXISTING_VERSION}"
    echo "   安装于: ${EXISTING_DATE}"
    echo "   来源: ${EXISTING_CHANNEL}"
    echo ""
    echo "   将覆盖现有安装。如需跳过，请 Ctrl+C 取消。"
    echo "   （使用 --force 可跳过此提示）"
    echo ""
    echo "   继续安装..."
  fi
fi

TMPDIR_PATH="$(mktemp -d)"
cleanup() {
  rm -rf "${TMPDIR_PATH}"
}
trap cleanup EXIT

echo "==> 克隆仓库到临时目录..."
if ! git clone --depth 1 "${GITHUB_URL}.git" "${TMPDIR_PATH}/repo" 2>&1; then
  echo "❌ 克隆失败，请检查："
  echo "   1. URL 是否正确: ${GITHUB_URL}"
  echo "   2. 网络是否正常"
  echo "   3. 仓库是否存在且为 public"
  exit 1
fi

COMMIT_HASH=$(cd "${TMPDIR_PATH}/repo" && git rev-parse HEAD 2>/dev/null || echo "unknown")

echo "==> 查找 SKILL.md 位置..."

SKILL_MD_PATH=$(find "${TMPDIR_PATH}/repo" -name "SKILL.md" -not -path "*/node_modules/*" | grep -E "(${SKILL_NAME}|${SKILL_NAME//-/_})" | head -1)

if [ -z "${SKILL_MD_PATH}" ]; then
  SKILL_MD_PATH=$(find "${TMPDIR_PATH}/repo" -name "SKILL.md" -not -path "*/node_modules/*" | head -1)
fi

if [ -z "${SKILL_MD_PATH}" ]; then
  echo "❌ 未找到 SKILL.md 文件，该仓库可能不是标准 Skill。"
  echo "   仓库内容:"
  ls -la "${TMPDIR_PATH}/repo/"
  exit 1
fi

SKILL_SRC_DIR=$(dirname "${SKILL_MD_PATH}")
SKILL_PATH_IN_REPO=$(echo "${SKILL_MD_PATH}" | sed "s|${TMPDIR_PATH}/repo/||")
SKILL_DIR_IN_REPO=$(dirname "${SKILL_PATH_IN_REPO}")
echo "   找到: ${SKILL_PATH_IN_REPO}"

# ─── 提取 SKILL.md frontmatter 元数据 ─────────────────────────────
SKILL_VERSION="1.0.0"
SKILL_DESCRIPTION=""
SKILL_TAGS="[]"
if command -v python3 &>/dev/null; then
  FRONTMATTER=$(python3 -c "
import re, sys
try:
    with open('${SKILL_MD_PATH}') as f:
        content = f.read()
    m = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
    if m:
        fm = m.group(1)
        for line in fm.split('\n'):
            if line.startswith('version:'):
                print('VERSION=' + line.split(':', 1)[1].strip().strip('\"').strip(\"'\"))
            elif line.startswith('description:'):
                desc = line.split(':', 1)[1].strip().strip('\"').strip(\"'\").strip('>')
                if desc:
                    print('DESCRIPTION=' + desc[:200])
            elif line.startswith('tags:'):
                tags = line.split(':', 1)[1].strip()
                print('TAGS=' + tags)
except Exception:
    pass
" 2>/dev/null || true)
  while IFS='=' read -r key value; do
    case "${key}" in
      VERSION) SKILL_VERSION="${value}" ;;
      DESCRIPTION) SKILL_DESCRIPTION="${value}" ;;
      TAGS) SKILL_TAGS="${value}" ;;
    esac
  done <<< "${FRONTMATTER}"
fi

# ─── 安全扫描 ───────────────────────────────────────────────────────
SCAN_PASSED=true
SCAN_CRITICAL=0
SCAN_HIGH=0
SCAN_MEDIUM=0

if [ "${SKIP_AUDIT}" = "true" ]; then
  echo "   ⏭️  已跳过安全扫描（--skip-audit）。"
  SCAN_PASSED=false
else
  SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
  AUDIT_SCRIPT="${SCRIPT_DIR}/skill_audit.py"

  if [ -f "${AUDIT_SCRIPT}" ] && command -v python3 &>/dev/null; then
    echo "==> 安装前安全扫描..."
    SCAN_OUTPUT=$(python3 "${AUDIT_SCRIPT}" --path "${SKILL_SRC_DIR}" --json --severity medium 2>/dev/null || true)

    if [ -n "${SCAN_OUTPUT}" ]; then
      SCAN_CRITICAL=$(echo "${SCAN_OUTPUT}" | python3 -c "import sys,json; print(json.load(sys.stdin)['summary']['severity_counts'].get('CRITICAL',0))" 2>/dev/null || echo "0")
      SCAN_HIGH=$(echo "${SCAN_OUTPUT}" | python3 -c "import sys,json; print(json.load(sys.stdin)['summary']['severity_counts'].get('HIGH',0))" 2>/dev/null || echo "0")
      SCAN_MEDIUM=$(echo "${SCAN_OUTPUT}" | python3 -c "import sys,json; print(json.load(sys.stdin)['summary']['severity_counts'].get('MEDIUM',0))" 2>/dev/null || echo "0")

      if [ "${SCAN_CRITICAL}" -gt 0 ] 2>/dev/null; then
        echo "🚨 发现 ${SCAN_CRITICAL} 个严重安全风险！"
        echo "${SCAN_OUTPUT}"
        echo ""
        echo "⚠️  建议不要安装。如需继续，请在 AI 对话中确认。"
        exit 10
      elif [ "${SCAN_HIGH}" -gt 0 ] 2>/dev/null; then
        echo "⚠️  发现 ${SCAN_HIGH} 个高风险项，${SCAN_MEDIUM} 个中风险项。"
        echo "${SCAN_OUTPUT}"
        echo ""
        echo "⚠️  建议审查后再安装。如需继续，请在 AI 对话中确认。"
        exit 11
      elif [ "${SCAN_MEDIUM}" -gt 0 ] 2>/dev/null; then
        echo "ℹ️  发现 ${SCAN_MEDIUM} 个中风险项（可能是误报）。"
      else
        echo "   ✅ 扫描通过，未发现安全风险。"
      fi
    else
      echo "   ⏭️  扫描器无输出，跳过安全检查。"
      SCAN_PASSED=false
    fi
  else
    echo "   ⏭️  扫描器不可用（缺少 python3 或 skill_audit.py），跳过安全检查。"
    SCAN_PASSED=false
  fi
fi

# ─── P2: skills.sh audit API（三方安全参考，非阻塞）──────────────────
AUDIT_API_RESULT=""
OWNER_REPO=$(echo "${GITHUB_URL}" | sed -E 's|https?://github\.com/||; s|\.git$||; s|/$||')

if command -v curl &>/dev/null; then
  AUDIT_API_RESULT=$(curl -s --max-time 3 "https://add-skill.vercel.sh/audit?source=${OWNER_REPO}&skills=${SKILL_NAME}" 2>/dev/null || true)
  if [ -n "${AUDIT_API_RESULT}" ] && command -v python3 &>/dev/null; then
    AUDIT_SUMMARY=$(python3 -c "
import json, sys
try:
    data = json.loads('${AUDIT_API_RESULT}'.replace(\"'\", '\"'))
    skill_data = data.get('${SKILL_NAME}', {})
    parts = []
    for partner, info in skill_data.items():
        risk = info.get('risk', 'unknown')
        parts.append(f'{partner}: {risk}')
    if parts:
        print('   🔍 三方审计: ' + ' | '.join(parts))
except Exception:
    pass
" 2>/dev/null || true)
    if [ -n "${AUDIT_SUMMARY}" ]; then
      echo "${AUDIT_SUMMARY}"
    fi
  fi
fi

# ─── 安装文件 ─────────────────────────────────────────────────────────
echo "==> 安装到 ${SKILL_DEST}/ ..."
mkdir -p "${SKILL_DEST}"

if [ "${SKILL_SRC_DIR}" = "${TMPDIR_PATH}/repo" ]; then
  rsync -a --exclude='.git' --exclude='node_modules' --exclude='.github' \
    "${TMPDIR_PATH}/repo/" "${SKILL_DEST}/"
else
  rsync -a "${SKILL_SRC_DIR}/" "${SKILL_DEST}/"
fi

echo "==> 验证安装..."
if [ -f "${SKILL_DEST}/SKILL.md" ]; then
  echo "✅ 安装成功！"
  echo ""
  echo "   位置: ${SKILL_DEST}/"
  echo "   文件:"
  ls -la "${SKILL_DEST}/"
  echo ""
  head -5 "${SKILL_DEST}/SKILL.md"

  # ─── P0: skillFolderHash（GitHub Trees API 精确变更检测）───────────
  FOLDER_HASH=""
  if command -v gh &>/dev/null && [ "${SKILL_DIR_IN_REPO}" != "." ]; then
    FOLDER_HASH=$(gh api "repos/${OWNER_REPO}/git/trees/HEAD?recursive=1" \
      --jq ".tree[] | select(.type==\"tree\" and .path==\"${SKILL_DIR_IN_REPO}\") | .sha" 2>/dev/null || true)
    if [ -n "${FOLDER_HASH}" ]; then
      echo "   🔗 folderHash: ${FOLDER_HASH:0:12}..."
    fi
  fi

  # ─── P3: 本地内容 hash（完整性校验）────────────────────────────────
  LOCAL_HASH=""
  if command -v shasum &>/dev/null; then
    LOCAL_HASH=$(find "${SKILL_DEST}" -type f -not -name '_skill_meta.json' -not -name '_meta.json' | sort | xargs cat 2>/dev/null | shasum -a 256 | cut -d' ' -f1 || true)
  elif command -v sha256sum &>/dev/null; then
    LOCAL_HASH=$(find "${SKILL_DEST}" -type f -not -name '_skill_meta.json' -not -name '_meta.json' | sort | xargs cat 2>/dev/null | sha256sum | cut -d' ' -f1 || true)
  fi

  # ─── 生成 _skill_meta.json（含所有新增字段）─────────────────────────
  INSTALL_TIME=$(date -u +"%Y-%m-%dT%H:%M:%S.000Z")
  SCAN_TIME="${INSTALL_TIME}"

  if command -v python3 &>/dev/null; then
    python3 -c "
import json

meta = {
    'name': '${SKILL_NAME}',
    'version': '${SKILL_VERSION}',
    'source': {
        'type': 'github',
        'repo': '${OWNER_REPO}',
        'path': '${SKILL_DIR_IN_REPO}',
        'branch': 'main',
        'commitHash': '${COMMIT_HASH}',
        'folderHash': '${FOLDER_HASH}' if '${FOLDER_HASH}' else None,
    },
    'channel': '${CHANNEL}',
    'installedAt': '${INSTALL_TIME}',
    'installedVia': 'install_skill.sh',
    'security': {
        'scanned': ${SCAN_PASSED},
        'scannedAt': '${SCAN_TIME}' if ${SCAN_PASSED} else None,
        'findings': {
            'critical': int('${SCAN_CRITICAL}'),
            'high': int('${SCAN_HIGH}'),
            'medium': int('${SCAN_MEDIUM}')
        },
    },
    'integrity': {
        'localHash': '${LOCAL_HASH}' if '${LOCAL_HASH}' else None,
        'computedAt': '${INSTALL_TIME}' if '${LOCAL_HASH}' else None,
    },
    'skillMeta': {
        'description': '''${SKILL_DESCRIPTION}''',
        'tags': ${SKILL_TAGS}
    }
}

# 清理 None 值（递归）
def clean_none(d):
    if isinstance(d, dict):
        return {k: clean_none(v) for k, v in d.items() if v is not None}
    return d

meta = clean_none(meta)
with open('${SKILL_DEST}/_skill_meta.json', 'w') as f:
    json.dump(meta, f, indent=2, ensure_ascii=False)
" 2>/dev/null && echo "   📋 已生成 _skill_meta.json（版本追踪）" || echo "   ⚠️  _skill_meta.json 生成失败，不影响使用"
  else
    cat > "${SKILL_DEST}/_skill_meta.json" << METAEOF
{
  "name": "${SKILL_NAME}",
  "version": "${SKILL_VERSION}",
  "source": {
    "type": "github",
    "repo": "${OWNER_REPO}",
    "commitHash": "${COMMIT_HASH}"
  },
  "channel": "${CHANNEL}",
  "installedAt": "${INSTALL_TIME}",
  "installedVia": "install_skill.sh"
}
METAEOF
    echo "   📋 已生成 _skill_meta.json（简化版）"
  fi

  # ─── P1: 私有仓库检测 + P2: Telemetry 参数对齐 ─────────────────────
  if [ "${NO_TELEMETRY}" = "false" ]; then
    IS_PRIVATE="false"
    if command -v gh &>/dev/null; then
      IS_PRIVATE=$(gh api "repos/${OWNER_REPO}" --jq '.private' 2>/dev/null || echo "unknown")
    fi

    if [ "${IS_PRIVATE}" = "true" ]; then
      echo "   🔒 私有仓库，跳过 telemetry 上报"
    else
      TELEMETRY_URL="https://add-skill.vercel.sh/t"
      SKILL_FILES_JSON="{\"${SKILL_NAME}\":\"${SKILL_PATH_IN_REPO}\"}"
      ENCODED_FILES=$(python3 -c "import urllib.parse; print(urllib.parse.quote('${SKILL_FILES_JSON}'))" 2>/dev/null || echo "")
      TELEMETRY_PARAMS="event=install&source=${OWNER_REPO}&skills=${SKILL_NAME}&agents=cursor&sourceType=github"
      if [ -n "${ENCODED_FILES}" ]; then
        TELEMETRY_PARAMS="${TELEMETRY_PARAMS}&skillFiles=${ENCODED_FILES}"
      fi
      curl -s "${TELEMETRY_URL}?${TELEMETRY_PARAMS}" >/dev/null 2>&1 &
      echo "   📊 已通知 skills.sh 统计安装量"
    fi
  fi
else
  echo "❌ 安装验证失败 — SKILL.md 未找到"
  exit 1
fi
