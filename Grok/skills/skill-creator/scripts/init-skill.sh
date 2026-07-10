#!/usr/bin/env bash
# Initialize a new skill directory with a SKILL.md template.
#
# Usage:
#   init-skill.sh <skill-name> <output-directory> [--resources scripts,references,assets]
#
# Examples:
#   init-skill.sh my-skill .grok/skills
#   init-skill.sh api-helper .grok/skills --resources scripts,references

set -euo pipefail

die() { echo "[ERROR] $*" >&2; exit 1; }

# --- Parse arguments ---
[[ $# -lt 2 ]] && die "Usage: init-skill.sh <skill-name> <output-directory> [--resources scripts,references,assets]"

RAW_NAME="$1"
OUTPUT_DIR="$2"
RESOURCES=""

shift 2
while [[ $# -gt 0 ]]; do
  case "$1" in
    --resources) RESOURCES="$2"; shift 2 ;;
    *) die "Unknown option: $1" ;;
  esac
done

# --- Normalize name ---
NAME=$(echo "$RAW_NAME" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g; s/--*/-/g; s/^-//; s/-$//')
[[ -z "$NAME" ]] && die "Skill name must include at least one letter or digit."
[[ ${#NAME} -lt 2 ]] && die "Skill name too short (${#NAME} char, min 2)."
[[ ${#NAME} -gt 64 ]] && die "Skill name too long (${#NAME} chars, max 64)."
[[ "$NAME" != "$RAW_NAME" ]] && echo "Note: Normalized skill name to '$NAME'."

SKILL_DIR="$OUTPUT_DIR/$NAME"
[[ -d "$SKILL_DIR" ]] && die "Directory already exists: $SKILL_DIR"

# --- Create skill directory ---
mkdir -p "$SKILL_DIR"
echo "[OK] Created $SKILL_DIR"

# --- Create SKILL.md ---
TITLE=$(echo "$NAME" | sed 's/-/ /g' | awk '{for(i=1;i<=NF;i++) $i=toupper(substr($i,1,1)) substr($i,2)}1')

cat > "$SKILL_DIR/SKILL.md" << TEMPLATE
---
name: $NAME
description: TODO — describe what this skill does and when to use it. Include trigger words and scenarios. Write as a plain YAML scalar (no quotes, no ': ', no angle brackets).
---

# $TITLE

## Overview

TODO — 1-2 sentences explaining what this skill enables.

## Instructions

TODO — write concise, imperative instructions. Only include what the model doesn't already know.
TEMPLATE

echo "[OK] Created SKILL.md"

# --- Create resource directories ---
if [[ -n "$RESOURCES" ]]; then
  IFS=',' read -ra DIRS <<< "$RESOURCES"
  for DIR in "${DIRS[@]}"; do
    DIR=$(echo "$DIR" | tr -d ' ')
    case "$DIR" in
      scripts|references|assets)
        mkdir -p "$SKILL_DIR/$DIR"
        echo "[OK] Created $DIR/"
        ;;
      *) echo "[WARN] Skipping unknown resource type: $DIR" ;;
    esac
  done
fi

echo ""
echo "[OK] Skill '$NAME' initialized at $SKILL_DIR"
echo ""
echo "Next steps:"
echo "  1. Edit SKILL.md — write the description and instructions"
echo "  2. Add resources to scripts/, references/, assets/ as needed"
echo "  3. Run validate-skill.sh to check the structure"
