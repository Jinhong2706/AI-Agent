#!/usr/bin/env bash
# Install a skill from a GitHub repository.
#
# Usage:
#   install-skill.sh --repo owner/repo --path path/to/skill [--ref branch] [--dest dir] [--name name]
#   install-skill.sh --url https://github.com/owner/repo/tree/ref/path/to/skill [--dest dir]
#
# Examples:
#   install-skill.sh --repo xai-org/skills --path skills/.curated/pdf
#   install-skill.sh --url https://github.com/xai-org/skills/tree/main/skills/.curated/pdf
#   install-skill.sh --repo myorg/skills --path my-skill --dest .grok/skills

set -euo pipefail

die() { echo "Error: $*" >&2; exit 1; }

REPO=""
SKILL_PATH=""
REF="main"
DEST="${GROK_SKILLS_HOME:-.grok/skills}"
NAME=""
URL=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo) REPO="$2"; shift 2 ;;
    --path) SKILL_PATH="$2"; shift 2 ;;
    --ref)  REF="$2"; shift 2 ;;
    --dest) DEST="$2"; shift 2 ;;
    --name) NAME="$2"; shift 2 ;;
    --url)  URL="$2"; shift 2 ;;
    *) die "Unknown option: $1" ;;
  esac
done

# --- Parse URL if provided ---
if [[ -n "$URL" ]]; then
  # Extract owner/repo/ref/path from GitHub URL
  # Format: https://github.com/owner/repo/tree/ref/path/to/skill
  URL_PATH="${URL#https://github.com/}"
  IFS='/' read -ra PARTS <<< "$URL_PATH"
  [[ ${#PARTS[@]} -lt 2 ]] && die "Invalid GitHub URL"
  REPO="${PARTS[0]}/${PARTS[1]}"
  if [[ ${#PARTS[@]} -ge 5 && "${PARTS[2]}" == "tree" ]]; then
    REF="${PARTS[3]}"
    SKILL_PATH=$(IFS='/'; echo "${PARTS[*]:4}")
  elif [[ ${#PARTS[@]} -ge 3 ]]; then
    SKILL_PATH=$(IFS='/'; echo "${PARTS[*]:2}")
  fi
fi

[[ -z "$REPO" ]] && die "Missing --repo or --url"
[[ -z "$SKILL_PATH" ]] && die "Missing --path"

# Derive skill name from path basename
if [[ -z "$NAME" ]]; then
  NAME=$(basename "$SKILL_PATH")
fi
[[ -z "$NAME" ]] && die "Could not determine skill name"

DEST_DIR="$DEST/$NAME"
[[ -d "$DEST_DIR" ]] && die "Destination already exists: $DEST_DIR"

# Build auth header
AUTH_HEADER=""
TOKEN="${GITHUB_TOKEN:-${GH_TOKEN:-}}"
if [[ -n "$TOKEN" ]]; then
  AUTH_HEADER="Authorization: token $TOKEN"
fi

TMP_DIR=$(mktemp -d)
trap 'rm -rf "$TMP_DIR"' EXIT

# --- Try zip download first (works for public repos) ---
download_zip() {
  local ZIP_URL="https://codeload.github.com/${REPO}/zip/${REF}"
  local ZIP_FILE="$TMP_DIR/repo.zip"

  echo "Downloading ${REPO}@${REF}..."
  if curl -sS -f -L \
    -H "User-Agent: grok-computer-skill-installer" \
    ${AUTH_HEADER:+-H "$AUTH_HEADER"} \
    -o "$ZIP_FILE" "$ZIP_URL" 2>/dev/null; then

    # Extract
    unzip -q "$ZIP_FILE" -d "$TMP_DIR"

    # Find the extracted root (GitHub zips have a top-level dir like repo-ref/)
    local EXTRACTED_ROOT
    EXTRACTED_ROOT=$(find "$TMP_DIR" -mindepth 1 -maxdepth 1 -type d ! -name "__MACOSX" | head -1)
    [[ -z "$EXTRACTED_ROOT" ]] && return 1

    local SKILL_SRC="$EXTRACTED_ROOT/$SKILL_PATH"
    [[ -d "$SKILL_SRC" ]] || { echo "Skill path not found in archive: $SKILL_PATH" >&2; return 1; }
    [[ -f "$SKILL_SRC/SKILL.md" ]] || { echo "No SKILL.md found in $SKILL_PATH" >&2; return 1; }

    mkdir -p "$(dirname "$DEST_DIR")"
    cp -R "$SKILL_SRC" "$DEST_DIR"
    return 0
  fi
  return 1
}

# --- Fallback: git sparse checkout (works for private repos) ---
git_checkout() {
  local REPO_URL="https://github.com/${REPO}.git"
  local REPO_DIR="$TMP_DIR/repo"

  echo "Trying git sparse checkout..."

  # Try HTTPS first, then SSH
  if ! git clone --filter=blob:none --depth 1 --sparse --single-branch \
    --branch "$REF" "$REPO_URL" "$REPO_DIR" 2>/dev/null; then
    REPO_URL="git@github.com:${REPO}.git"
    git clone --filter=blob:none --depth 1 --sparse --single-branch \
      --branch "$REF" "$REPO_URL" "$REPO_DIR" || die "Failed to clone repository"
  fi

  git -C "$REPO_DIR" sparse-checkout set "$SKILL_PATH"
  git -C "$REPO_DIR" checkout "$REF" 2>/dev/null || true

  local SKILL_SRC="$REPO_DIR/$SKILL_PATH"
  [[ -d "$SKILL_SRC" ]] || die "Skill path not found: $SKILL_PATH"
  [[ -f "$SKILL_SRC/SKILL.md" ]] || die "No SKILL.md found in $SKILL_PATH"

  mkdir -p "$(dirname "$DEST_DIR")"
  cp -R "$SKILL_SRC" "$DEST_DIR"
}

# --- Install ---
if download_zip; then
  echo "Installed $NAME to $DEST_DIR"
elif git_checkout; then
  echo "Installed $NAME to $DEST_DIR"
else
  die "Failed to download skill from $REPO"
fi
