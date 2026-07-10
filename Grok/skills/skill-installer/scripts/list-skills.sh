#!/usr/bin/env bash
# List skills from a GitHub repository.
#
# Usage:
#   list-skills.sh [--repo owner/repo] [--path skills-dir] [--ref branch]
#
# Examples:
#   list-skills.sh
#   list-skills.sh --repo xai-org/skills --path skills/.curated
#   list-skills.sh --repo myorg/my-skills --path skills

set -euo pipefail

REPO="xai-org/skills"
SKILLS_PATH="skills/.curated"
REF="main"
SKILLS_HOME="${GROK_SKILLS_HOME:-.grok/skills}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo) REPO="$2"; shift 2 ;;
    --path) SKILLS_PATH="$2"; shift 2 ;;
    --ref)  REF="$2"; shift 2 ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

# Build auth header if token is available
AUTH_HEADER=""
TOKEN="${GITHUB_TOKEN:-${GH_TOKEN:-}}"
if [[ -n "$TOKEN" ]]; then
  AUTH_HEADER="Authorization: token $TOKEN"
fi

API_URL="https://api.github.com/repos/${REPO}/contents/${SKILLS_PATH}?ref=${REF}"

# Fetch directory listing
RESPONSE=$(curl -sS -f \
  -H "User-Agent: grok-computer-skill-installer" \
  ${AUTH_HEADER:+-H "$AUTH_HEADER"} \
  "$API_URL" 2>&1) || {
  echo "Error: Failed to fetch skills from $API_URL" >&2
  echo "  Make sure the repo and path exist and are accessible." >&2
  exit 1
}

# Parse directory names from JSON response (requires no dependencies beyond curl)
SKILLS=$(echo "$RESPONSE" | grep '"name"' | sed 's/.*"name": *"\([^"]*\)".*/\1/' | sort)

if [[ -z "$SKILLS" ]]; then
  echo "No skills found at ${REPO}/${SKILLS_PATH} (ref: ${REF})"
  exit 0
fi

# List with installed annotations
INDEX=1
while IFS= read -r NAME; do
  if [[ -d "$SKILLS_HOME/$NAME" ]]; then
    echo "${INDEX}. ${NAME} (already installed)"
  else
    echo "${INDEX}. ${NAME}"
  fi
  INDEX=$((INDEX + 1))
done <<< "$SKILLS"
