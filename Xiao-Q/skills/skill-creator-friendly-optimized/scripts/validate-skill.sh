#!/usr/bin/env bash
set -u

ROOT_DIR="${1:-.}"
REPORT_DIR="${2:-reports}"
ZIP_FILE="${3:-}"
JSON_REPORT="$REPORT_DIR/qa-report.json"
MD_REPORT="$REPORT_DIR/qa-report.md"
TMP_MATCH="$REPORT_DIR/validate-match.tmp"

PASS_COUNT=0
FAIL_COUNT=0
WARN_COUNT=0
RESULTS=""

mkdir -p "$REPORT_DIR"

json_escape() {
  printf '%s' "$1" | sed 's/\\/\\\\/g; s/"/\\"/g; s/\t/\\t/g'
}

add_result() {
  local status="$1"
  local check="$2"
  local message="$3"
  local escaped_check
  local escaped_message
  escaped_check=$(json_escape "$check")
  escaped_message=$(json_escape "$message")
  if [ "$status" = "PASS" ]; then
    PASS_COUNT=$((PASS_COUNT + 1))
  elif [ "$status" = "WARN" ]; then
    WARN_COUNT=$((WARN_COUNT + 1))
  else
    FAIL_COUNT=$((FAIL_COUNT + 1))
  fi
  RESULTS="$RESULTS
    {\"status\":\"$status\",\"check\":\"$escaped_check\",\"message\":\"$escaped_message\"},"
}

check_file_exists() {
  local file="$1"
  if [ -s "$ROOT_DIR/$file" ]; then
    add_result "PASS" "file:$file" "required file exists and is non-empty"
  else
    add_result "FAIL" "file:$file" "required file is missing or empty"
  fi
}

check_contains() {
  local file="$1"
  local pattern="$2"
  local label="$3"
  if [ -f "$ROOT_DIR/$file" ] && grep -Eq "$pattern" "$ROOT_DIR/$file"; then
    add_result "PASS" "$label" "pattern found in $file"
  else
    add_result "FAIL" "$label" "pattern not found in $file"
  fi
}

check_no_pattern() {
  local pattern="$1"
  local label="$2"
  : > "$TMP_MATCH"
  if find "$ROOT_DIR" -type f \
    -not -path "*/scripts/*" \
    -not -path "*/reports/*" \
    -not -path "*/.git/*" \
    -print0 | xargs -0 grep -IE "$pattern" > "$TMP_MATCH" 2>/dev/null; then
    local sample
    sample=$(head -5 "$TMP_MATCH" | tr '\n' '; ')
    add_result "FAIL" "$label" "unexpected pattern found: $sample"
  else
    add_result "PASS" "$label" "unexpected pattern not found"
  fi
}

check_front_matter() {
  local file="$ROOT_DIR/SKILL.md"
  if [ ! -f "$file" ]; then
    add_result "FAIL" "front_matter:exists" "SKILL.md missing"
    return
  fi
  if [ "$(sed -n '1p' "$file")" = "---" ] && sed -n '2,40p' "$file" | grep -q '^---$'; then
    add_result "PASS" "front_matter:block" "YAML front matter block exists"
  else
    add_result "FAIL" "front_matter:block" "YAML front matter block missing"
  fi
  for field in name description; do
    if sed -n '1,40p' "$file" | grep -Eq "^$field:[[:space:]]*.+"; then
      add_result "PASS" "front_matter:$field" "$field exists"
    else
      add_result "FAIL" "front_matter:$field" "$field missing or empty"
    fi
  done
}

check_zip_root() {
  local zip_file="$1"
  if [ -z "$zip_file" ]; then
    add_result "WARN" "zip:provided" "zip file not provided; skipped zip root check"
    return
  fi
  if [ ! -f "$zip_file" ]; then
    add_result "FAIL" "zip:exists" "zip file does not exist: $zip_file"
    return
  fi
  if unzip -t "$zip_file" >/dev/null 2>&1; then
    add_result "PASS" "zip:integrity" "zip integrity test passed"
  else
    add_result "FAIL" "zip:integrity" "zip integrity test failed"
  fi
  if unzip -l "$zip_file" | awk '{print $4}' | grep -Eq '^[^/]+/SKILL\.md$'; then
    add_result "PASS" "zip:root_skill" "zip contains root skill directory with SKILL.md"
  else
    add_result "FAIL" "zip:root_skill" "zip does not contain expected root skill directory with SKILL.md"
  fi
}

check_file_exists "SKILL.md"
check_file_exists "AGENTS.md"
check_file_exists "README.md"
check_file_exists "package.json"
check_file_exists "examples/usage.md"
check_file_exists "references/workflow.md"
check_file_exists "references/qa-checklist.md"
check_file_exists "references/error-handling.md"
check_file_exists "references/progress-template.md"
check_front_matter
check_contains "SKILL.md" "输入诊断|需求诊断" "capability:input_diagnosis"
check_contains "SKILL.md" "YAML front matter" "capability:front_matter"
check_contains "SKILL.md" "自纠错|自动纠错" "capability:self_healing"
check_contains "SKILL.md" "质量门禁|QA" "capability:qa_gate"
check_contains "SKILL.md" "进度保存|恢复" "capability:progress_recovery"
check_contains "references/qa-checklist.md" "质量门禁" "reference:qa_checklist"
check_contains "references/error-handling.md" "异常处理|自纠错" "reference:error_handling"
check_contains "references/progress-template.md" "当前阶段|恢复" "reference:progress_template"
check_no_pattern "Full tool-call argument omitted|TODO_PLACEHOLDER|待补充" "content:no_placeholders"

EMPTY_FILES=$(find "$ROOT_DIR" -type f -size 0 -not -path "*/.git/*" -not -path "*/reports/*" | sed 's#^./##' | tr '\n' '; ')
if [ -n "$EMPTY_FILES" ]; then
  add_result "FAIL" "content:no_empty_files" "empty files found: $EMPTY_FILES"
else
  add_result "PASS" "content:no_empty_files" "no empty files found"
fi

if [ -n "$ZIP_FILE" ]; then
  check_zip_root "$ZIP_FILE"
fi

STATUS="PASS"
if [ "$FAIL_COUNT" -gt 0 ]; then
  STATUS="FAIL"
elif [ "$WARN_COUNT" -gt 0 ]; then
  STATUS="WARN"
fi

RESULTS="${RESULTS%,}"
cat > "$JSON_REPORT" <<JSON
{
  "status": "$STATUS",
  "summary": {
    "pass": $PASS_COUNT,
    "warn": $WARN_COUNT,
    "fail": $FAIL_COUNT
  },
  "root_dir": "$(json_escape "$ROOT_DIR")",
  "zip_file": "$(json_escape "$ZIP_FILE")",
  "checks": [$RESULTS
  ]
}
JSON

cat > "$MD_REPORT" <<MD
# Skill QA Report

## Summary

- Status: $STATUS
- Pass: $PASS_COUNT
- Warn: $WARN_COUNT
- Fail: $FAIL_COUNT
- Root: $ROOT_DIR
- Zip: ${ZIP_FILE:-not provided}

## Checks

MD

printf '%s
' "$RESULTS" | sed 's/^[[:space:]]*{//; s/},*$//' | while IFS= read -r line; do
  [ -z "$line" ] && continue
  status=$(printf '%s' "$line" | sed -n 's/.*"status":"\([^"]*\)".*/\1/p')
  check=$(printf '%s' "$line" | sed -n 's/.*"check":"\([^"]*\)".*/\1/p')
  message=$(printf '%s' "$line" | sed -n 's/.*"message":"\([^"]*\)".*/\1/p')
  printf -- '- **%s** `%s`: %s
' "$status" "$check" "$message" >> "$MD_REPORT"
done

if [ "$FAIL_COUNT" -gt 0 ]; then
  exit 1
fi
exit 0
