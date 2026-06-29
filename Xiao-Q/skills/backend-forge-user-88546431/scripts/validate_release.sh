#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

fail() {
  printf 'FAIL %s\n' "$1" >&2
  exit 1
}

info() {
  printf 'PASS %s\n' "$1"
}

version="$(tr -d '[:space:]' < VERSION)"
grep -q "^## ${version}$" CHANGELOG.md || fail "CHANGELOG.md has no section for $version"
info "version metadata is consistent: $version"

tmp_empty="$(mktemp -d -t backend-forge-empty.XXXXXX)"
python3 scripts/detect_project_root_state.py "$tmp_empty" | grep -q '"root_type": "empty_new"' || fail "empty project detection failed"
rm -rf "$tmp_empty"

tmp_spring="$(mktemp -d -t backend-forge-spring.XXXXXX)"
cat > "$tmp_spring/pom.xml" <<'EOF'
<project><dependencies><dependency><groupId>org.springframework.boot</groupId><artifactId>spring-boot-starter-web</artifactId></dependency></dependencies></project>
EOF
python3 scripts/detect_project_root_state.py "$tmp_spring" | grep -q '"root_type": "spring_boot_existing"' || fail "Spring Boot detection failed"
rm -rf "$tmp_spring"

tmp_fastapi="$(mktemp -d -t backend-forge-fastapi.XXXXXX)"
printf 'fastapi\n' > "$tmp_fastapi/requirements.txt"
python3 scripts/detect_project_root_state.py "$tmp_fastapi" | grep -q '"root_type": "fastapi_existing"' || fail "FastAPI detection failed"
rm -rf "$tmp_fastapi"

tmp_django="$(mktemp -d -t backend-forge-django.XXXXXX)"
touch "$tmp_django/manage.py"
python3 scripts/detect_project_root_state.py "$tmp_django" | grep -q '"root_type": "django_existing"' || fail "Django detection failed"
rm -rf "$tmp_django"

python3 scripts/route_golden_tests.py
python3 scripts/validate_release_bindings.py

tmp_gate="$(mktemp -d -t backend-forge-gate.XXXXXX)"
if python3 scripts/gate_check.py --project-root "$tmp_gate" --target-path src/main.py >/dev/null 2>&1; then
  rm -rf "$tmp_gate"
  fail "gate_check allowed implementation write without session"
fi
scripts/bf_session.sh --project-root "$tmp_gate" init --phase S4 --mode "API/功能开发" --policy "标准" >/dev/null
scripts/bf_session.sh --project-root "$tmp_gate" update \
  --goal_status 已确认 \
  --architecture_status 已确认 \
  --data_status 已确认 \
  --security_status 已确认 \
  --test_status 已确认 \
  --current_work_unit "订单接口" \
  --work_unit_status 已冻结 \
  --change_contract "允许修改订单查询 API，不改认证模型" \
  --confirmation_status 用户已确认 >/dev/null
python3 scripts/gate_check.py --project-root "$tmp_gate" --target-path src/main.py | grep -q '"decision": "allow"' || fail "gate_check did not allow confirmed S4 write"
scripts/bf_session.sh --project-root "$tmp_gate" validate >/dev/null
rm -rf "$tmp_gate"
info "session and gate validation passed"

printf '[backend-forge] 进入 controller\n[backend-forge] 模式：API/功能开发\n[backend-forge] 阶段：S5 验证\n[backend-forge] 本轮完成：订单接口测试通过\n' \
  | bash scripts/validate_output.sh --require-complete >/dev/null
if printf '模式：API/功能开发\n' | bash scripts/validate_output.sh >/dev/null 2>&1; then
  fail "validate_output accepted bare mode log"
fi
info "output protocol validation passed"

info "release validation completed"
