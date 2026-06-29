#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="."
if [[ "${1:-}" == "--project-root" ]]; then
  PROJECT_ROOT="$2"
  shift 2
fi

COMMAND="${1:-read}"
shift || true

PROJECT_ROOT_ABS="$(cd "$PROJECT_ROOT" && pwd)"
SESSION_FILE="$PROJECT_ROOT_ABS/.backend-forge/session.md"

ensure_dir() {
  mkdir -p "$(dirname "$SESSION_FILE")"
}

write_session() {
  local phase="$1" mode="$2" policy="$3"
  ensure_dir
  cat > "$SESSION_FILE" <<EOF
- 当前阶段：${phase}
- 当前模式：${mode}
- 执行策略：${policy}
- 目标状态：未确认
- 架构状态：未确认
- 数据影响状态：未确认
- 安全边界状态：未确认
- 测试闭环状态：未确认
- 当前子单元：-
- 子单元状态：未冻结
- 验证状态：未验证
- 改动契约：-
- 确认状态：未确认
EOF
}

update_field() {
  local label="$1" value="$2"
  ensure_dir
  if [[ ! -f "$SESSION_FILE" ]]; then
    write_session "S0" "API/功能开发" "标准"
  fi
  if grep -q "^- ${label}：" "$SESSION_FILE"; then
    python3 - "$SESSION_FILE" "$label" "$value" <<'PY'
from pathlib import Path
import sys
path = Path(sys.argv[1])
label = sys.argv[2]
value = sys.argv[3]
lines = path.read_text(encoding="utf-8").splitlines()
for index, line in enumerate(lines):
    if line.startswith(f"- {label}："):
        lines[index] = f"- {label}：{value}"
        break
path.write_text("\n".join(lines) + "\n", encoding="utf-8")
PY
  else
    printf -- '- %s：%s\n' "$label" "$value" >> "$SESSION_FILE"
  fi
}

case "$COMMAND" in
  init)
    phase="S0"
    mode="API/功能开发"
    policy="标准"
    while [[ $# -gt 0 ]]; do
      case "$1" in
        --phase) phase="$2"; shift 2 ;;
        --mode) mode="$2"; shift 2 ;;
        --policy) policy="$2"; shift 2 ;;
        *) shift ;;
      esac
    done
    write_session "$phase" "$mode" "$policy"
    printf '{"status":"initialized","path":"%s"}\n' "$SESSION_FILE"
    ;;
  update)
    while [[ $# -gt 0 ]]; do
      case "$1" in
        --phase) update_field "当前阶段" "$2"; shift 2 ;;
        --mode) update_field "当前模式" "$2"; shift 2 ;;
        --policy) update_field "执行策略" "$2"; shift 2 ;;
        --goal_status) update_field "目标状态" "$2"; shift 2 ;;
        --architecture_status) update_field "架构状态" "$2"; shift 2 ;;
        --data_status) update_field "数据影响状态" "$2"; shift 2 ;;
        --security_status) update_field "安全边界状态" "$2"; shift 2 ;;
        --test_status) update_field "测试闭环状态" "$2"; shift 2 ;;
        --current_work_unit) update_field "当前子单元" "$2"; shift 2 ;;
        --work_unit_status) update_field "子单元状态" "$2"; shift 2 ;;
        --verification_status) update_field "验证状态" "$2"; shift 2 ;;
        --change_contract) update_field "改动契约" "$2"; shift 2 ;;
        --confirmation_status) update_field "确认状态" "$2"; shift 2 ;;
        *) shift ;;
      esac
    done
    printf '{"status":"updated","path":"%s"}\n' "$SESSION_FILE"
    ;;
  read)
    [[ -f "$SESSION_FILE" ]] && cat "$SESSION_FILE" || true
    ;;
  reset)
    rm -f "$SESSION_FILE"
    printf '{"status":"reset"}\n'
    ;;
  validate)
    [[ -f "$SESSION_FILE" ]] || { echo "FAIL missing session" >&2; exit 1; }
    grep -q '^- 当前阶段：' "$SESSION_FILE" || { echo "FAIL missing phase" >&2; exit 1; }
    grep -q '^- 当前模式：' "$SESSION_FILE" || { echo "FAIL missing mode" >&2; exit 1; }
    printf '{"status":"valid","path":"%s"}\n' "$SESSION_FILE"
    ;;
  *)
    echo "Usage: bf_session.sh {read|init|update|reset|validate}" >&2
    exit 2
    ;;
esac
