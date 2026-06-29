#!/usr/bin/env bash
set -euo pipefail

REQUIRE_COMPLETE=false
if [[ "${1:-}" == "--require-complete" ]]; then
  REQUIRE_COMPLETE=true
fi

TEXT="$(cat)"

fail() {
  printf 'FAIL %s\n' "$1" >&2
  exit 1
}

grep -q '\[backend-forge\]' <<<"$TEXT" || fail "missing [backend-forge] status line"
grep -q '\[backend-forge\] 进入 controller' <<<"$TEXT" || fail "missing entry log"

if "$REQUIRE_COMPLETE"; then
  grep -q '\[backend-forge\] 本轮完成：' <<<"$TEXT" || fail "missing completion log"
fi

if grep -Eq '^\s*(模式|阶段|本轮完成)[:：]' <<<"$TEXT"; then
  fail "bare workflow log without [backend-forge] prefix"
fi

printf 'PASS backend output protocol validated\n'
